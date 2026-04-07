from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from packages.core.ai.model_strategy import GEMINI_MODEL_PRO_31
from packages.core.ai.provision import provision_langchain_model
from packages.core.auditable import AuditableLLMOutput, build_auditable_artifact
from packages.core.observability.logger import logger
from packages.core.utils import clean_thinking_content
from packages.core.utils.text_utils import extract_text_content


class AuditableTransformationState(TypedDict):
    input_text: str
    model: str
    language: str
    near_dedup_threshold: float
    output: dict


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
    input_text: str,
    candidate_pids: list[str],
) -> AuditableLLMOutput | None:
    prompt = """You are an auditable long-text organizer.
Your task is to turn the input text into structured JSON, and every claim must cite source_pids.

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
      "source_pids": ["P000001"]
    }
  ],
  "claims": [
    {
      "text": "A verifiable claim",
      "source_pids": ["P000001", "P000003"]
    }
  ],
  "dedup_groups": [],
  "unclassified_pids": []
}
"""

    user_payload = f"PID list:\n{candidate_pids}\n\nInput text:\n{input_text}"

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_payload),
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
        "source_paragraphs": [p.model_dump() for p in artifact.source_paragraphs],
        "sections": [s.model_dump() for s in artifact.sections],
        "claims": [c.model_dump() for c in artifact.claims],
        "dedup_entries": [e.model_dump() for e in artifact.dedup_entries],
        "metrics": artifact.metrics.model_dump(),
        "coverage_json": artifact.coverage_json.model_dump(),
        "dedup_json": artifact.dedup_json.model_dump(),
        "result_markdown": artifact.result_markdown,
    }


async def run_auditable_transformation(state: dict) -> dict:
    model_id = state.get("model", GEMINI_MODEL_PRO_31)
    language = state.get("language", "zh-CN")
    near_threshold = state.get("near_dedup_threshold", 0.97)
    input_text = state["input_text"]

    base_artifact = build_auditable_artifact(
        input_text,
        model_id=model_id,
        language=language,
        near_dedup_threshold=near_threshold,
    )

    candidate_pids = [p.pid for p in base_artifact.source_paragraphs]

    llm_output = None
    try:
        llm_output = await _generate_llm_output(
            model_id=model_id,
            input_text=input_text,
            candidate_pids=candidate_pids,
        )
    except Exception as exc:
        logger.warning(
            f"LLM structured rewrite failed, fallback to deterministic output: {exc}"
        )

    if llm_output:
        artifact = build_auditable_artifact(
            input_text,
            model_id=model_id,
            language=language,
            near_dedup_threshold=near_threshold,
            llm_output=llm_output,
        )
    else:
        artifact = base_artifact

    return {"output": _serialize_artifact(artifact)}


workflow = StateGraph(AuditableTransformationState)
workflow.add_node("auditable_transformation", run_auditable_transformation)  # type: ignore[type-var]
workflow.add_edge(START, "auditable_transformation")
workflow.add_edge("auditable_transformation", END)
graph = workflow.compile()
