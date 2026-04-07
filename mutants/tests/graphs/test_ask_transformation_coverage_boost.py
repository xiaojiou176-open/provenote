from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from packages.core.exceptions import OpenNotebookError
from packages.core.graphs import ask as ask_module
from packages.core.graphs import transformation as transformation_module


def test_ask_helper_branches_cover_edge_inputs() -> None:
    assert ask_module._latest_thought_signature({"thought_signatures": "bad"}) is None
    assert ask_module._latest_thought_signature({"thought_signatures": ["", 1]}) is None

    assert (
        ask_module._thought_signature_from_telemetry({"extracted_result": "bad"})
        is None
    )
    assert (
        ask_module._thought_signature_from_telemetry(
            {"extracted_result": {"thought_signature": "   "}}
        )
        is None
    )

    assert ask_module._coerce_tool_input("   ") == {}
    assert ask_module._coerce_tool_input(123) == 123


@pytest.mark.asyncio
async def test_execute_tool_call_covers_sync_success_and_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync_tool = SimpleNamespace(invoke=lambda args: {"args": args, "ok": True})

    def _boom(_args: object) -> object:
        raise RuntimeError("boom")

    failing_tool = SimpleNamespace(invoke=_boom)
    monkeypatch.setattr(
        ask_module,
        "ASK_TOOL_REGISTRY",
        {"sync_ok": sync_tool, "sync_fail": failing_tool},
    )

    name_ok, output_ok, status_ok = await ask_module._execute_tool_call(
        {"name": "sync_ok", "args": {"value": 1}}
    )
    assert name_ok == "sync_ok"
    assert status_ok == "success"
    assert '"ok": true' in output_ok

    name_fail, output_fail, status_fail = await ask_module._execute_tool_call(
        {"name": "sync_fail", "args": {}}
    )
    assert name_fail == "sync_fail"
    assert status_fail == "error"
    assert "Tool 'sync_fail' failed: boom" in output_fail


def test_coerce_ai_message_normalizes_non_ai_payload() -> None:
    raw = SimpleNamespace(content=123, additional_kwargs="bad", tool_calls="bad")

    converted = ask_module._coerce_ai_message(raw)

    assert isinstance(converted, AIMessage)
    assert converted.content == "123"
    assert converted.additional_kwargs == {}
    assert converted.tool_calls == []


@pytest.mark.asyncio
async def test_invoke_with_tool_loop_returns_early_without_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ainvoke_mock = AsyncMock(
        return_value=(
            AIMessage(content="plain"),
            {"extracted_result": {"tool_calls": []}},
        )
    )
    monkeypatch.setattr(ask_module, "ainvoke_with_gemini_telemetry", ainvoke_mock)

    message, telemetries = await ask_module._invoke_with_tool_loop(
        model=object(),
        initial_prompt="prompt",
        gemini_features=object(),
        thought_signature="sig-init",
    )

    assert isinstance(message, AIMessage)
    assert message.content == "plain"
    assert len(telemetries) == 1
    assert telemetries[0]["extracted_result"]["tool_calls"] == []


@pytest.mark.asyncio
async def test_call_model_with_messages_success_adds_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ask_module.Prompter,
        "render",
        lambda self, data: "ask-system-prompt",
    )
    monkeypatch.setattr(
        ask_module,
        "provision_with_gemini_features",
        AsyncMock(return_value=(object(), object())),
    )
    monkeypatch.setattr(
        ask_module,
        "_invoke_with_tool_loop",
        AsyncMock(
            return_value=(
                AIMessage(
                    content='{"reasoning":"r","searches":[{"term":"t","instructions":"i"}]}'
                ),
                [{"extracted_result": {"thought_signature": "sig-next"}}],
            )
        ),
    )

    result = await ask_module.call_model_with_messages(
        {
            "question": "q",
            "strategy": ask_module.Strategy(reasoning="seed", searches=[]),
            "answers": [],
            "final_answer": "",
            "gemini_telemetry": [],
            "thought_signatures": ["sig-prev"],
        },
        RunnableConfig(configurable={}),
    )

    assert result["strategy"].reasoning == "r"
    assert result["strategy"].searches[0].term == "t"
    assert result["thought_signatures"] == ["sig-next"]


@pytest.mark.asyncio
async def test_call_model_with_messages_error_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _ClassifiedAskError(Exception):
        pass

    monkeypatch.setattr(
        ask_module.Prompter,
        "render",
        lambda self, data: "ask-system-prompt",
    )

    monkeypatch.setattr(
        ask_module,
        "provision_with_gemini_features",
        AsyncMock(side_effect=OpenNotebookError("upstream-open-notebook-error")),
    )
    with pytest.raises(OpenNotebookError, match="upstream-open-notebook-error"):
        await ask_module.call_model_with_messages(
            {
                "question": "q",
                "strategy": ask_module.Strategy(reasoning="seed", searches=[]),
                "answers": [],
                "final_answer": "",
                "gemini_telemetry": [],
                "thought_signatures": [],
            },
            RunnableConfig(configurable={}),
        )

    monkeypatch.setattr(
        ask_module,
        "provision_with_gemini_features",
        AsyncMock(side_effect=RuntimeError("boom")),
    )
    monkeypatch.setattr(
        ask_module,
        "classify_error",
        lambda exc: (_ClassifiedAskError, "friendly-ask-error"),
    )
    with pytest.raises(_ClassifiedAskError, match="friendly-ask-error"):
        await ask_module.call_model_with_messages(
            {
                "question": "q",
                "strategy": ask_module.Strategy(reasoning="seed", searches=[]),
                "answers": [],
                "final_answer": "",
                "gemini_telemetry": [],
                "thought_signatures": [],
            },
            RunnableConfig(configurable={}),
        )


@pytest.mark.asyncio
async def test_trigger_queries_builds_send_payloads() -> None:
    state = {
        "question": "what",
        "strategy": ask_module.Strategy(
            reasoning="why",
            searches=[
                ask_module.Search(term="alpha", instructions="find alpha"),
                ask_module.Search(term="beta", instructions="find beta"),
            ],
        ),
        "thought_signatures": [" ", "sig-active"],
    }

    sends = await ask_module.trigger_queries(state, RunnableConfig(configurable={}))

    assert len(sends) == 2
    assert sends[0].node == "provide_answer"
    assert sends[0].arg["term"] == "alpha"
    assert sends[0].arg["thought_signature"] == "sig-active"
    assert sends[1].arg["instructions"] == "find beta"


@pytest.mark.asyncio
async def test_provide_answer_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ask_module, "vector_search", AsyncMock(return_value=[]))
    empty = await ask_module.provide_answer(
        {
            "question": "q",
            "term": "t",
            "instructions": "i",
            "results": {},
            "answer": "",
            "ids": [],
        },
        RunnableConfig(configurable={}),
    )
    assert empty == {"answers": []}

    monkeypatch.setattr(
        ask_module,
        "vector_search",
        AsyncMock(return_value=[{"id": "A"}, {"id": "B"}]),
    )
    monkeypatch.setattr(
        ask_module.Prompter,
        "render",
        lambda self, data: "answer-system-prompt",
    )
    monkeypatch.setattr(
        ask_module,
        "provision_with_gemini_features",
        AsyncMock(return_value=(object(), object())),
    )
    monkeypatch.setattr(
        ask_module,
        "_invoke_with_tool_loop",
        AsyncMock(
            return_value=(
                AIMessage(content="answer-body"),
                [{"extracted_result": {"thought_signature": "sig-answer"}}],
            )
        ),
    )

    success = await ask_module.provide_answer(
        {
            "question": "q",
            "term": "t",
            "instructions": "i",
            "results": {},
            "answer": "",
            "ids": [],
            "thought_signature": "sig-prev",
        },
        RunnableConfig(configurable={}),
    )
    assert success["answers"] == ["answer-body"]
    assert success["thought_signatures"] == ["sig-answer"]


@pytest.mark.asyncio
async def test_provide_answer_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _ClassifiedProvideAnswerError(Exception):
        pass

    monkeypatch.setattr(
        ask_module,
        "vector_search",
        AsyncMock(side_effect=RuntimeError("vector-search-failed")),
    )
    monkeypatch.setattr(
        ask_module,
        "classify_error",
        lambda exc: (_ClassifiedProvideAnswerError, "friendly-provide-answer"),
    )

    with pytest.raises(_ClassifiedProvideAnswerError, match="friendly-provide-answer"):
        await ask_module.provide_answer(
            {
                "question": "q",
                "term": "t",
                "instructions": "i",
                "results": {},
                "answer": "",
                "ids": [],
            },
            RunnableConfig(configurable={}),
        )


@pytest.mark.asyncio
async def test_provide_answer_reraises_open_notebook_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ask_module,
        "vector_search",
        AsyncMock(side_effect=OpenNotebookError("provider-down")),
    )

    with pytest.raises(OpenNotebookError, match="provider-down"):
        await ask_module.provide_answer(
            {
                "question": "q",
                "term": "t",
                "instructions": "i",
                "results": {},
                "answer": "",
                "ids": [],
            },
            RunnableConfig(configurable={}),
        )


@pytest.mark.asyncio
async def test_write_final_answer_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _ClassifiedFinalAnswerError(Exception):
        pass

    monkeypatch.setattr(
        ask_module.Prompter,
        "render",
        lambda self, data: "final-system-prompt",
    )
    monkeypatch.setattr(
        ask_module,
        "provision_with_gemini_features",
        AsyncMock(side_effect=RuntimeError("final-failure")),
    )
    monkeypatch.setattr(
        ask_module,
        "classify_error",
        lambda exc: (_ClassifiedFinalAnswerError, "friendly-final-error"),
    )

    with pytest.raises(_ClassifiedFinalAnswerError, match="friendly-final-error"):
        await ask_module.write_final_answer(
            {
                "question": "q",
                "strategy": ask_module.Strategy(reasoning="r", searches=[]),
                "answers": [],
                "final_answer": "",
                "gemini_telemetry": [],
                "thought_signatures": [],
            },
            RunnableConfig(configurable={}),
        )


@pytest.mark.asyncio
async def test_write_final_answer_reraises_open_notebook_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ask_module.Prompter,
        "render",
        lambda self, data: "final-system-prompt",
    )
    monkeypatch.setattr(
        ask_module,
        "provision_with_gemini_features",
        AsyncMock(side_effect=OpenNotebookError("final-provider-down")),
    )

    with pytest.raises(OpenNotebookError, match="final-provider-down"):
        await ask_module.write_final_answer(
            {
                "question": "q",
                "strategy": ask_module.Strategy(reasoning="r", searches=[]),
                "answers": [],
                "final_answer": "",
                "gemini_telemetry": [],
                "thought_signatures": [],
            },
            RunnableConfig(configurable={}),
        )


def test_resolve_prompt_pack_uses_fallback_when_file_read_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _BrokenTemplatePath:
        def read_text(self, encoding: str = "utf-8") -> str:
            _ = encoding
            raise OSError("cannot read")

        def __str__(self) -> str:
            return "broken-template-path"

    warning_calls: list[str] = []
    monkeypatch.setattr(
        transformation_module,
        "PROMPT_PACKS",
        {"extract": _BrokenTemplatePath()},
    )
    monkeypatch.setattr(
        transformation_module.logger,
        "warning",
        lambda message: warning_calls.append(str(message)),
    )

    raw_prompt = "@prompt-pack:extract"
    resolved = transformation_module._resolve_prompt_pack(raw_prompt)

    assert resolved == raw_prompt
    assert warning_calls


@pytest.mark.asyncio
async def test_run_transformation_source_content_and_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeSource:
        def __init__(self, full_text: str) -> None:
            self.full_text = full_text
            self.add_insight = AsyncMock()

    source = _FakeSource("source-full-text")
    transformation = SimpleNamespace(prompt="prompt-text", title="Summary")

    monkeypatch.setattr(transformation_module, "Source", _FakeSource)
    monkeypatch.setattr(
        transformation_module.DefaultPrompts,
        "get_instance",
        AsyncMock(
            return_value=SimpleNamespace(transformation_instructions="GLOBAL-INSTR")
        ),
    )
    monkeypatch.setattr(
        transformation_module.Prompter,
        "render",
        lambda self, data: "transformation-system-prompt",
    )
    provision_mock = AsyncMock(return_value=(object(), object()))
    monkeypatch.setattr(
        transformation_module,
        "provision_with_gemini_features",
        provision_mock,
    )
    monkeypatch.setattr(
        transformation_module,
        "ainvoke_with_gemini_telemetry",
        AsyncMock(
            return_value=(
                SimpleNamespace(content="<think>hidden</think>clean-output"),
                {"extracted_result": {"thought_signature": " sig-out "}},
            )
        ),
    )

    result = await transformation_module.run_transformation(
        {
            "input_text": "",
            "source": source,
            "transformation": transformation,
            "thought_signature": "sig-in",
        },
        RunnableConfig(configurable={}),
    )

    assert result["output"] == "clean-output"
    assert result["thought_signature"] == "sig-out"
    source.add_insight.assert_awaited_once_with("Summary", "clean-output")
    assert provision_mock.await_args.kwargs["thought_signature"] == "sig-in"


@pytest.mark.asyncio
async def test_run_transformation_reraises_open_notebook_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        transformation_module.DefaultPrompts,
        "get_instance",
        AsyncMock(return_value=SimpleNamespace(transformation_instructions="")),
    )
    monkeypatch.setattr(
        transformation_module.Prompter,
        "render",
        lambda self, data: "transformation-system-prompt",
    )
    monkeypatch.setattr(
        transformation_module,
        "provision_with_gemini_features",
        AsyncMock(side_effect=OpenNotebookError("stop-here")),
    )

    with pytest.raises(OpenNotebookError, match="stop-here"):
        await transformation_module.run_transformation(
            {
                "input_text": "plain-text",
                "source": None,
                "transformation": SimpleNamespace(prompt="prompt", title="Summary"),
            },
            RunnableConfig(configurable={}),
        )


@pytest.mark.asyncio
async def test_run_transformation_omits_signature_when_extracted_payload_not_usable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        transformation_module.DefaultPrompts,
        "get_instance",
        AsyncMock(return_value=SimpleNamespace(transformation_instructions="")),
    )
    monkeypatch.setattr(
        transformation_module.Prompter,
        "render",
        lambda self, data: "transformation-system-prompt",
    )
    monkeypatch.setattr(
        transformation_module,
        "provision_with_gemini_features",
        AsyncMock(return_value=(object(), object())),
    )
    monkeypatch.setattr(
        transformation_module,
        "ainvoke_with_gemini_telemetry",
        AsyncMock(
            return_value=(
                SimpleNamespace(content="plain-output"),
                {"extracted_result": []},
            )
        ),
    )

    result = await transformation_module.run_transformation(
        {
            "input_text": "plain-text",
            "source": None,
            "transformation": SimpleNamespace(prompt="prompt", title="Summary"),
        },
        RunnableConfig(configurable={}),
    )

    assert result["output"] == "plain-output"
    assert "thought_signature" not in result
