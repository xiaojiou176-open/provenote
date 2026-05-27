from __future__ import annotations

import types
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI

from packages.core.application.models import UITestRunRequest
from packages.core.application.ui_test_service import ui_test_service
from services.api import main as api_main


@pytest.mark.asyncio
async def test_lifespan_runs_migrations_and_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPEN_NOTEBOOK_SKIP_MIGRATIONS", raising=False)

    manager = AsyncMock()
    manager.get_current_version = AsyncMock(side_effect=[16, 17])
    manager.needs_migration = AsyncMock(return_value=True)
    manager.run_migration_up = AsyncMock(return_value=None)

    with (
        patch("services.api.main.AsyncMigrationManager", return_value=manager),
        patch("services.api.main.get_secret_from_env", return_value="enc-key"),
        patch("services.api.main.assert_no_legacy_provider_env", return_value=None),
        patch(
            "services.api.main.assert_gemini_model_bootstrap_probe",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "services.api.main.assert_provider_policy_bootstrap",
            new=AsyncMock(return_value=None),
        ),
    ):
        async with api_main.lifespan(FastAPI()):
            pass

    manager.needs_migration.assert_awaited_once()
    manager.run_migration_up.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_skips_migrations_when_flag_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_SKIP_MIGRATIONS", "true")

    with (
        patch("services.api.main.AsyncMigrationManager") as mock_manager_cls,
        patch("services.api.main.get_secret_from_env", return_value=None),
        patch("services.api.main.assert_no_legacy_provider_env", return_value=None),
        patch(
            "services.api.main.assert_gemini_model_bootstrap_probe",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "services.api.main.assert_provider_policy_bootstrap",
            new=AsyncMock(return_value=None),
        ),
    ):
        async with api_main.lifespan(FastAPI()):
            pass

    mock_manager_cls.assert_not_called()


@pytest.mark.asyncio
async def test_lifespan_wraps_migration_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPEN_NOTEBOOK_SKIP_MIGRATIONS", raising=False)

    manager = AsyncMock()
    manager.get_current_version = AsyncMock(return_value=16)
    manager.needs_migration = AsyncMock(return_value=True)
    manager.run_migration_up = AsyncMock(side_effect=ValueError("migration broken"))

    with (
        patch("services.api.main.AsyncMigrationManager", return_value=manager),
        patch("services.api.main.get_secret_from_env", return_value="enc-key"),
        patch("services.api.main.assert_no_legacy_provider_env", return_value=None),
        patch(
            "services.api.main.assert_gemini_model_bootstrap_probe",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "services.api.main.assert_provider_policy_bootstrap",
            new=AsyncMock(return_value=None),
        ),
    ):
        with pytest.raises(
            RuntimeError, match="Failed to run database migrations: migration broken"
        ):
            async with api_main.lifespan(FastAPI()):
                pass


@pytest.mark.asyncio
async def test_lifespan_tolerates_phoenix_setup_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPEN_NOTEBOOK_SKIP_MIGRATIONS", raising=False)
    fake_module = types.ModuleType("packages.core.telemetry.phoenix")

    def _boom() -> None:
        raise RuntimeError("phoenix unavailable")

    fake_module.setup_phoenix_tracing = _boom

    manager = AsyncMock()
    manager.get_current_version = AsyncMock(return_value=16)
    manager.needs_migration = AsyncMock(return_value=False)

    with (
        patch.dict("sys.modules", {"packages.core.telemetry.phoenix": fake_module}),
        patch("services.api.main.AsyncMigrationManager", return_value=manager),
        patch("services.api.main.get_secret_from_env", return_value=None),
        patch("services.api.main.assert_no_legacy_provider_env", return_value=None),
        patch(
            "services.api.main.assert_gemini_model_bootstrap_probe",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "services.api.main.assert_provider_policy_bootstrap",
            new=AsyncMock(return_value=None),
        ),
    ):
        async with api_main.lifespan(FastAPI()):
            pass
    manager.get_current_version.assert_awaited_once()
    manager.needs_migration.assert_awaited_once()
    manager.run_migration_up.assert_not_called()


@pytest.mark.asyncio
async def test_root_and_health_routes_return_expected_payloads() -> None:
    assert await api_main.root() == {"message": "Notebooklab API is running"}
    assert await api_main.health() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_lifespan_shutdown_keeps_ui_test_service_reusable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_SKIP_MIGRATIONS", "true")

    await ui_test_service.shutdown()
    ui_test_service._runs.clear()
    ui_test_service._active_tasks.clear()
    ui_test_service._is_shutting_down = False
    original_shutdown = ui_test_service.shutdown
    shutdown_spy = AsyncMock(wraps=original_shutdown)

    with (
        patch("services.api.main.get_secret_from_env", return_value=None),
        patch("services.api.main.assert_no_legacy_provider_env", return_value=None),
        patch(
            "services.api.main.assert_gemini_model_bootstrap_probe",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "services.api.main.assert_provider_policy_bootstrap",
            new=AsyncMock(return_value=None),
        ),
        patch.object(ui_test_service, "shutdown", new=shutdown_spy),
    ):
        async with api_main.lifespan(FastAPI()):
            pass

    shutdown_spy.assert_awaited_once()
    assert ui_test_service._is_shutting_down is False

    try:
        response = await ui_test_service.run(
            UITestRunRequest(project="chromium", dry_run=True, timeout_seconds=5)
        )
        assert response.status == "queued"
    finally:
        # Global singleton: ensure no run state leaks into other tests.
        await ui_test_service.shutdown()
        ui_test_service._runs.clear()
        ui_test_service._active_tasks.clear()
        ui_test_service._is_shutting_down = False
