"""Google GenAI SDK adapter for Gemini model operations."""

from __future__ import annotations

import asyncio
from typing import Dict, Iterable, List, Literal, TypedDict

import pydantic.root_model  # noqa: F401
from google import genai

from packages.core.ai.model_strategy import GEMINI_MODEL_FLASH_30
from packages.core.observability.logger import logger

CapabilityState = Literal["supported", "preview", "unsupported"]


class CapabilityEntry(TypedDict):
    status: CapabilityState
    detail: str


class CapabilityMatrix(TypedDict):
    language: CapabilityEntry
    embedding: CapabilityEntry
    speech_to_text: CapabilityEntry
    text_to_speech: CapabilityEntry


def _normalize_action(action: str) -> str:
    return action.replace("_", "").replace("-", "").lower()


def build_google_capability_matrix(model_names: Iterable[str]) -> CapabilityMatrix:
    names = [name.lower() for name in model_names]

    has_language = any("gemini" in name for name in names)
    has_embedding = any("embed" in name for name in names)
    has_speech_to_text = any(
        hint in name
        for name in names
        for hint in ("speech", "stt", "audio", "transcribe")
    )
    has_text_to_speech = any(
        hint in name for name in names for hint in ("tts", "speech", "audio")
    )

    return {
        "language": {
            "status": "supported" if has_language else "unsupported",
            "detail": "Gemini language models discovered"
            if has_language
            else "No Gemini language model found",
        },
        "embedding": {
            "status": "supported" if has_embedding else "preview",
            "detail": "Gemini embedding model discovered"
            if has_embedding
            else "Embedding model not discovered yet; may require explicit sync",
        },
        "speech_to_text": {
            "status": "supported" if has_speech_to_text else "preview",
            "detail": "Speech-capable model discovered"
            if has_speech_to_text
            else "No speech-capable model discovered yet; keep as preview",
        },
        "text_to_speech": {
            "status": "supported" if has_text_to_speech else "preview",
            "detail": "TTS-capable model discovered"
            if has_text_to_speech
            else "No TTS-capable model discovered yet; keep as preview",
        },
    }


async def list_google_models(api_key: str) -> List[Dict[str, object]]:
    """List Google models via google-genai SDK."""
    if not api_key:
        return []

    def _list_sync() -> List[Dict[str, object]]:
        client = genai.Client(api_key=api_key)
        try:
            result: List[Dict[str, object]] = []
            for model in client.models.list():
                name = (getattr(model, "name", "") or "").replace("models/", "")
                if not name:
                    continue
                raw_actions = getattr(model, "supported_actions", []) or []
                actions = [str(action) for action in raw_actions]
                normalized_actions = {_normalize_action(action) for action in actions}
                model_type = "language"
                name_lower = name.lower()
                if (
                    "generateaudio" in normalized_actions
                    or "tts" in name_lower
                    or "texttospeech" in normalized_actions
                ):
                    model_type = "text_to_speech"
                elif (
                    "transcribecontent" in normalized_actions
                    or "speech" in name_lower
                    or "audio" in name_lower
                    or "transcribe" in name_lower
                ):
                    model_type = "speech_to_text"
                elif "embedcontent" in normalized_actions or "embedding" in name_lower:
                    model_type = "embedding"

                result.append(
                    {
                        "name": name,
                        "provider": "google",
                        "model_type": model_type,
                        "description": getattr(model, "display_name", None),
                        "supported_actions": actions,
                    }
                )
            return result
        finally:
            client.close()

    return await asyncio.to_thread(_list_sync)


async def test_google_connection(
    api_key: str,
    model_name: str = GEMINI_MODEL_FLASH_30,
) -> tuple[bool, str]:
    """Validate Google credential via a minimal generate-content call."""
    if not api_key:
        return False, "No Google API key configured"

    def _test_sync() -> tuple[bool, str]:
        client = genai.Client(api_key=api_key)
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="ping",
            )
            text = getattr(response, "text", "") or ""
            if text.strip():
                return True, "Connection successful"
            return True, "Connection successful (empty response body)"
        finally:
            client.close()

    try:
        return await asyncio.to_thread(_test_sync)
    except Exception as exc:
        # Google GenAI raises SDK-specific ClientError/APIError objects for
        # model availability mismatches, so normalize them into probe results
        # instead of letting startup crash before fallbacks can run.
        logger.exception(
            "Google connection test raised SDK/runtime exception; normalizing for probe semantics."
        )
        message = str(exc).lower()
        if "401" in message or "unauthorized" in message:
            return False, "Invalid API key"
        if "403" in message or "forbidden" in message:
            return False, "API key lacks required permissions"
        if "429" in message or ("rate" in message and "limit" in message):
            return True, "Rate limited - but connection works"
        if "not found" in message and "model" in message:
            return True, "API key valid (test model not available)"
        truncated = str(exc)[:100] + "..." if len(str(exc)) > 100 else str(exc)
        return False, f"Error: {truncated}"


async def generate_google_text(
    *,
    api_key: str,
    model_name: str,
    prompt: str,
) -> str:
    """Generate text via Google GenAI SDK (adapter-only import boundary)."""
    if not api_key:
        raise RuntimeError("missing GEMINI_API_KEY")

    def _generate_sync() -> str:
        client = genai.Client(api_key=api_key)
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return (getattr(response, "text", "") or "").strip()
        finally:
            client.close()

    text = await asyncio.to_thread(_generate_sync)
    if not text:
        raise RuntimeError("empty gemini response")
    return text
