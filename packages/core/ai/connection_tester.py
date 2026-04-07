"""
Connection testing for AI providers.

Gemini-only runtime: provider-level connection tests are restricted to Google.
Model-level tests remain provider-agnostic for already-registered models.
"""

import io
import struct
from typing import Any, List, Optional, Tuple, TypedDict, cast

from packages.core.ai.google_genai_adapter import test_google_connection
from packages.core.ai.key_provider import get_api_key
from packages.core.ai.model_strategy import (
    GEMINI_DEFAULT_FAST_PATH_MODEL,
    GEMINI_MODEL_FLASH_25,
    GEMINI_MODEL_FLASH_30,
    GEMINI_MODEL_PRO_30,
)
from packages.core.domain.credential import Credential
from packages.core.observability.logger import logger
from packages.core.settings import read_env

# Test models for provider-level connection checks.
# Format: (model_name, model_type)
TEST_MODELS = {
    "google": (GEMINI_MODEL_FLASH_25, "language"),
}

# Keep local startup on the repo's stable generate-content path by default.
DEFAULT_STARTUP_GEMINI_MODEL = GEMINI_MODEL_FLASH_25
STARTUP_GEMINI_MODEL_FALLBACKS = (
    "gemini-2.5-pro",
    GEMINI_MODEL_PRO_30,
    GEMINI_MODEL_FLASH_30,
)


class ModelProbeResult(TypedDict):
    provider: str
    model: str
    success: bool
    message: str
    key_source: str


class GeminiStartupProbeResult(TypedDict):
    model_probe_result: ModelProbeResult
    blocked_reason: Optional[str]
    remediation: List[str]


def _resolve_startup_gemini_model(configured_model: Optional[str] = None) -> str:
    model = configured_model or read_env("GEMINI_MODEL", DEFAULT_STARTUP_GEMINI_MODEL)
    if not model:
        return DEFAULT_STARTUP_GEMINI_MODEL
    return model.strip()


def _startup_probe_candidates(configured_model: Optional[str] = None) -> list[str]:
    configured_env_model = read_env("GEMINI_MODEL")
    primary = _resolve_startup_gemini_model(configured_model)
    explicit_model_requested = configured_model is not None or bool(
        configured_env_model and configured_env_model.strip()
    )

    candidates = [primary]
    if explicit_model_requested:
        return candidates

    for candidate in STARTUP_GEMINI_MODEL_FALLBACKS:
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


async def _resolve_google_api_key() -> tuple[Optional[str], str]:
    gemini_api_key = read_env("GEMINI_API_KEY")
    if gemini_api_key:
        return gemini_api_key, "environment:GEMINI_API_KEY"

    db_api_key = await get_api_key("google")
    if db_api_key:
        return db_api_key, "database:credential"

    return None, "none"


async def probe_startup_gemini_model(
    configured_model: Optional[str] = None,
) -> GeminiStartupProbeResult:
    """
    Probe startup Gemini model availability and return structured diagnostics.

    This probe is strict:
    - Missing API key blocks startup
    - Model-not-found blocks startup
    - Any connection failure blocks startup
    """
    probe_candidates = _startup_probe_candidates(configured_model)
    target_model = probe_candidates[0]
    api_key, key_source = await _resolve_google_api_key()

    if not api_key:
        return {
            "model_probe_result": {
                "provider": "google",
                "model": target_model,
                "success": False,
                "message": "No Google API key configured",
                "key_source": key_source,
            },
            "blocked_reason": "missing_google_api_key",
            "remediation": [
                "Set GEMINI_API_KEY, or add a Google credential in Settings -> API Keys.",
                "Restart the API after credentials are configured.",
            ],
        }

    unavailable_candidates: list[str] = []
    for target_model in probe_candidates:
        success, message = await test_google_connection(api_key, target_model)
        public_message = _safe_public_error_message(message)
        normalized_message = (message or "").lower()
        model_unavailable = (
            "model not available" in normalized_message
            or "not found" in normalized_message
        )

        if success and not model_unavailable:
            return {
                "model_probe_result": {
                    "provider": "google",
                    "model": target_model,
                    "success": True,
                    "message": public_message,
                    "key_source": key_source,
                },
                "blocked_reason": None,
                "remediation": ["No action required."],
            }

        if model_unavailable:
            unavailable_candidates.append(target_model)
            continue

        return {
            "model_probe_result": {
                "provider": "google",
                "model": target_model,
                "success": False,
                "message": public_message,
                "key_source": key_source,
            },
            "blocked_reason": "gemini_model_probe_failed",
            "remediation": [
                "Verify Google API key permissions and network access to Gemini API.",
                "Re-run connection test in Settings -> API Keys and restart the API.",
            ],
        }

    tried_models = (
        ", ".join(unavailable_candidates) if unavailable_candidates else target_model
    )
    return {
        "model_probe_result": {
            "provider": "google",
            "model": target_model,
            "success": False,
            "message": _safe_public_error_message(
                f"No startup probe candidate was available. Tried: {tried_models}."
            ),
            "key_source": key_source,
        },
        "blocked_reason": "gemini_model_unavailable",
        "remediation": [
            (
                f"Set GEMINI_MODEL to an available Google model, or leave GEMINI_MODEL unset so startup can fall back through the built-in candidates. Tried: {tried_models}."
            ),
            "Re-run connection test in Settings -> API Keys and restart the API.",
        ],
    }


async def _get_default_credential_config(provider: str) -> dict:
    """Get the first credential config for a provider, if present."""
    try:
        credentials = await Credential.get_by_provider(provider)
        if credentials:
            return credentials[0].to_esperanto_config()
    except Exception as exc:
        logger.exception(
            "Default credential config lookup failed provider={} error_type={}",
            provider,
            type(exc).__name__,
        )
    return {}


async def test_provider_connection(
    provider: str, model_type: str = "language", config_id: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Test if a provider API key is valid by making a minimal API call.

    Gemini-only runtime supports provider-level testing for Google only.

    Args:
        provider: Provider name (must be google)
        model_type: Reserved for backward compatibility.
        config_id: Optional specific credential ID to test.

    Returns:
        Tuple of (success: bool, message: str)
    """
    _ = model_type

    try:
        api_key: Optional[str] = None
        model_name: Optional[str] = None

        normalized_provider = provider.replace("-", "_")
        if normalized_provider != "google":
            return False, "Only Google provider is supported in Gemini-only mode"

        if config_id:
            try:
                cred = await Credential.get(config_id)
                config = cred.to_esperanto_config()
                api_key = config.get("api_key")
                model_name = config.get("model")
            except Exception as exc:
                logger.exception(
                    "Provider credential lookup failed provider={} config_id={} error_type={}",
                    normalized_provider,
                    config_id,
                    type(exc).__name__,
                )
                return False, f"Credential not found: {config_id}"
        else:
            config = await _get_default_credential_config(normalized_provider)
            api_key = config.get("api_key")
            model_name = config.get("model")

        if not api_key:
            api_key = await get_api_key(normalized_provider)
        if not api_key:
            return False, f"No database credential configured for {provider}"

        default_test_model, _default_type = TEST_MODELS[normalized_provider]
        model_to_use = model_name or default_test_model
        if not model_to_use:
            return False, "No test model configured for google"

        return await test_google_connection(api_key, model_to_use)

    except Exception as exc:
        error_msg = str(exc)

        if "401" in error_msg or "unauthorized" in error_msg.lower():
            return False, "Invalid API key"
        if "403" in error_msg or "forbidden" in error_msg.lower():
            return False, "API key lacks required permissions"
        if "rate" in error_msg.lower() and "limit" in error_msg.lower():
            # Rate limit means the key is valid but we hit limits
            return True, "Rate limited - but connection works"
        if "connection" in error_msg.lower() or "network" in error_msg.lower():
            return False, "Connection error - check network/endpoint"
        if "timeout" in error_msg.lower():
            return False, "Connection timed out - check network/endpoint"
        if "not found" in error_msg.lower() and "model" in error_msg.lower():
            # Model not found but auth worked - this is connectivity success.
            return True, "API key valid (test model not available)"

        logger.exception(
            "Provider connection test failed provider={} error_type={}",
            provider,
            type(exc).__name__,
        )
        return False, _safe_public_error_message(error_msg)


# Default voices for TTS testing per provider.
DEFAULT_TEST_VOICES = {
    "google": "Kore",
}


def _generate_test_wav() -> io.BytesIO:
    """Generate a minimal 0.5s silence WAV file in memory (16kHz, 16-bit mono)."""
    sample_rate = 16000
    num_samples = sample_rate // 2  # 0.5 seconds
    bits_per_sample = 16
    num_channels = 1
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = num_samples * block_align

    buf = io.BytesIO()
    # RIFF header
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    # fmt chunk
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))  # chunk size
    buf.write(struct.pack("<H", 1))  # PCM format
    buf.write(struct.pack("<H", num_channels))
    buf.write(struct.pack("<I", sample_rate))
    buf.write(struct.pack("<I", byte_rate))
    buf.write(struct.pack("<H", block_align))
    buf.write(struct.pack("<H", bits_per_sample))
    # data chunk
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(b"\x00" * data_size)  # silence

    buf.seek(0)
    buf.name = "test.wav"
    return buf


def _normalize_error_message(error_msg: str) -> Tuple[bool, str]:
    """Normalize common error patterns into user-friendly messages."""
    lower = error_msg.lower()

    if "401" in error_msg or "unauthorized" in lower:
        return False, "Invalid API key"
    if "403" in error_msg or "forbidden" in lower:
        return False, "API key lacks required permissions"
    if "rate" in lower and "limit" in lower:
        return True, "Rate limited - but connection works"
    if "not found" in lower and "model" in lower:
        return False, "Model not found on this provider"
    if "connection" in lower or "network" in lower:
        return False, "Connection error - check network/endpoint"
    if "timeout" in lower:
        return False, "Connection timed out - check network/endpoint"

    return False, error_msg


def _safe_public_error_message(error_msg: str) -> str:
    success, normalized = _normalize_error_message(error_msg)
    if success:
        return normalized
    if normalized != error_msg:
        return normalized
    return "Connection test failed. Check provider configuration and server logs."


async def test_individual_model(model) -> Tuple[bool, str]:
    """
    Test a specific model configuration end-to-end by making a real API call.

    Args:
        model: A Model instance (from packages.core.ai.models)

    Returns:
        Tuple of (success: bool, message: str)
    """
    from packages.core.ai.models import ModelManager

    try:
        manager = ModelManager()
        esp_model = await manager.get_model(model.id)

        if esp_model is None:
            return False, "Could not create model instance"

        if model.type == "language":
            language_model = cast(Any, esp_model)
            response = await language_model.achat_complete(
                messages=[{"role": "user", "content": "Hi!"}]
            )
            response_content = getattr(response, "content", None)
            text = (
                str(response_content)[:100] if response_content else "(empty response)"
            )
            return True, f"Response: {text}"

        if model.type == "embedding":
            embedding_model = cast(Any, esp_model)
            result = await embedding_model.aembed(["This is a test."])
            if result and len(result) > 0:
                dims = len(result[0])
                return True, f"Embedding dimensions: {dims}"
            return True, "Embedding successful"

        if model.type == "text_to_speech":
            tts_model = cast(Any, esp_model)
            voice = DEFAULT_TEST_VOICES.get(model.provider)
            if not voice and hasattr(tts_model, "available_voices"):
                try:
                    voices = tts_model.available_voices
                    if voices:
                        voice = next(iter(voices.keys()))
                except Exception as exc:
                    logger.exception(
                        "TTS voice discovery failed provider={} model_id={} error_type={}",
                        model.provider,
                        model.id,
                        type(exc).__name__,
                    )
            if not voice:
                voice = "alloy"

            result = await tts_model.agenerate_speech(
                text="Hello from Provenote", voice=voice
            )
            if result and hasattr(result, "content"):
                size = len(result.content)
                return True, f"Audio generated: {size} bytes"
            return True, "Speech generation successful"

        if model.type == "speech_to_text":
            stt_model = cast(Any, esp_model)
            audio_file = _generate_test_wav()
            result = await stt_model.atranscribe(audio_file=audio_file, language="en")
            text = str(result.text) if hasattr(result, "text") else str(result)
            return True, f"Transcription: {text[:100]}"

        return False, f"Unsupported model type: {model.type}"

    except Exception as exc:
        error_msg = str(exc)
        success, normalized = _normalize_error_message(error_msg)
        if success:
            return True, normalized
        logger.exception(
            "Individual model test failed model_id={} error_type={}",
            model.id,
            type(exc).__name__,
        )
        return False, normalized
