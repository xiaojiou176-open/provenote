"""Centralized runtime settings and ENV governance helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


class SettingsValidationError(ValueError):
    """Raised when environment configuration is invalid."""


def read_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Read a single ENV variable by name.

    Resolution order:
    1) {NAME}
    2) default
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip()
    return value if value else default


def read_env_str(name: str, default: str) -> str:
    """Read a required string setting with explicit default."""
    value = read_env(name, default)
    return default if value is None else value


def read_bool(name: str, default: bool = False) -> bool:
    value = read_env(name)
    if value is None:
        return default
    normalized = value.lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise SettingsValidationError(
        f"Invalid boolean value for {name}: {value!r}. "
        f"Use one of {sorted(_TRUE_VALUES | _FALSE_VALUES)}."
    )


def read_int(name: str, default: int) -> int:
    value = read_env(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        raise SettingsValidationError(
            f"Invalid integer value for {name}: {value!r}"
        ) from None


def read_float(name: str, default: float) -> float:
    value = read_env(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        raise SettingsValidationError(
            f"Invalid float value for {name}: {value!r}"
        ) from None


# These provider-specific ENV names are retained to detect and block legacy
# configuration surfaces during migration/reference periods. Their presence here
# does not imply that the active runtime contract is multi-provider.
LEGACY_PROVIDER_ENV_VARS: Dict[str, tuple[str, ...]] = {
    "openai": ("OPENAI_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "groq": ("GROQ_API_KEY",),
    "mistral": ("MISTRAL_API_KEY",),
    "deepseek": ("DEEPSEEK_API_KEY",),
    "xai": ("XAI_API_KEY",),
    "openrouter": ("OPENROUTER_API_KEY", "OPENROUTER_BASE_URL"),
    "voyage": ("VOYAGE_API_KEY",),
    "elevenlabs": ("ELEVENLABS_API_KEY",),
    "ollama": ("OLLAMA_API_BASE", "OLLAMA_BASE_URL"),
    "vertex": ("VERTEX_PROJECT", "VERTEX_LOCATION", "GOOGLE_APPLICATION_CREDENTIALS"),
    "azure": (
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_ENDPOINT_LLM",
        "AZURE_OPENAI_ENDPOINT_EMBEDDING",
        "AZURE_OPENAI_ENDPOINT_STT",
        "AZURE_OPENAI_ENDPOINT_TTS",
        "AZURE_OPENAI_API_KEY_LLM",
        "AZURE_OPENAI_API_KEY_EMBEDDING",
        "AZURE_OPENAI_API_KEY_STT",
        "AZURE_OPENAI_API_KEY_TTS",
        "AZURE_OPENAI_API_VERSION_LLM",
        "AZURE_OPENAI_API_VERSION_EMBEDDING",
        "AZURE_OPENAI_API_VERSION_STT",
        "AZURE_OPENAI_API_VERSION_TTS",
    ),
    "openai_compatible": (
        "OPENAI_COMPATIBLE_BASE_URL",
        "OPENAI_COMPATIBLE_API_KEY",
        "OPENAI_COMPATIBLE_BASE_URL_LLM",
        "OPENAI_COMPATIBLE_BASE_URL_EMBEDDING",
        "OPENAI_COMPATIBLE_BASE_URL_STT",
        "OPENAI_COMPATIBLE_BASE_URL_TTS",
        "OPENAI_COMPATIBLE_API_KEY_LLM",
        "OPENAI_COMPATIBLE_API_KEY_EMBEDDING",
        "OPENAI_COMPATIBLE_API_KEY_STT",
        "OPENAI_COMPATIBLE_API_KEY_TTS",
    ),
}

# Allowed Google runtime ENV in ENV-first policy.
GOOGLE_PROVIDER_ENV_VARS: tuple[str, ...] = (
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
)

LEGACY_PROVIDER_ENV_BLOCKLIST: tuple[str, ...] = tuple(
    sorted(
        {
            env_var
            for env_vars in LEGACY_PROVIDER_ENV_VARS.values()
            for env_var in env_vars
        }
    )
)


def detect_legacy_provider_env() -> Dict[str, bool]:
    """Return provider->bool map indicating legacy provider ENV usage."""
    result: Dict[str, bool] = {}
    for provider, env_vars in LEGACY_PROVIDER_ENV_VARS.items():
        result[provider] = any(bool(read_env(env_var, "")) for env_var in env_vars)
    return result


def list_legacy_provider_env_vars() -> list[str]:
    """List currently set legacy provider ENV vars."""
    found: list[str] = []
    for env_vars in LEGACY_PROVIDER_ENV_VARS.values():
        for env_var in env_vars:
            if read_env(env_var, ""):
                found.append(env_var)
    return sorted(set(found))


@dataclass(frozen=True)
class Settings:
    api_host: str
    api_port: int
    api_reload: bool
    api_client_timeout: float
    api_url: str
    internal_api_url: str
    surreal_url: str
    surreal_user: str
    surreal_password: Optional[str]
    surreal_namespace: str
    surreal_database: str
    open_notebook_password: Optional[str]
    open_notebook_chunk_size: int
    open_notebook_chunk_overlap: Optional[int]
    open_notebook_phoenix_enabled: bool
    open_notebook_phoenix_collector_endpoint: str
    open_notebook_phoenix_project_name: str
    open_notebook_phoenix_api_key: Optional[str]
    gemini_model: Optional[str]


def get_settings() -> Settings:
    default_api_url = "http://127.0.0.1:5055"
    api_url = read_env_str("API_URL", default_api_url)
    internal_api_url = read_env_str("INTERNAL_API_URL", default_api_url)
    return Settings(
        api_host=read_env_str("API_HOST", "127.0.0.1"),
        api_port=read_int("API_PORT", 5055),
        api_reload=read_bool("API_RELOAD", True),
        api_client_timeout=read_float("API_CLIENT_TIMEOUT", 300.0),
        api_url=api_url,
        internal_api_url=internal_api_url,
        surreal_url=read_env_str("SURREAL_URL", "ws://127.0.0.1:8000/rpc"),
        surreal_user=read_env_str("SURREAL_USER", "root"),
        surreal_password=read_env("SURREAL_PASSWORD"),
        surreal_namespace=read_env_str("SURREAL_NAMESPACE", "open_notebook"),
        surreal_database=read_env_str("SURREAL_DATABASE", "open_notebook"),
        open_notebook_password=read_env("OPEN_NOTEBOOK_PASSWORD"),
        open_notebook_chunk_size=read_int("OPEN_NOTEBOOK_CHUNK_SIZE", 1200),
        open_notebook_chunk_overlap=(
            read_int("OPEN_NOTEBOOK_CHUNK_OVERLAP", -1)
            if read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP") is not None
            else None
        ),
        open_notebook_phoenix_enabled=read_bool("OPEN_NOTEBOOK_PHOENIX_ENABLED", False),
        open_notebook_phoenix_collector_endpoint=read_env_str(
            "OPEN_NOTEBOOK_PHOENIX_COLLECTOR_ENDPOINT",
            "http://127.0.0.1:6006/v1/traces",
        ),
        open_notebook_phoenix_project_name=read_env_str(
            "OPEN_NOTEBOOK_PHOENIX_PROJECT_NAME", "open-notebook"
        ),
        open_notebook_phoenix_api_key=read_env("OPEN_NOTEBOOK_PHOENIX_API_KEY"),
        gemini_model=read_env("GEMINI_MODEL"),
    )
