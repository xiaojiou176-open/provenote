from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from packages.core.application.models import SourceCreate, SourceUpdate
from packages.core.exceptions import InvalidInputError
from services.api.routers import sources_service as sources_service_router


class _FakeSource:
    def __init__(self, source_id: str = "source:1") -> None:
        self.id = source_id
        self.title = "old"
        self.topics = ["old"]
        self.asset = None
        self.full_text = None
        self.command = None
        self.created = "2026-01-01"
        self.updated = "2026-01-02"
        self.saved = 0
        self.deleted = 0

    async def save(self) -> None:
        self.saved += 1

    async def delete(self) -> None:
        self.deleted += 1

    async def add_to_notebook(self, _notebook_id: str) -> None:
        return None

    async def get_embedded_chunks(self) -> int:
        return 3

    async def get_status(self) -> str:
        return "done"


class _FakeSyncResult:
    def __init__(self, ok: bool, error_message: str = "boom") -> None:
        self._ok = ok
        self.error_message = error_message

    def is_success(self) -> bool:
        return self._ok


@pytest.mark.asyncio
async def test_sources_service_validate_create_process_update_and_retry_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(HTTPException) as nb_exc:
        monkeypatch.setattr(
            sources_service_router.Notebook, "get", AsyncMock(return_value=None)
        )
        await sources_service_router._validate_notebooks(["notebook:404"])
    assert nb_exc.value.status_code == 404

    with pytest.raises(HTTPException) as trans_exc:
        monkeypatch.setattr(
            sources_service_router.Transformation,
            "get",
            AsyncMock(return_value=None),
        )
        await sources_service_router._validate_transformations(["trans:404"])
    assert trans_exc.value.status_code == 404

    source_shell = _FakeSource("source:shell")
    source_shell.add_to_notebook = AsyncMock()
    source_factory = Mock(return_value=source_shell)
    monkeypatch.setattr(sources_service_router, "Source", source_factory)
    created_shell = await sources_service_router._create_source_shell(
        SourceCreate(type="text", content="hello", notebooks=["n1", "n2"])
    )
    assert created_shell.id == "source:shell"
    source_factory.assert_called_once_with(
        title="Processing...",
        topics=[],
        full_text="hello",
    )
    assert source_shell.add_to_notebook.await_count == 2

    async_source = _FakeSource("source:async")
    monkeypatch.setattr(
        sources_service_router,
        "_create_source_shell",
        AsyncMock(return_value=async_source),
    )
    monkeypatch.setattr(
        sources_service_router.CommandService,
        "submit_command_job",
        AsyncMock(return_value="command:async"),
    )
    monkeypatch.setattr(
        sources_service_router, "ensure_record_id", lambda x: f"RID:{x}"
    )
    async_resp = await sources_service_router._process_source_async(
        SourceCreate(
            type="text", content="hello", notebooks=["n1"], async_processing=True
        ),
        {"content": "hello"},
        [],
    )
    assert async_resp.command_id == "command:async"
    assert async_source.command == "RID:command:async"

    failing_async_source = _FakeSource("source:async-fail")
    monkeypatch.setattr(
        sources_service_router,
        "_create_source_shell",
        AsyncMock(return_value=failing_async_source),
    )
    monkeypatch.setattr(
        sources_service_router.CommandService,
        "submit_command_job",
        AsyncMock(side_effect=RuntimeError("queue down")),
    )
    with pytest.raises(HTTPException) as async_fail:
        await sources_service_router._process_source_async(
            SourceCreate(
                type="text", content="x", notebooks=["n1"], async_processing=True
            ),
            {"content": "x"},
            [],
        )
    assert async_fail.value.status_code == 500
    assert failing_async_source.deleted == 1

    sync_source = _FakeSource("source:sync")
    monkeypatch.setattr(
        sources_service_router,
        "_create_source_shell",
        AsyncMock(return_value=sync_source),
    )
    monkeypatch.setattr(
        sources_service_router,
        "process_source_command",
        AsyncMock(return_value=SimpleNamespace(success=True, error_message=None)),
    )
    processed_source = _FakeSource("source:sync")
    processed_source.full_text = "processed text"
    monkeypatch.setattr(
        sources_service_router.Source,
        "get",
        AsyncMock(return_value=processed_source),
    )
    monkeypatch.setattr(
        sources_service_router,
        "build_source_response",
        lambda src, chunks, **_kwargs: {"id": src.id, "embedded_chunks": chunks},
    )
    sync_resp = await sources_service_router._process_source_sync(
        SourceCreate(type="text", content="x", notebooks=["n1"]),
        {"content": "x"},
        [],
    )
    assert sync_resp["embedded_chunks"] == 3

    failed_sync_source = _FakeSource("source:sync-fail")
    monkeypatch.setattr(
        sources_service_router,
        "_create_source_shell",
        AsyncMock(return_value=failed_sync_source),
    )
    monkeypatch.setattr(
        sources_service_router,
        "process_source_command",
        AsyncMock(
            return_value=SimpleNamespace(success=False, error_message="bad proc")
        ),
    )
    with pytest.raises(HTTPException) as sync_fail:
        await sources_service_router._process_source_sync(
            SourceCreate(type="text", content="x", notebooks=["n1"]),
            {"content": "x"},
            [],
        )
    assert sync_fail.value.detail == "Failed to process source"
    assert failed_sync_source.deleted == 1

    no_id_source = _FakeSource(source_id="")
    monkeypatch.setattr(
        sources_service_router,
        "_create_source_shell",
        AsyncMock(return_value=no_id_source),
    )
    monkeypatch.setattr(
        sources_service_router,
        "process_source_command",
        AsyncMock(return_value=SimpleNamespace(success=True, error_message=None)),
    )
    with pytest.raises(HTTPException) as no_id_exc:
        await sources_service_router._process_source_sync(
            SourceCreate(type="text", content="x", notebooks=["n1"]),
            {"content": "x"},
            [],
        )
    assert no_id_exc.value.detail == "Source ID is missing"

    monkeypatch.setattr(
        sources_service_router,
        "_validate_notebooks",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        sources_service_router,
        "_validate_transformations",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        sources_service_router,
        "_process_source_sync",
        AsyncMock(return_value={"mode": "sync"}),
    )
    create_sync = await sources_service_router.create_source_service(
        SourceCreate(
            type="text", content="hello", notebooks=["n1"], async_processing=False
        ),
        upload_file=None,
    )
    assert create_sync["mode"] == "sync"

    monkeypatch.setattr(
        sources_service_router,
        "_process_source_async",
        AsyncMock(return_value={"mode": "async"}),
    )
    create_async = await sources_service_router.create_source_service(
        SourceCreate(
            type="text", content="hello", notebooks=["n1"], async_processing=True
        ),
        upload_file=None,
    )
    assert create_async["mode"] == "async"

    upload = SimpleNamespace(filename="x.txt")
    monkeypatch.setattr(
        sources_service_router,
        "save_uploaded_file",
        AsyncMock(side_effect=ValueError("bad file")),
    )
    cleanup_mock = Mock()
    monkeypatch.setattr(sources_service_router, "cleanup_uploaded_file", cleanup_mock)
    with pytest.raises(HTTPException) as upload_exc:
        await sources_service_router.create_source_service(
            SourceCreate(type="upload", file_path="/tmp/x", notebooks=["n1"]),
            upload_file=upload,
        )
    assert upload_exc.value.status_code == 400
    assert cleanup_mock.call_count == 1

    monkeypatch.setattr(
        sources_service_router,
        "_build_content_state",
        Mock(side_effect=InvalidInputError("bad input")),
    )
    with pytest.raises(HTTPException) as invalid_exc:
        await sources_service_router.create_source_service(
            SourceCreate(type="text", content="hello", notebooks=["n1"]),
            upload_file=None,
        )
    assert invalid_exc.value.status_code == 400

    monkeypatch.setattr(
        sources_service_router,
        "_build_content_state",
        Mock(side_effect=RuntimeError("explode")),
    )
    with pytest.raises(HTTPException) as create_exc:
        await sources_service_router.create_source_service(
            SourceCreate(type="text", content="hello", notebooks=["n1"]),
            upload_file=None,
        )
    assert create_exc.value.status_code == 500

    source_for_update = _FakeSource("source:update")
    monkeypatch.setattr(
        sources_service_router.Source,
        "get",
        AsyncMock(return_value=source_for_update),
    )
    monkeypatch.setattr(
        sources_service_router,
        "build_source_response",
        lambda src, chunks, **_kwargs: {
            "id": src.id,
            "title": src.title,
            "chunks": chunks,
        },
    )
    update_resp = await sources_service_router.update_source_service(
        "source:update", SourceUpdate(title="new", topics=["t1"])
    )
    assert update_resp["title"] == "new"

    monkeypatch.setattr(
        sources_service_router.Source,
        "get",
        AsyncMock(return_value=None),
    )
    with pytest.raises(HTTPException) as update_404:
        await sources_service_router.update_source_service(
            "source:404", SourceUpdate(title="new")
        )
    assert update_404.value.status_code == 404

    invalid_source = _FakeSource("source:invalid")
    invalid_source.save = AsyncMock(side_effect=InvalidInputError("invalid payload"))
    monkeypatch.setattr(
        sources_service_router.Source,
        "get",
        AsyncMock(return_value=invalid_source),
    )
    with pytest.raises(HTTPException) as update_400:
        await sources_service_router.update_source_service(
            "source:invalid", SourceUpdate(title="new")
        )
    assert update_400.value.status_code == 400

    retry_source = _FakeSource("source:retry")
    retry_source.command = "command:1"
    retry_source.get_status = AsyncMock(return_value="failed")
    retry_source.full_text = "retry text"
    monkeypatch.setattr(
        sources_service_router.Source,
        "get",
        AsyncMock(return_value=retry_source),
    )
    monkeypatch.setattr(
        sources_service_router,
        "repo_query",
        AsyncMock(return_value=[{"notebook_id": "notebook:1"}]),
    )
    monkeypatch.setattr(
        sources_service_router.CommandService,
        "submit_command_job",
        AsyncMock(return_value="cmd-2"),
    )
    monkeypatch.setattr(
        sources_service_router, "ensure_record_id", lambda v: f"RID:{v}"
    )
    monkeypatch.setattr(
        sources_service_router,
        "build_source_response",
        lambda src, chunks, **kwargs: {
            "id": src.id,
            "chunks": chunks,
            "command_id": kwargs.get("command_id"),
            "status": kwargs.get("status"),
        },
    )
    retry_resp = await sources_service_router.retry_source_processing_service(
        "source:retry"
    )
    assert retry_resp["command_id"] == "cmd-2"
    assert retry_resp["status"] == "queued"

    no_ref_source = _FakeSource("source:no-ref")
    no_ref_source.full_text = "x"
    monkeypatch.setattr(
        sources_service_router.Source,
        "get",
        AsyncMock(return_value=no_ref_source),
    )
    monkeypatch.setattr(
        sources_service_router, "repo_query", AsyncMock(return_value=[])
    )
    with pytest.raises(HTTPException) as no_ref_exc:
        await sources_service_router.retry_source_processing_service("source:no-ref")
    assert no_ref_exc.value.status_code == 400

    asset_bad_source = _FakeSource("source:asset-bad")
    asset_bad_source.asset = SimpleNamespace(file_path=None, url=None)
    monkeypatch.setattr(
        sources_service_router.Source,
        "get",
        AsyncMock(return_value=asset_bad_source),
    )
    monkeypatch.setattr(
        sources_service_router,
        "repo_query",
        AsyncMock(return_value=[{"notebook_id": "notebook:1"}]),
    )
    with pytest.raises(HTTPException) as asset_bad_exc:
        await sources_service_router.retry_source_processing_service("source:asset-bad")
    assert asset_bad_exc.value.status_code == 400

    no_content_source = _FakeSource("source:no-content")
    no_content_source.asset = None
    no_content_source.full_text = None
    monkeypatch.setattr(
        sources_service_router.Source,
        "get",
        AsyncMock(return_value=no_content_source),
    )
    with pytest.raises(HTTPException) as no_content_exc:
        await sources_service_router.retry_source_processing_service(
            "source:no-content"
        )
    assert no_content_exc.value.status_code == 400

    submit_fail_source = _FakeSource("source:submit-fail")
    submit_fail_source.full_text = "x"
    monkeypatch.setattr(
        sources_service_router.Source,
        "get",
        AsyncMock(return_value=submit_fail_source),
    )
    monkeypatch.setattr(
        sources_service_router,
        "repo_query",
        AsyncMock(return_value=[{"notebook_id": "notebook:1"}]),
    )
    monkeypatch.setattr(
        sources_service_router.CommandService,
        "submit_command_job",
        AsyncMock(side_effect=RuntimeError("queue down")),
    )
    with pytest.raises(HTTPException) as submit_fail_exc:
        await sources_service_router.retry_source_processing_service(
            "source:submit-fail"
        )
    assert submit_fail_exc.value.status_code == 500

    monkeypatch.setattr(
        sources_service_router.Source,
        "get",
        AsyncMock(side_effect=RuntimeError("db offline")),
    )
    with pytest.raises(HTTPException) as retry_outer_exc:
        await sources_service_router.retry_source_processing_service("source:boom")
    assert retry_outer_exc.value.status_code == 500
