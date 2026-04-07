from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import packages.core.ai.connection_tester as connection_tester


class _FakeCredential:
    def __init__(self, config):
        self._config = config

    def to_esperanto_config(self):
        return dict(self._config)


@pytest.mark.asyncio
async def test_resolve_google_api_key_returns_none_when_sources_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(connection_tester, "read_env", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(connection_tester, "get_api_key", AsyncMock(return_value=None))

    assert await connection_tester._resolve_google_api_key() == (None, "none")


def test_resolve_startup_gemini_model_uses_default_when_env_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(connection_tester, "read_env", lambda *_args, **_kwargs: "")

    assert (
        connection_tester._resolve_startup_gemini_model(None)
        == connection_tester.DEFAULT_STARTUP_GEMINI_MODEL
    )


@pytest.mark.asyncio
async def test_get_default_credential_config_returns_first_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        connection_tester.Credential,
        "get_by_provider",
        AsyncMock(return_value=[_FakeCredential({"api_key": "k", "model": "m"})]),
    )

    assert await connection_tester._get_default_credential_config("google") == {
        "api_key": "k",
        "model": "m",
    }


@pytest.mark.asyncio
async def test_test_provider_connection_uses_config_id_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_mock = AsyncMock(return_value=_FakeCredential({"api_key": "k", "model": "m"}))
    test_conn_mock = AsyncMock(return_value=(True, "ok"))

    monkeypatch.setattr(connection_tester.Credential, "get", get_mock)
    monkeypatch.setattr(connection_tester, "test_google_connection", test_conn_mock)

    assert await connection_tester.test_provider_connection(
        "google", config_id="cred-1"
    ) == (
        True,
        "ok",
    )
    get_mock.assert_awaited_once_with("cred-1")
    test_conn_mock.assert_awaited_once_with("k", "m")


@pytest.mark.asyncio
async def test_test_provider_connection_truncates_unknown_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        connection_tester,
        "_get_default_credential_config",
        AsyncMock(return_value={"api_key": "k"}),
    )
    monkeypatch.setattr(connection_tester, "get_api_key", AsyncMock(return_value="k"))
    monkeypatch.setattr(
        connection_tester,
        "test_google_connection",
        AsyncMock(side_effect=Exception("x" * 120)),
    )

    log_mock = MagicMock()
    monkeypatch.setattr(connection_tester.logger, "exception", log_mock)

    success, message = await connection_tester.test_provider_connection("google")

    assert success is False
    assert (
        message
        == "Connection test failed. Check provider configuration and server logs."
    )
    log_mock.assert_called_once()


@pytest.mark.asyncio
async def test_test_individual_model_embedding_empty_result_returns_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    embedding_model_instance = SimpleNamespace(aembed=AsyncMock(return_value=[]))

    class _Manager:
        async def get_model(self, _model_id):
            return embedding_model_instance

    monkeypatch.setattr("packages.core.ai.models.ModelManager", _Manager)

    model = SimpleNamespace(id="embed-1", type="embedding", provider="google")

    assert await connection_tester.test_individual_model(model) == (
        True,
        "Embedding successful",
    )


@pytest.mark.asyncio
async def test_test_individual_model_tts_voice_probe_error_falls_back_to_alloy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _BrokenVoices:
        def keys(self):
            raise RuntimeError("voice list unavailable")

    tts_model_instance = SimpleNamespace(
        available_voices=_BrokenVoices(),
        agenerate_speech=AsyncMock(return_value=SimpleNamespace()),
    )

    class _Manager:
        async def get_model(self, _model_id):
            return tts_model_instance

    monkeypatch.setattr("packages.core.ai.models.ModelManager", _Manager)

    log_mock = MagicMock()
    monkeypatch.setattr(connection_tester.logger, "exception", log_mock)

    model = SimpleNamespace(id="tts-1", type="text_to_speech", provider="custom")

    assert await connection_tester.test_individual_model(model) == (
        True,
        "Speech generation successful",
    )
    tts_model_instance.agenerate_speech.assert_awaited_once_with(
        text="Hello from Provenote",
        voice="alloy",
    )
    log_mock.assert_called_once()


@pytest.mark.asyncio
async def test_test_individual_model_uses_successful_error_normalization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    language_model = SimpleNamespace(
        achat_complete=AsyncMock(side_effect=Exception("rate limit hit"))
    )

    class _Manager:
        async def get_model(self, _model_id):
            return language_model

    monkeypatch.setattr("packages.core.ai.models.ModelManager", _Manager)

    model = SimpleNamespace(id="lang-1", type="language", provider="google")

    assert await connection_tester.test_individual_model(model) == (
        True,
        "Rate limited - but connection works",
    )
