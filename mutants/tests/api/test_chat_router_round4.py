from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from langchain_core.messages import AIMessage

from services.api.routers import chat as chat_router
from services.api.session_locks import SessionLockCapacityError


@pytest.mark.asyncio
async def test_execute_chat_uses_session_override_when_request_override_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = SimpleNamespace(model_override="session-model", save=AsyncMock())
    monkeypatch.setattr(chat_router.ChatSession, "get", AsyncMock(return_value=session))

    captured: dict[str, object] = {}

    def _thread_id(config):
        if isinstance(config, dict):
            return config["configurable"]["thread_id"]
        return config.configurable["thread_id"]

    def _model_id(config):
        if isinstance(config, dict):
            return config["configurable"]["model_id"]
        return config.configurable["model_id"]

    def _fake_get_state(*, config):
        captured["thread_id_get_state"] = _thread_id(config)
        return SimpleNamespace(values={"messages": []})

    def _fake_invoke(*, input, config):
        captured["thread_id_invoke"] = _thread_id(config)
        captured["model_id"] = _model_id(config)
        captured["user_message"] = input["messages"][-1].content
        return {"messages": [AIMessage(content="ok", id="ai-1")]}

    monkeypatch.setattr(
        chat_router,
        "chat_graph",
        SimpleNamespace(get_state=_fake_get_state, invoke=_fake_invoke),
    )

    request = chat_router.ExecuteChatRequest(
        session_id="s1",
        message="hello",
        context={"sources": [], "notes": []},
    )
    response = await chat_router.execute_chat(request)

    assert response.session_id == "s1"
    assert captured["thread_id_get_state"] == "chat_session:s1"
    assert captured["thread_id_invoke"] == "chat_session:s1"
    assert captured["model_id"] == "session-model"
    assert captured["user_message"] == "hello"
    session.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_chat_request_override_takes_precedence_over_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = SimpleNamespace(model_override="session-model", save=AsyncMock())
    monkeypatch.setattr(chat_router.ChatSession, "get", AsyncMock(return_value=session))

    captured_model_ids: list[str] = []

    def _fake_get_state(*, config):
        _ = config
        return SimpleNamespace(values={"messages": []})

    def _fake_invoke(*, input, config):
        _ = input
        if isinstance(config, dict):
            captured_model_ids.append(config["configurable"]["model_id"])
        else:
            captured_model_ids.append(config.configurable["model_id"])
        return {"messages": [AIMessage(content="ok", id="ai-2")]}

    monkeypatch.setattr(
        chat_router,
        "chat_graph",
        SimpleNamespace(get_state=_fake_get_state, invoke=_fake_invoke),
    )

    await chat_router.execute_chat(
        chat_router.ExecuteChatRequest(
            session_id="s2",
            message="hello",
            context={"sources": [], "notes": []},
            model_override="request-model",
        )
    )

    assert captured_model_ids == ["request-model"]


@pytest.mark.asyncio
async def test_execute_chat_maps_session_lock_capacity_to_429(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = SimpleNamespace(model_override=None, save=AsyncMock())
    monkeypatch.setattr(chat_router.ChatSession, "get", AsyncMock(return_value=session))
    monkeypatch.setattr(
        chat_router,
        "get_session_lock",
        AsyncMock(side_effect=SessionLockCapacityError("capacity full")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await chat_router.execute_chat(
            chat_router.ExecuteChatRequest(
                session_id="s-cap",
                message="hello",
                context={"sources": [], "notes": []},
            )
        )

    assert exc_info.value.status_code == 429
    assert "capacity" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_build_context_respects_filters_and_context_sizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notebook = SimpleNamespace()
    monkeypatch.setattr(chat_router.Notebook, "get", AsyncMock(return_value=notebook))

    source_insight = SimpleNamespace(
        get_context=AsyncMock(return_value={"id": "source:s2", "mode": "short"})
    )
    source_full = SimpleNamespace(
        get_context=AsyncMock(return_value={"id": "source:s3", "mode": "long"})
    )
    source_get_mock = AsyncMock(side_effect=[source_insight, source_full])
    monkeypatch.setattr(chat_router.Source, "get", source_get_mock)

    note = SimpleNamespace(get_context=lambda *, context_size: f"note-{context_size}")
    note_get_mock = AsyncMock(return_value=note)
    monkeypatch.setattr(chat_router.Note, "get", note_get_mock)

    request = chat_router.BuildContextRequest(
        notebook_id="nb-1",
        context_config={
            "sources": {
                "s1": "not in context",
                "s2": "insights only",
                "s3": "full content",
            },
            "notes": {
                "n1": "full content",
                "n2": "not in context",
            },
        },
    )
    response = await chat_router.build_context(request)

    called_source_ids = [call.args[0] for call in source_get_mock.await_args_list]
    assert called_source_ids == ["source:s2", "source:s3"]
    assert source_insight.get_context.await_args.kwargs["context_size"] == "short"
    assert source_full.get_context.await_args.kwargs["context_size"] == "long"
    note_get_mock.assert_awaited_once_with("note:n1")
    assert len(response.context["sources"]) == 2
    assert response.context["notes"] == ["note-long"]
    assert response.char_count > 0
