import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from packages.core.application.command_service import (
    CommandConflictError,
    CommandService,
)
from packages.core.database.repository import ensure_record_id


@pytest.mark.asyncio
async def test_submit_idempotent_job_reserves_before_submit() -> None:
    state = {"reserved": False, "stored_status": None}

    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM $record_id"):
            return []
        if query.startswith("CREATE command_idempotency:"):
            state["reserved"] = True
            return []
        if query.startswith("UPSERT command_idempotency:"):
            state["stored_status"] = params["data"]["status"]
            return []
        raise AssertionError(f"Unexpected query: {query}")

    def fake_submit_command(
        module_name: str, command_name: str, command_args: dict, context=None
    ):
        assert state["reserved"] is True
        return "command:new"

    with (
        patch(
            "packages.core.application.command_service.repo_query",
            new=AsyncMock(side_effect=fake_repo_query),
        ),
        patch(
            "packages.core.application.command_service.submit_command",
            new=fake_submit_command,
        ),
    ):
        command_id = await CommandService._submit_command_job_impl(
            module_name="open_notebook",
            command_name="embed_note",
            command_args={"note_id": "note:1"},
            context={},
            idempotency_key="idem-atomic-1",
        )

    assert command_id == "command:new"
    assert state["stored_status"] == "submitted"


@pytest.mark.asyncio
async def test_submit_idempotent_job_conflicts_when_placeholder_processing() -> None:
    state = {"select_calls": 0}

    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM $record_id"):
            state["select_calls"] += 1
            if state["select_calls"] == 1:
                return []
            return [{"request_hash": "", "status": "processing", "command_id": None}]
        if query.startswith("CREATE command_idempotency:"):
            raise RuntimeError("already contains")
        raise AssertionError(f"Unexpected query: {query}")

    with (
        patch(
            "packages.core.application.command_service.repo_query",
            new=AsyncMock(side_effect=fake_repo_query),
        ),
        patch(
            "packages.core.application.command_service.submit_command"
        ) as mock_submit,
    ):
        with pytest.raises(
            CommandConflictError, match="currently being processed; retry later"
        ):
            await CommandService._submit_command_job_impl(
                module_name="open_notebook",
                command_name="embed_note",
                command_args={"note_id": "note:1"},
                context={},
                idempotency_key="idem-atomic-2",
            )

    mock_submit.assert_not_called()


@pytest.mark.asyncio
async def test_submit_idempotent_job_conflicts_when_failed_cooldown_not_elapsed() -> (
    None
):
    state = {"select_calls": 0, "update_calls": 0}

    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM $record_id"):
            state["select_calls"] += 1
            if state["select_calls"] == 1:
                return []
            return [
                {
                    "request_hash": "",
                    "status": "failed",
                    "command_id": None,
                    "updated": datetime.now(timezone.utc) - timedelta(seconds=60),
                }
            ]
        if query.startswith("CREATE command_idempotency:"):
            raise RuntimeError("already contains")
        if query.startswith("UPDATE $record_id MERGE $data"):
            state["update_calls"] += 1
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with (
        patch(
            "packages.core.application.command_service.repo_query",
            new=AsyncMock(side_effect=fake_repo_query),
        ),
        patch(
            "packages.core.application.command_service.submit_command"
        ) as mock_submit,
    ):
        with pytest.raises(
            CommandConflictError, match="cooling down after failure; retry later"
        ):
            await CommandService._submit_command_job_impl(
                module_name="open_notebook",
                command_name="embed_note",
                command_args={"note_id": "note:1"},
                context={},
                idempotency_key="idem-atomic-failed-cooldown",
            )

    assert state["update_calls"] == 0
    mock_submit.assert_not_called()


@pytest.mark.asyncio
async def test_submit_idempotent_job_retries_when_failed_cooldown_elapsed() -> None:
    state = {"select_calls": 0, "update_calls": 0, "stored_status": None}

    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM $record_id"):
            state["select_calls"] += 1
            if state["select_calls"] == 1:
                return []
            return [
                {
                    "request_hash": "",
                    "status": "failed",
                    "command_id": None,
                    "updated": datetime.now(timezone.utc) - timedelta(minutes=10),
                }
            ]
        if query.startswith("CREATE command_idempotency:"):
            raise RuntimeError("already contains")
        if query.startswith("UPDATE $record_id MERGE $data"):
            state["update_calls"] += 1
            state["update_data"] = dict(params.get("data", {}))
            return [{"status": "processing"}]
        if query.startswith("UPSERT command_idempotency:"):
            state["stored_status"] = params["data"]["status"]
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with (
        patch(
            "packages.core.application.command_service.repo_query",
            new=AsyncMock(side_effect=fake_repo_query),
        ),
        patch(
            "packages.core.application.command_service.submit_command",
            return_value="command:retry",
        ),
    ):
        command_id = await CommandService._submit_command_job_impl(
            module_name="open_notebook",
            command_name="embed_note",
            command_args={"note_id": "note:1"},
            context={},
            idempotency_key="idem-atomic-failed-retry",
        )

    assert command_id == "command:retry"
    assert state["update_calls"] == 1
    assert state["stored_status"] == "submitted"
    data = state.get("update_data", {})
    assert data.get("status") == "processing" and data.get("command_id") is None
    assert data.get("last_error") is None


@pytest.mark.asyncio
async def test_submit_idempotent_job_repairs_legacy_schema_fields() -> None:
    state = {"create_calls": 0, "repairs": []}

    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM $record_id"):
            return []
        if query.startswith("CREATE command_idempotency:"):
            state["create_calls"] += 1
            if state["create_calls"] == 1:
                raise RuntimeError(
                    "Field `status` is not defined on command_idempotency"
                )
            return []
        if query.startswith(
            "DEFINE FIELD IF NOT EXISTS status ON command_idempotency TYPE string"
        ):
            state["repairs"].append("status")
            return []
        if query.startswith(
            "DEFINE FIELD IF NOT EXISTS last_error ON command_idempotency TYPE option<string>"
        ):
            state["repairs"].append("last_error")
            return []
        if query.startswith("UPSERT command_idempotency:"):
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with (
        patch(
            "packages.core.application.command_service.repo_query",
            new=AsyncMock(side_effect=fake_repo_query),
        ),
        patch(
            "packages.core.application.command_service._IDEMPOTENCY_SCHEMA_REPAIRED",
            new=False,
        ),
        patch(
            "packages.core.application.command_service.submit_command",
            return_value="command:fixed",
        ),
    ):
        command_id = await CommandService._submit_command_job_impl(
            module_name="open_notebook",
            command_name="embed_note",
            command_args={"note_id": "note:1"},
            context={},
            idempotency_key="idem-legacy-schema-1",
        )

    assert command_id == "command:fixed"
    assert state["create_calls"] == 2
    assert state["repairs"] == ["status", "last_error"]


@pytest.mark.asyncio
async def test_submit_idempotent_job_conflicts_on_payload_mismatch() -> None:
    state = {"select_calls": 0}

    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM $record_id"):
            state["select_calls"] += 1
            if state["select_calls"] == 1:
                return []
            return [
                {
                    "request_hash": "different-hash",
                    "status": "submitted",
                    "command_id": "command:old",
                }
            ]
        if query.startswith("CREATE command_idempotency:"):
            raise RuntimeError("already contains")
        raise AssertionError(f"Unexpected query: {query}")

    with (
        patch(
            "packages.core.application.command_service.repo_query",
            new=AsyncMock(side_effect=fake_repo_query),
        ),
        patch(
            "packages.core.application.command_service.submit_command"
        ) as mock_submit,
    ):
        with pytest.raises(
            CommandConflictError, match="already used with different payload"
        ):
            await CommandService._submit_command_job_impl(
                module_name="open_notebook",
                command_name="embed_note",
                command_args={"note_id": "note:1"},
                context={},
                idempotency_key="idem-atomic-3",
            )

    mock_submit.assert_not_called()


@pytest.mark.asyncio
async def test_sync_dead_letter_does_not_double_increment_for_same_failed_state() -> (
    None
):
    command_updated = datetime(2026, 2, 22, 0, 0, tzinfo=timezone.utc)
    existing_row = {
        "failure_count": 3,
        "first_failed_at": command_updated - timedelta(hours=2),
        "last_failed_at": command_updated + timedelta(minutes=1),
        "created": command_updated - timedelta(hours=2),
        "requeue_count": 0,
        "last_requeued_command_id": None,
        "last_requeued_at": None,
    }

    recorded_payload: dict = {}

    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM $record_id"):
            return [existing_row]
        if query.startswith("UPSERT command_dead_letter:"):
            recorded_payload.update(params["data"])
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=fake_repo_query),
    ):
        await CommandService._sync_dead_letter_if_failed(
            {
                "id": "command:abc",
                "app": "open_notebook",
                "name": "embed_source",
                "args": {"source_id": "source:1"},
                "context": {},
                "error_message": "failed",
                "status": "failed",
                "updated": command_updated,
            }
        )

    assert recorded_payload["failure_count"] == 3
    assert recorded_payload["status"] == "failed"


@pytest.mark.asyncio
async def test_requeue_dead_letter_uses_service_submit_and_tracks_lifecycle() -> None:
    entry_row = {
        "id": "command_dead_letter:abc",
        "app": "open_notebook",
        "name": "run_transformation",
        "args": {"source_id": "source:1", "transformation_id": "transformation:1"},
        "context": {},
        "requeue_count": 1,
        "last_requeued_command_id": None,
    }
    update_payload: dict = {}

    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM $entry_id"):
            return [entry_row]
        if query.startswith("UPDATE $entry_id MERGE $data"):
            update_payload.update(params["data"])
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with (
        patch(
            "packages.core.application.command_service.repo_query",
            new=AsyncMock(side_effect=fake_repo_query),
        ),
        patch(
            "packages.core.application.command_service.CommandService.submit_command_job",
            new=AsyncMock(return_value="command:new"),
        ) as mock_submit,
    ):
        result = await CommandService.requeue_dead_letter("command_dead_letter:abc")

    assert result["command_id"] == "command:new"
    assert update_payload["status"] == "requeued"
    assert update_payload["requeue_count"] == 2
    mock_submit.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_command_job_accepts_queued_state() -> None:
    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT id, status FROM $command_id"):
            return [{"id": "command:queued", "status": "queued"}]
        if query.startswith("UPDATE $command_id MERGE $data WHERE"):
            return [{"id": "command:queued", "status": "canceled"}]
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=fake_repo_query),
    ):
        result = await CommandService.cancel_command_job("command:queued")

    assert result["cancelled"] is True
    assert result["status"] == "canceled"


@pytest.mark.asyncio
async def test_cancel_command_job_detects_race_to_running_state() -> None:
    state = {"select_calls": 0}

    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT id, status FROM $command_id"):
            state["select_calls"] += 1
            if state["select_calls"] == 1:
                return [{"id": "command:queued", "status": "queued"}]
            return [{"id": "command:queued", "status": "running"}]
        if query.startswith("UPDATE $command_id MERGE $data WHERE"):
            return []
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=fake_repo_query),
    ):
        with pytest.raises(
            CommandConflictError, match="already running and cannot be canceled safely"
        ):
            await CommandService.cancel_command_job("command:queued")


@pytest.mark.asyncio
async def test_get_command_status_failed_triggers_dead_letter_event() -> None:
    status_obj = SimpleNamespace(
        status="failed",
        result=None,
        error_message="boom",
        created=None,
        updated=None,
        progress=None,
    )
    with (
        patch(
            "packages.core.application.command_service.get_command_status",
            new=AsyncMock(return_value=status_obj),
        ),
        patch(
            "packages.core.application.command_service.CommandService.record_command_failure_event",
            new=AsyncMock(),
        ) as mock_record,
    ):
        result = await CommandService.get_command_status("command:1")

    assert result["status"] == "failed"
    mock_record.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_dead_letter_entries_adds_requeued_status() -> None:
    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM command_dead_letter"):
            return [
                {
                    "id": "command_dead_letter:1",
                    "status": "failed",
                    "last_requeued_command_id": "command:2",
                }
            ]
        if query.startswith("SELECT status FROM $command_id"):
            return [{"status": "cancelled"}]
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=fake_repo_query),
    ):
        result = await CommandService.list_dead_letter_entries()

    assert result[0]["status"] == "failed"
    assert result[0]["last_requeued_status"] == "canceled"


@pytest.mark.asyncio
async def test_list_dead_letter_entries_accepts_recordid_requeue_id() -> None:
    expected_command_id = ensure_record_id("command:2")
    captured_command_id = []

    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM command_dead_letter"):
            return [
                {
                    "id": "command_dead_letter:1",
                    "status": "failed",
                    "last_requeued_command_id": expected_command_id,
                }
            ]
        if query.startswith("SELECT status FROM $command_id"):
            captured_command_id.append(str(params.get("command_id", "")))
            return [{"status": "queued"}]
        raise AssertionError(f"Unexpected query: {query}")

    with patch(
        "packages.core.application.command_service.repo_query",
        new=AsyncMock(side_effect=fake_repo_query),
    ):
        result = await CommandService.list_dead_letter_entries()

    assert result[0]["last_requeued_status"] == "queued"
    assert captured_command_id == [str(expected_command_id)], (
        f"command_id mismatch: {captured_command_id} vs {expected_command_id}"
    )


@pytest.mark.asyncio
async def test_requeue_dead_letter_prevents_duplicate_concurrent_submissions() -> None:
    state = {
        "entry": {
            "id": "command_dead_letter:abc",
            "app": "open_notebook",
            "name": "run_transformation",
            "args": {"source_id": "source:1"},
            "context": {},
            "requeue_count": 0,
            "last_requeued_command_id": None,
        },
        "submitted": 0,
        "status_by_command": {},
    }

    async def fake_repo_query(query: str, params: dict | None = None):
        if query.startswith("SELECT * FROM $entry_id"):
            return [dict(state["entry"])]
        if query.startswith("SELECT status FROM $command_id"):
            command_id = str(params["command_id"])
            for known_id, known_status in state["status_by_command"].items():
                if known_id in command_id:
                    return [{"status": known_status}]
            return []
        if query.startswith("UPDATE $entry_id MERGE $data"):
            state["entry"].update(params["data"])
            return []
        raise AssertionError(f"Unexpected query: {query}")

    async def fake_submit_command_job(**kwargs):
        state["submitted"] += 1
        command_id = f"command:new-{state['submitted']}"
        state["status_by_command"][command_id] = "queued"
        state["status_by_command"][str(ensure_record_id(command_id))] = "queued"
        await asyncio.sleep(0)
        return command_id

    with (
        patch(
            "packages.core.application.command_service.repo_query",
            new=AsyncMock(side_effect=fake_repo_query),
        ),
        patch(
            "packages.core.application.command_service.CommandService.submit_command_job",
            new=AsyncMock(side_effect=fake_submit_command_job),
        ),
    ):
        results = await asyncio.gather(
            CommandService.requeue_dead_letter("command_dead_letter:abc"),
            CommandService.requeue_dead_letter("command_dead_letter:abc"),
            return_exceptions=True,
        )

    success_results = [item for item in results if not isinstance(item, Exception)]
    errors = [item for item in results if isinstance(item, Exception)]

    assert len(success_results) == 1
    assert len(errors) == 1
    assert isinstance(errors[0], CommandConflictError)
    assert "active requeued command" in str(errors[0])
    assert state["submitted"] == 1
