from langchain_core.runnables import RunnableConfig

from packages.core.ai.gemini_features import (
    build_gemini_invoke_kwargs,
    build_gemini_model_kwargs,
    enabled_feature_names,
    normalize_media_resolution,
    normalize_thinking_level,
    parse_gemini_features_config,
)


def test_normalizers_apply_safe_defaults() -> None:
    assert normalize_thinking_level(None) == "high"
    assert normalize_thinking_level("invalid") == "high"
    assert normalize_media_resolution("4k") == "native"
    assert normalize_media_resolution("??") == "auto"


def test_parse_gemini_features_from_runnable_config() -> None:
    config = RunnableConfig(
        configurable={
            "gemini_features": {
                "thinking_level": "medium",
                "structured_output_schema": {"type": "object"},
                "function_tools": [{"name": "lookup"}],
                "include_thoughts": "true",
                "context_cache": {"handle": "cache-handle", "ttl_seconds": "120"},
                "media_resolution": "hd",
                "fallback_reason": "provider_fallback",
                "strict_features": "true",
            }
        }
    )

    features = parse_gemini_features_config(config)
    kwargs = build_gemini_model_kwargs(features)
    invoke_kwargs = build_gemini_invoke_kwargs(features)

    assert kwargs["thinking_level"] == "medium"
    assert kwargs["response_schema"] == {"type": "object"}
    assert kwargs["response_mime_type"] == "application/json"
    assert kwargs["structured_output_schema"] == {"type": "object"}
    assert kwargs["function_tools"] == [{"name": "lookup"}]
    assert kwargs["include_thoughts"] is True
    assert kwargs["context_cache"] == {"handle": "cache-handle", "ttl_seconds": 120}
    assert kwargs["cached_content"] == "cache-handle"
    assert kwargs["media_resolution"] == "high"
    assert invoke_kwargs == {
        "thinking_level": "medium",
        "response_schema": {"type": "object"},
        "response_mime_type": "application/json",
        "cached_content": "cache-handle",
        "include_thoughts": True,
        "media_resolution": "high",
    }
    assert "function_calling_tools" in enabled_feature_names(features)
    assert "include_thoughts" in enabled_feature_names(features)
    assert features.fallback_reason == "provider_fallback"
    assert features.strict_features is True
