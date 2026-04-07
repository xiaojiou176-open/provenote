"""Gemini advanced capability configuration and normalization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

from langchain_core.runnables import RunnableConfig

ThinkingLevel = str
MediaResolution = str


@dataclass(frozen=True)
class GeminiContextCacheConfig:
    """Runtime context cache parameters."""

    handle: Optional[str] = None
    ttl_seconds: Optional[int] = None


@dataclass(frozen=True)
class GeminiFeaturesConfig:
    """Optional Gemini advanced runtime features."""

    thinking_level: ThinkingLevel = "high"
    structured_output_schema: Optional[Mapping[str, Any]] = None
    function_tools: List[Mapping[str, Any]] = field(default_factory=list)
    include_thoughts: bool = False
    context_cache: Optional[GeminiContextCacheConfig] = None
    media_resolution: Optional[MediaResolution] = None
    cache_status: Optional[str] = None
    cache_ttl_seconds: Optional[int] = None
    fallback_reason: Optional[str] = None
    effective_features: List[str] = field(default_factory=list)
    strict_features: bool = False
    binding_failures: List[Mapping[str, str]] = field(default_factory=list)


def normalize_thinking_level(value: Optional[str]) -> ThinkingLevel:
    normalized = str(value or "high").strip().lower()
    if normalized in {"low", "medium", "high"}:
        return normalized
    return "high"


def normalize_media_resolution(value: Optional[str]) -> MediaResolution:
    normalized = str(value or "auto").strip().lower()
    aliases = {
        "sd": "low",
        "ld": "low",
        "hd": "high",
        "fhd": "high",
        "full-hd": "high",
        "2k": "native",
        "4k": "native",
        "auto": "auto",
        "low": "low",
        "medium": "medium",
        "high": "high",
        "native": "native",
    }
    return aliases.get(normalized, "auto")


def _as_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, MutableMapping):
        return dict(value)
    return {}


def _normalize_context_cache(value: Any) -> Optional[GeminiContextCacheConfig]:
    payload = _as_mapping(value)
    if not payload:
        return None
    handle = payload.get("handle")
    ttl_raw = payload.get("ttl_seconds")
    ttl_seconds: Optional[int]
    if ttl_raw in (None, ""):
        ttl_seconds = None
    else:
        try:
            if isinstance(ttl_raw, bool):
                ttl_seconds = max(int(ttl_raw), 1)
            else:
                ttl_seconds = max(int(str(ttl_raw).strip()), 1)
        except (TypeError, ValueError):
            ttl_seconds = None
    if handle is None and ttl_seconds is None:
        return None
    return GeminiContextCacheConfig(
        handle=str(handle) if handle is not None else None,
        ttl_seconds=ttl_seconds,
    )


def _normalize_tools(value: Any) -> List[Mapping[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [dict(value)]
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        output: List[Mapping[str, Any]] = []
        for item in value:
            if isinstance(item, Mapping):
                output.append(dict(item))
        return output
    return []


def _extract_configurable(config: Optional[RunnableConfig]) -> Mapping[str, Any]:
    if not config:
        return {}
    configurable = config.get("configurable")
    return configurable if isinstance(configurable, Mapping) else {}


def _normalize_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def parse_gemini_features_config(
    config: Optional[RunnableConfig],
) -> GeminiFeaturesConfig:
    configurable = _extract_configurable(config)
    root_payload = configurable.get("gemini_features")
    payload = _as_mapping(root_payload)

    thinking_level = normalize_thinking_level(
        payload.get("thinking_level", configurable.get("gemini_thinking_level"))
    )
    schema = payload.get(
        "structured_output_schema", configurable.get("gemini_structured_output_schema")
    )
    structured_output_schema = schema if isinstance(schema, Mapping) else None

    tools = _normalize_tools(
        payload.get("function_tools", configurable.get("gemini_function_tools"))
    )
    include_thoughts = _normalize_bool(
        payload.get("include_thoughts", configurable.get("gemini_include_thoughts")),
        default=False,
    )
    context_cache = _normalize_context_cache(
        payload.get("context_cache", configurable.get("gemini_context_cache"))
    )
    media_resolution = normalize_media_resolution(
        payload.get("media_resolution", configurable.get("gemini_media_resolution"))
    )

    fallback_reason = payload.get(
        "fallback_reason", configurable.get("gemini_fallback_reason")
    )
    fallback_reason_text = str(fallback_reason) if fallback_reason else None
    strict_features = _normalize_bool(
        payload.get("strict_features", configurable.get("gemini_strict_features")),
        default=False,
    )

    return GeminiFeaturesConfig(
        thinking_level=thinking_level,
        structured_output_schema=structured_output_schema,
        function_tools=tools,
        include_thoughts=include_thoughts,
        context_cache=context_cache,
        media_resolution=media_resolution,
        fallback_reason=fallback_reason_text,
        strict_features=strict_features,
    )


def enabled_feature_names(features: GeminiFeaturesConfig) -> List[str]:
    names: List[str] = []
    if features.thinking_level:
        names.append(f"thinking:{features.thinking_level}")
    if features.structured_output_schema:
        names.append("structured_output_schema")
    if features.function_tools:
        names.append("function_calling_tools")
    if features.include_thoughts:
        names.append("include_thoughts")
    if features.context_cache:
        names.append("context_caching")
    if features.media_resolution and features.media_resolution != "auto":
        names.append(f"media_resolution:{features.media_resolution}")
    return names


def build_gemini_invoke_kwargs(features: GeminiFeaturesConfig) -> Dict[str, Any]:
    """Build Gemini runtime kwargs that are recognized by langchain-google-genai."""
    kwargs: Dict[str, Any] = {"thinking_level": features.thinking_level}
    if features.structured_output_schema:
        kwargs["response_schema"] = dict(features.structured_output_schema)
        kwargs["response_mime_type"] = "application/json"
    if features.context_cache and features.context_cache.handle:
        kwargs["cached_content"] = features.context_cache.handle
    if features.include_thoughts:
        kwargs["include_thoughts"] = True
    if features.media_resolution:
        kwargs["media_resolution"] = features.media_resolution
    return kwargs


def build_gemini_model_kwargs(features: GeminiFeaturesConfig) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = build_gemini_invoke_kwargs(features)
    # Keep legacy keys for backward compatibility with existing call sites/tests.
    if features.structured_output_schema:
        kwargs["structured_output_schema"] = dict(features.structured_output_schema)
    if features.function_tools:
        kwargs["function_tools"] = [dict(item) for item in features.function_tools]
    if features.include_thoughts:
        kwargs["include_thoughts"] = True
    if features.context_cache:
        kwargs["context_cache"] = {
            "handle": features.context_cache.handle,
            "ttl_seconds": features.context_cache.ttl_seconds,
        }
    if features.media_resolution:
        kwargs["media_resolution"] = features.media_resolution
    return kwargs
