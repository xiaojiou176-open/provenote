from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from packages.core.exceptions import NotFoundError
from services.api.routers import source_chat as source_chat_router


@pytest.mark.asyncio
async def test_create_source_chat_session_success_and_not_found_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = SimpleNamespace(
        id="chat_session:s1",
        title="generated",
        model_override="m1",
        created="2026-01-01T00:00:00Z",
        updated="2026-01-01T00:00:00Z",
        save=AsyncMock(),
        relate=AsyncMock(),
        delete=AsyncMock(),
    )
    monkeypatch.setattr(
        source_chat_router, "ChatSession", MagicMock(return_value=session)
    )
    monkeypatch.setattr(
        source_chat_router.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1")),
    )

    created = await source_chat_router.create_source_chat_session(
        request=source_chat_router.CreateSourceChatSessionRequest(
            source_id="1", title="t", model_override="m1"
        ),
        source_id="source:1",
    )
    assert created.id == "chat_session:s1"
    session.relate.assert_awaited_once()

    monkeypatch.setattr(source_chat_router.Source, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as not_found_exc:
        await source_chat_router.create_source_chat_session(
            request=source_chat_router.CreateSourceChatSessionRequest(),
            source_id="source:missing",
        )
    assert not_found_exc.value.status_code == 404

    monkeypatch.setattr(
        source_chat_router.Source, "get", AsyncMock(side_effect=NotFoundError("x"))
    )
    with pytest.raises(HTTPException) as not_found_err2:
        await source_chat_router.create_source_chat_session(
            request=source_chat_router.CreateSourceChatSessionRequest(),
            source_id="source:oops",
        )
    assert not_found_err2.value.status_code == 404


@pytest.mark.asyncio
async def test_get_source_chat_sessions_not_found_and_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(source_chat_router.Source, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as exc_info:
        await source_chat_router.get_source_chat_sessions("src-1")
    assert exc_info.value.status_code == 500

    monkeypatch.setattr(
        source_chat_router.Source, "get", AsyncMock(side_effect=NotFoundError("x"))
    )
    with pytest.raises(HTTPException) as exc_info2:
        await source_chat_router.get_source_chat_sessions("src-1")
    assert exc_info2.value.status_code == 404

    monkeypatch.setattr(
        source_chat_router.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:src-1")),
    )
    monkeypatch.setattr(
        source_chat_router,
        "repo_query",
        AsyncMock(side_effect=RuntimeError("db crash")),
    )
    with pytest.raises(HTTPException) as exc_info3:
        await source_chat_router.get_source_chat_sessions("src-1")
    assert exc_info3.value.status_code == 500


@pytest.mark.asyncio
async def test_get_source_chat_session_success_and_guard_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        source_chat_router.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1")),
    )
    session_obj = SimpleNamespace(
        id="chat_session:s1",
        title="session",
        created="2026-01-01T00:00:00Z",
        updated="2026-01-01T00:00:00Z",
        model_override="mo",
    )
    monkeypatch.setattr(
        source_chat_router.ChatSession, "get", AsyncMock(return_value=session_obj)
    )
    monkeypatch.setattr(
        source_chat_router, "repo_query", AsyncMock(return_value=[{"ok": True}])
    )

    state = SimpleNamespace(
        values={
            "messages": [SimpleNamespace(id="m1", type="ai", content="ai says")],
            "context_indicators": {
                "sources": ["source:1"],
                "insights": ["i1"],
                "notes": [],
            },
        }
    )
    monkeypatch.setattr(
        source_chat_router.asyncio, "to_thread", AsyncMock(return_value=state)
    )

    result = await source_chat_router.get_source_chat_session("1", "s1")
    assert result.id == "chat_session:s1"
    assert result.message_count == 1
    assert result.context_indicators.sources == ["source:1"]
    assert result.context_indicators.insights == ["i1"]
    assert result.context_indicators.notes == []

    monkeypatch.setattr(source_chat_router.Source, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as source_404:
        await source_chat_router.get_source_chat_session("1", "s1")
    assert source_404.value.status_code == 500

    monkeypatch.setattr(
        source_chat_router.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1")),
    )
    monkeypatch.setattr(
        source_chat_router.ChatSession, "get", AsyncMock(return_value=None)
    )
    with pytest.raises(HTTPException) as session_404:
        await source_chat_router.get_source_chat_session("1", "s1")
    assert session_404.value.status_code == 500

    monkeypatch.setattr(
        source_chat_router.ChatSession, "get", AsyncMock(return_value=session_obj)
    )
    monkeypatch.setattr(source_chat_router, "repo_query", AsyncMock(return_value=[]))
    with pytest.raises(HTTPException) as relation_404:
        await source_chat_router.get_source_chat_session("1", "s1")
    assert relation_404.value.status_code == 500


@pytest.mark.asyncio
async def test_update_and_delete_source_chat_session_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SimpleNamespace(id="source:1")
    session = SimpleNamespace(
        id="chat_session:s1",
        title="old",
        model_override=None,
        created="2026-01-01T00:00:00Z",
        updated="2026-01-01T00:00:00Z",
        save=AsyncMock(),
        delete=AsyncMock(),
    )
    monkeypatch.setattr(
        source_chat_router.Source, "get", AsyncMock(return_value=source)
    )
    monkeypatch.setattr(
        source_chat_router.ChatSession, "get", AsyncMock(return_value=session)
    )
    monkeypatch.setattr(
        source_chat_router, "repo_query", AsyncMock(return_value=[{"ok": True}])
    )
    monkeypatch.setattr(
        source_chat_router, "get_session_message_count", AsyncMock(return_value=2)
    )

    updated = await source_chat_router.update_source_chat_session(
        source_chat_router.UpdateSourceChatSessionRequest(
            title="new", model_override="m2"
        ),
        source_id="1",
        session_id="s1",
    )
    assert updated.title == "new"
    assert updated.model_override == "m2"
    session.save.assert_awaited()

    deleted = await source_chat_router.delete_source_chat_session("1", "s1")
    assert deleted.success is True
    session.delete.assert_awaited()

    monkeypatch.setattr(source_chat_router.Source, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as update_source_404:
        await source_chat_router.update_source_chat_session(
            source_chat_router.UpdateSourceChatSessionRequest(), "1", "s1"
        )
    assert update_source_404.value.status_code == 500

    with pytest.raises(HTTPException) as delete_source_404:
        await source_chat_router.delete_source_chat_session("1", "s1")
    assert delete_source_404.value.status_code == 500


@pytest.mark.asyncio
async def test_stream_source_chat_response_non_mapping_and_error_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BadState:
        values = "not-a-mapping"

    async def fake_to_thread(func, *args, **kwargs):
        if getattr(func, "__name__", "") == "get_state":
            return BadState()
        return {"messages": [SimpleNamespace(type="ai", content="ok")]}

    class AsyncLock:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc, tb):
            _ = (exc_type, exc, tb)
            return False

    lock = AsyncLock()
    monkeypatch.setattr(
        source_chat_router, "get_session_lock", AsyncMock(return_value=lock)
    )
    monkeypatch.setattr(
        source_chat_router,
        "source_chat_graph",
        SimpleNamespace(get_state=lambda **_kwargs: None, invoke=lambda **_kwargs: {}),
    )
    monkeypatch.setattr(source_chat_router.asyncio, "to_thread", fake_to_thread)

    chunks = []
    async for chunk in source_chat_router.stream_source_chat_response(
        session_id="chat_session:s1", source_id="source:1", message="hello"
    ):
        chunks.append(chunk)

    payloads = [
        json.loads(chunk.removeprefix("data: ").strip())
        for chunk in chunks
        if chunk.startswith("data: ")
    ]
    assert payloads[0]["type"] == "user_message"
    assert payloads[-1]["type"] == "complete"

    monkeypatch.setattr(
        source_chat_router,
        "get_session_lock",
        AsyncMock(side_effect=RuntimeError("lock fail")),
    )

    error_chunks = []
    async for chunk in source_chat_router.stream_source_chat_response(
        session_id="chat_session:s1", source_id="source:1", message="hello"
    ):
        error_chunks.append(chunk)
    assert any('"type": "error"' in c for c in error_chunks)


@pytest.mark.asyncio
async def test_send_message_to_source_chat_source_session_relation_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(source_chat_router.Source, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as source_missing:
        await source_chat_router.send_message_to_source_chat(
            source_chat_router.SendMessageRequest(message="hi"), "1", "s1"
        )
    assert source_missing.value.status_code == 404

    monkeypatch.setattr(
        source_chat_router.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1")),
    )
    monkeypatch.setattr(
        source_chat_router.ChatSession, "get", AsyncMock(return_value=None)
    )
    with pytest.raises(HTTPException) as session_missing:
        await source_chat_router.send_message_to_source_chat(
            source_chat_router.SendMessageRequest(message="hi"), "1", "s1"
        )
    assert session_missing.value.status_code == 404

    monkeypatch.setattr(
        source_chat_router.ChatSession,
        "get",
        AsyncMock(return_value=SimpleNamespace(model_override=None, save=AsyncMock())),
    )
    monkeypatch.setattr(source_chat_router, "repo_query", AsyncMock(return_value=[]))
    with pytest.raises(HTTPException) as relation_missing:
        await source_chat_router.send_message_to_source_chat(
            source_chat_router.SendMessageRequest(message="hi"), "1", "s1"
        )
    assert relation_missing.value.status_code == 404


@pytest.mark.asyncio
async def test_get_update_delete_handle_notfounderror_and_internal_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        source_chat_router.Source, "get", AsyncMock(side_effect=NotFoundError("x"))
    )
    with pytest.raises(HTTPException) as get_nf:
        await source_chat_router.get_source_chat_session("1", "s1")
    assert get_nf.value.status_code == 404

    with pytest.raises(HTTPException) as upd_nf:
        await source_chat_router.update_source_chat_session(
            source_chat_router.UpdateSourceChatSessionRequest(), "1", "s1"
        )
    assert upd_nf.value.status_code == 404

    with pytest.raises(HTTPException) as del_nf:
        await source_chat_router.delete_source_chat_session("1", "s1")
    assert del_nf.value.status_code == 404

    monkeypatch.setattr(
        source_chat_router.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1")),
    )
    monkeypatch.setattr(
        source_chat_router.ChatSession, "get", AsyncMock(side_effect=RuntimeError("db"))
    )
    with pytest.raises(HTTPException) as get_500:
        await source_chat_router.get_source_chat_session("1", "s1")
    assert get_500.value.status_code == 500
