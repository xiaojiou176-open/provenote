from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from packages.core.graphs import ask as ask_module


def test_extract_tool_calls_skips_non_dict_telemetry_entries() -> None:
    telemetry = {
        "extracted_result": {
            "tool_calls": ["bad-entry", {"id": "ok", "name": "tool_ok", "args": {}}]
        }
    }

    calls = ask_module._extract_tool_calls(SimpleNamespace(tool_calls=[]), telemetry)

    assert calls == [{"id": "ok", "name": "tool_ok", "args": {}}]


@pytest.mark.asyncio
async def test_invoke_with_tool_loop_keeps_previous_signature_when_followup_has_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_tool = SimpleNamespace(ainvoke=AsyncMock(return_value={"ok": True}))
    monkeypatch.setattr(ask_module, "ASK_TOOL_REGISTRY", {"tool_ok": fake_tool})

    async def _fake_invoke(
        _model: object,
        payload: object,
        *,
        features: object,
        thought_signature: str | None = None,
        fallback_reason: str | None = None,
    ) -> tuple[AIMessage, dict]:
        _ = (features, fallback_reason)
        if isinstance(payload, str):
            return AIMessage(
                content="need tool",
                tool_calls=[{"id": "call-1", "name": "tool_ok", "args": {}}],
            ), {
                "extracted_result": {
                    "tool_calls": [{"id": "call-1", "name": "tool_ok", "args": {}}],
                    "thought_signature": "sig-from-first",
                }
            }

        assert thought_signature == "sig-from-first"
        assert isinstance(payload, list)
        assert any(isinstance(item, ToolMessage) for item in payload)
        return AIMessage(content="done"), {"extracted_result": {"tool_calls": []}}

    monkeypatch.setattr(ask_module, "ainvoke_with_gemini_telemetry", _fake_invoke)

    message, telemetries = await ask_module._invoke_with_tool_loop(
        model=object(),
        initial_prompt="prompt",
        gemini_features=object(),
        thought_signature="sig-initial",
    )

    assert message.content == "done"
    assert len(telemetries) == 2
    fake_tool.ainvoke.assert_awaited_once_with({})


@pytest.mark.asyncio
async def test_call_model_with_messages_omits_signature_when_telemetry_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ask_module.Prompter, "render", lambda self, data: "prompt")
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
                AIMessage(content='{"reasoning":"r","searches":[]}'),
                [{"extracted_result": {}}],
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
    assert "thought_signatures" not in result


@pytest.mark.asyncio
async def test_provide_answer_omits_signature_when_telemetry_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ask_module,
        "vector_search",
        AsyncMock(return_value=[{"id": "source-1"}]),
    )
    monkeypatch.setattr(ask_module.Prompter, "render", lambda self, data: "prompt")
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
                [{"extracted_result": {}}],
            )
        ),
    )

    result = await ask_module.provide_answer(
        {
            "question": "q",
            "term": "term",
            "instructions": "instructions",
            "results": {},
            "answer": "",
            "ids": [],
            "thought_signature": "sig-prev",
        },
        RunnableConfig(configurable={}),
    )

    assert result["answers"] == ["answer-body"]
    assert "thought_signatures" not in result


@pytest.mark.asyncio
async def test_write_final_answer_omits_signature_when_telemetry_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ask_module.Prompter, "render", lambda self, data: "prompt")
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
                AIMessage(content="final-body"),
                [{"extracted_result": {}}],
            )
        ),
    )

    result = await ask_module.write_final_answer(
        {
            "question": "q",
            "strategy": ask_module.Strategy(reasoning="r", searches=[]),
            "answers": [],
            "final_answer": "",
            "gemini_telemetry": [],
            "thought_signatures": ["sig-prev"],
        },
        RunnableConfig(configurable={}),
    )

    assert result["final_answer"] == "final-body"
    assert "thought_signatures" not in result
