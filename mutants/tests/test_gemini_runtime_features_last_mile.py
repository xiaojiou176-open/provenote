from types import SimpleNamespace

import pytest

from packages.core.ai import gemini_features as gf
from packages.core.ai import gemini_runtime as gr
from packages.core.ai.gemini_features import (
    GeminiContextCacheConfig,
    GeminiFeaturesConfig,
)


class _AwaitableValue:
    def __await__(self):
        if False:  # pragma: no cover
            yield None
        return None


def test_gemini_features_helper_edge_cases() -> None:
    assert gf._normalize_context_cache(
        {"ttl_seconds": True}
    ) == GeminiContextCacheConfig(handle=None, ttl_seconds=1)
    assert gf._normalize_context_cache({"ttl_seconds": "bad"}) is None
    assert gf._normalize_context_cache({"handle": "h", "ttl_seconds": "bad"}) == (
        GeminiContextCacheConfig(handle="h", ttl_seconds=None)
    )
    assert gf._normalize_context_cache({"handle": "h", "ttl_seconds": ""}) == (
        GeminiContextCacheConfig(handle="h", ttl_seconds=None)
    )

    assert gf._normalize_tools({"name": "single"}) == [{"name": "single"}]
    assert gf._normalize_tools("bad-tools") == []

    assert gf._extract_configurable(None) == {}
    assert gf._normalize_bool("no", default=True) is False
    assert gf._normalize_bool("unknown", default=True) is True


def test_runtime_bind_and_boolish_helpers() -> None:
    class _Model:
        def bind(self, **_kwargs):
            return _AwaitableValue()

    model, applied, reason = gr._try_bind(_Model(), thinking_level="high")

    assert isinstance(model, _Model)
    assert applied is False
    assert reason == "bind_returned_awaitable"

    assert gr._normalize_boolish(None, default=True) is True
    assert gr._normalize_boolish("yes") is True
    assert gr._normalize_boolish("0", default=True) is False
    assert gr._normalize_boolish("weird", default=True) is True


def test_bind_thought_signature_returns_first_successful_binding() -> None:
    class _SnakeModel:
        def bind(self, **kwargs):
            if "thought_signature" in kwargs:
                return "snake-bound"
            raise RuntimeError("unexpected")

    assert gr._bind_thought_signature(_SnakeModel(), "sig-1") == "snake-bound"


def test_response_and_extraction_helpers_cover_nested_shapes() -> None:
    assert gr._response_to_payload({"tool_calls": [{"name": "top"}]}) == {
        "tool_calls": [{"name": "top"}]
    }

    payload = {
        "tool_calls": [{"name": "top"}],
        "nested": [
            "skip",
            {"function_call": {"name": "f1"}},
            {"function_calls": [{"name": "f2"}]},
            {"tool_calls": [{"name": "nested-call"}]},
            {"thoughtSignature": "sig-camel"},
        ],
    }

    tool_calls = gr._extract_tool_calls(payload)
    assert {"function_call": {"name": "f1"}} in tool_calls
    assert {"function_call": {"name": "f2"}} in tool_calls
    assert {"name": "nested-call"} in tool_calls

    assert gr._extract_thought_signature(payload) == "sig-camel"

    assert gr._extract_thoughts({"content": "no-list"}) == []
    assert gr._extract_thoughts(
        {
            "content": [
                "skip",
                {"thinking": True, "text": "Thought A"},
                {"thought": True, "text": "   "},
                {"thought": True, "text": "Thought B"},
            ]
        }
    ) == ["Thought A", "Thought B"]

    assert gr._extract_configurable(None) == {}


def test_media_resolution_helpers_cover_nonstandard_payload_items() -> None:
    assert gr._part_media_resolution({"type": "image"}, "auto") == "high"
    assert gr._part_media_resolution({"type": "audio"}, "auto") == "medium"
    assert gr._part_media_resolution({"type": "unknown"}, "high") == "high"
    assert gr._part_media_resolution({"type": "unknown"}, "auto") is None

    class _Message:
        def __init__(self, content):
            self.content = content

    payload = [
        SimpleNamespace(content="not-a-list"),
        _Message([42, {"type": "text", "text": "hello"}]),
        _Message([{"type": "image", "mime_type": "image/png"}]),
    ]

    updated, counts = gr._apply_media_resolution_to_parts(payload, "auto")

    assert updated[0] is payload[0]
    assert updated[1] is not payload[1]
    assert updated[1].content[0] == 42
    assert updated[1].content[1]["media_resolution"] == "low"
    assert updated[2].content[0]["media_resolution"] == "high"
    assert counts["low"] == 1
    assert counts["high"] == 1


def test_apply_features_to_model_records_fallback_failures_and_bind_only_success() -> (
    None
):
    class _FailingBindToolsModel:
        def bind_tools(self, _tools):
            raise RuntimeError("bind_tools_failed")

        def bind(self, **_kwargs):
            raise RuntimeError("bind_failed")

    failing_features = GeminiFeaturesConfig(
        thinking_level="high",
        structured_output_schema={"type": "object"},
        function_tools=[{"name": "lookup"}],
        include_thoughts=True,
        context_cache=GeminiContextCacheConfig(handle="cache-h", ttl_seconds=30),
        media_resolution="high",
    )

    _, effective_features, failures = gr._apply_features_to_model(
        _FailingBindToolsModel(),
        failing_features,
        "sig-in",
        strict_features=False,
    )

    assert effective_features == []
    assert any(
        item["feature"] == "function_calling_tools"
        and item["reason"].startswith("bind_tools_error")
        for item in failures
    )
    assert any(item["feature"] == "thought_signature" for item in failures)

    class _BindOnlyModel:
        def __init__(self):
            self.bind_calls = []

        def bind(self, **kwargs):
            self.bind_calls.append(kwargs)
            return self

    bind_only_features = GeminiFeaturesConfig(function_tools=[{"name": "lookup"}])
    bind_only_model = _BindOnlyModel()

    _, effective_features, failures = gr._apply_features_to_model(
        bind_only_model,
        bind_only_features,
        None,
        strict_features=False,
    )

    assert "function_calling_tools" in effective_features
    assert failures == []


def test_resolve_strict_features_and_cache_hydration_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_STRICT_FEATURES", "true")
    assert (
        gr._resolve_strict_features(GeminiFeaturesConfig(strict_features=False)) is True
    )

    monkeypatch.setenv("GEMINI_STRICT_FEATURES", "0")
    assert (
        gr._resolve_strict_features(GeminiFeaturesConfig(strict_features=True)) is False
    )

    monkeypatch.delenv("GEMINI_STRICT_FEATURES", raising=False)
    assert (
        gr._resolve_strict_features(GeminiFeaturesConfig(strict_features=True)) is True
    )

    cache_manager = SimpleNamespace(
        resolve=lambda *_args, **_kwargs: SimpleNamespace(
            handle="cache-handle", ttl_seconds=42, status="hit"
        )
    )
    monkeypatch.setitem(
        gr._hydrate_context_cache.__globals__,
        "get_default_cache_manager",
        lambda: cache_manager,
    )

    hydrated = gr._hydrate_context_cache(
        GeminiFeaturesConfig(
            context_cache=GeminiContextCacheConfig(handle=None, ttl_seconds=15)
        ),
        content={"hello": "world"},
        model_id="gemini-model",
        default_type="chat",
        config={"configurable": {"gemini_context_cache_key": "explicit-cache-key"}},
    )

    assert hydrated.context_cache.handle == "cache-handle"
    assert hydrated.context_cache.ttl_seconds == 42
    assert hydrated.cache_status == "hit"
    assert hydrated.cache_ttl_seconds == 42

    assert (
        gr._build_cache_key(
            content="ignored",
            model_id="x",
            default_type="chat",
            config={"configurable": {"gemini_context_cache_key": "manual-key"}},
        )
        == "manual-key"
    )


def test_telemetry_payload_and_ainvoke_guardrails() -> None:
    telemetry = gr._telemetry_payload(
        GeminiFeaturesConfig(
            function_tools=[{"name": "lookup"}],
            effective_features=["function_calling_tools"],
        ),
        duration_ms=123,
        fallback_reason="fallback",
        media_resolution_parts={"high": 2},
    )
    assert telemetry["duration_ms"] == 123
    assert telemetry["fallback_reason"] == "fallback"
    assert telemetry["feature_binding"]["effective"] == ["function_calling_tools"]
    assert telemetry["media_resolution_parts"] == {"high": 2}


@pytest.mark.asyncio
async def test_ainvoke_with_gemini_telemetry_errors_for_missing_thought_settings() -> (
    None
):
    class _DummyModel:
        async def ainvoke(self, _payload):
            return {"content": []}

    with pytest.raises(gr.InvalidInputError):
        await gr.ainvoke_with_gemini_telemetry(
            _DummyModel(),
            payload=[],
            features=GeminiFeaturesConfig(
                function_tools=[{"name": "lookup"}], include_thoughts=False
            ),
        )

    with pytest.raises(gr.ExternalServiceError):
        await gr.ainvoke_with_gemini_telemetry(
            _DummyModel(),
            payload=[],
            features=GeminiFeaturesConfig(
                function_tools=[{"name": "lookup"}], include_thoughts=True
            ),
            thought_signature="sig-in",
        )
