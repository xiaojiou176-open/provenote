"""Gemini runtime helpers for unified advanced feature handling."""

from __future__ import annotations

import copy
import inspect
import os
import time
from dataclasses import replace
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from packages.core.ai.gemini_cache import get_default_cache_manager
from packages.core.ai.gemini_features import (
    GeminiContextCacheConfig,
    GeminiFeaturesConfig,
    build_gemini_invoke_kwargs,
    build_gemini_model_kwargs,
    enabled_feature_names,
    normalize_media_resolution,
    parse_gemini_features_config,
)
from packages.core.ai.provision import provision_langchain_model
from packages.core.exceptions import ExternalServiceError, InvalidInputError


def _copy_mapping_list(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(item) for item in items]


_TRUE_VALUES = {"1", "true", "yes", "y", "on"}
_FALSE_VALUES = {"0", "false", "no", "n", "off"}


def _try_bind(model: Any, **kwargs: Any) -> Tuple[Any, bool, Optional[str]]:
    bind_fn = getattr(model, "bind", None)
    if not callable(bind_fn):
        return model, False, "bind_not_available"
    if inspect.iscoroutinefunction(bind_fn):
        return model, False, "bind_is_async"
    try:
        bound = bind_fn(**kwargs)
        if inspect.isawaitable(bound):
            return model, False, "bind_returned_awaitable"
        return bound, True, None
    except Exception as exc:
        return model, False, f"bind_error:{type(exc).__name__}"


def _normalize_boolish(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return default


def _resolve_strict_features(features: GeminiFeaturesConfig) -> bool:
    env_raw = os.getenv("GEMINI_STRICT_FEATURES")
    if env_raw is not None:
        normalized = str(env_raw).strip().lower()
        if normalized in _TRUE_VALUES:
            return True
        if normalized in _FALSE_VALUES:
            return False
    return bool(features.strict_features)


def _bind_thought_signature(model: Any, thought_signature: Optional[str]) -> Any:
    signature = (thought_signature or "").strip()
    if not signature:
        return model
    bound_model, applied, _reason = _try_bind(model, thought_signature=signature)
    if applied:
        return bound_model
    bound_model, applied, _reason = _try_bind(model, thoughtSignature=signature)
    if applied:
        return bound_model
    return model


def _iter_nodes(value: Any):
    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from _iter_nodes(child)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_nodes(item)


def _response_to_payload(response: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for field in ("content", "additional_kwargs", "response_metadata", "tool_calls"):
        if hasattr(response, field):
            payload[field] = getattr(response, field)
    if isinstance(response, Mapping):
        payload.update(dict(response))
    return payload


def _extract_tool_calls(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    direct_tool_calls = payload.get("tool_calls")
    if isinstance(direct_tool_calls, list):
        output.extend(
            dict(item) for item in direct_tool_calls if isinstance(item, Mapping)
        )
    for node in _iter_nodes(payload):
        if not isinstance(node, Mapping):
            continue
        node_tool_calls = node.get("tool_calls")
        if isinstance(node_tool_calls, list):
            output.extend(
                dict(item) for item in node_tool_calls if isinstance(item, Mapping)
            )
        function_call = node.get("function_call")
        if isinstance(function_call, Mapping):
            output.append({"function_call": dict(function_call)})
        function_calls = node.get("function_calls")
        if isinstance(function_calls, list):
            output.extend(
                {"function_call": dict(item)}
                for item in function_calls
                if isinstance(item, Mapping)
            )
    return output


def _extract_thought_signature(payload: Mapping[str, Any]) -> Optional[str]:
    for node in _iter_nodes(payload):
        if not isinstance(node, Mapping):
            continue
        for key in ("thought_signature", "thoughtSignature", "signature"):
            value = node.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _extract_thoughts(payload: Mapping[str, Any]) -> list[str]:
    thoughts: list[str] = []
    content = payload.get("content")
    if not isinstance(content, list):
        return thoughts
    for item in content:
        if not isinstance(item, Mapping):
            continue
        if item.get("thought") is True or item.get("thinking") is True:
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                thoughts.append(text.strip())
    return thoughts


def extract_gemini_response_artifacts(
    response: Any, *, include_thoughts: bool
) -> Dict[str, Any]:
    payload = _response_to_payload(response)
    extracted: Dict[str, Any] = {
        "tool_calls": _extract_tool_calls(payload),
        "thought_signature": _extract_thought_signature(payload),
    }
    if include_thoughts:
        extracted["thoughts"] = _extract_thoughts(payload)
    return extracted


def _extract_configurable(config: Optional[RunnableConfig]) -> Mapping[str, Any]:
    if not config:
        return {}
    configurable = config.get("configurable")
    return configurable if isinstance(configurable, Mapping) else {}


def _build_cache_key(
    *,
    content: Any,
    model_id: Optional[str],
    default_type: str,
    config: Optional[RunnableConfig],
) -> str:
    configurable = _extract_configurable(config)
    explicit = configurable.get("gemini_context_cache_key")
    if explicit:
        return str(explicit)
    content_hash = hash(str(content))
    return f"{default_type}:{model_id or 'default'}:{content_hash}"


def _hydrate_context_cache(
    features: GeminiFeaturesConfig,
    *,
    content: Any,
    model_id: Optional[str],
    default_type: str,
    config: Optional[RunnableConfig],
) -> GeminiFeaturesConfig:
    if not features.context_cache:
        return features
    cache_manager = get_default_cache_manager()
    cache_key = _build_cache_key(
        content=content,
        model_id=model_id,
        default_type=default_type,
        config=config,
    )
    resolution = cache_manager.resolve(
        cache_key,
        requested_handle=features.context_cache.handle,
        ttl_seconds=features.context_cache.ttl_seconds,
    )
    return replace(
        features,
        context_cache=GeminiContextCacheConfig(
            handle=resolution.handle,
            ttl_seconds=resolution.ttl_seconds,
        ),
        cache_status=resolution.status,
        cache_ttl_seconds=resolution.ttl_seconds,
    )


def _part_media_resolution(
    part: Mapping[str, Any], default_resolution: str
) -> Optional[str]:
    metadata = part.get("metadata")
    metadata_map = metadata if isinstance(metadata, Mapping) else {}
    candidate = metadata_map.get("media_resolution", part.get("media_resolution"))
    normalized = (
        normalize_media_resolution(str(candidate)) if candidate is not None else "auto"
    )
    if normalized != "auto":
        return normalized

    part_type = str(part.get("type", "")).lower()
    mime_type = str(part.get("mime_type", "")).lower()
    if part_type in {"image", "image_url"} or mime_type.startswith("image/"):
        return "high"
    if part_type in {"audio", "video"} or mime_type.startswith(("audio/", "video/")):
        return "medium"
    if part_type in {"text", "text_plain"}:
        return "low"
    if default_resolution != "auto":
        return default_resolution
    return None


def _apply_media_resolution_to_parts(
    payload: Any, default_resolution: str
) -> Tuple[Any, Dict[str, int]]:
    counts: Dict[str, int] = {}
    if not isinstance(payload, list):
        return payload, counts

    updated_payload = []
    for item in payload:
        item_content = getattr(item, "content", None)
        if not isinstance(item_content, list):
            updated_payload.append(item)
            continue

        content_changed = False
        updated_parts = []
        for raw_part in item_content:
            if not isinstance(raw_part, Mapping):
                updated_parts.append(raw_part)
                continue

            part = dict(raw_part)
            resolution = _part_media_resolution(part, default_resolution)
            if resolution:
                previous = part.get("media_resolution")
                if previous != resolution:
                    part["media_resolution"] = resolution
                    content_changed = True
                counts[resolution] = counts.get(resolution, 0) + 1
            updated_parts.append(part)

        if content_changed:
            model_copy = getattr(item, "model_copy", None)
            if callable(model_copy):
                updated_payload.append(model_copy(update={"content": updated_parts}))
            else:
                item_copy = copy.copy(item)
                setattr(item_copy, "content", updated_parts)
                updated_payload.append(item_copy)
        else:
            updated_payload.append(item)
    return updated_payload, counts


def _apply_features_to_model(
    model: Any,
    features: GeminiFeaturesConfig,
    thought_signature: Optional[str],
    *,
    strict_features: bool,
) -> Tuple[Any, list[str], list[Mapping[str, str]]]:
    effective_features: list[str] = []
    binding_failures: list[Mapping[str, str]] = []
    active_model = model
    invoke_kwargs = build_gemini_invoke_kwargs(features)

    def _record_failure(feature_name: str, reason: str) -> None:
        binding_failures.append({"feature": feature_name, "reason": reason})

    if features.function_tools:
        applied = False
        bind_tools_fn = getattr(active_model, "bind_tools", None)
        if callable(bind_tools_fn):
            try:
                active_model = bind_tools_fn(
                    _copy_mapping_list(features.function_tools)
                )
                effective_features.append("function_calling_tools")
                applied = True
            except Exception as exc:
                active_model, applied, bind_reason = _try_bind(
                    active_model, tools=_copy_mapping_list(features.function_tools)
                )
                if applied:
                    effective_features.append("function_calling_tools")
                else:
                    combined_reason = (
                        f"bind_tools_error:{type(exc).__name__}; "
                        f"{bind_reason or 'bind_not_available'}"
                    )
                    _record_failure("function_calling_tools", combined_reason)
        else:
            active_model, applied, bind_reason = _try_bind(
                active_model, tools=_copy_mapping_list(features.function_tools)
            )
            if applied:
                effective_features.append("function_calling_tools")
            else:
                _record_failure(
                    "function_calling_tools",
                    bind_reason or "bind_not_available",
                )

    if "thinking_level" in invoke_kwargs:
        active_model, applied, reason = _try_bind(
            active_model, thinking_level=invoke_kwargs["thinking_level"]
        )
        if applied:
            effective_features.append(f"thinking:{features.thinking_level}")
        else:
            _record_failure("thinking", reason or "bind_failed")

    if features.structured_output_schema:
        active_model, applied, reason = _try_bind(
            active_model,
            response_schema=dict(features.structured_output_schema),
            response_mime_type="application/json",
        )
        if applied:
            effective_features.append("structured_output_schema")
        else:
            _record_failure("structured_output_schema", reason or "bind_failed")

    if "cached_content" in invoke_kwargs:
        active_model, applied, reason = _try_bind(
            active_model, cached_content=invoke_kwargs["cached_content"]
        )
        if applied:
            effective_features.append("context_caching")
        else:
            _record_failure("context_caching", reason or "bind_failed")

    if features.media_resolution and features.media_resolution != "auto":
        active_model, applied, reason = _try_bind(
            active_model, media_resolution=features.media_resolution
        )
        if applied:
            effective_features.append(f"media_resolution:{features.media_resolution}")
        else:
            _record_failure(
                f"media_resolution:{features.media_resolution}",
                reason or "bind_failed",
            )

    signature = (thought_signature or "").strip()
    if signature:
        active_model, applied, reason = _try_bind(
            active_model, thought_signature=signature
        )
        if not applied:
            active_model, applied, reason = _try_bind(
                active_model, thoughtSignature=signature
            )
        if not applied:
            _record_failure("thought_signature", reason or "bind_failed")

    if strict_features and binding_failures:
        details = ", ".join(
            f"{item['feature']}={item['reason']}" for item in binding_failures
        )
        raise ExternalServiceError(
            "Gemini strict feature binding failed: "
            f"{details}. Disable strict mode or use a compatible model binding interface."
        )

    return active_model, effective_features, binding_failures


def _telemetry_payload(
    features: GeminiFeaturesConfig,
    duration_ms: int,
    fallback_reason: Optional[str],
    media_resolution_parts: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    configured_features = enabled_feature_names(features)
    effective_features = features.effective_features or configured_features
    binding_failures = getattr(features, "binding_failures", [])
    strict_features = bool(getattr(features, "strict_features", False))
    payload = {
        "configured_features": configured_features,
        "effective_features": effective_features,
        # Keep legacy telemetry key for backward compatibility.
        "enabled_features": effective_features,
        "duration_ms": duration_ms,
        "fallback_reason": fallback_reason or features.fallback_reason,
        "cache": {
            "status": features.cache_status,
            "ttl_seconds": features.cache_ttl_seconds,
            "handle": features.context_cache.handle if features.context_cache else None,
        },
        "feature_binding": {
            "configured": configured_features,
            "effective": effective_features,
            "failed": [dict(item) for item in binding_failures],
            "strict": strict_features,
        },
    }
    if media_resolution_parts:
        payload["media_resolution_parts"] = dict(media_resolution_parts)
    return payload


async def provision_with_gemini_features(
    *,
    content: Any,
    model_id: Optional[str],
    default_type: str,
    config: Optional[RunnableConfig],
    thought_signature: Optional[str] = None,
    **kwargs: Any,
) -> Tuple[BaseChatModel, GeminiFeaturesConfig]:
    features = parse_gemini_features_config(config)
    strict_features = _resolve_strict_features(features)
    features = _hydrate_context_cache(
        features,
        content=content,
        model_id=model_id,
        default_type=default_type,
        config=config,
    )
    model_kwargs = build_gemini_model_kwargs(features)
    merged_kwargs = dict(kwargs)
    merged_kwargs.update(model_kwargs)
    model = await provision_langchain_model(
        content,
        model_id,
        default_type,
        **merged_kwargs,
    )
    model_with_features, effective_features, binding_failures = (
        _apply_features_to_model(
            model,
            features,
            thought_signature,
            strict_features=strict_features,
        )
    )
    return model_with_features, replace(
        features,
        effective_features=effective_features,
        strict_features=strict_features,
        binding_failures=binding_failures,
    )


async def ainvoke_with_gemini_telemetry(
    model: BaseChatModel,
    payload: Any,
    *,
    features: GeminiFeaturesConfig,
    thought_signature: Optional[str] = None,
    fallback_reason: Optional[str] = None,
) -> Tuple[Any, Dict[str, Any]]:
    if features.function_tools and not features.include_thoughts:
        raise InvalidInputError(
            "Gemini function calling requires thought signatures. "
            "Enable gemini_features.include_thoughts=true."
        )
    runtime_payload = payload
    media_part_counts: Dict[str, int] = {}
    if features.media_resolution:
        runtime_payload, media_part_counts = _apply_media_resolution_to_parts(
            payload, features.media_resolution
        )
    started = time.perf_counter()
    invoke_model = _bind_thought_signature(model, thought_signature)
    response = await invoke_model.ainvoke(runtime_payload)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    telemetry = _telemetry_payload(
        features,
        elapsed_ms,
        fallback_reason,
        media_resolution_parts=media_part_counts,
    )
    extracted = extract_gemini_response_artifacts(
        response, include_thoughts=features.include_thoughts
    )
    if features.function_tools and not extracted.get("thought_signature"):
        raise ExternalServiceError(
            "Gemini function calling response is missing thought signature; "
            "cannot continue tool-calling chain safely."
        )
    telemetry["thought_signature_in"] = thought_signature
    telemetry["thought_signature_out"] = extracted.get("thought_signature")
    telemetry["extracted_result"] = extracted
    return response, telemetry
