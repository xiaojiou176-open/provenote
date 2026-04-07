from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from packages.core.database.repository import ensure_record_id
from services.api.routers.notebooks import remove_source_from_notebook
from services.api.routers.sources_service import retry_source_processing_service


class _FakeRetrySource:
    def __init__(self) -> None:
        self.id = "source:1"
        self.command = None
        self.asset = None
        self.full_text = "retry text"
        self.saved = False

    async def save(self) -> None:
        self.saved = True

    async def get_embedded_chunks(self) -> int:
        return 0


@pytest.mark.asyncio
@patch("services.api.routers.notebooks.repo_query", new_callable=AsyncMock)
@patch("services.api.routers.notebooks.Notebook.get", new_callable=AsyncMock)
async def test_remove_source_from_notebook_uses_same_direction_as_create(
    mock_notebook_get: AsyncMock,
    mock_repo_query: AsyncMock,
) -> None:
    mock_notebook_get.return_value = SimpleNamespace(id="notebook:1")
    mock_repo_query.return_value = []

    result = await remove_source_from_notebook("notebook:1", "source:1")

    assert result["message"] == "Source removed from notebook successfully"
    mock_repo_query.assert_awaited_once()
    query, params = mock_repo_query.await_args.args
    assert query == "DELETE FROM reference WHERE out = $source_id AND in = $notebook_id"
    assert params["source_id"] == ensure_record_id("source:1")
    assert params["notebook_id"] == ensure_record_id("notebook:1")


@pytest.mark.asyncio
@patch("services.api.routers.sources_service.build_source_response")
@patch(
    "services.api.routers.sources_service.CommandService.submit_command_job",
    new_callable=AsyncMock,
)
@patch("services.api.routers.sources_service.repo_query", new_callable=AsyncMock)
@patch("services.api.routers.sources_service.Source.get", new_callable=AsyncMock)
async def test_retry_source_processing_queries_reference_by_in_out_fields(
    mock_source_get: AsyncMock,
    mock_repo_query: AsyncMock,
    mock_submit_command_job: AsyncMock,
    mock_build_source_response,
) -> None:
    source = _FakeRetrySource()
    mock_source_get.return_value = source
    mock_repo_query.return_value = [{"notebook_id": "notebook:1"}]
    mock_submit_command_job.return_value = "cmd-1"
    mock_build_source_response.return_value = {"status": "queued", "ok": True}

    result = await retry_source_processing_service("source:1")

    assert result == {"status": "queued", "ok": True}
    assert source.saved is True

    query, params = mock_repo_query.await_args.args
    assert query == "SELECT in AS notebook_id FROM reference WHERE out = $source_id"
    assert params["source_id"] == ensure_record_id("source:1")

    submit_args = mock_submit_command_job.await_args.args
    assert submit_args[0] == "open_notebook"
    assert submit_args[1] == "process_source"
    assert submit_args[2]["notebook_ids"] == ["notebook:1"]
