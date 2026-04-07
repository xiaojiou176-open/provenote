from __future__ import annotations

from types import SimpleNamespace

import pytest

from packages.core.ai import google_genai_adapter as adapter
from packages.core.ai.google_genai_adapter import (
    _normalize_action,
    build_google_capability_matrix,
    generate_google_text,
    list_google_models,
)
from packages.core.ai.google_genai_adapter import (
    test_google_connection as verify_google_connection,
)


class _FakeModels:
    def __init__(
        self, *, listed=None, generated=None, generate_exc: Exception | None = None
    ):
        self._listed = listed if listed is not None else []
        self._generated = generated
        self._generate_exc = generate_exc

    def list(self):
        if isinstance(self._listed, Exception):
            raise self._listed
        return self._listed

    def generate_content(self, *, model: str, contents: str):
        _ = (model, contents)
        if self._generate_exc is not None:
            raise self._generate_exc
        return self._generated


class _FakeClient:
    last_instance: "_FakeClient | None" = None
    list_payload = []
    list_exception: Exception | None = None
    generate_payload = None
    generate_exception: Exception | None = None

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.closed = False
        self.models = _FakeModels(
            listed=self.list_exception if self.list_exception else self.list_payload,
            generated=self.generate_payload,
            generate_exc=self.generate_exception,
        )
        type(self).last_instance = self

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def inline_to_thread(monkeypatch: pytest.MonkeyPatch):
    async def _inline(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(adapter.asyncio, "to_thread", _inline)


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch):
    _FakeClient.list_payload = []
    _FakeClient.list_exception = None
    _FakeClient.generate_payload = None
    _FakeClient.generate_exception = None
    _FakeClient.last_instance = None
    monkeypatch.setattr(adapter.genai, "Client", _FakeClient)
    return _FakeClient


def test_normalize_action_removes_separators_and_lowercases() -> None:
    assert _normalize_action("Generate-Audio_Content") == "generateaudiocontent"


def test_build_google_capability_matrix_marks_supported_modalities() -> None:
    matrix = build_google_capability_matrix(
        [
            "gemini-2.0-flash",
            "text-embedding-004",
            "gemini-tts-preview",
            "gemini-audio-transcribe",
        ]
    )
    assert matrix["language"]["status"] == "supported"
    assert matrix["embedding"]["status"] == "supported"
    assert matrix["speech_to_text"]["status"] == "supported"
    assert matrix["text_to_speech"]["status"] == "supported"


def test_build_google_capability_matrix_returns_preview_for_speech_without_models() -> (
    None
):
    matrix = build_google_capability_matrix(["gemini-2.0-flash"])
    assert matrix["language"]["status"] == "supported"
    assert matrix["embedding"]["status"] == "preview"
    assert matrix["speech_to_text"]["status"] == "preview"
    assert matrix["text_to_speech"]["status"] == "preview"


def test_build_google_capability_matrix_handles_non_gemini_models() -> None:
    matrix = build_google_capability_matrix(["text-embedding-004"])
    assert matrix["language"]["status"] == "unsupported"
    assert matrix["embedding"]["status"] == "supported"
    assert matrix["speech_to_text"]["status"] == "preview"
    assert matrix["text_to_speech"]["status"] == "preview"


@pytest.mark.asyncio
async def test_list_google_models_returns_empty_without_api_key() -> None:
    assert await list_google_models(api_key="") == []


@pytest.mark.asyncio
async def test_list_google_models_classifies_model_types(
    inline_to_thread, fake_client
) -> None:
    _ = inline_to_thread
    fake_client.list_payload = [
        SimpleNamespace(
            name="models/gemini-tts-preview",
            display_name="TTS",
            supported_actions=["generate_audio"],
        ),
        SimpleNamespace(
            name="models/gemini-audio-transcribe",
            display_name="STT",
            supported_actions=["transcribe-content"],
        ),
        SimpleNamespace(
            name="models/text-embedding-004",
            display_name="Embedding",
            supported_actions=["embed_content"],
        ),
        SimpleNamespace(
            name="models/gemini-3.0-pro",
            display_name="Language",
            supported_actions=[],
        ),
        SimpleNamespace(
            name="",
            display_name="Missing name",
            supported_actions=["generate_content"],
        ),
    ]

    models = await list_google_models(api_key="k")

    assert [item["name"] for item in models] == [
        "gemini-tts-preview",
        "gemini-audio-transcribe",
        "text-embedding-004",
        "gemini-3.0-pro",
    ]
    assert [item["model_type"] for item in models] == [
        "text_to_speech",
        "speech_to_text",
        "embedding",
        "language",
    ]
    assert models[0]["supported_actions"] == ["generate_audio"]
    assert fake_client.last_instance.closed is True


@pytest.mark.asyncio
async def test_list_google_models_closes_client_when_listing_fails(
    inline_to_thread, fake_client
) -> None:
    _ = inline_to_thread
    fake_client.list_exception = RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await list_google_models(api_key="k")

    assert fake_client.last_instance.closed is True


@pytest.mark.asyncio
async def test_google_connection_returns_error_when_key_missing() -> None:
    ok, message = await verify_google_connection(
        api_key="", model_name="gemini-3.0-flash"
    )
    assert ok is False
    assert message == "No Google API key configured"


@pytest.mark.asyncio
async def test_google_connection_success_and_empty_body_paths(
    inline_to_thread, fake_client
) -> None:
    _ = inline_to_thread

    fake_client.generate_payload = SimpleNamespace(text="pong")
    ok, message = await verify_google_connection(api_key="k", model_name="gemini")
    assert ok is True
    assert message == "Connection successful"

    fake_client.generate_payload = SimpleNamespace(text="   ")
    ok, message = await verify_google_connection(api_key="k", model_name="gemini")
    assert ok is True
    assert message == "Connection successful (empty response body)"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "expected_ok", "expected_message"),
    [
        (RuntimeError("401 unauthorized"), False, "Invalid API key"),
        (RuntimeError("403 forbidden"), False, "API key lacks required permissions"),
        (RuntimeError("429 rate limit"), True, "Rate limited - but connection works"),
        (
            RuntimeError("model not found"),
            True,
            "API key valid (test model not available)",
        ),
    ],
)
async def test_google_connection_maps_known_error_messages(
    inline_to_thread,
    fake_client,
    error: Exception,
    expected_ok: bool,
    expected_message: str,
) -> None:
    _ = inline_to_thread
    fake_client.generate_exception = error

    ok, message = await verify_google_connection(api_key="k", model_name="gemini")
    assert ok is expected_ok
    assert message == expected_message
    assert fake_client.last_instance.closed is True


@pytest.mark.asyncio
async def test_google_connection_truncates_unknown_errors(
    inline_to_thread, fake_client
) -> None:
    _ = inline_to_thread
    long_message = "x" * 150
    fake_client.generate_exception = RuntimeError(long_message)

    ok, message = await verify_google_connection(api_key="k", model_name="gemini")

    assert ok is False
    assert message == f"Error: {'x' * 100}..."


@pytest.mark.asyncio
async def test_generate_google_text_happy_path(inline_to_thread, fake_client) -> None:
    _ = inline_to_thread
    fake_client.generate_payload = SimpleNamespace(text="  generated text  ")

    text = await generate_google_text(api_key="k", model_name="gemini", prompt="hello")

    assert text == "generated text"
    assert fake_client.last_instance.closed is True


@pytest.mark.asyncio
async def test_generate_google_text_rejects_missing_api_key() -> None:
    with pytest.raises(RuntimeError, match="missing GEMINI_API_KEY"):
        await generate_google_text(api_key="", model_name="gemini", prompt="hello")


@pytest.mark.asyncio
async def test_generate_google_text_rejects_empty_response(
    inline_to_thread, fake_client
) -> None:
    _ = inline_to_thread
    fake_client.generate_payload = SimpleNamespace(text="   ")

    with pytest.raises(RuntimeError, match="empty gemini response"):
        await generate_google_text(api_key="k", model_name="gemini", prompt="hello")


@pytest.mark.asyncio
async def test_generate_google_text_closes_client_when_generation_raises(
    inline_to_thread, fake_client
) -> None:
    _ = inline_to_thread
    fake_client.generate_exception = OSError("network down")

    with pytest.raises(OSError, match="network down"):
        await generate_google_text(api_key="k", model_name="gemini", prompt="hello")

    assert fake_client.last_instance.closed is True
