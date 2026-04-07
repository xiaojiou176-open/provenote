import asyncio
import os
import re
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException, UploadFile
from surreal_commands import execute_command_sync

from packages.core.application.command_service import CommandService
from packages.core.application.commands.source_commands import (
    SourceProcessingInput,
    validate_source_link_url,
)
from packages.core.application.models import SourceCreate, SourceResponse, SourceUpdate
from packages.core.config import UPLOADS_FOLDER
from packages.core.database.repository import ensure_record_id, repo_query
from packages.core.domain.notebook import Notebook, Source
from packages.core.domain.transformation import Transformation
from packages.core.exceptions import InvalidInputError
from packages.core.observability.logger import logger
from services.api.routers.sources_helpers import (
    cleanup_uploaded_file,
    save_uploaded_file,
)
from services.api.routers.sources_serializers import build_source_response


_SAFE_UPLOAD_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._() -]{0,255}$")


async def _validate_notebooks(notebook_ids: Optional[list[str]]) -> None:
    for notebook_id in notebook_ids or []:
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise HTTPException(
                status_code=404, detail=f"Notebook {notebook_id} not found"
            )


async def _validate_transformations(transformation_ids: list[str]) -> None:
    for trans_id in transformation_ids:
        transformation = await Transformation.get(trans_id)
        if not transformation:
            raise HTTPException(
                status_code=404,
                detail=f"Transformation {trans_id} not found",
            )


def _is_path_within_directory(path: Path, directory: Path) -> bool:
    try:
        return os.path.commonpath([str(path), str(directory)]) == str(directory)
    except ValueError:
        return False


def _resolve_legacy_upload_file_path(file_path: str) -> str:
    del file_path
    raise HTTPException(
        status_code=400,
        detail="Legacy file_path upload is no longer supported. Use multipart upload.",
    )


def _build_content_state(
    source_data: SourceCreate, file_path: Optional[str]
) -> dict[str, Any]:
    content_state: dict[str, Any] = {}

    if source_data.type == "link":
        if not source_data.url:
            raise HTTPException(status_code=400, detail="URL is required for link type")
        try:
            content_state["url"] = validate_source_link_url(source_data.url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    elif source_data.type == "upload":
        if not file_path:
            raise HTTPException(
                status_code=400,
                detail="File upload is required for upload type",
            )
        content_state["file_path"] = file_path
        content_state["delete_source"] = source_data.delete_source
    elif source_data.type == "text":
        if not source_data.content:
            raise HTTPException(
                status_code=400, detail="Content is required for text type"
            )
        content_state["content"] = source_data.content
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid source type. Must be link, upload, or text",
        )

    return content_state


async def _create_source_shell(source_data: SourceCreate) -> Source:
    source = Source(
        title=source_data.title or "Processing...",
        topics=[],
    )
    await source.save()

    for notebook_id in source_data.notebooks or []:
        await source.add_to_notebook(notebook_id)

    return source


async def _process_source_async(
    source_data: SourceCreate,
    content_state: dict[str, Any],
    transformation_ids: list[str],
) -> SourceResponse:
    source = await _create_source_shell(source_data)
    try:
        import packages.core.application.commands.source_commands  # noqa: F401

        command_input = SourceProcessingInput(
            source_id=str(source.id),
            content_state=content_state,
            notebook_ids=source_data.notebooks,
            transformations=transformation_ids,
            embed=source_data.embed,
        )

        command_id = await CommandService.submit_command_job(
            "open_notebook",
            "process_source",
            command_input.model_dump(),
        )

        logger.info("Submitted async processing command command_id={}", command_id)
        source.command = ensure_record_id(command_id)
        await source.save()

        return SourceResponse(
            id=source.id or "",
            title=source.title,
            topics=source.topics or [],
            asset=None,
            full_text=None,
            embedded=False,
            embedded_chunks=0,
            created=str(source.created),
            updated=str(source.updated),
            command_id=command_id,
            status="new",
            processing_info={"async": True, "queued": True},
        )
    except Exception as exc:
        logger.exception(
            "Failed to submit async processing command error_type={}",
            type(exc).__name__,
        )
        try:
            await source.delete()
        except Exception as cleanup_exc:
            logger.exception(
                "Failed to cleanup source after async submit failure source_id={} error_type={}",
                source.id,
                type(cleanup_exc).__name__,
            )
        raise HTTPException(
            status_code=500,
            detail="Failed to queue processing",
        )


async def _process_source_sync(
    source_data: SourceCreate,
    content_state: dict[str, Any],
    transformation_ids: list[str],
) -> SourceResponse:
    source = await _create_source_shell(source_data)
    try:
        import packages.core.application.commands.source_commands  # noqa: F401

        command_input = SourceProcessingInput(
            source_id=str(source.id),
            content_state=content_state,
            notebook_ids=source_data.notebooks,
            transformations=transformation_ids,
            embed=source_data.embed,
        )

        result = await asyncio.to_thread(
            execute_command_sync,
            "open_notebook",
            "process_source",
            command_input.model_dump(),
            timeout=300,
        )

        if not result.is_success():
            logger.error(
                "Sync processing failed source_id={} error_message={}",
                source.id,
                result.error_message,
            )
            try:
                await source.delete()
            except Exception as cleanup_exc:
                logger.exception(
                    "Failed to cleanup source after sync processing failure source_id={} error_type={}",
                    source.id,
                    type(cleanup_exc).__name__,
                )
            raise HTTPException(
                status_code=500,
                detail="Failed to process source",
            )

        if not source.id:
            raise HTTPException(status_code=500, detail="Source ID is missing")

        processed_source = await Source.get(source.id)
        if not processed_source:
            raise HTTPException(status_code=500, detail="Processed source not found")

        embedded_chunks = await processed_source.get_embedded_chunks()
        return build_source_response(processed_source, embedded_chunks)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Failed sync source processing source_id={} error_type={}",
            source.id,
            type(exc).__name__,
        )
        try:
            await source.delete()
        except Exception as cleanup_exc:
            logger.exception(
                "Failed to cleanup source after sync processing exception source_id={} error_type={}",
                source.id,
                type(cleanup_exc).__name__,
            )
        raise HTTPException(
            status_code=500,
            detail="Failed to process source",
        )


async def create_source_service(
    source_data: SourceCreate,
    upload_file: Optional[UploadFile],
) -> SourceResponse:
    file_path: Optional[str] = None

    try:
        await _validate_notebooks(source_data.notebooks)

        if source_data.type == "upload":
            if upload_file:
                if source_data.file_path:
                    logger.warning(
                        "Ignoring deprecated file_path because multipart file is provided file_path={} filename={}",
                        source_data.file_path,
                        upload_file.filename,
                    )
                try:
                    file_path = await save_uploaded_file(upload_file)
                except (ValueError, OSError) as exc:
                    logger.exception(
                        "File upload failed filename={} error_type={}",
                        upload_file.filename,
                        type(exc).__name__,
                    )
                    raise HTTPException(
                        status_code=400,
                        detail="File upload failed",
                    )
            elif source_data.file_path:
                file_path = _resolve_legacy_upload_file_path(source_data.file_path)

        content_state = _build_content_state(source_data, file_path)
        transformation_ids = source_data.transformations or []
        await _validate_transformations(transformation_ids)

        if source_data.async_processing:
            logger.info("Using async processing path")
            return await _process_source_async(
                source_data,
                content_state,
                transformation_ids,
            )

        logger.info("Using sync processing path")
        return await _process_source_sync(
            source_data, content_state, transformation_ids
        )

    except HTTPException:
        cleanup_uploaded_file(file_path, upload_file)
        raise
    except InvalidInputError as exc:
        cleanup_uploaded_file(file_path, upload_file)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception(
            "Error creating source source_type={} error_type={}",
            source_data.type,
            type(exc).__name__,
        )
        cleanup_uploaded_file(file_path, upload_file)
        raise HTTPException(status_code=500, detail="Error creating source")


async def update_source_service(
    source_id: str, source_update: SourceUpdate
) -> SourceResponse:
    try:
        source = await Source.get(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        if source_update.title is not None:
            source.title = source_update.title
        if source_update.topics is not None:
            source.topics = source_update.topics

        await source.save()
        embedded_chunks = await source.get_embedded_chunks()
        return build_source_response(source, embedded_chunks)
    except HTTPException:
        raise
    except InvalidInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


async def retry_source_processing_service(source_id: str) -> SourceResponse:
    try:
        source = await Source.get(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        if source.command:
            try:
                status = await source.get_status()
                if status in ["running", "queued"]:
                    raise HTTPException(
                        status_code=400,
                        detail="Source is already processing. Cannot retry while processing is active.",
                    )
            except HTTPException:
                raise
            except Exception as exc:
                logger.exception(
                    "Failed to check current status for source source_id={} error_type={}",
                    source_id,
                    type(exc).__name__,
                )

        query = "SELECT in AS notebook_id FROM reference WHERE out = $source_id"
        references = await repo_query(query, {"source_id": ensure_record_id(source_id)})
        notebook_ids = [str(ref["notebook_id"]) for ref in references]

        if not notebook_ids:
            raise HTTPException(
                status_code=400,
                detail="Source is not associated with any notebooks",
            )

        content_state: dict[str, Any] = {}
        if source.asset:
            if source.asset.file_path:
                content_state = {
                    "file_path": source.asset.file_path,
                    "delete_source": False,
                }
            elif source.asset.url:
                try:
                    content_state = {"url": validate_source_link_url(source.asset.url)}
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail=str(exc))
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Source asset has no file_path or url",
                )
        elif source.full_text:
            content_state = {"content": source.full_text}
        else:
            raise HTTPException(
                status_code=400,
                detail="Cannot determine source content for retry",
            )

        try:
            import packages.core.application.commands.source_commands  # noqa: F401

            command_input = SourceProcessingInput(
                source_id=str(source.id),
                content_state=content_state,
                notebook_ids=notebook_ids,
                transformations=[],
                embed=True,
            )

            command_id = await CommandService.submit_command_job(
                "open_notebook",
                "process_source",
                command_input.model_dump(),
            )

            logger.info(
                "Submitted retry processing command command_id={} source_id={}",
                command_id,
                source_id,
            )

            source.command = ensure_record_id(f"command:{command_id}")
            await source.save()

            embedded_chunks = await source.get_embedded_chunks()
            return build_source_response(
                source,
                embedded_chunks,
                command_id=command_id,
                status="queued",
                processing_info={"retry": True, "queued": True},
            )

        except Exception as exc:
            logger.exception(
                "Failed to submit retry processing command source_id={} error_type={}",
                source_id,
                type(exc).__name__,
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to queue retry processing",
            )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Error retrying source processing source_id={} error_type={}",
            source_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="Error retrying source processing",
        )
