from __future__ import annotations

from types import SimpleNamespace

import pytest

from packages.core.ai import gemini_runtime as gr
from packages.core.ai.gemini_features import GeminiFeaturesConfig


def test_bool_and_strict_feature_helpers_cover_fallback_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_STRICT_FEATURES", "maybe")
    assert gr._normalize_boolish(True, default=False) is True
    assert (
        gr._resolve_strict_features(GeminiFeaturesConfig(strict_features=True)) is True
    )


def test_extraction_helpers_skip_non_mapping_nodes() -> None:
    tool_calls = gr._extract_tool_calls(
        {
            "nested": [
                1,
                {"tool_calls": [{"name": "lookup"}]},
                {"function_call": {"name": "call_1"}},
            ]
        }
    )
    assert {"name": "lookup"} in tool_calls
    assert {"function_call": {"name": "call_1"}} in tool_calls

    signature = gr._extract_thought_signature({"nested": [42, {"signature": "sig-x"}]})
    assert signature == "sig-x"


def test_apply_media_resolution_to_parts_keeps_item_when_parts_are_unchanged() -> None:
    message = SimpleNamespace(
        content=[{"type": "text", "text": "hello", "media_resolution": "low"}]
    )

    updated, counts = gr._apply_media_resolution_to_parts([message], "auto")

    assert updated[0] is message
    assert counts == {"low": 1}


def test_apply_features_to_model_uses_bind_fallback_after_bind_tools_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gr, "build_gemini_invoke_kwargs", lambda _features: {})

    class _Model:
        def bind_tools(self, _tools):
            raise RuntimeError("bind_tools_failed")

        def bind(self, **_kwargs):
            return self

    _, effective_features, binding_failures = gr._apply_features_to_model(
        _Model(),
        GeminiFeaturesConfig(function_tools=[{"name": "lookup"}]),
        None,
        strict_features=False,
    )

    assert "function_calling_tools" in effective_features
    assert binding_failures == []
