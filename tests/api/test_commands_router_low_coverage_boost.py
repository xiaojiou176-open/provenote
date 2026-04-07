from unittest.mock import AsyncMock, patch

from packages.core.application.command_service import (
    CommandConflictError,
    CommandNotFoundError,
)


def test_execute_command_prefers_body_idempotency_key_over_header(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.submit_command_job",
        new=AsyncMock(return_value="command:job:1"),
    ) as mock_submit:
        response = api_client.post(
            "/api/commands/jobs",
            json={
                "app": "open_notebook",
                "command": "process_text",
                "input": {"text": "hello"},
                "idempotency_key": "body-key",
            },
            headers={"Idempotency-Key": "header-key"},
        )

    assert response.status_code == 200
    assert response.json()["job_id"] == "command:job:1"
    assert mock_submit.await_args.kwargs["idempotency_key"] == "body-key"


def test_execute_command_conflict_returns_409(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.submit_command_job",
        new=AsyncMock(side_effect=CommandConflictError("duplicate job")),
    ):
        response = api_client.post(
            "/api/commands/jobs",
            json={
                "app": "open_notebook",
                "command": "process_text",
                "input": {"text": "hello"},
            },
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "duplicate job"


def test_execute_command_unexpected_error_returns_500(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.submit_command_job",
        new=AsyncMock(side_effect=RuntimeError("queue unavailable")),
    ):
        response = api_client.post(
            "/api/commands/jobs",
            json={
                "app": "open_notebook",
                "command": "process_text",
                "input": {"text": "hello"},
            },
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_get_command_job_status_success(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.get_command_status",
        new=AsyncMock(
            return_value={
                "job_id": "command:1",
                "status": "running",
                "result": None,
                "error_message": None,
                "created": "2026-01-01T00:00:00Z",
                "updated": "2026-01-01T00:00:01Z",
                "progress": {"done": 1, "total": 2},
            }
        ),
    ):
        response = api_client.get("/api/commands/jobs/command:1")

    assert response.status_code == 200
    assert response.json()["status"] == "running"
    assert response.json()["progress"] == {"done": 1, "total": 2}


def test_get_command_job_status_failure_returns_500(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.get_command_status",
        new=AsyncMock(side_effect=RuntimeError("db down")),
    ):
        response = api_client.get("/api/commands/jobs/command:missing")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_cancel_command_job_success(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.cancel_command_job",
        new=AsyncMock(
            return_value={
                "job_id": "command:1",
                "cancelled": True,
                "status": "cancelled",
                "message": "Cancelled",
            }
        ),
    ):
        response = api_client.delete("/api/commands/jobs/command:1")

    assert response.status_code == 200
    assert response.json()["cancelled"] is True


def test_cancel_command_job_not_found_returns_404(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.cancel_command_job",
        new=AsyncMock(side_effect=CommandNotFoundError("job missing")),
    ):
        response = api_client.delete("/api/commands/jobs/command:missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "job missing"


def test_cancel_command_job_unexpected_error_returns_500(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.cancel_command_job",
        new=AsyncMock(side_effect=RuntimeError("cancel failed")),
    ):
        response = api_client.delete("/api/commands/jobs/command:1")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_list_dead_letter_jobs_success(api_client) -> None:
    rows = [{"id": "command_dead_letter:1", "status": "failed"}]
    with patch(
        "services.api.routers.commands.CommandService.list_dead_letter_entries",
        new=AsyncMock(return_value=rows),
    ):
        response = api_client.get("/api/commands/dead-letter?limit=5&offset=1")

    assert response.status_code == 200
    assert response.json() == rows


def test_list_dead_letter_jobs_failure_returns_500(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.list_dead_letter_entries",
        new=AsyncMock(side_effect=RuntimeError("dead-letter query failed")),
    ):
        response = api_client.get("/api/commands/dead-letter")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_requeue_dead_letter_success(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.requeue_dead_letter",
        new=AsyncMock(
            return_value={
                "entry_id": "command_dead_letter:1",
                "command_id": "command:1",
                "message": "Requeued",
            }
        ),
    ):
        response = api_client.post(
            "/api/commands/dead-letter/command_dead_letter:1/requeue"
        )

    assert response.status_code == 200
    assert response.json()["command_id"] == "command:1"


def test_requeue_dead_letter_conflict_returns_409(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.requeue_dead_letter",
        new=AsyncMock(side_effect=CommandConflictError("already running")),
    ):
        response = api_client.post(
            "/api/commands/dead-letter/command_dead_letter:1/requeue"
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "already running"


def test_requeue_dead_letter_unexpected_error_returns_500(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.requeue_dead_letter",
        new=AsyncMock(side_effect=RuntimeError("requeue failed")),
    ):
        response = api_client.post(
            "/api/commands/dead-letter/command_dead_letter:1/requeue"
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_debug_registry_handles_item_level_errors(api_client) -> None:
    class GoodItem:
        app_id = "open_notebook"
        name = "process_text"

    class BadItem:
        @property
        def app_id(self):  # pragma: no cover - executed during test
            raise RuntimeError("broken item")

    with patch(
        "services.api.routers.commands.registry.get_all_commands",
        return_value=[GoodItem(), BadItem()],
    ):
        response = api_client.get("/api/commands/registry/debug")

    assert response.status_code == 200
    data = response.json()
    assert data["total_commands"] == 2
    assert data["command_items"][0]["full_id"] == "open_notebook.process_text"
    assert data["commands_by_app"] == {}


def test_debug_registry_top_level_error_fallback(api_client) -> None:
    with patch(
        "services.api.routers.commands.registry.get_all_commands",
        side_effect=RuntimeError("registry unavailable"),
    ):
        response = api_client.get("/api/commands/registry/debug")

    assert response.status_code == 200
    data = response.json()
    assert data["total_commands"] == 0
    assert data["commands_by_app"] == {}
    assert data["command_items"] == []
    assert data["error"] == "Failed to inspect command registry"
