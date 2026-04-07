import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from langchain_core.messages import AIMessage

from services.api.routers import source_chat as source_chat_router
from services.api.session_locks import SessionLockCapacityError


@pytest.mark.asyncio
async def test_send_message_to_source_chat_rejects_empty_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SimpleNamespace(id="source:src-1")
    session = SimpleNamespace(model_override="session-model", save=AsyncMock())
    monkeypatch.setattr(
        source_chat_router.Source, "get", AsyncMock(return_value=source)
    )
    monkeypatch.setattr(
        source_chat_router.ChatSession, "get", AsyncMock(return_value=session)
    )
    monkeypatch.setattr(
        source_chat_router,
        "repo_query",
        AsyncMock(return_value=[{"in": "chat_session:s1", "out": "source:src-1"}]),
    )

    with pytest.raises(HTTPException) as exc_info:
        await source_chat_router.send_message_to_source_chat(
            request=source_chat_router.SendMessageRequest(message=""),
            source_id="src-1",
            session_id="s1",
        )

    assert exc_info.value.status_code == 400
    assert "Message content is required" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_send_message_to_source_chat_passes_prefixed_ids_and_request_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SimpleNamespace(id="source:src-2")
    session = SimpleNamespace(model_override="session-model", save=AsyncMock())
    monkeypatch.setattr(
        source_chat_router.Source, "get", AsyncMock(return_value=source)
    )
    monkeypatch.setattr(
        source_chat_router.ChatSession, "get", AsyncMock(return_value=session)
    )
    monkeypatch.setattr(
        source_chat_router,
        "repo_query",
        AsyncMock(return_value=[{"in": "chat_session:s2", "out": "source:src-2"}]),
    )

    captured: dict[str, object] = {}

    async def _fake_stream(
        *, session_id, source_id, message, model_override, session_lock=None
    ):
        captured["session_id"] = session_id
        captured["source_id"] = source_id
        captured["message"] = message
        captured["model_override"] = model_override
        captured["session_lock"] = session_lock
        yield "data: {}\n\n"

    monkeypatch.setattr(source_chat_router, "stream_source_chat_response", _fake_stream)

    response = await source_chat_router.send_message_to_source_chat(
        request=source_chat_router.SendMessageRequest(
            message="hello",
            model_override="request-model",
        ),
        source_id="src-2",
        session_id="s2",
    )

    body_chunks = []
    async for chunk in response.body_iterator:
        body_chunks.append(chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk)

    assert "data:" in "".join(body_chunks)
    assert response.media_type == "text/event-stream"
    assert captured["session_id"] == "chat_session:s2"
    assert captured["source_id"] == "source:src-2"
    assert captured["message"] == "hello"
    assert captured["model_override"] == "request-model"
    lock = captured["session_lock"]
    assert lock is not None and (
        hasattr(lock, "acquire") or hasattr(lock, "__aenter__")
    )
    session.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_stream_source_chat_response_emits_user_ai_context_and_complete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_get_state(*, config):
        _ = config
        return SimpleNamespace(values={"messages": []})

    def _fake_invoke(*, input, config):
        _ = (input, config)
        return {
            "messages": [AIMessage(content="ai reply")],
            "context_indicators": {
                "sources": ["source:src-3"],
                "insights": [],
                "notes": [],
            },
        }

    monkeypatch.setattr(
        source_chat_router,
        "source_chat_graph",
        SimpleNamespace(get_state=_fake_get_state, invoke=_fake_invoke),
    )

    chunks: list[str] = []
    async for chunk in source_chat_router.stream_source_chat_response(
        session_id="chat_session:s3",
        source_id="source:src-3",
        message="hello",
        model_override=None,
    ):
        chunks.append(chunk)

    events = [
        json.loads(chunk.removeprefix("data: ").strip())
        for chunk in chunks
        if chunk.startswith("data: ")
    ]
    assert [event["type"] for event in events] == [
        "user_message",
        "ai_message",
        "context_indicators",
        "complete",
    ]
    assert events[1]["content"] == "ai reply"


@pytest.mark.asyncio
async def test_get_source_chat_sessions_uses_parameterized_session_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SimpleNamespace(id="source:src-4")
    query_calls: list[tuple[str, dict | None]] = []

    async def _fake_repo_query(query: str, params: dict | None = None):
        query_calls.append((query, params))
        if query == "SELECT in FROM refers_to WHERE out = $source_id":
            return [{"in": "chat_session:s4"}]
        if query == "SELECT * FROM $session_id":
            return [
                {
                    "id": "chat_session:s4",
                    "title": "s4",
                    "created": "2026-01-01T00:00:00Z",
                    "updated": "2026-01-01T00:00:00Z",
                }
            ]
        raise AssertionError(f"Unexpected query: {query}")

    monkeypatch.setattr(
        source_chat_router.Source, "get", AsyncMock(return_value=source)
    )
    monkeypatch.setattr(source_chat_router, "repo_query", _fake_repo_query)
    monkeypatch.setattr(
        source_chat_router,
        "get_session_message_count",
        AsyncMock(return_value=0),
    )

    result = await source_chat_router.get_source_chat_sessions("src-4")

    assert len(result) == 1
    session_lookup = [
        call for call in query_calls if call[0] == "SELECT * FROM $session_id"
    ]
    assert session_lookup[0][1] == {
        "session_id": source_chat_router.ensure_record_id("chat_session:s4")
    }


@pytest.mark.asyncio
async def test_send_message_to_source_chat_hides_internal_error_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SimpleNamespace(id="source:src-5")
    session = SimpleNamespace(
        model_override=None, save=AsyncMock(side_effect=RuntimeError("db leak"))
    )
    monkeypatch.setattr(
        source_chat_router.Source, "get", AsyncMock(return_value=source)
    )
    monkeypatch.setattr(
        source_chat_router.ChatSession, "get", AsyncMock(return_value=session)
    )
    monkeypatch.setattr(
        source_chat_router,
        "repo_query",
        AsyncMock(return_value=[{"in": "chat_session:s5", "out": "source:src-5"}]),
    )

    with pytest.raises(HTTPException) as exc_info:
        await source_chat_router.send_message_to_source_chat(
            request=source_chat_router.SendMessageRequest(message="hello"),
            source_id="src-5",
            session_id="s5",
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to send message"


@pytest.mark.asyncio
async def test_send_message_to_source_chat_maps_session_lock_capacity_to_429(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SimpleNamespace(id="source:src-cap")
    session = SimpleNamespace(model_override=None, save=AsyncMock())
    monkeypatch.setattr(
        source_chat_router.Source, "get", AsyncMock(return_value=source)
    )
    monkeypatch.setattr(
        source_chat_router.ChatSession, "get", AsyncMock(return_value=session)
    )
    monkeypatch.setattr(
        source_chat_router,
        "repo_query",
        AsyncMock(return_value=[{"in": "chat_session:s-cap", "out": "source:src-cap"}]),
    )
    monkeypatch.setattr(
        source_chat_router,
        "get_session_lock",
        AsyncMock(side_effect=SessionLockCapacityError("capacity full")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await source_chat_router.send_message_to_source_chat(
            request=source_chat_router.SendMessageRequest(message="hello"),
            source_id="src-cap",
            session_id="s-cap",
        )

    assert exc_info.value.status_code == 429
    assert "capacity" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_create_source_chat_session_rejects_body_path_source_id_mismatch() -> (
    None
):
    with pytest.raises(HTTPException) as exc_info:
        await source_chat_router.create_source_chat_session(
            request=source_chat_router.CreateSourceChatSessionRequest(
                source_id="source:body-id",
                title="t",
            ),
            source_id="path-id",
        )

    assert exc_info.value.status_code == 400
    assert "must match path source_id" in str(exc_info.value.detail)
