from pathlib import Path
from typing import Any, Dict, List

from ai_prompter import Prompter
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from typing_extensions import NotRequired, TypedDict

from packages.core.ai.gemini_runtime import (
    ainvoke_with_gemini_telemetry,
    provision_with_gemini_features,
)
from packages.core.domain.notebook import Source
from packages.core.domain.transformation import DefaultPrompts, Transformation
from packages.core.exceptions import OpenNotebookError
from packages.core.observability.logger import logger
from packages.core.utils import clean_thinking_content
from packages.core.utils.error_classifier import classify_error
from packages.core.utils.text_utils import extract_text_content


class TransformationState(TypedDict):
    input_text: str
    source: NotRequired[Source]
    transformation: Transformation
    output: NotRequired[str]
    gemini_telemetry: NotRequired[dict[str, Any]]
    input_parts: NotRequired[List[Dict[str, Any]]]
    thought_signature: NotRequired[str]


PROMPT_PACKS = {
    "extract": Path("packages/prompts/transformation/extract.jinja"),
    "rewrite": Path("packages/prompts/transformation/rewrite.jinja"),
    "audit": Path("packages/prompts/transformation/audit.jinja"),
    "chat_knowledgeization": Path(
        "packages/prompts/transformation/chat_knowledgeization.jinja"
    ),
}


def _resolve_prompt_pack(prompt: str) -> str:
    marker_prefix = "@prompt-pack:"
    stripped = (prompt or "").strip()
    if not stripped.startswith(marker_prefix):
        return prompt

    pack_key = stripped[len(marker_prefix) :].strip().lower()
    template_path = PROMPT_PACKS.get(pack_key)
    if not template_path:
        logger.warning(
            f"Unknown prompt pack marker '{pack_key}', keeping original prompt"
        )
        return prompt
    try:
        return template_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning(
            f"Failed to load prompt pack '{pack_key}' from {template_path}: {exc}"
        )
        return prompt


def _build_input_parts(content: str, state: dict) -> List[Dict[str, Any]]:
    explicit_parts = state.get("input_parts")
    if isinstance(explicit_parts, list):
        normalized: List[Dict[str, Any]] = []
        for part in explicit_parts:
            if isinstance(part, dict):
                normalized.append(dict(part))
        if normalized:
            return normalized
    return [{"type": "text", "text": content, "metadata": {"media_resolution": "low"}}]


async def run_transformation(state: dict, config: RunnableConfig) -> dict:
    source_obj = state.get("source")
    source: Source = source_obj if isinstance(source_obj, Source) else None  # type: ignore[assignment]
    content = state.get("input_text")
    assert source or content, "No content to transform"
    transformation: Transformation = state["transformation"]
    thought_signature = state.get("thought_signature")

    try:
        if not content:
            content = source.full_text
        transformation_template_text = _resolve_prompt_pack(transformation.prompt)
        default_prompts: DefaultPrompts = await DefaultPrompts.get_instance()  # type: ignore[assignment]
        if default_prompts and default_prompts.transformation_instructions:
            transformation_template_text = f"{default_prompts.transformation_instructions}\n\n{transformation_template_text}"

        transformation_template_text = f"{transformation_template_text}\n\n# INPUT"

        system_prompt = Prompter(template_text=transformation_template_text).render(
            data=state
        )
        content_str = str(content) if content else ""
        payload = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=_build_input_parts(content_str, state)),
        ]
        chain, gemini_features = await provision_with_gemini_features(
            content=str(payload),
            model_id=config.get("configurable", {}).get("model_id"),
            default_type="transformation",
            config=config,
            thought_signature=thought_signature,
            max_tokens=8192,
        )

        response, telemetry = await ainvoke_with_gemini_telemetry(
            chain,
            payload,
            features=gemini_features,
            thought_signature=thought_signature,
        )

        # Clean thinking content from the response
        response_content = extract_text_content(response.content)
        cleaned_content = clean_thinking_content(response_content)

        if source:
            await source.add_insight(transformation.title, cleaned_content)

        output = {
            "output": cleaned_content,
            "gemini_telemetry": telemetry,
        }
        extracted = telemetry.get("extracted_result")
        if isinstance(extracted, dict):
            latest_signature = extracted.get("thought_signature")
            if isinstance(latest_signature, str) and latest_signature.strip():
                output["thought_signature"] = latest_signature.strip()
        return output
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


agent_state = StateGraph(TransformationState)
agent_state.add_node("agent", run_transformation)  # type: ignore[type-var]
agent_state.add_edge(START, "agent")
agent_state.add_edge("agent", END)
graph = agent_state.compile()
