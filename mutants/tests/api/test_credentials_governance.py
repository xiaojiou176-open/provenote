import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from packages.core.ai.connection_tester import _resolve_google_api_key
from packages.core.ai.key_provider import (
    get_provisioned_provider_config,
    provision_provider_keys,
)
from packages.core.ai.model_discovery import (
    get_provider_model_count,
    sync_provider_models,
)
from packages.core.domain.credential import Credential
from packages.core.settings import (
    GOOGLE_PROVIDER_ENV_VARS,
    LEGACY_PROVIDER_ENV_BLOCKLIST,
    LEGACY_PROVIDER_ENV_VARS,
    SettingsValidationError,
    read_bool,
    read_env,
    read_int,
)
from services.api.credentials_service import PROVIDER_ENV_CONFIG, get_provider_status
from services.api.main import (
    assert_gemini_model_bootstrap_probe,
    assert_no_legacy_provider_env,
)


@pytest.fixture
def client():
    with patch("services.api.main.AsyncMigrationManager") as mock_migration_manager:
        manager = mock_migration_manager.return_value
        manager.get_current_version = AsyncMock(return_value=16)
        manager.needs_migration = AsyncMock(return_value=False)
        with (
            patch("services.api.main.list_legacy_provider_env_vars", return_value=[]),
            patch(
                "services.api.main.assert_gemini_model_bootstrap_probe",
                new=AsyncMock(return_value=None),
            ),
        ):
            from services.api.main import app

            with TestClient(app) as test_client:
                auth_header_value = f"Bearer {os.environ['OPEN_NOTEBOOK_PASSWORD']}"
                test_client.headers.update({"Authorization": auth_header_value})
                yield test_client


def test_removed_env_migration_endpoints_are_not_available(client):
    env_status_response = client.get("/api/credentials/env-status")
    migrate_response = client.post("/api/credentials/migrate-from-env")

    assert env_status_response.status_code == 404
    assert migrate_response.status_code == 405
    assert env_status_response.json()["detail"] == "Credential not found"
    assert "Method Not Allowed" in migrate_response.text


@pytest.mark.asyncio
@patch(
    "services.api.credentials_service.evaluate_policy_effectiveness",
    new_callable=AsyncMock,
)
@patch("services.api.credentials_service.detect_legacy_provider_env")
@patch(
    "services.api.credentials_service.Credential.get_by_provider",
    new_callable=AsyncMock,
)
@patch("services.api.credentials_service.get_secret_from_env")
@patch("services.api.credentials_service.repo_query", new_callable=AsyncMock)
async def test_provider_status_prefers_environment_source_for_google(
    mock_repo_query,
    mock_get_secret,
    mock_get_by_provider,
    mock_detect_legacy_env,
    mock_evaluate_policy_effectiveness,
    monkeypatch,
):
    mock_get_secret.return_value = "encryption-key"
    mock_detect_legacy_env.return_value = {}
    mock_repo_query.return_value = []
    mock_evaluate_policy_effectiveness.return_value = {
        "effective": {
            "language": True,
            "embedding": False,
            "speech_to_text": False,
            "text_to_speech": False,
        },
        "active_provider": {
            "language": "google",
            "embedding": None,
            "speech_to_text": None,
            "text_to_speech": None,
        },
        "blocking_reason": {
            "language": None,
            "embedding": "not configured",
            "speech_to_text": "not configured",
            "text_to_speech": "not configured",
        },
    }
    monkeypatch.setenv("GEMINI_API_KEY", "env-google-key")

    async def by_provider(provider: str):
        return [SimpleNamespace(id="cred:1")] if provider == "google" else []

    mock_get_by_provider.side_effect = by_provider

    status = await get_provider_status()

    assert status["configured"]["google"] is True
    assert status["source"]["google"] == "environment"
    assert "environment" in set(status["source"].values())
    assert status["legacy_env_detected"]["google"] is False
    assert "language" in status["policy_effective"]
    assert "google" in status["provider_capabilities"]
    mock_evaluate_policy_effectiveness.assert_awaited_once_with({"google": True})
    google_models_query = mock_repo_query.call_args.args[0]
    assert "WHERE provider = 'google'" in google_models_query


@pytest.mark.asyncio
@patch(
    "services.api.credentials_service.evaluate_policy_effectiveness",
    new_callable=AsyncMock,
)
@patch("services.api.credentials_service.detect_legacy_provider_env")
@patch(
    "services.api.credentials_service.Credential.get_by_provider",
    new_callable=AsyncMock,
)
@patch("services.api.credentials_service.get_secret_from_env")
@patch("services.api.credentials_service.repo_query", new_callable=AsyncMock)
async def test_provider_status_handles_model_query_failure_with_capability_fallback(
    mock_repo_query,
    mock_get_secret,
    mock_get_by_provider,
    mock_detect_legacy_env,
    mock_evaluate_policy_effectiveness,
    monkeypatch,
):
    mock_get_secret.return_value = "encryption-key"
    mock_detect_legacy_env.return_value = {}
    mock_get_by_provider.return_value = []
    mock_repo_query.side_effect = RuntimeError("db query failed")
    mock_evaluate_policy_effectiveness.return_value = {
        "effective": {
            "language": True,
            "embedding": False,
            "speech_to_text": False,
            "text_to_speech": False,
        },
        "active_provider": {
            "language": "google",
            "embedding": None,
            "speech_to_text": None,
            "text_to_speech": None,
        },
        "blocking_reason": {
            "language": None,
            "embedding": "not configured",
            "speech_to_text": "not configured",
            "text_to_speech": "not configured",
        },
    }
    monkeypatch.setenv("GEMINI_API_KEY", "env-google-key")

    status = await get_provider_status()

    assert status["configured"]["google"] is True
    assert (
        status["provider_capabilities"]["google"]["language"]["status"] == "unsupported"
    )
    assert status["provider_capabilities"]["google"]["embedding"]["status"] == "preview"
    mock_repo_query.assert_awaited_once()
    mock_evaluate_policy_effectiveness.assert_awaited_once_with({"google": True})


@patch("services.api.routers.credentials.get_provider_status", new_callable=AsyncMock)
def test_status_endpoint_exposes_legacy_env_detected(mock_get_provider_status, client):
    mock_get_provider_status.return_value = {
        "configured": {"google": False},
        "source": {"google": "none"},
        "legacy_env_detected": {"google": True},
        "encryption_configured": True,
        "policy_effective": {
            "language": False,
            "embedding": False,
            "speech_to_text": False,
            "text_to_speech": False,
        },
        "policy_active_provider": {
            "language": None,
            "embedding": None,
            "speech_to_text": None,
            "text_to_speech": None,
        },
        "policy_blockers": {
            "language": "not configured",
            "embedding": "not configured",
            "speech_to_text": "not configured",
            "text_to_speech": "not configured",
        },
        "provider_capabilities": {
            "google": {
                "language": {"status": "preview", "detail": "n/a"},
                "embedding": {"status": "preview", "detail": "n/a"},
                "speech_to_text": {"status": "preview", "detail": "n/a"},
                "text_to_speech": {"status": "preview", "detail": "n/a"},
            }
        },
    }

    response = client.get("/api/credentials/status")
    assert response.status_code == 200
    assert response.json()["legacy_env_detected"]["google"] is True
    assert response.json()["source"]["google"] == "none"


def test_startup_fails_when_legacy_provider_env_exists():
    with patch(
        "services.api.main.list_legacy_provider_env_vars",
        return_value=["OPENAI_API_KEY"],
    ):
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            assert_no_legacy_provider_env()


def test_startup_allows_google_env_first_configuration():
    with patch("services.api.main.list_legacy_provider_env_vars", return_value=[]):
        assert_no_legacy_provider_env()


@pytest.mark.asyncio
async def test_startup_probe_blocks_when_model_probe_fails(monkeypatch):
    monkeypatch.setenv("OPEN_NOTEBOOK_SKIP_GEMINI_STARTUP_PROBE", "0")
    with patch(
        "services.api.main.probe_startup_gemini_model",
        new=AsyncMock(
            return_value={
                "model_probe_result": {
                    "provider": "google",
                    "model": "gemini-3.1-pro-preview",
                    "success": False,
                    "message": "Model not found",
                    "key_source": "environment:GEMINI_API_KEY",
                },
                "blocked_reason": "gemini_model_unavailable",
                "remediation": ["Set GEMINI_MODEL to an available model."],
            }
        ),
    ):
        with pytest.raises(RuntimeError, match="gemini_model_probe_blocked"):
            await assert_gemini_model_bootstrap_probe()


@pytest.mark.asyncio
async def test_startup_probe_passes_when_model_probe_succeeds(monkeypatch):
    monkeypatch.setenv("OPEN_NOTEBOOK_SKIP_GEMINI_STARTUP_PROBE", "0")
    with patch(
        "services.api.main.probe_startup_gemini_model",
        new=AsyncMock(
            return_value={
                "model_probe_result": {
                    "provider": "google",
                    "model": "gemini-3.1-pro-preview",
                    "success": True,
                    "message": "Connection successful",
                    "key_source": "database:credential",
                },
                "blocked_reason": None,
                "remediation": ["No action required."],
            }
        ),
    ):
        await assert_gemini_model_bootstrap_probe()


@pytest.mark.asyncio
@patch("packages.core.ai.connection_tester.get_api_key", new_callable=AsyncMock)
async def test_startup_path_rejects_legacy_google_api_key_alias(
    mock_get_api_key,
    monkeypatch,
):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "legacy-google-key")
    mock_get_api_key.return_value = None

    api_key, key_source = await _resolve_google_api_key()

    assert api_key is None
    assert key_source == "none"
    mock_get_api_key.assert_awaited_once_with("google")


def test_legacy_env_blocklist_is_derived_from_mapping():
    flattened = {
        env_var
        for env_vars in LEGACY_PROVIDER_ENV_VARS.values()
        for env_var in env_vars
    }
    assert set(LEGACY_PROVIDER_ENV_BLOCKLIST) == flattened
    assert set(GOOGLE_PROVIDER_ENV_VARS).isdisjoint(set(LEGACY_PROVIDER_ENV_BLOCKLIST))


def test_read_env_ignores_file_compat_variable(monkeypatch, tmp_path):
    missing = tmp_path / "missing-secret.txt"
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD_FILE", str(missing))
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "env-password")

    assert read_env("OPEN_NOTEBOOK_PASSWORD") == "env-password"


def test_read_int_fail_fast_on_invalid_value(monkeypatch):
    monkeypatch.setenv("API_PORT", "invalid")

    with pytest.raises(SettingsValidationError, match="API_PORT"):
        read_int("API_PORT", 5055)


def test_read_bool_fail_fast_on_invalid_value(monkeypatch):
    monkeypatch.setenv("API_RELOAD", "maybe")

    with pytest.raises(SettingsValidationError, match="API_RELOAD"):
        read_bool("API_RELOAD", True)


@pytest.mark.asyncio
@patch("packages.core.ai.key_provider._get_default_credential", new_callable=AsyncMock)
async def test_provision_provider_keys_avoids_global_env_pollution(
    mock_get_default_credential, monkeypatch
):
    class FakeCredential:
        api_key = SecretStr("sk-test")
        base_url = "https://services.api.example.com"

        def to_esperanto_config(self) -> dict[str, str]:
            return {
                "api_key": self.api_key.get_secret_value(),
                "base_url": self.base_url,
            }

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    mock_get_default_credential.return_value = FakeCredential()

    assert await provision_provider_keys("google") is True
    assert "GEMINI_API_KEY" not in os.environ
    assert get_provisioned_provider_config("google") == {
        "api_key": "sk-test",
        "base_url": "https://services.api.example.com",
    }


@pytest.mark.asyncio
@patch("packages.core.domain.credential.repo_query", new_callable=AsyncMock)
async def test_credential_get_by_provider_uses_normalized_index_filter(mock_repo_query):
    mock_repo_query.return_value = []
    await Credential.get_by_provider("Google-Cloud")

    query = mock_repo_query.call_args.args[0]
    params = mock_repo_query.call_args.args[1]
    assert "WHERE provider = $provider" in query
    assert "string::lowercase(provider)" not in query
    assert params["provider"] == "google_cloud"


@pytest.mark.asyncio
@patch(
    "packages.core.ai.model_discovery.discover_provider_models", new_callable=AsyncMock
)
@patch("packages.core.ai.model_discovery.repo_query", new_callable=AsyncMock)
@patch("packages.core.ai.model_discovery.Model.save", new_callable=AsyncMock)
async def test_sync_provider_models_uses_provider_equality_filter(
    mock_model_save, mock_repo_query, mock_discover_provider_models
):
    from packages.core.ai.model_discovery import DiscoveredModel

    mock_discover_provider_models.return_value = [
        DiscoveredModel(
            name="gemini-3.1-pro-preview", provider="google", model_type="language"
        )
    ]
    mock_repo_query.return_value = []
    await sync_provider_models("Google", auto_register=True)

    query = mock_repo_query.call_args.args[0]
    params = mock_repo_query.call_args.args[1]
    assert "WHERE provider = $provider" in query
    assert "string::lowercase(provider)" not in query
    assert params["provider"] == "google"
    mock_model_save.assert_awaited()


@pytest.mark.asyncio
@patch("packages.core.ai.model_discovery.repo_query", new_callable=AsyncMock)
async def test_get_provider_model_count_uses_provider_equality_filter(mock_repo_query):
    mock_repo_query.return_value = []
    await get_provider_model_count("Google")

    query = mock_repo_query.call_args.args[0]
    params = mock_repo_query.call_args.args[1]
    assert "WHERE provider = $provider" in query
    assert "string::lowercase(provider)" not in query
    assert params["provider"] == "google"
