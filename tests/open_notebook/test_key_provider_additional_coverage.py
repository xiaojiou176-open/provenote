from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import SecretStr

import packages.core.ai.key_provider as key_provider


@pytest.fixture(autouse=True)
def _clear_runtime_provider_cache() -> None:
    key_provider._PROVISIONED_PROVIDER_CONFIG.clear()


def test_cache_provider_config_handles_none_and_empty_payload() -> None:
    assert key_provider._cache_provider_config("google", None) is False
    assert key_provider.get_provisioned_provider_config("google") == {}

    cred = SimpleNamespace(to_esperanto_config=lambda: {"api_key": None})
    assert key_provider._cache_provider_config("google", cred) is False
    assert key_provider.get_provisioned_provider_config("google") == {}


@pytest.mark.asyncio
async def test_get_default_credential_success_and_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cred = SimpleNamespace(api_key=SecretStr("sk-test"))
    monkeypatch.setattr(
        key_provider.Credential,
        "get_by_provider",
        AsyncMock(return_value=[cred]),
    )
    assert await key_provider._get_default_credential("google") is cred

    debug_mock = MagicMock()
    monkeypatch.setattr(key_provider.logger, "debug", debug_mock)
    monkeypatch.setattr(
        key_provider.Credential,
        "get_by_provider",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    assert await key_provider._get_default_credential("google") is None
    debug_mock.assert_called_once()


@pytest.mark.asyncio
async def test_get_default_credential_returns_none_for_empty_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        key_provider.Credential,
        "get_by_provider",
        AsyncMock(return_value=[]),
    )
    assert await key_provider._get_default_credential("google") is None


@pytest.mark.asyncio
async def test_get_api_key_returns_none_when_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        key_provider,
        "_get_default_credential",
        AsyncMock(return_value=SimpleNamespace(api_key=None)),
    )
    assert await key_provider.get_api_key("google") is None


@pytest.mark.asyncio
async def test_provision_simple_provider_returns_false_for_unsupported() -> None:
    assert await key_provider._provision_simple_provider("openai") is False


@pytest.mark.asyncio
async def test_provision_provider_keys_rejects_unsupported_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    warning_mock = MagicMock()
    monkeypatch.setattr(key_provider.logger, "warning", warning_mock)

    ok = await key_provider.provision_provider_keys("OpenAI-Compatible")

    assert ok is False
    warning_mock.assert_called_once()


@pytest.mark.asyncio
async def test_provision_all_keys_iterates_all_simple_providers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(key_provider, "SIMPLE_PROVIDERS", ("google", "google_alt"))
    monkeypatch.setattr(
        key_provider,
        "provision_provider_keys",
        AsyncMock(side_effect=[True, False]),
    )

    result = await key_provider.provision_all_keys()

    assert result == {"google": True, "google_alt": False}
