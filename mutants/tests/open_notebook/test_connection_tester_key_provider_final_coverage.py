from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import SecretStr

import packages.core.ai.connection_tester as connection_tester
import packages.core.ai.key_provider as key_provider


def test_resolve_startup_gemini_model_falls_back_when_env_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(connection_tester, "read_env", lambda *_a, **_k: "")

    resolved = connection_tester._resolve_startup_gemini_model(None)

    assert resolved == connection_tester.DEFAULT_STARTUP_GEMINI_MODEL


@pytest.mark.asyncio
async def test_get_default_credential_config_returns_first_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cred = SimpleNamespace(
        to_esperanto_config=lambda: {"api_key": "db-key", "model": "gemini-custom"}
    )
    monkeypatch.setattr(
        connection_tester.Credential, "get_by_provider", AsyncMock(return_value=[cred])
    )

    result = await connection_tester._get_default_credential_config("google")

    assert result == {"api_key": "db-key", "model": "gemini-custom"}


@pytest.mark.asyncio
async def test_provider_connection_config_id_path_truncates_unknown_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cred = SimpleNamespace(
        to_esperanto_config=lambda: {
            "api_key": "cfg-key",
            "model": "gemini-from-credential",
        }
    )
    monkeypatch.setattr(
        connection_tester.Credential, "get", AsyncMock(return_value=cred)
    )

    long_error = "x" * 140

    async def _raise_unknown(api_key: str, model_name: str) -> tuple[bool, str]:
        assert api_key == "cfg-key"
        assert model_name == "gemini-from-credential"
        raise RuntimeError(long_error)

    exception_mock = MagicMock()
    monkeypatch.setattr(connection_tester.logger, "exception", exception_mock)
    monkeypatch.setattr(connection_tester, "test_google_connection", _raise_unknown)

    success, message = await connection_tester.test_provider_connection(
        "google", config_id="cred-42"
    )

    assert success is False
    assert (
        message
        == "Connection test failed. Check provider configuration and server logs."
    )
    exception_mock.assert_called_once()


@pytest.mark.asyncio
async def test_individual_model_embedding_empty_result_is_still_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeModelManager:
        async def get_model(self, _model_id: str):
            return SimpleNamespace(aembed=AsyncMock(return_value=[]))

    monkeypatch.setattr("packages.core.ai.models.ModelManager", FakeModelManager)

    result = await connection_tester.test_individual_model(
        SimpleNamespace(id="embed-empty", type="embedding", provider="google")
    )

    assert result == (True, "Embedding successful")


@pytest.mark.asyncio
async def test_individual_model_tts_voice_discovery_failure_falls_back_to_alloy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenVoices:
        def keys(self):
            raise RuntimeError("voice discovery broken")

    class FakeTTS:
        available_voices = BrokenVoices()

        async def agenerate_speech(self, text: str, voice: str):
            assert "Notebooklab" in text
            assert voice == "alloy"
            return SimpleNamespace()

    class FakeModelManager:
        async def get_model(self, _model_id: str):
            return FakeTTS()

    exception_mock = MagicMock()
    monkeypatch.setattr(connection_tester.logger, "exception", exception_mock)
    monkeypatch.setattr("packages.core.ai.models.ModelManager", FakeModelManager)

    result = await connection_tester.test_individual_model(
        SimpleNamespace(id="tts-1", type="text_to_speech", provider="custom-provider")
    )

    assert result == (True, "Speech generation successful")
    exception_mock.assert_called_once()


@pytest.mark.asyncio
async def test_individual_model_error_can_map_to_successful_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class RaisingModelManager:
        async def get_model(self, _model_id: str):
            raise RuntimeError("rate limit exceeded")

    exception_mock = MagicMock()
    monkeypatch.setattr(connection_tester.logger, "exception", exception_mock)
    monkeypatch.setattr("packages.core.ai.models.ModelManager", RaisingModelManager)

    result = await connection_tester.test_individual_model(
        SimpleNamespace(id="lang-1", type="language", provider="google")
    )

    assert result == (True, "Rate limited - but connection works")
    exception_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_api_key_returns_secret_value_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    debug_mock = MagicMock()
    monkeypatch.setattr(key_provider.logger, "debug", debug_mock)
    monkeypatch.setattr(
        key_provider,
        "_get_default_credential",
        AsyncMock(return_value=SimpleNamespace(api_key=SecretStr("sk-db-real"))),
    )

    result = await key_provider.get_api_key("google")

    assert result == "sk-db-real"
    debug_mock.assert_called_once()
