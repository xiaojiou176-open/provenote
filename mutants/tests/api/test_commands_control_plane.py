from unittest.mock import AsyncMock, patch

from packages.core.application.command_service import (
    CommandConflictError,
    CommandNotFoundError,
)


def test_execute_command_passes_idempotency_key_header(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.submit_command_job",
        new=AsyncMock(return_value="command:123"),
    ) as mock_submit:
        response = api_client.post(
            "/api/commands/jobs",
            json={
                "app": "open_notebook",
                "command": "process_text",
                "input": {"text": "hello"},
            },
            headers={"Idempotency-Key": "idem-key-1"},
        )

    assert response.status_code == 200
    mock_submit.assert_awaited_once()
    assert mock_submit.await_args.kwargs["idempotency_key"] == "idem-key-1"


def test_cancel_running_command_returns_409(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.cancel_command_job",
        new=AsyncMock(side_effect=CommandConflictError("running")),
    ):
        response = api_client.delete("/api/commands/jobs/command:abc")

    assert response.status_code == 409


def test_list_command_jobs_forwards_filters(api_client) -> None:
    fake_rows = [{"id": "command:1", "status": "new"}]
    with patch(
        "services.api.routers.commands.CommandService.list_command_jobs",
        new=AsyncMock(return_value=fake_rows),
    ) as mock_list:
        response = api_client.get(
            "/api/commands/jobs?app_filter=open_notebook&command_filter=embed_source&status_filter=new&limit=10&offset=5"
        )

    assert response.status_code == 200
    assert response.json() == fake_rows
    mock_list.assert_awaited_once()


def test_requeue_dead_letter_not_found_returns_404(api_client) -> None:
    with patch(
        "services.api.routers.commands.CommandService.requeue_dead_letter",
        new=AsyncMock(side_effect=CommandNotFoundError("missing")),
    ):
        response = api_client.post(
            "/api/commands/dead-letter/command_dead_letter:missing/requeue"
        )

    assert response.status_code == 404
