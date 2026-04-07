import ipaddress
import socket
import time
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlparse

from pydantic import BaseModel
from surreal_commands import CommandInput, CommandOutput, command

from packages.core.application.command_service import (
    RETRY_POLICY_DEEP_QUEUE,
    RETRY_POLICY_TRANSACTIONAL,
    CommandService,
)
from packages.core.database.repository import ensure_record_id
from packages.core.domain.notebook import Source
from packages.core.domain.transformation import Transformation
from packages.core.exceptions import ConfigurationError
from packages.core.observability import bind_observability_context
from packages.core.observability.logger import logger

try:
    from packages.core.graphs.source import source_graph
    from packages.core.graphs.transformation import graph as transform_graph
except ImportError as e:
    logger.error(f"Failed to import graphs: {e}")
    raise ValueError("graphs not available")


_ALLOWED_SOURCE_LINK_SCHEMES = {"http", "https"}
_BLOCKED_SOURCE_HOSTNAMES = {
    "localhost",
    "metadata",
    "metadata.google.internal",
    "instance-data",
    "instance-data.ec2.internal",
}
_BLOCKED_SOURCE_HOSTNAME_SUFFIXES = (
    ".localhost",
    ".local",
    ".localdomain",
    ".internal",
    ".lan",
    ".home",
)
_BLOCKED_METADATA_IPS = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("169.254.170.2"),
    ipaddress.ip_address("100.100.100.200"),
}


def _is_disallowed_source_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if ip in _BLOCKED_METADATA_IPS:
        return True
    if (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_unspecified
        or ip.is_reserved
    ):
        return True
    ipv4_mapped = getattr(ip, "ipv4_mapped", None)
    if ipv4_mapped and _is_disallowed_source_ip(ipv4_mapped):
        return True
    return False


def validate_source_link_url(url: str) -> str:
    normalized_url = url.strip()
    parsed = urlparse(normalized_url)
    scheme = parsed.scheme.lower()
    if scheme not in _ALLOWED_SOURCE_LINK_SCHEMES:
        raise ValueError("Invalid link URL scheme. Only http and https are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid link URL: hostname could not be determined.")

    normalized_host = hostname.rstrip(".").lower()
    if normalized_host in _BLOCKED_SOURCE_HOSTNAMES or normalized_host.endswith(
        _BLOCKED_SOURCE_HOSTNAME_SUFFIXES
    ):
        raise ValueError("Link URL targets a blocked local/metadata hostname.")

    try:
        ip = ipaddress.ip_address(normalized_host)
    except ValueError:
        try:
            resolved = socket.getaddrinfo(normalized_host, None)
        except socket.gaierror as exc:
            raise ValueError(
                "Link URL hostname could not be resolved for SSRF validation."
            ) from exc

        resolved_ip_count = 0
        for _family, _socktype, _proto, _canonname, sockaddr in resolved:
            candidate = sockaddr[0]
            try:
                resolved_ip = ipaddress.ip_address(candidate)
            except ValueError:
                continue
            resolved_ip_count += 1
            if _is_disallowed_source_ip(resolved_ip):
                raise ValueError(
                    "Link URL resolves to a blocked loopback/private/link-local/"
                    "metadata address."
                )
        if resolved_ip_count == 0:
            raise ValueError(
                "Link URL hostname did not resolve to an IP address for SSRF validation."
            )
        return normalized_url

    if _is_disallowed_source_ip(ip):
        raise ValueError(
            "Link URL targets a blocked loopback/private/link-local/metadata address."
        )

    return normalized_url


def full_model_dump(model):
    if isinstance(model, BaseModel):
        return model.model_dump()
    elif isinstance(model, dict):
        return {k: full_model_dump(v) for k, v in model.items()}
    elif isinstance(model, list):
        return [full_model_dump(item) for item in model]
    else:
        return model


def _retry_policy(max_attempts: int, wait_max: int) -> Dict[str, object]:
    base = dict(RETRY_POLICY_TRANSACTIONAL)
    if max_attempts > 5:
        base = dict(RETRY_POLICY_DEEP_QUEUE)
    base.update(
        {
            "max_attempts": max_attempts,
            "wait_max": wait_max,
            "stop_on": [ValueError, ConfigurationError],
        }
    )
    return base


async def _record_command_failure(
    input_data: CommandInput,
    *,
    command_name: str,
    error_message: str,
) -> None:
    if not input_data.execution_context:
        return
    await CommandService.record_command_failure_event(
        str(input_data.execution_context.command_id),
        app="open_notebook",
        name=command_name,
        error_message=error_message,
    )


class SourceProcessingInput(CommandInput):
    source_id: str
    content_state: Dict[str, Any]
    notebook_ids: List[str]
    transformations: List[str]
    embed: bool


class SourceProcessingOutput(CommandOutput):
    success: bool
    source_id: str
    embedded_chunks: int = 0
    insights_created: int = 0
    processing_time: float
    error_message: Optional[str] = None


@command(
    "process_source",
    app="open_notebook",
    retry=_retry_policy(max_attempts=15, wait_max=120),
)
async def process_source_command(
    input_data: SourceProcessingInput,
) -> SourceProcessingOutput:
    """
    Process source content using the source_graph workflow
    """
    start_time = time.time()
    command_id = (
        str(input_data.execution_context.command_id)
        if input_data.execution_context
        else "unknown"
    )

    with bind_observability_context(
        command_id=command_id,
        job_kind="process_source",
    ):
        try:
            raw_url = input_data.content_state.get("url")
            if raw_url is not None:
                if not isinstance(raw_url, str):
                    raise ValueError("Invalid link URL: expected string value.")
                input_data.content_state["url"] = validate_source_link_url(raw_url)

            logger.info(
                f"Starting source processing for source: {input_data.source_id}"
            )
            logger.info(f"Notebook IDs: {input_data.notebook_ids}")
            logger.info(f"Transformations: {input_data.transformations}")
            logger.info(f"Embed: {input_data.embed}")

            transformations = []
            for trans_id in input_data.transformations:
                logger.info(f"Loading transformation: {trans_id}")
                transformation = await Transformation.get(trans_id)
                if not transformation:
                    raise ValueError(f"Transformation '{trans_id}' not found")
                transformations.append(transformation)

            logger.info(f"Loaded {len(transformations)} transformations")

            source = await Source.get(input_data.source_id)
            if not source:
                raise ValueError(f"Source '{input_data.source_id}' not found")

            source.command = (
                ensure_record_id(input_data.execution_context.command_id)
                if input_data.execution_context
                else None
            )
            await source.save()

            logger.info(f"Updated source {source.id} with command reference")
            logger.info(
                f"Processing source with {len(input_data.notebook_ids)} notebooks"
            )

            graph = cast(Any, source_graph)
            result = cast(
                Dict[str, Any],
                await graph.ainvoke(
                    {
                        "content_state": input_data.content_state,
                        "notebook_ids": input_data.notebook_ids,
                        "apply_transformations": transformations,
                        "embed": input_data.embed,
                        "source_id": input_data.source_id,
                    }
                ),
            )

            processed_source = result["source"]
            insights_list = await processed_source.get_insights()
            insights_created = len(insights_list)

            processing_time = time.time() - start_time
            embed_status = "submitted" if input_data.embed else "skipped"
            logger.info(
                f"Successfully processed source: {processed_source.id} in {processing_time:.2f}s"
            )
            logger.info(
                f"Created {insights_created} insights, embedding {embed_status}"
            )

            return SourceProcessingOutput(
                success=True,
                source_id=str(processed_source.id),
                embedded_chunks=0,
                insights_created=insights_created,
                processing_time=processing_time,
            )

        except ValueError as e:
            # Validation errors are permanent failures - don't retry
            processing_time = time.time() - start_time
            logger.error(f"Source processing failed: {e}")
            await _record_command_failure(
                input_data,
                command_name="process_source",
                error_message=str(e),
            )
            return SourceProcessingOutput(
                success=False,
                source_id=input_data.source_id,
                processing_time=processing_time,
                error_message=str(e),
            )
        except Exception as e:
            # Transient failure - will be retried (surreal-commands logs final failure)
            logger.debug(
                f"Transient error processing source {input_data.source_id}: {e}"
            )
            raise


# =============================================================================
# RUN TRANSFORMATION COMMAND
# =============================================================================


class RunTransformationInput(CommandInput):
    """Input for running a transformation on an existing source."""

    source_id: str
    transformation_id: str


class RunTransformationOutput(CommandOutput):
    """Output from transformation command."""

    success: bool
    source_id: str
    transformation_id: str
    processing_time: float
    error_message: Optional[str] = None


@command(
    "run_transformation",
    app="open_notebook",
    retry=_retry_policy(max_attempts=5, wait_max=60),
)
async def run_transformation_command(
    input_data: RunTransformationInput,
) -> RunTransformationOutput:
    """
    Run a transformation on an existing source to generate an insight.

    This command runs the transformation graph which:
    1. Loads the source and transformation
    2. Calls the LLM to generate insight content
    3. Creates the insight via create_insight command (fire-and-forget)

    Use this command for UI-triggered insight generation to avoid blocking
    the HTTP request while the LLM processes.

    Retry Strategy:
    - Retries up to 5 times for transient failures (network, timeout, etc.)
    - Uses exponential-jitter backoff (1-60s)
    - Does NOT retry permanent failures (ValueError for validation errors)
    """
    start_time = time.time()
    command_id = (
        str(input_data.execution_context.command_id)
        if input_data.execution_context
        else "unknown"
    )

    with bind_observability_context(
        command_id=command_id,
        job_kind="run_transformation",
    ):
        try:
            logger.info(
                f"Running transformation {input_data.transformation_id} "
                f"on source {input_data.source_id}"
            )

            source = await Source.get(input_data.source_id)
            if not source:
                raise ValueError(f"Source '{input_data.source_id}' not found")

            transformation = await Transformation.get(input_data.transformation_id)
            if not transformation:
                raise ValueError(
                    f"Transformation '{input_data.transformation_id}' not found"
                )

            await transform_graph.ainvoke(
                cast(Any, dict(source=source, transformation=transformation))
            )

            processing_time = time.time() - start_time
            logger.info(
                f"Successfully ran transformation {input_data.transformation_id} "
                f"on source {input_data.source_id} in {processing_time:.2f}s"
            )

            return RunTransformationOutput(
                success=True,
                source_id=input_data.source_id,
                transformation_id=input_data.transformation_id,
                processing_time=processing_time,
            )

        except ValueError as e:
            # Validation errors are permanent failures - don't retry
            processing_time = time.time() - start_time
            logger.error(
                f"Failed to run transformation {input_data.transformation_id} "
                f"on source {input_data.source_id}: {e}"
            )
            await _record_command_failure(
                input_data,
                command_name="run_transformation",
                error_message=str(e),
            )
            return RunTransformationOutput(
                success=False,
                source_id=input_data.source_id,
                transformation_id=input_data.transformation_id,
                processing_time=processing_time,
                error_message=str(e),
            )
        except Exception as e:
            # Transient failure - will be retried (surreal-commands logs final failure)
            logger.debug(
                f"Transient error running transformation {input_data.transformation_id} "
                f"on source {input_data.source_id}: {e}"
            )
            raise
