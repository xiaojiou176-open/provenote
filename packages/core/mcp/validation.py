"""Validation helpers shared by the Provenote MCP server."""

from __future__ import annotations

from math import isfinite
from typing import Any, Mapping, TypeVar, cast

ActionT = TypeVar("ActionT")
PayloadT = TypeVar("PayloadT")


def ensure_non_empty(value: str, field: str, max_length: int = 4000) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{field} cannot be empty")
    if len(text) > max_length:
        raise ValueError(f"{field} exceeds max length {max_length}")
    return text


def ensure_int_range(value: int, field: str, minimum: int, maximum: int) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    if value < minimum or value > maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return value


def ensure_allowed(value: str, field: str, allowed: set[str]) -> str:
    normalized = value.strip().lower()
    if normalized not in allowed:
        allowed_csv = ", ".join(sorted(allowed))
        raise ValueError(f"{field} must be one of: {allowed_csv}")
    return normalized


def ensure_score(value: float, field: str) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    score = float(value)
    if not isfinite(score):
        raise ValueError(f"{field} must be a finite number")
    if score < 0 or score > 1:
        raise ValueError(f"{field} must be between 0 and 1")
    return score


def ensure_bool(value: bool, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def normalize_string_list(
    values: list[str] | None,
    field: str,
    *,
    max_length: int = 160,
    max_items: int = 200,
) -> list[str]:
    if values is None:
        return []
    if len(values) > max_items:
        raise ValueError(f"{field} exceeds max item count {max_items}")
    return [
        ensure_non_empty(value, f"{field}[{index}]", max_length=max_length)
        for index, value in enumerate(values)
    ]


def validate_settings_updates(updates: dict[str, Any]) -> dict[str, Any]:
    if not updates:
        raise ValueError("updates cannot be empty")

    allowed_keys = {
        "default_content_processing_engine_doc",
        "default_content_processing_engine_url",
        "default_embedding_option",
        "auto_delete_files",
        "youtube_preferred_languages",
    }
    unknown = sorted(key for key in updates if key not in allowed_keys)
    if unknown:
        raise ValueError(f"Unsupported settings keys: {', '.join(unknown)}")

    normalized = dict(updates)
    enum_constraints = {
        "default_content_processing_engine_doc": {"auto", "docling", "simple"},
        "default_content_processing_engine_url": {
            "auto",
            "firecrawl",
            "jina",
            "simple",
        },
        "default_embedding_option": {"ask", "always", "never"},
        "auto_delete_files": {"yes", "no"},
    }
    for key, allowed in enum_constraints.items():
        if key in normalized and normalized[key] is not None:
            if not isinstance(normalized[key], str):
                raise ValueError(f"{key} must be a string")
            normalized[key] = ensure_allowed(normalized[key], key, allowed)

    if "youtube_preferred_languages" not in normalized:
        return normalized

    languages = normalized["youtube_preferred_languages"]
    if languages is None:
        return normalized
    if not isinstance(languages, list):
        raise ValueError("youtube_preferred_languages must be a list of language codes")
    if not languages:
        raise ValueError("youtube_preferred_languages cannot be empty")
    if len(languages) > 20:
        raise ValueError("youtube_preferred_languages exceeds max length 20")

    normalized["youtube_preferred_languages"] = [
        ensure_non_empty(
            language, f"youtube_preferred_languages[{index}]", max_length=16
        )
        if isinstance(language, str)
        else (_raise_language_type(index))
        for index, language in enumerate(languages)
    ]
    return normalized


def _raise_language_type(index: int) -> str:
    raise ValueError(f"youtube_preferred_languages[{index}] must be a string")


def validate_action_data(
    action: ActionT,
    data: dict[str, Any],
    schema_map: Mapping[ActionT, type[PayloadT]],
) -> PayloadT:
    schema = cast(Any, schema_map[action])
    return cast(PayloadT, schema.model_validate(data))
