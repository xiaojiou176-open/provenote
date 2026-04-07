from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from packages.core.ai.gemini_runtime import (
    ainvoke_with_gemini_telemetry,
    provision_with_gemini_features,
)
from packages.core.exceptions import ExternalServiceError, InvalidInputError
from packages.core.graphs.transformation import run_transformation


@pytest.mark.asyncio
async def test_provision_with_gemini_features_passes_normalized_kwargs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}
    fake_model = object()

    async def _fake_provision(content, model_id, default_type, **kwargs):
        captured["content"] = content
        captured["model_id"] = model_id
        captured["default_type"] = default_type
        captured["kwargs"] = kwargs
        return fake_model

    monkeypatch.setattr(
        "packages.core.ai.gemini_runtime.provision_langchain_model", _fake_provision
    )

    config = RunnableConfig(
        configurable={
            "gemini_features": {
                "thinking_level": "high",
                "structured_output_schema": {"type": "object"},
                "function_tools": [{"name": "fn_tool"}],
                "include_thoughts": True,
                "context_cache": {"handle": "cache-1", "ttl_seconds": 30},
                "media_resolution": "fhd",
            }
        }
    )

    model, features = await provision_with_gemini_features(
        content="hello",
        model_id="model:1",
        default_type="transformation",
        config=config,
        max_tokens=99,
    )

    kwargs = captured["kwargs"]
    assert kwargs["max_tokens"] == 99
    assert kwargs["thinking_level"] == "high"
    assert kwargs["response_schema"] == {"type": "object"}
    assert kwargs["response_mime_type"] == "application/json"
    assert kwargs["structured_output_schema"] == {"type": "object"}
    assert kwargs["function_tools"] == [{"name": "fn_tool"}]
    assert kwargs["include_thoughts"] is True
    assert kwargs["context_cache"] == {"handle": "cache-1", "ttl_seconds": 30}
    assert kwargs["cached_content"] == "cache-1"
    assert kwargs["media_resolution"] == "high"
    assert model is fake_model
    assert features.effective_features == []
    assert features.thinking_level == "high"


@pytest.mark.asyncio
async def test_provision_with_gemini_features_applies_runtime_bindings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeModel:
        def __init__(self):
            self.bind_calls = []
            self.ainvoke = AsyncMock(return_value=SimpleNamespace(content="ok"))

        def bind_tools(self, tools):
            self.bind_calls.append(("bind_tools", tools))
            return self

        def bind(self, **kwargs):
            self.bind_calls.append(("bind", kwargs))
            return self

    fake_model = _FakeModel()

    async def _fake_provision(content, model_id, default_type, **kwargs):
        _ = (content, model_id, default_type, kwargs)
        return fake_model

    monkeypatch.setattr(
        "packages.core.ai.gemini_runtime.provision_langchain_model", _fake_provision
    )

    config = RunnableConfig(
        configurable={
            "gemini_features": {
                "thinking_level": "high",
                "structured_output_schema": {"type": "object"},
                "function_tools": [{"name": "fn_tool"}],
                "include_thoughts": True,
                "context_cache": {"handle": "cache-1", "ttl_seconds": 30},
                "media_resolution": "fhd",
            }
        }
    )

    model, features = await provision_with_gemini_features(
        content="hello",
        model_id=None,
        default_type="tools",
        config=config,
        thought_signature="sig-in-1",
    )

    assert model is fake_model
    assert ("bind_tools", [{"name": "fn_tool"}]) in fake_model.bind_calls
    assert ("bind", {"thinking_level": "high"}) in fake_model.bind_calls
    assert (
        "bind",
        {
            "response_schema": {"type": "object"},
            "response_mime_type": "application/json",
        },
    ) in fake_model.bind_calls
    assert ("bind", {"cached_content": "cache-1"}) in fake_model.bind_calls
    assert ("bind", {"media_resolution": "high"}) in fake_model.bind_calls
    assert ("bind", {"thought_signature": "sig-in-1"}) in fake_model.bind_calls
    assert set(features.effective_features) == {
        "thinking:high",
        "structured_output_schema",
        "function_calling_tools",
        "context_caching",
        "media_resolution:high",
    }
    assert features.cache_status == "provided"
    assert features.cache_ttl_seconds == 30


@pytest.mark.asyncio
async def test_provision_with_gemini_features_strict_mode_fails_fast_on_binding_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_provision(content, model_id, default_type, **kwargs):
        _ = (content, model_id, default_type, kwargs)
        return object()

    monkeypatch.setattr(
        "packages.core.ai.gemini_runtime.provision_langchain_model", _fake_provision
    )

    config = RunnableConfig(
        configurable={
            "gemini_features": {
                "thinking_level": "high",
                "strict_features": True,
            }
        }
    )

    with pytest.raises(ExternalServiceError, match="strict feature binding failed"):
        await provision_with_gemini_features(
            content="hello",
            model_id="model:strict",
            default_type="transformation",
            config=config,
        )


@pytest.mark.asyncio
async def test_ainvoke_with_gemini_telemetry_records_metrics_and_effective_features() -> (
    None
):
    model = AsyncMock()
    model.ainvoke.return_value = SimpleNamespace(content="ok")
    features = SimpleNamespace(
        thinking_level="high",
        structured_output_schema={"type": "object"},
        function_tools=[],
        include_thoughts=False,
        context_cache=None,
        media_resolution="auto",
        fallback_reason=None,
        effective_features=["thinking:high"],
        cache_status=None,
        cache_ttl_seconds=None,
    )

    response, telemetry = await ainvoke_with_gemini_telemetry(
        model,
        "payload",
        features=features,  # type: ignore[arg-type]
        fallback_reason="fallback_for_test",
    )

    assert response.content == "ok"
    assert "thinking:high" in telemetry["configured_features"]
    assert telemetry["effective_features"] == ["thinking:high"]
    assert "thinking:high" in telemetry["enabled_features"]
    assert telemetry["duration_ms"] >= 0
    assert telemetry["fallback_reason"] == "fallback_for_test"
    assert telemetry["cache"]["status"] is None
    assert telemetry["feature_binding"]["failed"] == []
    assert telemetry["feature_binding"]["strict"] is False
    assert telemetry["thought_signature_out"] is None
    assert telemetry["extracted_result"]["tool_calls"] == []


@pytest.mark.asyncio
async def test_ainvoke_with_gemini_telemetry_reports_binding_failures() -> None:
    model = AsyncMock()
    model.ainvoke.return_value = SimpleNamespace(content="ok")
    features = SimpleNamespace(
        thinking_level="high",
        structured_output_schema=None,
        function_tools=[],
        include_thoughts=False,
        context_cache=None,
        media_resolution="auto",
        fallback_reason=None,
        effective_features=["thinking:high"],
        cache_status=None,
        cache_ttl_seconds=None,
        strict_features=False,
        binding_failures=[{"feature": "thinking", "reason": "bind_not_available"}],
    )

    _, telemetry = await ainvoke_with_gemini_telemetry(
        model,
        "payload",
        features=features,  # type: ignore[arg-type]
    )

    assert telemetry["feature_binding"]["configured"] == ["thinking:high"]
    assert telemetry["feature_binding"]["effective"] == ["thinking:high"]
    assert telemetry["feature_binding"]["failed"] == [
        {"feature": "thinking", "reason": "bind_not_available"}
    ]
    assert telemetry["feature_binding"]["strict"] is False


@pytest.mark.asyncio
async def test_ainvoke_with_gemini_telemetry_applies_per_part_media_resolution() -> (
    None
):
    model = AsyncMock()
    model.ainvoke.return_value = SimpleNamespace(content="ok")
    features = SimpleNamespace(
        thinking_level="high",
        structured_output_schema=None,
        function_tools=[],
        include_thoughts=False,
        context_cache=None,
        media_resolution="auto",
        fallback_reason=None,
        effective_features=["thinking:high"],
        cache_status=None,
        cache_ttl_seconds=None,
    )
    payload = [
        HumanMessage(
            content=[
                {"type": "text", "text": "hello"},
                {
                    "type": "image",
                    "mime_type": "image/png",
                    "metadata": {"media_resolution": "medium"},
                },
            ]
        )
    ]

    await ainvoke_with_gemini_telemetry(
        model,
        payload,
        features=features,  # type: ignore[arg-type]
    )

    invoke_payload = model.ainvoke.call_args.args[0]
    parts = invoke_payload[0].content
    assert parts[0]["media_resolution"] == "low"
    assert parts[1]["media_resolution"] == "medium"


@pytest.mark.asyncio
async def test_ainvoke_with_gemini_telemetry_requires_include_thoughts_for_function_calls() -> (
    None
):
    model = AsyncMock()
    model.ainvoke.return_value = SimpleNamespace(content="ok")
    features = SimpleNamespace(
        thinking_level="high",
        structured_output_schema=None,
        function_tools=[{"name": "fn"}],
        include_thoughts=False,
        context_cache=None,
        media_resolution="auto",
        fallback_reason=None,
        effective_features=[],
        cache_status=None,
        cache_ttl_seconds=None,
    )

    with pytest.raises(InvalidInputError, match="include_thoughts"):
        await ainvoke_with_gemini_telemetry(
            model,
            "payload",
            features=features,  # type: ignore[arg-type]
        )


@pytest.mark.asyncio
async def test_ainvoke_with_gemini_telemetry_raises_when_function_call_signature_missing() -> (
    None
):
    model = AsyncMock()
    model.ainvoke.return_value = SimpleNamespace(
        content=[{"type": "tool_call", "name": "lookup"}],
        additional_kwargs={"tool_calls": [{"name": "lookup"}]},
    )
    features = SimpleNamespace(
        thinking_level="high",
        structured_output_schema=None,
        function_tools=[{"name": "lookup"}],
        include_thoughts=True,
        context_cache=None,
        media_resolution="auto",
        fallback_reason=None,
        effective_features=[],
        cache_status=None,
        cache_ttl_seconds=None,
    )

    with pytest.raises(ExternalServiceError, match="missing thought signature"):
        await ainvoke_with_gemini_telemetry(
            model,
            "payload",
            features=features,  # type: ignore[arg-type]
        )


@pytest.mark.asyncio
async def test_ainvoke_with_gemini_telemetry_extracts_signature_and_tool_calls() -> (
    None
):
    model = AsyncMock()
    model.ainvoke.return_value = SimpleNamespace(
        content=[
            {
                "type": "thought",
                "text": "Plan tool usage",
                "thought": True,
                "thought_signature": "sig-out-2",
            }
        ],
        additional_kwargs={"tool_calls": [{"name": "lookup", "args": {"q": "x"}}]},
    )
    features = SimpleNamespace(
        thinking_level="high",
        structured_output_schema=None,
        function_tools=[{"name": "lookup"}],
        include_thoughts=True,
        context_cache=None,
        media_resolution="auto",
        fallback_reason=None,
        effective_features=[],
        cache_status=None,
        cache_ttl_seconds=None,
    )

    _, telemetry = await ainvoke_with_gemini_telemetry(
        model,
        "payload",
        features=features,  # type: ignore[arg-type]
        thought_signature="sig-in-2",
    )

    assert telemetry["thought_signature_in"] == "sig-in-2"
    assert telemetry["thought_signature_out"] == "sig-out-2"
    assert telemetry["extracted_result"]["tool_calls"] == [
        {"name": "lookup", "args": {"q": "x"}}
    ]
    assert telemetry["extracted_result"]["thoughts"] == ["Plan tool usage"]


@pytest.mark.asyncio
async def test_run_transformation_includes_gemini_telemetry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chain = AsyncMock()

    async def _fake_provision_with_features(
        *, content, model_id, default_type, config, **kwargs
    ):
        assert content
        assert default_type == "transformation"
        assert kwargs["thought_signature"] == "sig-in-3"
        return chain, SimpleNamespace(
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
        _ = (features, thought_signature, fallback_reason)
        return SimpleNamespace(content="transformed"), {
            "enabled_features": ["thinking:high"],
            "duration_ms": 12,
            "fallback_reason": None,
            "extracted_result": {"thought_signature": "sig-out-3"},
        }

    monkeypatch.setattr(
        "packages.core.graphs.transformation.provision_with_gemini_features",
        _fake_provision_with_features,
    )
    monkeypatch.setattr(
        "packages.core.graphs.transformation.ainvoke_with_gemini_telemetry",
        _fake_invoke,
    )
    monkeypatch.setattr(
        "packages.core.graphs.transformation.DefaultPrompts.get_instance",
        AsyncMock(return_value=SimpleNamespace(transformation_instructions="")),
    )

    transformation = MagicMock()
    transformation.prompt = "Summarize the text."
    transformation.title = "Summary"

    state = {
        "input_text": "source text",
        "transformation": transformation,
        "source": None,
        "thought_signature": "sig-in-3",
    }
    result = await run_transformation(
        state, RunnableConfig(configurable={"model_id": ""})
    )

    assert result["output"] == "transformed"
    assert result["gemini_telemetry"]["enabled_features"] == ["thinking:high"]
    assert result["thought_signature"] == "sig-out-3"
