from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import packages.core.database.async_migrate as async_migrate


class _FakeConnectionContext:
    def __init__(self, connection: object) -> None:
        self._connection = connection

    async def __aenter__(self) -> object:
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


@pytest.mark.asyncio
async def test_async_migration_run_calls_bump_and_lower_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = SimpleNamespace(query=AsyncMock())
    monkeypatch.setattr(
        async_migrate,
        "db_connection",
        lambda: _FakeConnectionContext(connection),
    )
    bump_mock = AsyncMock()
    lower_mock = AsyncMock()
    monkeypatch.setattr(async_migrate, "bump_version", bump_mock)
    monkeypatch.setattr(async_migrate, "lower_version", lower_mock)

    migration = async_migrate.AsyncMigration("SELECT 1;")
    await migration.run(bump=True)
    await migration.run(bump=False)

    connection.query.assert_any_await("SELECT 1;")
    assert connection.query.await_count == 2
    bump_mock.assert_awaited_once()
    lower_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_migration_run_logs_and_raises_on_query_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = SimpleNamespace(query=AsyncMock(side_effect=RuntimeError("db down")))
    monkeypatch.setattr(
        async_migrate,
        "db_connection",
        lambda: _FakeConnectionContext(connection),
    )
    error_mock = MagicMock()
    monkeypatch.setattr(async_migrate.logger, "error", error_mock)

    migration = async_migrate.AsyncMigration("SELECT 1;")
    with pytest.raises(RuntimeError, match="db down"):
        await migration.run()

    error_mock.assert_called_once()


@pytest.mark.asyncio
async def test_async_migration_runner_covers_up_and_down_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    up = [SimpleNamespace(run=AsyncMock()) for _ in range(3)]
    down = [SimpleNamespace(run=AsyncMock())]
    runner = async_migrate.AsyncMigrationRunner(up_migrations=up, down_migrations=down)

    monkeypatch.setattr(async_migrate, "get_latest_version", AsyncMock(return_value=1))
    await runner.run_all()
    up[0].run.assert_not_called()
    up[1].run.assert_awaited_once_with(bump=True)
    up[2].run.assert_awaited_once_with(bump=True)

    monkeypatch.setattr(async_migrate, "get_latest_version", AsyncMock(return_value=1))
    await runner.run_one_down()
    down[0].run.assert_awaited_once_with(bump=False)

    monkeypatch.setattr(async_migrate, "get_latest_version", AsyncMock(return_value=3))
    await runner.run_one_up()
    assert up[0].run.await_count == 0
    assert up[1].run.await_count == 1
    assert up[2].run.await_count == 1


@pytest.mark.asyncio
async def test_async_migration_runner_run_one_down_raises_when_missing_rollback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = async_migrate.AsyncMigrationRunner(
        up_migrations=[SimpleNamespace(run=AsyncMock()) for _ in range(4)],
        down_migrations=[SimpleNamespace(run=AsyncMock())],
    )
    monkeypatch.setattr(async_migrate, "get_latest_version", AsyncMock(return_value=3))

    with pytest.raises(RuntimeError, match="No rollback migration registered"):
        await runner.run_one_down()


@pytest.mark.asyncio
async def test_async_migration_manager_needs_migration_and_failure_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = async_migrate.AsyncMigrationManager.__new__(
        async_migrate.AsyncMigrationManager
    )
    manager.up_migrations = [object(), object(), object()]
    manager.runner = SimpleNamespace(
        run_all=AsyncMock(side_effect=RuntimeError("boom"))
    )
    manager.get_current_version = AsyncMock(return_value=1)
    manager.needs_migration = AsyncMock(return_value=True)
    error_mock = MagicMock()
    monkeypatch.setattr(async_migrate.logger, "error", error_mock)

    assert await manager.needs_migration() is True
    with pytest.raises(RuntimeError, match="boom"):
        await manager.run_migration_up()
    error_mock.assert_called_once()


@pytest.mark.asyncio
async def test_get_latest_versions_and_repo_fallback_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        async_migrate,
        "get_all_versions",
        AsyncMock(return_value=[{"version": 1}, {"version": 4}, {"version": 2}]),
    )
    assert await async_migrate.get_latest_version() == 4

    monkeypatch.setattr(
        async_migrate,
        "get_all_versions",
        AsyncMock(side_effect=RuntimeError("missing table")),
    )
    assert await async_migrate.get_latest_version() == 0


@pytest.mark.asyncio
async def test_get_all_versions_returns_empty_when_table_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        async_migrate,
        "repo_query",
        AsyncMock(side_effect=RuntimeError("table missing")),
    )
    assert await async_migrate.get_all_versions() == []


@pytest.mark.asyncio
async def test_bump_and_lower_version_execute_expected_queries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_query_mock = AsyncMock()
    monkeypatch.setattr(async_migrate, "repo_query", repo_query_mock)
    monkeypatch.setattr(async_migrate, "get_latest_version", AsyncMock(return_value=2))

    await async_migrate.bump_version()
    create_sql = repo_query_mock.await_args.args[0]
    assert "CREATE _sbl_migrations:3 SET version = 3" in create_sql

    repo_query_mock.reset_mock()
    monkeypatch.setattr(async_migrate, "get_latest_version", AsyncMock(return_value=0))
    await async_migrate.lower_version()
    repo_query_mock.assert_not_awaited()

    monkeypatch.setattr(async_migrate, "get_latest_version", AsyncMock(return_value=2))
    await async_migrate.lower_version()
    delete_sql = repo_query_mock.await_args.args[0]
    assert delete_sql == "DELETE _sbl_migrations:2;"
