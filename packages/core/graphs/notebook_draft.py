from __future__ import annotations

import json
import re
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from packages.core.ai.model_strategy import GEMINI_MODEL_PRO_31
from packages.core.ai.provision import provision_langchain_model
from packages.core.auditable import (
    AuditableLLMOutput,
    SourceParagraph,
    build_auditable_artifact_from_paragraphs,
)
from packages.core.auditable.paragraph_indexer import index_source_paragraphs
from packages.core.domain.notebook import Source
from packages.core.observability.logger import logger
from packages.core.utils import clean_thinking_content
from packages.core.utils.text_utils import extract_text_content


class NotebookDraftState(TypedDict):
    title: str
    sources: list[Source]
    model: str
    language: str
    near_dedup_threshold: float
    output: dict[str, Any]


def build_notebook_source_paragraphs(sources: list[Source]) -> list[SourceParagraph]:
    paragraphs: list[SourceParagraph] = []
    global_order = 1
    for source_index, source in enumerate(sources, start=1):
        if not source.full_text or not source.full_text.strip():
            continue
        for paragraph in index_source_paragraphs(source.full_text):
            paragraphs.append(
                SourceParagraph(
                    pid=f"S{source_index:03d}-{paragraph.pid}",
                    order=global_order,
                    raw_text=paragraph.raw_text,
                    canonical_text=paragraph.canonical_text,
                    canonical_hash=paragraph.canonical_hash,
                    source_id=source.id,
                    source_title=source.title or "Untitled Source",
                )
            )
            global_order += 1
    return paragraphs


def _build_llm_prompt_text(title: str, source_paragraphs: list[SourceParagraph]) -> str:
    lines = [
        f"Notebook draft title: {title}",
        "",
        "Source paragraphs with canonical PIDs:",
    ]
    for paragraph in source_paragraphs:
        source_title = paragraph.source_title or paragraph.source_id or "Source"
        lines.append(f"[{paragraph.pid}] ({source_title}) {paragraph.raw_text}")
        lines.append("")
    return "\n".join(lines).strip()


def _extract_json_payload(content: str) -> dict[str, Any] | None:
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


async def _generate_llm_output(
    *,
    model_id: str,
    title: str,
    source_paragraphs: list[SourceParagraph],
) -> AuditableLLMOutput | None:
    prompt = """You are assembling a notebook-level auditable research draft.
Return JSON only, and every claim must cite source_pids from the provided PID list.

Strict requirements:
1) Return a JSON object only.
2) source_pids may only come from the provided PID list.
3) Every claim in claims must include at least one source_pid.
4) Never invent a PID.

Return JSON with this structure:
{
  "sections": [
    {
      "title": "Section title",
      "bullets": ["Point 1", "Point 2"],
      "source_pids": ["S001-P000001"]
    }
  ],
  "claims": [
    {
      "text": "A verifiable claim",
      "source_pids": ["S001-P000001", "S002-P000002"]
    }
  ],
  "dedup_groups": [],
  "unclassified_pids": []
}
"""

    candidate_pids = [paragraph.pid for paragraph in source_paragraphs]
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(
            content=(
                f"PID list:\n{candidate_pids}\n\n"
                f"{_build_llm_prompt_text(title, source_paragraphs)}"
            )
        ),
    ]

    chain = await provision_langchain_model(
        str(messages),
        model_id,
        "transformation",
        max_tokens=8192,
    )
    response = await chain.ainvoke(messages)
    content = clean_thinking_content(extract_text_content(response.content))
    payload = _extract_json_payload(content)
    if not payload:
        return None

    try:
        return AuditableLLMOutput.model_validate(payload)
    except Exception:
        return None


def _serialize_artifact(artifact) -> dict[str, Any]:
    return {
        "model_id": artifact.model_id,
        "language": artifact.language,
        "near_dedup_threshold": artifact.near_dedup_threshold,
        "source_paragraphs": [
            paragraph.model_dump() for paragraph in artifact.source_paragraphs
        ],
        "sections": [section.model_dump() for section in artifact.sections],
        "claims": [claim.model_dump() for claim in artifact.claims],
        "dedup_entries": [entry.model_dump() for entry in artifact.dedup_entries],
        "metrics": artifact.metrics.model_dump(),
        "coverage_json": artifact.coverage_json.model_dump(),
        "dedup_json": artifact.dedup_json.model_dump(),
        "result_markdown": artifact.result_markdown,
    }


async def run_notebook_draft(state: NotebookDraftState) -> dict[str, Any]:
    model_id = state.get("model", GEMINI_MODEL_PRO_31)
    language = state.get("language", "zh-CN")
    near_threshold = state.get("near_dedup_threshold", 0.97)
    title = state["title"]
    source_paragraphs = build_notebook_source_paragraphs(state["sources"])
    if not source_paragraphs:
        raise ValueError(
            "Selected draft sources do not contain any non-empty paragraph"
        )

    llm_output = None
    try:
        llm_output = await _generate_llm_output(
            model_id=model_id,
            title=title,
            source_paragraphs=source_paragraphs,
        )
    except Exception as exc:
        logger.warning(
            "Notebook draft LLM rewrite failed, fallback to deterministic artifact: {}",
            exc,
        )

    artifact = build_auditable_artifact_from_paragraphs(
        source_paragraphs,
        model_id=model_id,
        language=language,
        near_dedup_threshold=near_threshold,
        llm_output=llm_output,
        title=title,
    )
    return {"output": _serialize_artifact(artifact)}


workflow = StateGraph(NotebookDraftState)
workflow.add_node("notebook_draft", run_notebook_draft)
workflow.add_edge(START, "notebook_draft")
workflow.add_edge("notebook_draft", END)
graph = workflow.compile()
