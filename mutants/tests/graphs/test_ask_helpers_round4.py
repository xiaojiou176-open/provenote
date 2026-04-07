from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from packages.core.graphs import ask as ask_module


def test_extract_tool_calls_normalizes_and_dedupes() -> None:
    ai_message = SimpleNamespace(
        tool_calls=[
            {"id": "1", "function_call": {"name": "tool_a", "args": {"x": 1}}},
            {"id": "1", "function_call": {"name": "tool_a", "args": {"x": 1}}},
        ]
    )
    telemetry = {
        "extracted_result": {
            "tool_calls": [
                {"id": "2", "name": "tool_b", "args": "{}"},
                {"id": "2", "name": "tool_b", "args": "{}"},
            ]
        }
    }

    calls = ask_module._extract_tool_calls(ai_message, telemetry)

    assert calls == [
        {"id": "1", "name": "tool_a", "args": {"x": 1}},
        {"id": "2", "name": "tool_b", "args": "{}"},
    ]


def test_coerce_tool_input_parses_json_and_keeps_invalid_literal() -> None:
    assert ask_module._coerce_tool_input('{"a": 1}') == {"a": 1}
    assert ask_module._coerce_tool_input("not-json") == "not-json"
    assert ask_module._coerce_tool_input(None) == {}


@pytest.mark.asyncio
async def test_execute_tool_call_returns_error_for_missing_and_unknown_tool() -> None:
    name, output, status = await ask_module._execute_tool_call({})
    assert name == ""
    assert status == "error"
    assert "missing required field 'name'" in output

    name, output, status = await ask_module._execute_tool_call({"name": "unknown_tool"})
    assert name == "unknown_tool"
    assert status == "error"
    assert "Unknown tool 'unknown_tool'" in output


@pytest.mark.asyncio
async def test_execute_tool_call_invokes_async_tool_and_serializes_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_tool = SimpleNamespace(
        ainvoke=AsyncMock(return_value={"ok": True, "count": 2})
    )
    monkeypatch.setattr(
        ask_module,
        "ASK_TOOL_REGISTRY",
        {"tool_ok": fake_tool},
    )

    name, output, status = await ask_module._execute_tool_call(
        {"name": "tool_ok", "args": '{"k":"v"}'}
    )

    assert name == "tool_ok"
    assert status == "success"
    assert '"ok": true' in output
    fake_tool.ainvoke.assert_awaited_once_with({"k": "v"})
