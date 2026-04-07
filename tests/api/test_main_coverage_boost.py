from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.api import main as api_main


def test_env_int_clamps_to_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REQUEST_LOG_SLOW_THRESHOLD_MS", "999999")
    assert (
        api_main._env_int(
            "REQUEST_LOG_SLOW_THRESHOLD_MS",
            default=2000,
            minimum=0,
            maximum=60000,
        )
        == 60000
    )


def test_load_cors_config_falls_back_to_dev_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPEN_NOTEBOOK_CORS_ALLOW_ORIGINS", raising=False)
    monkeypatch.setenv("OPEN_NOTEBOOK_ENV", "development")
    monkeypatch.setenv("OPEN_NOTEBOOK_CORS_ALLOW_CREDENTIALS", "true")

    cors_config = api_main._load_cors_config()

    assert cors_config.allow_credentials is True
    assert cors_config.allow_origins == api_main.DEFAULT_DEV_CORS_ALLOW_ORIGINS


@pytest.mark.asyncio
async def test_provider_policy_bootstrap_warns_when_not_enforced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPEN_NOTEBOOK_ENFORCE_PROVIDER_POLICY", raising=False)
    monkeypatch.delenv("OPEN_NOTEBOOK_SKIP_MIGRATIONS", raising=False)
    with (
        patch(
            "services.api.credentials_service.get_provider_status",
            new=AsyncMock(
                return_value={
                    "policy_effective": {"language": False, "embedding": True},
                    "policy_blockers": {"language": "not configured"},
                }
            ),
        ),
        patch("services.api.main.logger.warning") as warning_mock,
    ):
        await api_main.assert_provider_policy_bootstrap()

    warning_mock.assert_called_once()


@pytest.mark.asyncio
async def test_provider_policy_bootstrap_skips_when_migrations_are_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_SKIP_MIGRATIONS", "true")

    with patch(
        "services.api.credentials_service.get_provider_status", new=AsyncMock()
    ) as status_mock:
        await api_main.assert_provider_policy_bootstrap()

    status_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_provider_policy_bootstrap_raises_when_enforced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_ENFORCE_PROVIDER_POLICY", "true")
    monkeypatch.delenv("OPEN_NOTEBOOK_SKIP_MIGRATIONS", raising=False)
    with patch(
        "services.api.credentials_service.get_provider_status",
        new=AsyncMock(
            return_value={
                "policy_effective": {"language": False},
                "policy_blockers": {"language": "missing default"},
            }
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="Provider policy is not effective for required modalities",
        ):
            await api_main.assert_provider_policy_bootstrap()


@pytest.mark.asyncio
async def test_gemini_model_bootstrap_probe_can_be_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_SKIP_GEMINI_STARTUP_PROBE", "true")

    with patch(
        "services.api.main.probe_startup_gemini_model", new=AsyncMock()
    ) as probe_mock:
        await api_main.assert_gemini_model_bootstrap_probe()

    probe_mock.assert_not_awaited()
