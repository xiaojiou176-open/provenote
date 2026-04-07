import json
import operator
from pathlib import Path
from typing import Annotated, List

from ai_prompter import Prompter
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, Field
from typing_extensions import NotRequired, TypedDict

from packages.core.ai.gemini_runtime import (
    ainvoke_with_gemini_telemetry,
    provision_with_gemini_features,
)
from packages.core.domain.notebook import vector_search
from packages.core.exceptions import OpenNotebookError
from packages.core.graphs.tools import get_current_timestamp
from packages.core.utils import clean_thinking_content
from packages.core.utils.error_classifier import classify_error
from packages.core.utils.text_utils import extract_text_content

MAX_TOOL_LOOP_ROUNDS = 5
ASK_TOOLS = [get_current_timestamp]
ASK_TOOL_REGISTRY = {tool.name: tool for tool in ASK_TOOLS}
PROMPT_DIR = str(Path(__file__).resolve().parents[3] / "packages" / "prompts")


class SubGraphState(TypedDict):
    question: str
    term: str
    instructions: str
    results: dict
    answer: str
    ids: list  # Added for provide_answer function
    thought_signature: NotRequired[str]


class Search(BaseModel):
    term: str
    instructions: str = Field(
        description="Tell the answeting LLM what information you need extracted from this search"
    )


class Strategy(BaseModel):
    reasoning: str
    searches: List[Search] = Field(
        default_factory=list,
        description="You can add up to five searches to this strategy",
    )


class ThreadState(TypedDict):
    question: str
    strategy: NotRequired[Strategy]
    answers: NotRequired[Annotated[list, operator.add]]
    final_answer: NotRequired[str]
    gemini_telemetry: NotRequired[Annotated[list, operator.add]]
    thought_signatures: NotRequired[Annotated[list[str], operator.add]]


def _json_safe(data: object) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, ensure_ascii=False, default=str)


def _latest_thought_signature(state: dict) -> str | None:
    signatures = state.get("thought_signatures")
    if not isinstance(signatures, list) or not signatures:
        return None
    latest = signatures[-1]
    if isinstance(latest, str) and latest.strip():
        return latest.strip()
    return None


def _thought_signature_from_telemetry(telemetry: dict) -> str | None:
    extracted = telemetry.get("extracted_result")
    if not isinstance(extracted, dict):
        return None
    signature = extracted.get("thought_signature")
    if isinstance(signature, str) and signature.strip():
        return signature.strip()
    return None


def _extract_tool_calls(ai_message: object, telemetry: dict) -> list[dict]:
    calls: list[dict] = []
    if isinstance(getattr(ai_message, "tool_calls", None), list):
        calls.extend(
            dict(call)
            for call in getattr(ai_message, "tool_calls")
            if isinstance(call, dict)
        )

    extracted = telemetry.get("extracted_result")
    if isinstance(extracted, dict) and isinstance(extracted.get("tool_calls"), list):
        for call in extracted["tool_calls"]:
            if isinstance(call, dict):
                calls.append(dict(call))

    normalized: list[dict] = []
    for call in calls:
        function_call = call.get("function_call")
        if isinstance(function_call, dict):
            normalized.append(
                {
                    "id": call.get("id"),
                    "name": function_call.get("name"),
                    "args": function_call.get("args"),
                }
            )
            continue
        normalized.append(call)

    deduped: list[dict] = []
    seen: set[str] = set()
    for call in normalized:
        dedupe_identity = {
            "id": call.get("id"),
            "name": call.get("name"),
            "args": call.get("args"),
        }
        key = _json_safe(dedupe_identity)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(call)
    return deduped


def _coerce_tool_input(raw_args: object) -> object:
    if raw_args is None:
        return {}
    if isinstance(raw_args, dict):
        return raw_args
    if isinstance(raw_args, str):
        text = raw_args.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else text
        except json.JSONDecodeError:
            return text
    return raw_args


async def _execute_tool_call(tool_call: dict) -> tuple[str, str, str]:
    name = str(tool_call.get("name") or "").strip()
    if not name:
        return "", "Tool call missing required field 'name'.", "error"
    tool = ASK_TOOL_REGISTRY.get(name)
    if tool is None:
        return name, f"Unknown tool '{name}'.", "error"

    tool_input = _coerce_tool_input(tool_call.get("args"))
    try:
        if hasattr(tool, "ainvoke") and callable(tool.ainvoke):
            result = await tool.ainvoke(tool_input)
        else:
            result = tool.invoke(tool_input)
        return name, _json_safe(result), "success"
    except Exception as exc:
        return name, f"Tool '{name}' failed: {exc}", "error"


def _coerce_ai_message(message: object) -> AIMessage:
    if isinstance(message, AIMessage):
        return message
    content = getattr(message, "content", message)
    additional_kwargs = getattr(message, "additional_kwargs", {})
    tool_calls = getattr(message, "tool_calls", [])
    return AIMessage(
        content=content if isinstance(content, (str, list)) else str(content),
        additional_kwargs=additional_kwargs
        if isinstance(additional_kwargs, dict)
        else {},
        tool_calls=tool_calls if isinstance(tool_calls, list) else [],
    )


async def _invoke_with_tool_loop(
    *,
    model: object,
    initial_prompt: str,
    gemini_features: object,
    thought_signature: str | None,
) -> tuple[object, list[dict]]:
    current_signature = thought_signature
    ai_message, telemetry = await ainvoke_with_gemini_telemetry(
        model,
        initial_prompt,
        features=gemini_features,
        thought_signature=current_signature,
    )
    telemetry_items = [telemetry]
    extracted_signature = _thought_signature_from_telemetry(telemetry)
    if extracted_signature:
        current_signature = extracted_signature

    tool_calls = _extract_tool_calls(ai_message, telemetry)
    if not tool_calls:
        return ai_message, telemetry_items

    conversation = [HumanMessage(content=initial_prompt)]
    rounds = 0
    while tool_calls and rounds < MAX_TOOL_LOOP_ROUNDS:
        rounds += 1
        conversation.append(_coerce_ai_message(ai_message))
        for index, tool_call in enumerate(tool_calls, start=1):
            tool_call_id = str(tool_call.get("id") or f"tool-call-{rounds}-{index}")
            name, tool_output, status = await _execute_tool_call(tool_call)
            conversation.append(
                ToolMessage(
                    content=tool_output,
                    tool_call_id=tool_call_id,
                    name=name or None,
                    status=status,  # type: ignore[arg-type]
                )
            )
        ai_message, telemetry = await ainvoke_with_gemini_telemetry(
            model,
            conversation,
            features=gemini_features,
            thought_signature=current_signature,
        )
        telemetry_items.append(telemetry)
        extracted_signature = _thought_signature_from_telemetry(telemetry)
        if extracted_signature:
            current_signature = extracted_signature
        tool_calls = _extract_tool_calls(ai_message, telemetry)

    return ai_message, telemetry_items


async def call_model_with_messages(state: ThreadState, config: RunnableConfig) -> dict:
    try:
        parser = PydanticOutputParser(pydantic_object=Strategy)
        system_prompt = Prompter(  # type: ignore[arg-type]
            prompt_template="ask/entry",
            prompt_dir=PROMPT_DIR,
            parser=parser,
        ).render(
            data=state  # type: ignore[arg-type]
        )
        model, gemini_features = await provision_with_gemini_features(
            content=system_prompt,
            model_id=config.get("configurable", {}).get("strategy_model"),
            default_type="tools",
            config=config,
            thought_signature=_latest_thought_signature(state),
            max_tokens=2000,
            structured=dict(type="json"),
        )
        ai_message, telemetries = await _invoke_with_tool_loop(
            model=model,
            initial_prompt=system_prompt,
            gemini_features=gemini_features,
            thought_signature=_latest_thought_signature(state),
        )

        # Clean the thinking content from the response
        message_content = extract_text_content(ai_message.content)
        cleaned_content = clean_thinking_content(message_content)

        # Parse the cleaned JSON content
        strategy = parser.parse(cleaned_content)

        output = {"strategy": strategy, "gemini_telemetry": telemetries}
        signature = _thought_signature_from_telemetry(telemetries[-1])
        if signature:
            output["thought_signatures"] = [signature]
        return output
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


async def trigger_queries(state: ThreadState, config: RunnableConfig):
    return [
        Send(
            "provide_answer",
            {
                "question": state["question"],
                "instructions": s.instructions,
                "term": s.term,
                "thought_signature": _latest_thought_signature(state),
                # "type": s.type,
            },
        )
        for s in state["strategy"].searches
    ]


async def provide_answer(state: SubGraphState, config: RunnableConfig) -> dict:
    try:
        payload = state
        # if state["type"] == "text":
        #     results = text_search(state["term"], 10, True, True)
        # else:
        results = await vector_search(state["term"], 10, True, True)
        if len(results) == 0:
            return {"answers": []}
        payload["results"] = results
        ids = [r["id"] for r in results]
        payload["ids"] = ids
        system_prompt = Prompter(
            prompt_template="ask/query_process",
            prompt_dir=PROMPT_DIR,
        ).render(data=payload)  # type: ignore[arg-type]
        model, gemini_features = await provision_with_gemini_features(
            content=system_prompt,
            model_id=config.get("configurable", {}).get("answer_model"),
            default_type="tools",
            config=config,
            thought_signature=state.get("thought_signature"),
            max_tokens=2000,
        )
        ai_message, telemetries = await _invoke_with_tool_loop(
            model=model,
            initial_prompt=system_prompt,
            gemini_features=gemini_features,
            thought_signature=state.get("thought_signature"),
        )
        ai_content = extract_text_content(ai_message.content)
        output = {
            "answers": [clean_thinking_content(ai_content)],
            "gemini_telemetry": telemetries,
        }
        signature = _thought_signature_from_telemetry(telemetries[-1])
        if signature:
            output["thought_signatures"] = [signature]
        return output
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


async def write_final_answer(state: ThreadState, config: RunnableConfig) -> dict:
    try:
        system_prompt = Prompter(
            prompt_template="ask/final_answer",
            prompt_dir=PROMPT_DIR,
        ).render(data=state)  # type: ignore[arg-type]
        model, gemini_features = await provision_with_gemini_features(
            content=system_prompt,
            model_id=config.get("configurable", {}).get("final_answer_model"),
            default_type="tools",
            config=config,
            thought_signature=_latest_thought_signature(state),
            max_tokens=2000,
        )
        ai_message, telemetries = await _invoke_with_tool_loop(
            model=model,
            initial_prompt=system_prompt,
            gemini_features=gemini_features,
            thought_signature=_latest_thought_signature(state),
        )
        final_content = extract_text_content(ai_message.content)
        output = {
            "final_answer": clean_thinking_content(final_content),
            "gemini_telemetry": telemetries,
        }
        signature = _thought_signature_from_telemetry(telemetries[-1])
        if signature:
            output["thought_signatures"] = [signature]
        return output
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


agent_state = StateGraph(ThreadState)
agent_state.add_node("agent", call_model_with_messages)
agent_state.add_node("provide_answer", provide_answer)
agent_state.add_node("write_final_answer", write_final_answer)
agent_state.add_edge(START, "agent")
agent_state.add_conditional_edges("agent", trigger_queries, ["provide_answer"])
agent_state.add_edge("provide_answer", "write_final_answer")
agent_state.add_edge("write_final_answer", END)

graph = agent_state.compile()
