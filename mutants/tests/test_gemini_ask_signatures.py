from types import SimpleNamespace

import pytest
from langchain_core.runnables import RunnableConfig

from packages.core.graphs.ask import (
    Search,
    Strategy,
    trigger_queries,
    write_final_answer,
)


@pytest.mark.asyncio
async def test_trigger_queries_carries_latest_thought_signature() -> None:
    state = {
        "question": "what happened?",
        "strategy": Strategy(
            reasoning="check sources",
            searches=[Search(term="alpha", instructions="find alpha evidence")],
        ),
        "thought_signatures": ["sig-old", "sig-new"],
    }

    sends = await trigger_queries(state, RunnableConfig())

    assert len(sends) == 1
    assert sends[0].arg["thought_signature"] == "sig-new"


@pytest.mark.asyncio
async def test_write_final_answer_uses_latest_signature_and_returns_new_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received = {}

    async def _fake_provision_with_features(
        *, content, model_id, default_type, config, thought_signature=None, **kwargs
    ):
        _ = (content, model_id, default_type, config, kwargs)
        received["provision_signature"] = thought_signature
        return object(), SimpleNamespace(
            thinking_level="high",
            structured_output_schema=None,
            function_tools=[],
            include_thoughts=False,
            context_cache=None,
            media_resolution="auto",
            fallback_reason=None,
        )

    async def _fake_invoke(
        _model, _payload, *, features, thought_signature=None, fallback_reason=None
    ):
        _ = (features, fallback_reason)
        received["invoke_signature"] = thought_signature
        return SimpleNamespace(content="final answer"), {
            "extracted_result": {"thought_signature": "sig-out"},
            "enabled_features": ["thinking:high"],
            "duration_ms": 1,
            "fallback_reason": None,
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
        "thought_signatures": ["sig-prev", "sig-latest"],
    }

    result = await write_final_answer(state, RunnableConfig(configurable={}))

    assert received["provision_signature"] == "sig-latest"
    assert received["invoke_signature"] == "sig-latest"
    assert result["final_answer"] == "final answer"
    assert result["thought_signatures"] == ["sig-out"]
