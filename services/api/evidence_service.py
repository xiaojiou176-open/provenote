from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from packages.core.ai.provision import provision_langchain_model
from packages.core.application.models import SourceProcessingReportResponse
from packages.core.auditable.coverage_validator import build_coverage_report
from packages.core.auditable.markdown_renderer import render_markdown
from packages.core.auditable.paragraph_indexer import split_paragraphs
from packages.core.auditable.schemas import (
    AuditableClaim,
    AuditableMetrics,
    AuditableSection,
    DedupEntry,
    DedupJSON,
    SourceParagraph,
)
from packages.core.domain.notebook import Source
from packages.core.exceptions import NotFoundError
from packages.core.utils import clean_thinking_content
from packages.core.utils.text_utils import extract_text_content
from services.api.routers.sources_helpers import is_source_file_available


def _detect_source_type(source: Source) -> str:
    if source.asset and source.asset.url:
        return "link"
    if source.asset and source.asset.file_path:
        return "upload"
    return "text"


def _detect_processing_engine(processing_info: dict | None) -> str | None:
    if not processing_info:
        return None
    result = processing_info.get("result")
    if isinstance(result, dict):
        for key in ("url_engine", "document_engine", "engine"):
            value = result.get(key)
            if value:
                return str(value)
    return None


async def build_source_processing_report(
    source_id: str,
) -> SourceProcessingReportResponse:
    source = await Source.get(source_id)
    if not source:
        raise NotFoundError("Source not found")

    processing_status = None
    processing_info = None
    if source.command:
        processing_status = await source.get_status()
        processing_info = await source.get_processing_progress()

    embedded_chunks = await source.get_embedded_chunks()
    insights = await source.get_insights()
    text = source.full_text or ""

    if processing_status == "failed":
        processing_message = (
            "Processing failed. Inspect diagnostics and reprocess when ready."
        )
    elif processing_status in {"queued", "running", "new"}:
        processing_message = (
            "Processing is active. Diagnostics will refresh as the command progresses."
        )
    elif source.command:
        processing_message = "Processing history is available for this source."
    else:
        processing_message = (
            "Legacy or direct source without command-backed processing history."
        )

    return SourceProcessingReportResponse(
        source_id=source.id or source_id,
        source_type=_detect_source_type(source),
        title=source.title,
        processing_status=processing_status,
        processing_message=processing_message,
        processing_engine=_detect_processing_engine(processing_info),
        extracted_length=len(text),
        paragraph_count=len(split_paragraphs(text)),
        embedded=embedded_chunks > 0,
        embedded_chunks=embedded_chunks,
        insights_count=len(insights),
        has_file=bool(source.asset and source.asset.file_path),
        file_available=is_source_file_available(source),
        command_id=str(source.command) if source.command else None,
        processing_info=processing_info,
    )


def _extract_json_payload(content: str) -> dict | None:
    content = content.strip()
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", content)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


async def _repair_with_llm(
    *,
    model_id: str,
    source_paragraphs: list[SourceParagraph],
    target_type: str,
    target_payload: dict,
) -> dict:
    prompt = f"""You are repairing one {target_type} in an auditable markdown run.
Return JSON only. Every repaired element must cite source_pids from the provided PID list.

For a claim, return:
{{
  "text": "repaired claim",
  "source_pids": ["P000001"]
}}

For a section, return:
{{
  "title": "section title",
  "bullets": ["bullet 1", "bullet 2"],
  "source_pids": ["P000001"]
}}
"""
    candidate_pids = [paragraph.pid for paragraph in source_paragraphs]
    paragraph_dump = [
        {
            "pid": paragraph.pid,
            "source_id": paragraph.source_id,
            "source_title": paragraph.source_title,
            "text": paragraph.raw_text,
        }
        for paragraph in source_paragraphs
    ]
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(
            content=json.dumps(
                {
                    "pid_list": candidate_pids,
                    "target_type": target_type,
                    "target": target_payload,
                    "paragraphs": paragraph_dump,
                },
                ensure_ascii=False,
            )
        ),
    ]
    chain = await provision_langchain_model(
        str(messages),
        model_id,
        "transformation",
        max_tokens=4096,
    )
    response = await chain.ainvoke(messages)
    content = clean_thinking_content(extract_text_content(response.content))
    payload = _extract_json_payload(content)
    if not payload:
        raise ValueError(f"Repair model did not return valid JSON for {target_type}")
    return payload


def _build_metrics(
    claims: list[AuditableClaim],
    coverage_json,
    dedup_json: DedupJSON,
) -> AuditableMetrics:
    uncited_claims_count = sum(1 for claim in claims if not claim.source_pids)
    return AuditableMetrics(
        coverage_rate=coverage_json.coverage_rate,
        missing_count=len(coverage_json.missing_pids),
        duplicate_count=len(coverage_json.duplicate_pids),
        uncited_claims_count=uncited_claims_count,
        dedup_group_count=dedup_json.group_count,
        unknown_pid_count=len(coverage_json.unknown_pids),
        unclassified_count=len(coverage_json.unclassified_pids),
    )


def _as_source_paragraphs(items: list[dict]) -> list[SourceParagraph]:
    return [SourceParagraph.model_validate(item) for item in items]


def _as_claims(items: list[dict]) -> list[AuditableClaim]:
    return [AuditableClaim.model_validate(item) for item in items]


def _as_sections(items: list[dict]) -> list[AuditableSection]:
    return [AuditableSection.model_validate(item) for item in items]


def _as_dedup_entries(items: list[dict]) -> list[DedupEntry]:
    return [DedupEntry.model_validate(item) for item in items]


def rebuild_auditable_record(
    *,
    title: str,
    source_paragraphs: list[SourceParagraph],
    claims: list[AuditableClaim],
    sections: list[AuditableSection],
    dedup_entries: list[DedupEntry],
    dedup_json: DedupJSON,
    model_id: str,
    language: str,
    near_dedup_threshold: float,
) -> dict:
    coverage_json = build_coverage_report(
        expected_pids=[paragraph.pid for paragraph in source_paragraphs],
        claims=claims,
        dedup_entries=dedup_entries,
        unclassified_pids=[],
    )
    metrics = _build_metrics(claims, coverage_json, dedup_json)
    result_markdown = render_markdown(
        title=title,
        sections=sections,
        claims=claims,
        dedup_json=dedup_json,
        coverage_json=coverage_json,
        dedup_entries=dedup_entries,
    )
    return {
        "model_id": model_id,
        "language": language,
        "near_dedup_threshold": near_dedup_threshold,
        "source_paragraphs": [item.model_dump() for item in source_paragraphs],
        "sections": [item.model_dump() for item in sections],
        "claims": [item.model_dump() for item in claims],
        "dedup_entries": [item.model_dump() for item in dedup_entries],
        "metrics": metrics.model_dump(),
        "coverage_json": coverage_json.model_dump(),
        "dedup_json": dedup_json.model_dump(),
        "result_markdown": result_markdown,
    }
