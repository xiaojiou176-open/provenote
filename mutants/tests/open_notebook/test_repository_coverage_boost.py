from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from packages.core.database import repository


class DummyConnection:
    def __init__(self) -> None:
        self.query = AsyncMock()
        self.insert = AsyncMock()
        self.delete = AsyncMock()


def _patch_db_connection(
    monkeypatch: pytest.MonkeyPatch, conn: DummyConnection
) -> None:
    @asynccontextmanager
    async def _fake_db_connection():
        yield conn

    monkeypatch.setattr(repository, "db_connection", _fake_db_connection)


@pytest.mark.asyncio
async def test_repo_query_raises_runtime_error_when_db_returns_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = DummyConnection()
    conn.query.return_value = "transaction conflict"
    _patch_db_connection(monkeypatch, conn)
    debug_mock = MagicMock()
    monkeypatch.setattr(repository.logger, "debug", debug_mock)

    with pytest.raises(RuntimeError, match="transaction conflict"):
        await repository.repo_query("SELECT * FROM test")

    conn.query.assert_awaited_once_with("SELECT * FROM test", None)
    debug_mock.assert_called_once()


@pytest.mark.asyncio
async def test_repo_query_logs_and_reraises_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = DummyConnection()
    conn.query.side_effect = ValueError("bad query")
    _patch_db_connection(monkeypatch, conn)
    exception_mock = MagicMock()
    monkeypatch.setattr(repository.logger, "exception", exception_mock)

    with pytest.raises(ValueError, match="bad query"):
        await repository.repo_query("BAD QUERY", {"k": "v"})

    conn.query.assert_awaited_once_with("BAD QUERY", {"k": "v"})
    exception_mock.assert_called_once()


@pytest.mark.asyncio
async def test_repo_create_removes_id_and_adds_timestamps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = DummyConnection()
    conn.insert.return_value = {"id": "table:1", "name": "A"}
    _patch_db_connection(monkeypatch, conn)
    payload = {"id": "table:legacy", "name": "A"}

    result = await repository.repo_create("table", payload)

    assert result["id"] == "table:1"
    conn.insert.assert_awaited_once()
    inserted_table, inserted_data = conn.insert.await_args.args
    assert inserted_table == "table"
    assert "id" not in inserted_data
    assert isinstance(inserted_data["created"], datetime)
    assert isinstance(inserted_data["updated"], datetime)
    assert inserted_data["created"].tzinfo == timezone.utc
    assert inserted_data["updated"].tzinfo == timezone.utc
    assert "id" not in payload


@pytest.mark.asyncio
async def test_repo_create_wraps_generic_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = DummyConnection()
    conn.insert.side_effect = ValueError("db down")
    _patch_db_connection(monkeypatch, conn)

    with pytest.raises(RuntimeError, match="Failed to create record"):
        await repository.repo_create("table", {"name": "A"})


@pytest.mark.asyncio
async def test_repo_update_builds_prefixed_record_id_and_normalizes_created_datetime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_query_mock = AsyncMock(return_value=[{"id": "user:1"}])
    monkeypatch.setattr(repository, "repo_query", repo_query_mock)
    data = {
        "id": "should-be-removed",
        "created": "2024-01-01T00:00:00+00:00",
        "name": "alice",
    }

    result = await repository.repo_update("user", "1", data)

    assert result == [{"id": "user:1"}]
    query, params = repo_query_mock.await_args.args
    assert query == "UPDATE user:1 MERGE $data;"
    assert "id" not in params["data"]
    assert isinstance(params["data"]["created"], datetime)
    assert params["data"]["created"].tzinfo == timezone.utc
    assert params["data"]["updated"].tzinfo == timezone.utc


@pytest.mark.asyncio
async def test_repo_update_wraps_internal_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        repository, "repo_query", AsyncMock(side_effect=RuntimeError("boom"))
    )

    with pytest.raises(RuntimeError, match="Failed to update record: boom"):
        await repository.repo_update("user", "1", {"name": "alice"})


@pytest.mark.asyncio
async def test_repo_delete_uses_ensure_record_id_and_deletes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = DummyConnection()
    conn.delete.return_value = {"ok": True}
    _patch_db_connection(monkeypatch, conn)
    rid = SimpleNamespace(raw="user:1")
    ensure_mock = MagicMock(return_value=rid)
    monkeypatch.setattr(repository, "ensure_record_id", ensure_mock)

    result = await repository.repo_delete("user:1")

    assert result == {"ok": True}
    ensure_mock.assert_called_once_with("user:1")
    conn.delete.assert_awaited_once_with(rid)


@pytest.mark.asyncio
async def test_repo_delete_wraps_exceptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = DummyConnection()
    conn.delete.side_effect = ValueError("cannot delete")
    _patch_db_connection(monkeypatch, conn)
    monkeypatch.setattr(repository, "ensure_record_id", MagicMock(return_value="x"))

    with pytest.raises(RuntimeError, match="Failed to delete record: cannot delete"):
        await repository.repo_delete("user:1")


@pytest.mark.asyncio
async def test_repo_insert_ignore_duplicates_on_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = DummyConnection()
    conn.insert.return_value = "already contains this id"
    _patch_db_connection(monkeypatch, conn)

    result = await repository.repo_insert("item", [{"id": "item:1"}], True)

    assert result == []


@pytest.mark.asyncio
async def test_repo_insert_runtime_error_transaction_logs_debug_and_reraises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = DummyConnection()
    conn.insert.return_value = "Transaction conflict detected"
    _patch_db_connection(monkeypatch, conn)
    debug_mock = MagicMock()
    error_mock = MagicMock()
    monkeypatch.setattr(repository.logger, "debug", debug_mock)
    monkeypatch.setattr(repository.logger, "error", error_mock)

    with pytest.raises(RuntimeError, match="Transaction conflict detected"):
        await repository.repo_insert("item", [{"k": "v"}], False)

    debug_mock.assert_called_once()
    error_mock.assert_not_called()


@pytest.mark.asyncio
async def test_repo_insert_ignore_duplicates_on_generic_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn = DummyConnection()
    conn.insert.side_effect = Exception("already contains this id")
    _patch_db_connection(monkeypatch, conn)

    result = await repository.repo_insert("item", [{"k": "v"}], True)

    assert result == []


def test_parse_record_ids_recursively_handles_nested_structures() -> None:
    original = {
        "id": "root:1",
        "nested": [{"id": "child:1"}, {"values": [1, 2, 3]}],
    }

    parsed = repository.parse_record_ids(original)

    assert parsed == original
