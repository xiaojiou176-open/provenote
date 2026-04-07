from __future__ import annotations

import importlib
import socket
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

import services.api.credentials_service as credentials_service_module
from packages.core.application.command_service import (
    CANCELLABLE_STATUSES,
    RUNNING_STATUSES,
    CommandConflictError,
    CommandNotFoundError,
    CommandService,
    _normalize_status,
    _parse_datetime,
    _sanitize_row,
)
from services.api.credentials_service import (
    credential_to_response,
    discover_with_config,
    register_models,
    require_encryption_key,
    validate_url,
)
from services.api.podcast_service import DefaultProfiles, PodcastService


class _DummyHttpResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FailingHttpResponse:
    def raise_for_status(self) -> None:
        raise RuntimeError("http failure")


class _DummyAsyncClient:
    def __init__(self, timeout=None):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, **kwargs):
        return _DummyHttpResponse({"url": url, "kwargs": kwargs, "method": "get"})

    async def post(self, url: str, **kwargs):
        return _DummyHttpResponse(
            {"url": url, "kwargs": kwargs, "method": "post", "timeout": self.timeout}
        )

    async def put(self, url: str, **kwargs):
        return _DummyHttpResponse({"url": url, "kwargs": kwargs, "method": "put"})

    async def delete(self, url: str, **kwargs):
        return _DummyHttpResponse({"url": url, "kwargs": kwargs, "method": "delete"})


class _FailingAsyncClient(_DummyAsyncClient):
    async def get(self, *args, **kwargs):
        return _FailingHttpResponse()

    async def post(self, *args, **kwargs):
        return _FailingHttpResponse()

    async def put(self, *args, **kwargs):
        return _FailingHttpResponse()

    async def delete(self, *args, **kwargs):
        return _FailingHttpResponse()


# ---------------------------------------------------------------------------
# command_service coverage
# ---------------------------------------------------------------------------


def test_command_status_normalize_and_parse_datetime_branches() -> None:
    assert _normalize_status("cancelled") == "canceled"
    assert _normalize_status(" FAILED ") == "failed"

    naive = datetime(2026, 1, 1, 0, 0, 0)
    parsed_naive = _parse_datetime(naive)
    assert parsed_naive.tzinfo == timezone.utc

    parsed_z = _parse_datetime("2026-01-01T00:00:00Z")
    assert parsed_z.tzinfo == timezone.utc

    assert _parse_datetime("not-a-datetime") is None
    assert _parse_datetime("   ") is None
    assert _parse_datetime(123) is None


@pytest.mark.asyncio
async def test_get_existing_idempotent_command_branches() -> None:
    async def no_rows(_query: str, _params: dict | None = None):
        return []

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=no_rows),
    ):
        assert (
            await CommandService._get_existing_idempotent_command(
                idempotency_key="idem-1", request_hash="hash-1"
            )
            is None
        )

    async def mismatch_rows(_query: str, _params: dict | None = None):
        return [{"request_hash": "other-hash", "command_id": "command:1"}]

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=mismatch_rows),
    ):
        with pytest.raises(CommandConflictError):
            await CommandService._get_existing_idempotent_command(
                idempotency_key="idem-1", request_hash="hash-1"
            )

    async def hit_rows(_query: str, _params: dict | None = None):
        return [{"request_hash": "hash-1", "command_id": "command:1"}]

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=hit_rows),
    ):
        result = await CommandService._get_existing_idempotent_command(
            idempotency_key="idem-1", request_hash="hash-1"
        )
    assert result == "command:1"


@pytest.mark.asyncio
async def test_submit_impl_idempotency_hit_and_submit_failure() -> None:
    with (
        patch(
            "packages.core.application.command_service.CommandService._get_existing_idempotent_command",
            new=AsyncMock(return_value="command:existing"),
        ),
        patch(
            "packages.core.application.command_service.submit_command"
        ) as mock_submit,
    ):
        cmd_id = await CommandService._submit_command_job_impl(
            module_name="open_notebook",
            command_name="embed_note",
            command_args={"note_id": "n1"},
            context=None,
            idempotency_key="idem-1",
        )

    assert cmd_id == "command:existing"
    mock_submit.assert_not_called()

    with (
        patch(
            "packages.core.application.command_service.CommandService._get_existing_idempotent_command",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "packages.core.application.command_service.CommandService._reserve_idempotency_placeholder",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "packages.core.application.command_service.CommandService._mark_idempotency_failure",
            new=AsyncMock(return_value=None),
        ) as mock_mark_failed,
        patch(
            "packages.core.application.command_service.submit_command", return_value=""
        ),
    ):
        with pytest.raises(ValueError, match="Failed to get cmd_id"):
            await CommandService._submit_command_job_impl(
                module_name="open_notebook",
                command_name="embed_note",
                command_args={"note_id": "n1"},
                context=None,
                idempotency_key="idem-1",
            )
    mock_mark_failed.assert_awaited_once()


@pytest.mark.asyncio
async def test_submit_command_job_import_error_branch() -> None:
    original_import = __import__

    def _fake_import(name, *args, **kwargs):
        if name == "packages.core.application.commands.embedding_commands":
            raise ImportError("missing module")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=_fake_import):
        with pytest.raises(ValueError, match="Command modules not available"):
            await CommandService.submit_command_job(
                module_name="open_notebook",
                command_name="x",
                command_args={},
            )


@pytest.mark.asyncio
async def test_list_command_jobs_and_dead_letter_and_record_failure_event() -> None:
    recorded_queries: list[str] = []

    async def fake_repo_query(query: str, params: dict | None = None):
        recorded_queries.append(query)
        if query.startswith("SELECT id, app, name"):
            return [
                {
                    "id": "command:1",
                    "status": "cancelled",
                    "app": "open_notebook",
                    "name": "embed_note",
                    "args": {},
                    "context": {},
                    "result": None,
                    "error_message": None,
                    "created": None,
                    "updated": None,
                }
            ]
        if query.startswith("SELECT id, app, name, args"):
            return [
                {
                    "id": "command:2",
                    "app": "open_notebook",
                    "name": "embed_source",
                    "args": {"source_id": "source:1"},
                    "context": {"trace": "1"},
                    "updated": datetime.now(timezone.utc),
                    "error_message": "boom",
                }
            ]
        if query.startswith("SELECT * FROM $record_id"):
            return []
        if query.startswith("UPSERT command_dead_letter"):
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with (
        patch(
            "packages.core.application.command_service.repo_query",
            new=AsyncMock(side_effect=fake_repo_query),
        ),
        patch(
            "packages.core.application.command_service.CommandService._sync_dead_letter_if_failed",
            new=AsyncMock(),
        ) as sync_mock,
    ):
        rows = await CommandService.list_command_jobs(status_filter="cancelled")
        assert rows[0]["status"] == "canceled"
        assert "OR string::lowercase(status) = 'cancelled'" in recorded_queries[0]
        sync_mock.assert_not_awaited()

        await CommandService.record_command_failure_event(
            "command:2", error_message="", app=None, name=None
        )

    assert any(q.startswith("UPSERT command_dead_letter") for q in recorded_queries)


@pytest.mark.asyncio
async def test_store_idempotency_mapping_and_lock_reuse() -> None:
    captured: dict = {}

    async def fake_repo_query(query: str, params: dict | None = None):
        captured["query"] = query
        captured["params"] = params
        return []

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=fake_repo_query),
    ):
        await CommandService._store_idempotency_mapping(
            idempotency_key="idem-1",
            request_hash="hash-1",
            app_name="open_notebook",
            command_name="embed_note",
            command_id="command:1",
        )

    assert captured["query"].startswith("UPSERT command_idempotency:")

    first = await CommandService._get_idempotency_lock("idem-1")
    second = await CommandService._get_idempotency_lock("idem-1")
    assert first is second


@pytest.mark.asyncio
async def test_cancel_and_requeue_branch_coverage() -> None:
    async def repo_not_found(query: str, params: dict | None = None):
        if query.startswith("SELECT id, status FROM $command_id"):
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=repo_not_found),
    ):
        with pytest.raises(CommandNotFoundError):
            await CommandService.cancel_command_job("command:404")

    async def repo_running(query: str, params: dict | None = None):
        if query.startswith("SELECT id, status FROM $command_id"):
            return [{"id": "command:1", "status": "running"}]
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=repo_running),
    ):
        with pytest.raises(CommandConflictError):
            await CommandService.cancel_command_job("command:1")

    async def repo_terminal(query: str, params: dict | None = None):
        if query.startswith("SELECT id, status FROM $command_id"):
            return [{"id": "command:1", "status": "completed"}]
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=repo_terminal),
    ):
        terminal = await CommandService.cancel_command_job("command:1")
    assert terminal["cancelled"] is False
    assert terminal["status"] == "completed"

    async def dead_letter_missing(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM $entry_id"):
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=dead_letter_missing),
    ):
        with pytest.raises(CommandNotFoundError):
            await CommandService.requeue_dead_letter("command_dead_letter:404")

    async def dead_letter_missing_metadata(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM $entry_id"):
            return [{"id": "command_dead_letter:1", "app": "", "name": ""}]
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=dead_letter_missing_metadata),
    ):
        with pytest.raises(CommandConflictError):
            await CommandService.requeue_dead_letter("command_dead_letter:1")

    # Active prior requeue should conflict.
    active_status = next(iter(CANCELLABLE_STATUSES | RUNNING_STATUSES))

    async def dead_letter_active_requeue(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM $entry_id"):
            return [
                {
                    "id": "command_dead_letter:1",
                    "app": "open_notebook",
                    "name": "embed_source",
                    "args": {},
                    "context": {},
                    "last_requeued_command_id": "command:active",
                }
            ]
        if query.startswith("SELECT status FROM $command_id"):
            return [{"status": active_status}]
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=dead_letter_active_requeue),
    ):
        with pytest.raises(CommandConflictError):
            await CommandService.requeue_dead_letter("command_dead_letter:1")


@pytest.mark.asyncio
async def test_list_dead_letter_entries_unknown_last_requeue_status() -> None:
    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM command_dead_letter"):
            return [
                {
                    "id": "command_dead_letter:1",
                    "status": "failed",
                    "last_requeued_command_id": "command:9",
                }
            ]
        if query.startswith("SELECT status FROM $command_id"):
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=fake_repo_query),
    ):
        rows = await CommandService.list_dead_letter_entries()

    assert rows[0]["last_requeued_status"] == "unknown"


@pytest.mark.asyncio
async def test_command_service_additional_filters_and_early_return_paths() -> None:
    captured: dict[str, object] = {}

    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT id, app, name"):
            captured["query"] = query
            captured["params"] = params or {}
            return [
                {
                    "id": "command:77",
                    "app": "open_notebook",
                    "name": "embed_note",
                    "status": "failed",
                    "args": {},
                    "context": {},
                    "result": None,
                    "error_message": "boom",
                    "created": None,
                    "updated": None,
                }
            ]
        if query.startswith("SELECT * FROM command_dead_letter"):
            return [{"id": "command_dead_letter:1", "status": "failed"}]
        raise AssertionError(f"Unexpected query: {query}")

    with (
        patch(
            "packages.core.application.command_service.repo_query",
            new=AsyncMock(side_effect=fake_repo_query),
        ),
        patch(
            "packages.core.application.command_service.CommandService._sync_dead_letter_if_failed",
            new=AsyncMock(),
        ) as sync_mock,
    ):
        rows = await CommandService.list_command_jobs(
            module_filter="open_notebook",
            command_filter="embed_note",
            status_filter="failed",
        )
        assert rows[0]["id"] == "command:77"
        sync_mock.assert_awaited_once()

        rows_without_requeue = await CommandService.list_dead_letter_entries()
        assert rows_without_requeue[0]["last_requeued_status"] is None

    query = str(captured["query"])
    params = dict(captured["params"])  # type: ignore[arg-type]
    assert "module_filter" in params
    assert "command_filter" in params
    assert params["status_filter"] == "failed"
    assert "string::lowercase(app)" in query
    assert "string::lowercase(name)" in query

    assert _sanitize_row(
        {
            "id": 1,
            "command_id": 2,
            "last_requeued_command_id": 3,
            "status": "cancelled",
        }
    ) == {
        "id": "1",
        "command_id": "2",
        "last_requeued_command_id": "3",
        "status": "canceled",
    }

    with patch(
        "packages.core.application.command_service.CommandService._upsert_dead_letter_from_failure",
        new=AsyncMock(),
    ) as upsert_mock:
        await CommandService._sync_dead_letter_if_failed(
            {"id": "command:1", "status": "queued"}
        )
        await CommandService._sync_dead_letter_if_failed({"id": "", "status": "failed"})
    upsert_mock.assert_not_called()


@pytest.mark.asyncio
async def test_command_service_submit_and_status_exception_paths() -> None:
    with patch(
        "packages.core.application.command_service.CommandService._submit_command_job_impl",
        new=AsyncMock(return_value="command:ok"),
    ) as submit_impl:
        command_id = await CommandService.submit_command_job(
            module_name="open_notebook",
            command_name="embed_note",
            command_args={"note_id": "n1"},
            idempotency_key=None,
        )
    assert command_id == "command:ok"
    assert submit_impl.await_args.kwargs["idempotency_key"] is None

    with patch(
        "packages.core.application.command_service.get_command_status",
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(RuntimeError, match="boom"):
            await CommandService.get_command_status("command:1")


@pytest.mark.asyncio
async def test_command_service_remaining_branch_edges() -> None:
    # _sanitize_row branches where optional fields are absent.
    assert _sanitize_row({"command_id": "command:1"}) == {"command_id": "command:1"}
    assert _sanitize_row(
        {"id": "command:1", "last_requeued_command_id": "command:2"}
    ) == {
        "id": "command:1",
        "last_requeued_command_id": "command:2",
    }

    with (
        patch(
            "packages.core.application.command_service.submit_command",
            return_value="command:5",
        ),
        patch(
            "packages.core.application.command_service.CommandService._store_idempotency_mapping",
            new=AsyncMock(),
        ),
    ):
        created = await CommandService._submit_command_job_impl(
            module_name="open_notebook",
            command_name="embed_note",
            command_args={"note_id": "n1"},
            context={},
            idempotency_key=None,
        )
    assert created == "command:5"

    # app/name provided => skip backfill query.
    with (
        patch("packages.core.application.command_service.repo_query", new=AsyncMock()),
        patch(
            "packages.core.application.command_service.CommandService._upsert_dead_letter_from_failure",
            new=AsyncMock(),
        ) as upsert_mock,
    ):
        await CommandService.record_command_failure_event(
            "command:10",
            error_message="boom",
            app="open_notebook",
            name="embed_source",
        )
    upsert_mock.assert_awaited_once()

    # app/name missing + no command row => still upserts with empty metadata.
    async def repo_empty_for_backfill(query: str, _params: dict | None = None):
        if query.startswith(
            "SELECT id, app, name, args, context, updated, error_message"
        ):
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with (
        patch(
            "packages.core.application.command_service.repo_query",
            new=AsyncMock(side_effect=repo_empty_for_backfill),
        ),
        patch(
            "packages.core.application.command_service.CommandService._upsert_dead_letter_from_failure",
            new=AsyncMock(),
        ) as upsert_mock,
    ):
        await CommandService.record_command_failure_event(
            "command:11",
            error_message="",
            app=None,
            name=None,
        )
    upsert_mock.assert_awaited_once()

    completed_status = SimpleNamespace(
        status="completed",
        result={"ok": True},
        error_message=None,
        created=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated=datetime(2026, 1, 1, tzinfo=timezone.utc),
        progress=100,
    )
    with (
        patch(
            "packages.core.application.command_service.get_command_status",
            new=AsyncMock(return_value=completed_status),
        ),
        patch(
            "packages.core.application.command_service.CommandService.record_command_failure_event",
            new=AsyncMock(),
        ) as record_failure_mock,
    ):
        status_payload = await CommandService.get_command_status("command:12")
    assert status_payload["status"] == "completed"
    record_failure_mock.assert_not_awaited()

    captured_queries: list[str] = []

    async def repo_for_unfiltered_list(query: str, _params: dict | None = None):
        if query.startswith("SELECT id, app, name"):
            captured_queries.append(query)
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=repo_for_unfiltered_list),
    ):
        await CommandService.list_command_jobs()
    assert "WHERE" not in captured_queries[0]

    # Prior requeue exists but lookup returns no status rows => allow requeue.
    async def repo_requeue_no_prior_status(query: str, _params: dict | None = None):
        if query.startswith("SELECT * FROM $entry_id"):
            return [
                {
                    "id": "command_dead_letter:9",
                    "app": "open_notebook",
                    "name": "embed_source",
                    "args": {},
                    "context": {},
                    "requeue_count": 0,
                    "last_requeued_command_id": "command:old",
                }
            ]
        if query.startswith("SELECT status FROM $command_id"):
            return []
        if query.startswith("UPDATE $entry_id MERGE $data"):
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with (
        patch(
            "packages.core.application.command_service.repo_query",
            new=AsyncMock(side_effect=repo_requeue_no_prior_status),
        ),
        patch(
            "packages.core.application.command_service.CommandService.submit_command_job",
            new=AsyncMock(return_value="command:new"),
        ),
    ):
        result = await CommandService.requeue_dead_letter("command_dead_letter:9")
    assert result["command_id"] == "command:new"


# ---------------------------------------------------------------------------
# chat_service coverage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_service_happy_paths_and_payload_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chat_service_module = importlib.import_module(
        "packages.core.application.chat_service"
    )

    monkeypatch.setattr(
        chat_service_module,
        "get_settings",
        lambda: SimpleNamespace(
            internal_api_url="http://service.test",
            open_notebook_password="secret-pass",
        ),
    )
    monkeypatch.setattr(
        chat_service_module.httpx,
        "AsyncClient",
        _DummyAsyncClient,
    )

    service = chat_service_module.ChatService()
    assert service.headers["Authorization"] == "Bearer secret-pass"

    sessions = await service.get_sessions("notebook:1")
    assert sessions["method"] == "get"
    assert sessions["kwargs"]["params"]["notebook_id"] == "notebook:1"

    created = await service.create_session(
        "notebook:1", title="Title", model_override="gemini-3.0-flash"
    )
    assert created["kwargs"]["json"]["title"] == "Title"
    assert created["kwargs"]["json"]["model_override"] == "gemini-3.0-flash"

    session_detail = await service.get_session("chat_session:1")
    assert session_detail["url"].endswith("/api/chat/sessions/chat_session:1")

    updated = await service.update_session(
        "chat_session:1", title="Renamed", model_override="gemini-3.1-pro"
    )
    assert updated["kwargs"]["json"]["title"] == "Renamed"

    deleted = await service.delete_session("chat_session:1")
    assert deleted["method"] == "delete"

    chat_result = await service.execute_chat(
        "chat_session:1",
        "hello",
        {"sources": [], "notes": []},
        model_override="gemini-3.0-pro",
    )
    timeout = chat_result["timeout"]
    assert timeout.connect == pytest.approx(10.0)
    assert timeout.read == pytest.approx(600.0)
    assert chat_result["kwargs"]["json"]["model_override"] == "gemini-3.0-pro"

    context_result = await service.build_context(
        "notebook:1", {"sources": {"source:1": "full content"}}
    )
    assert context_result["kwargs"]["json"]["notebook_id"] == "notebook:1"


@pytest.mark.asyncio
async def test_chat_service_error_and_validation_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chat_service_module = importlib.import_module(
        "packages.core.application.chat_service"
    )

    monkeypatch.setattr(
        chat_service_module,
        "get_settings",
        lambda: SimpleNamespace(
            internal_api_url="http://service.test",
            open_notebook_password="",
        ),
    )
    monkeypatch.setattr(
        chat_service_module.httpx,
        "AsyncClient",
        _FailingAsyncClient,
    )

    service = chat_service_module.ChatService()
    assert service.headers == {}

    with pytest.raises(RuntimeError, match="http failure"):
        await service.get_sessions("notebook:1")

    with pytest.raises(RuntimeError, match="http failure"):
        await service.create_session("notebook:1", title="x")

    with pytest.raises(RuntimeError, match="http failure"):
        await service.get_session("chat_session:1")

    with pytest.raises(ValueError, match="At least one field"):
        await service.update_session("chat_session:1")

    with pytest.raises(RuntimeError, match="http failure"):
        await service.update_session("chat_session:1", title="x")

    with pytest.raises(RuntimeError, match="http failure"):
        await service.delete_session("chat_session:1")

    with pytest.raises(RuntimeError, match="http failure"):
        await service.execute_chat(
            "chat_session:1", "hello", {"sources": [], "notes": []}
        )

    with pytest.raises(RuntimeError, match="http failure"):
        await service.build_context("notebook:1", {"sources": {}})


# ---------------------------------------------------------------------------
# credentials_service coverage
# ---------------------------------------------------------------------------


def test_validate_url_and_require_encryption_key_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        validate_url("ftp://example.com", "google")

    with pytest.raises(ValueError, match="Link-local addresses"):
        validate_url("http://169.254.1.2", "google")

    monkeypatch.setattr(
        "services.api.credentials_service.socket.getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("169.254.1.2", 0))],
    )
    with pytest.raises(ValueError, match="resolves to a link-local address"):
        validate_url("https://metadata.google.internal", "google")

    def _raise_gaierror(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr(
        "services.api.credentials_service.socket.getaddrinfo", _raise_gaierror
    )
    with pytest.raises(ValueError, match="Invalid URL format"):
        validate_url("https://unresolvable.example", "google")

    with patch("services.api.credentials_service.get_secret_from_env", return_value=""):
        with pytest.raises(ValueError, match="Encryption key not configured"):
            require_encryption_key()


def test_validate_url_additional_branches_and_encryption_key_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="hostname could not be determined"):
        validate_url("https:///missing-host", "google")

    real_ip_address = credentials_service_module.ipaddress.ip_address

    def fake_ip_address_direct(value: str):
        if value == "198.51.100.10":
            return SimpleNamespace(
                is_link_local=False,
                ipv4_mapped=SimpleNamespace(is_link_local=True),
            )
        return real_ip_address(value)

    monkeypatch.setattr(
        credentials_service_module.ipaddress, "ip_address", fake_ip_address_direct
    )
    with pytest.raises(ValueError, match="Link-local addresses"):
        validate_url("http://198.51.100.10", "google")

    def fake_ip_address_resolve(value: str):
        if value == "mapped-host.internal":
            raise ValueError("not an ip literal")
        if value == "2001:db8::5":
            return SimpleNamespace(
                is_link_local=False,
                ipv4_mapped=SimpleNamespace(is_link_local=True),
            )
        return real_ip_address(value)

    monkeypatch.setattr(
        credentials_service_module.ipaddress, "ip_address", fake_ip_address_resolve
    )
    monkeypatch.setattr(
        "services.api.credentials_service.socket.getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET6, None, None, None, ("2001:db8::5", 0, 0, 0))
        ],
    )
    with pytest.raises(ValueError, match="resolves to a link-local address"):
        validate_url("https://mapped-host.internal", "google")

    def fake_ip_address_continue(value: str):
        if value == "safe-host.internal":
            raise ValueError("not an ip literal")
        if value == "bad-ip":
            raise ValueError("not parseable")
        return real_ip_address(value)

    monkeypatch.setattr(
        credentials_service_module.ipaddress, "ip_address", fake_ip_address_continue
    )
    monkeypatch.setattr(
        "services.api.credentials_service.socket.getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, None, None, None, ("bad-ip", 0))],
    )
    validate_url("https://safe-host.internal", "google")

    with patch(
        "services.api.credentials_service.get_secret_from_env",
        return_value="configured",
    ):
        require_encryption_key()


def test_credential_to_response_maps_fields() -> None:
    cred = SimpleNamespace(
        id="cred:1",
        name="Google",
        provider="google",
        modalities=["language"],
        base_url="https://generativelanguage.googleapis.com",
        endpoint="/v1beta/models",
        api_version="v1beta",
        endpoint_llm="/llm",
        endpoint_embedding="/embedding",
        endpoint_stt="/stt",
        endpoint_tts="/tts",
        project="proj",
        location="us-central1",
        credentials_path=None,
        api_key="secret",
        created=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    response = credential_to_response(cred, model_count=3)

    assert response.id == "cred:1"
    assert response.has_api_key is True
    assert response.model_count == 3
    assert response.created.startswith("2026-01-01")


@pytest.mark.asyncio
async def test_test_credential_and_discovery_and_register_models_branches() -> None:
    def _async_return(value):
        async def _fn(*_args, **_kwargs):
            return value

        return _fn

    def _async_raise(exc: Exception):
        async def _fn(*_args, **_kwargs):
            raise exc

        return _fn

    with patch(
        "services.api.credentials_service.Credential.get",
        new=_async_return(
            SimpleNamespace(
                provider="openai", to_esperanto_config=lambda: {"api_key": "k"}
            )
        ),
    ):
        unsupported = await credentials_service_module.test_credential(
            "cred:unsupported"
        )
    assert unsupported["success"] is False

    with (
        patch(
            "services.api.credentials_service.Credential.get",
            new=_async_return(
                SimpleNamespace(
                    provider="google",
                    to_esperanto_config=lambda: {"api_key": "k"},
                )
            ),
        ),
        patch(
            "services.api.credentials_service.test_google_connection",
            new=_async_return((True, "ok")),
        ),
    ):
        success = await credentials_service_module.test_credential("cred:google")
    assert success["success"] is True

    for message, expected in [
        ("401 unauthorized", "Invalid API key"),
        ("403 forbidden", "required permissions"),
        ("rate limit exceeded", "Rate limited - but connection works"),
        ("model not found", "test model not available"),
    ]:
        with patch(
            "services.api.credentials_service.Credential.get",
            new=_async_raise(RuntimeError(message)),
        ):
            result = await credentials_service_module.test_credential("cred:error")
            assert expected in result["message"]

    long_message = "x" * 120
    with patch(
        "services.api.credentials_service.Credential.get",
        new=_async_raise(RuntimeError(long_message)),
    ):
        default_error = await credentials_service_module.test_credential("cred:long")
    assert (
        default_error["message"]
        == "Connection test failed. Check provider configuration and server logs."
    )

    rejected = await discover_with_config("openai", {"api_key": "k"})
    assert rejected == []

    with patch(
        "services.api.credentials_service.list_google_models",
        new=_async_return([{"name": "gemini-3.0-pro", "description": "pro"}]),
    ):
        discovered = await discover_with_config("google", {"api_key": "k"})
    assert discovered[0]["provider"] == "google"

    with patch(
        "services.api.credentials_service.Credential.get",
        new=_async_return(SimpleNamespace(provider="openai", id="cred:1")),
    ):
        with pytest.raises(ValueError, match="Only Google credential"):
            await register_models("cred:1", [])

    save_calls: list[tuple[str, str]] = []

    class _FakeModel:
        def __init__(self, name: str, provider: str, type: str, credential: str):
            self.name = name
            self.provider = provider
            self.type = type
            self.credential = credential

        async def save(self):
            save_calls.append((self.name, self.type))

    with (
        patch(
            "services.api.credentials_service.Credential.get",
            new=_async_return(SimpleNamespace(provider="google", id="cred:1")),
        ),
        patch(
            "packages.core.database.repository.repo_query",
            new=_async_return([{"name": "gemini-3.0-pro", "type": "language"}]),
        ),
        patch("packages.core.ai.models.Model", _FakeModel),
    ):
        result = await register_models(
            "cred:1",
            [
                SimpleNamespace(
                    name="gemini-3.0-pro", provider="google", model_type="language"
                ),
                SimpleNamespace(
                    name="gemini-embedding-001",
                    provider="google",
                    model_type="embedding",
                ),
            ],
        )

    assert result == {"created": 1, "existing": 1}
    assert save_calls == [("gemini-embedding-001", "embedding")]

    with (
        patch(
            "services.api.credentials_service.Credential.get",
            new=_async_return(SimpleNamespace(provider="google", id="cred:1")),
        ),
        patch(
            "packages.core.database.repository.repo_query",
            new=_async_return([]),
        ),
        patch("packages.core.ai.models.Model", _FakeModel),
    ):
        with pytest.raises(ValueError, match="Only Google provider models"):
            await register_models(
                "cred:1",
                [
                    SimpleNamespace(
                        name="gpt-4.1", provider="openai", model_type="language"
                    )
                ],
            )


# ---------------------------------------------------------------------------
# podcast_service coverage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_podcast_submit_generation_job_success_and_fallback_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "services.api.podcast_service.EpisodeProfile.get_by_name",
        AsyncMock(return_value=SimpleNamespace(name="ep")),
    )
    monkeypatch.setattr(
        "services.api.podcast_service.SpeakerProfile.get_by_name",
        AsyncMock(return_value=SimpleNamespace(name="sp")),
    )
    monkeypatch.setattr(
        "services.api.podcast_service.CommandService.submit_command_job",
        AsyncMock(return_value="command:1"),
    )

    job_id = await PodcastService.submit_generation_job(
        episode_profile_name="ep",
        speaker_profile_name="sp",
        episode_name="episode-1",
        content="content-body",
        idempotency_key="idem-1",
    )
    assert job_id == "command:1"

    notebook_obj = SimpleNamespace(
        get_context=AsyncMock(side_effect=RuntimeError("ctx fail"))
    )
    monkeypatch.setattr(
        "services.api.podcast_service.Notebook.get",
        AsyncMock(return_value=notebook_obj),
    )

    captured_args: dict[str, object] = {}

    async def fake_submit(**kwargs):
        captured_args.update(kwargs)
        return "command:2"

    monkeypatch.setattr(
        "services.api.podcast_service.CommandService.submit_command_job",
        AsyncMock(side_effect=fake_submit),
    )

    fallback_id = await PodcastService.submit_generation_job(
        episode_profile_name="ep",
        speaker_profile_name="sp",
        episode_name="episode-2",
        notebook_id="notebook:1",
    )
    assert fallback_id == "command:2"
    assert "Notebook ID: notebook:1" in str(captured_args["command_args"]["content"])


@pytest.mark.asyncio
async def test_podcast_service_error_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "services.api.podcast_service.EpisodeProfile.get_by_name",
        AsyncMock(return_value=None),
    )
    with pytest.raises(HTTPException) as missing_episode:
        await PodcastService.submit_generation_job(
            episode_profile_name="missing",
            speaker_profile_name="sp",
            episode_name="e1",
            content="x",
        )
    assert missing_episode.value.status_code == 500

    monkeypatch.setattr(
        "services.api.podcast_service.EpisodeProfile.get_by_name",
        AsyncMock(return_value=SimpleNamespace(name="ep")),
    )
    monkeypatch.setattr(
        "services.api.podcast_service.SpeakerProfile.get_by_name",
        AsyncMock(return_value=None),
    )
    with pytest.raises(HTTPException) as missing_speaker:
        await PodcastService.submit_generation_job(
            episode_profile_name="ep",
            speaker_profile_name="missing",
            episode_name="e1",
            content="x",
        )
    assert missing_speaker.value.status_code == 500

    monkeypatch.setattr(
        "services.api.podcast_service.SpeakerProfile.get_by_name",
        AsyncMock(return_value=SimpleNamespace(name="sp")),
    )
    with pytest.raises(HTTPException) as no_content:
        await PodcastService.submit_generation_job(
            episode_profile_name="ep",
            speaker_profile_name="sp",
            episode_name="e1",
            notebook_id=None,
            content=None,
        )
    assert no_content.value.status_code == 500

    monkeypatch.setattr(
        "services.api.podcast_service.CommandService.submit_command_job",
        AsyncMock(return_value=""),
    )
    with pytest.raises(HTTPException) as no_job_id:
        await PodcastService.submit_generation_job(
            episode_profile_name="ep",
            speaker_profile_name="sp",
            episode_name="e1",
            content="x",
        )
    assert no_job_id.value.status_code == 500

    monkeypatch.setattr(
        "services.api.podcast_service.CommandService.get_command_status",
        AsyncMock(side_effect=RuntimeError("status failed")),
    )
    with pytest.raises(HTTPException) as status_exc:
        await PodcastService.get_job_status("command:1")
    assert status_exc.value.status_code == 500

    monkeypatch.setattr(
        "services.api.podcast_service.PodcastEpisode.get_all",
        AsyncMock(side_effect=RuntimeError("list failed")),
    )
    with pytest.raises(HTTPException) as list_exc:
        await PodcastService.list_episodes()
    assert list_exc.value.status_code == 500

    monkeypatch.setattr(
        "services.api.podcast_service.PodcastEpisode.get",
        AsyncMock(side_effect=RuntimeError("not found")),
    )
    with pytest.raises(HTTPException) as get_exc:
        await PodcastService.get_episode("episode:404")
    assert get_exc.value.status_code == 404


@pytest.mark.asyncio
async def test_default_profiles_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "services.api.podcast_service.EpisodeProfile.get_all",
        AsyncMock(return_value=[SimpleNamespace(name="default")]),
    )
    existing_episode_profiles = await DefaultProfiles.create_default_episode_profiles()
    assert len(existing_episode_profiles) == 1

    monkeypatch.setattr(
        "services.api.podcast_service.EpisodeProfile.get_all",
        AsyncMock(return_value=[]),
    )
    created_episode_profiles = await DefaultProfiles.create_default_episode_profiles()
    assert created_episode_profiles == []

    monkeypatch.setattr(
        "services.api.podcast_service.EpisodeProfile.get_all",
        AsyncMock(side_effect=RuntimeError("episode profile failure")),
    )
    with pytest.raises(RuntimeError):
        await DefaultProfiles.create_default_episode_profiles()

    monkeypatch.setattr(
        "services.api.podcast_service.SpeakerProfile.get_all",
        AsyncMock(return_value=[SimpleNamespace(name="speaker")]),
    )
    existing_speaker_profiles = await DefaultProfiles.create_default_speaker_profiles()
    assert len(existing_speaker_profiles) == 1

    monkeypatch.setattr(
        "services.api.podcast_service.SpeakerProfile.get_all",
        AsyncMock(return_value=[]),
    )
    created_speaker_profiles = await DefaultProfiles.create_default_speaker_profiles()
    assert created_speaker_profiles == []

    monkeypatch.setattr(
        "services.api.podcast_service.SpeakerProfile.get_all",
        AsyncMock(side_effect=RuntimeError("speaker profile failure")),
    )
    with pytest.raises(RuntimeError):
        await DefaultProfiles.create_default_speaker_profiles()
