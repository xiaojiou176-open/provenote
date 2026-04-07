import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from packages.core.application.command_service import CommandService
from services.api.auditable_service import AuditableService
from services.api.routers import chat as chat_router
from services.api.routers import notes as notes_router
from services.api.routers import podcasts as podcasts_router
from services.api.routers import source_chat as source_chat_router


@pytest.mark.asyncio
async def test_create_session_rolls_back_when_relation_fails(monkeypatch):
    session = SimpleNamespace(
        id="chat_session:s1",
        title="s1",
        model_override=None,
        created="2026-01-01T00:00:00+00:00",
        updated="2026-01-01T00:00:00+00:00",
        save=AsyncMock(),
        relate_to_notebook=AsyncMock(side_effect=RuntimeError("relate failed")),
        delete=AsyncMock(),
    )

    monkeypatch.setattr(chat_router.Notebook, "get", AsyncMock(return_value=object()))
    monkeypatch.setattr(chat_router, "ChatSession", Mock(return_value=session))

    with pytest.raises(HTTPException):
        await chat_router.create_session(
            chat_router.CreateSessionRequest(notebook_id="notebook:1")
        )

    session.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_source_session_rolls_back_when_relation_fails(monkeypatch):
    session = SimpleNamespace(
        id="chat_session:s1",
        title="s1",
        model_override=None,
        created="2026-01-01T00:00:00+00:00",
        updated="2026-01-01T00:00:00+00:00",
        save=AsyncMock(),
        relate=AsyncMock(side_effect=RuntimeError("relate failed")),
        delete=AsyncMock(),
    )

    monkeypatch.setattr(
        source_chat_router.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1")),
    )
    monkeypatch.setattr(source_chat_router, "ChatSession", Mock(return_value=session))

    with pytest.raises(HTTPException):
        await source_chat_router.create_source_chat_session(
            request=source_chat_router.CreateSourceChatSessionRequest(
                source_id="source:1"
            ),
            source_id="source:1",
        )

    session.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_note_rolls_back_when_notebook_relation_fails(monkeypatch):
    note = SimpleNamespace(
        id="note:1",
        title="t",
        content="c",
        note_type="human",
        created="2026-01-01T00:00:00+00:00",
        updated="2026-01-01T00:00:00+00:00",
        save=AsyncMock(return_value=None),
        add_to_notebook=AsyncMock(side_effect=RuntimeError("relation failed")),
        delete=AsyncMock(),
    )
    monkeypatch.setattr(notes_router.Note, "get", AsyncMock(return_value=note))
    monkeypatch.setattr(notes_router, "Note", Mock(return_value=note))
    monkeypatch.setattr(
        "packages.core.domain.notebook.Notebook.get", AsyncMock(return_value=object())
    )

    with pytest.raises(HTTPException):
        await notes_router.create_note(
            notes_router.NoteCreate(
                title="t", content="c", note_type="human", notebook_id="notebook:1"
            )
        )

    note.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_command_submit_uses_idempotency_lock_for_concurrent_requests():
    in_memory_mapping = {"command_id": None}
    submit_count = {"count": 0}

    async def fake_get_existing_idempotent_command(
        *, idempotency_key: str, request_hash: str
    ):
        return in_memory_mapping["command_id"]

    async def fake_store_idempotency_mapping(
        *,
        idempotency_key: str,
        request_hash: str,
        app_name: str,
        command_name: str,
        command_id: str,
    ) -> None:
        await asyncio.sleep(0.02)
        in_memory_mapping["command_id"] = command_id

    def fake_submit_command(
        module_name: str, command_name: str, command_args: dict, context=None
    ):
        submit_count["count"] += 1
        return "command:one"

    with (
        patch(
            "packages.core.application.command_service.CommandService._get_existing_idempotent_command",
            new=AsyncMock(side_effect=fake_get_existing_idempotent_command),
        ),
        patch(
            "packages.core.application.command_service.CommandService._reserve_idempotency_placeholder",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "packages.core.application.command_service.CommandService._store_idempotency_mapping",
            new=AsyncMock(side_effect=fake_store_idempotency_mapping),
        ),
        patch(
            "packages.core.application.command_service.submit_command",
            new=fake_submit_command,
        ),
    ):
        first, second = await asyncio.gather(
            CommandService.submit_command_job(
                module_name="open_notebook",
                command_name="embed_note",
                command_args={"note_id": "note:1"},
                idempotency_key="idem-1",
            ),
            CommandService.submit_command_job(
                module_name="open_notebook",
                command_name="embed_note",
                command_args={"note_id": "note:1"},
                idempotency_key="idem-1",
            ),
        )

    assert first == "command:one"
    assert second == "command:one"
    assert submit_count["count"] == 1


@pytest.mark.asyncio
async def test_retry_podcast_submits_before_cleanup_and_uses_default_idempotency_key(
    monkeypatch,
):
    delete_calls = []
    submit_kwargs = {}

    async def fake_submit_generation_job(**kwargs):
        submit_kwargs.update(kwargs)
        return "command:new"

    async def fake_delete():
        delete_calls.append("deleted")

    episode = SimpleNamespace(
        id="episode:1",
        name="ep",
        episode_profile={"name": "eprofile"},
        speaker_profile={"name": "sprofile"},
        content="content",
        audio_file=None,
        get_job_detail=AsyncMock(
            return_value={"status": "failed", "error_message": "x"}
        ),
        delete=AsyncMock(side_effect=fake_delete),
    )

    monkeypatch.setattr(
        podcasts_router.PodcastService, "get_episode", AsyncMock(return_value=episode)
    )
    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "submit_generation_job",
        AsyncMock(side_effect=fake_submit_generation_job),
    )

    result = await podcasts_router.retry_podcast_episode(
        "episode:1", idempotency_key=None
    )

    assert result["job_id"] == "command:new"
    assert submit_kwargs["idempotency_key"] == "podcast-retry:episode:1"
    assert delete_calls == ["deleted"]


@pytest.mark.asyncio
async def test_auditable_run_rolls_back_source_paragraphs_when_create_fails(
    monkeypatch,
):
    service = AuditableService()
    monkeypatch.setattr(
        "services.api.auditable_service.Source.get",
        AsyncMock(return_value=SimpleNamespace(id="source:1", full_text="hello")),
    )
    monkeypatch.setattr(
        "services.api.auditable_service.auditable_graph.ainvoke",
        AsyncMock(return_value={"output": {"source_paragraphs": [{"pid": "P1"}]}}),
    )
    monkeypatch.setattr(
        service,
        "_upsert_source_paragraphs",
        AsyncMock(return_value=["source_paragraph:source_1__P1"]),
    )
    monkeypatch.setattr(
        "services.api.auditable_service.repo_create",
        AsyncMock(side_effect=RuntimeError("create failed")),
    )
    cleanup_calls = []

    async def fake_repo_query(query: str, params: dict | None = None):
        cleanup_calls.append((query, params))
        return []

    monkeypatch.setattr(
        "services.api.auditable_service.repo_query",
        AsyncMock(side_effect=fake_repo_query),
    )

    with pytest.raises(RuntimeError, match="create failed"):
        await service.create_run(
            "source:1",
            SimpleNamespace(
                model_id="gemini-3.1-pro-preview",
                language="zh-CN",
                near_dedup_threshold=0.97,
            ),
        )

    assert len(cleanup_calls) == 1
    assert cleanup_calls[0][0] == "DELETE $id"
