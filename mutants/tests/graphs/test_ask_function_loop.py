from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from packages.core.graphs.ask import Strategy, write_final_answer


@pytest.mark.asyncio
async def test_write_final_answer_runs_tool_loop_and_passes_thought_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: dict[str, object] = {"signatures": []}

    async def _fake_provision_with_features(
        *, content, model_id, default_type, config, thought_signature=None, **kwargs
    ):
        _ = (content, model_id, default_type, config, thought_signature, kwargs)
        return object(), SimpleNamespace(
            thinking_level="high",
            structured_output_schema=None,
            function_tools=[{"name": "get_current_timestamp"}],
            include_thoughts=True,
            context_cache=None,
            media_resolution="auto",
            fallback_reason=None,
        )

    async def _fake_invoke(
        _model, payload, *, features, thought_signature=None, fallback_reason=None
    ):
        _ = (features, fallback_reason)
        signatures = received["signatures"]
        assert isinstance(signatures, list)
        signatures.append(thought_signature)

        if isinstance(payload, str):
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "tool-1",
                        "name": "get_current_timestamp",
                        "args": {},
                    }
                ],
            ), {
                "extracted_result": {
                    "tool_calls": [
                        {"id": "tool-1", "name": "get_current_timestamp", "args": {}}
                    ],
                    "thought_signature": "sig-after-tool-request",
                }
            }

        assert isinstance(payload, list)
        assert len(payload) == 3
        assert isinstance(payload[-1], ToolMessage)
        assert payload[-1].tool_call_id == "tool-1"
        return AIMessage(content="final answer"), {
            "extracted_result": {
                "tool_calls": [],
                "thought_signature": "sig-final",
            }
        }

    monkeypatch.setattr(
        "packages.core.graphs.ask.provision_with_gemini_features",
        _fake_provision_with_features,
    )
    monkeypatch.setattr(
        "packages.core.graphs.ask.ainvoke_with_gemini_telemetry",
        _fake_invoke,
    )
    monkeypatch.setattr(
        "packages.core.graphs.ask.Prompter.render",
        lambda self, data: "rendered-final-prompt",
    )

    state = {
        "question": "q",
        "strategy": Strategy(reasoning="r", searches=[]),
        "answers": [],
        "final_answer": "",
        "gemini_telemetry": [],
        "thought_signatures": ["sig-initial"],
    }

    result = await write_final_answer(state, RunnableConfig(configurable={}))

    signatures = received["signatures"]
    assert signatures == ["sig-initial", "sig-after-tool-request"]
    assert result["final_answer"] == "final answer"
    assert len(result["gemini_telemetry"]) == 2
    assert result["thought_signatures"] == ["sig-final"]
