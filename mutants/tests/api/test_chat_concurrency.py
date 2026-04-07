import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from services.api.routers import chat as chat_router
from services.api.session_locks import reset_session_locks


class _FakeChatGraph:
    def __init__(self) -> None:
        self._state: dict[str, list] = {}
        self._state_lock = threading.Lock()
        self.invoke_thread_ids: list[int] = []
        self._critical_lock = threading.Lock()
        self._critical_active = 0
        self.max_critical_active = 0

    @staticmethod
    def _extract_thread_id(config) -> str:
        if isinstance(config, dict):
            return str(config["configurable"]["thread_id"])
        return str(config.configurable["thread_id"])

    @staticmethod
    def _simulate_sync_work() -> None:
        checksum = 0
        for i in range(20_000):
            checksum ^= (i * 31) & 0xFF
        if checksum == -1:  # pragma: no cover
            raise RuntimeError("unreachable")

    def get_state(self, *, config):
        with self._critical_lock:
            self._critical_active += 1
            self.max_critical_active = max(
                self.max_critical_active, self._critical_active
            )
        self._simulate_sync_work()
        thread_id = self._extract_thread_id(config)
        with self._state_lock:
            messages = list(self._state.get(thread_id, []))
        with self._critical_lock:
            self._critical_active -= 1
        return SimpleNamespace(values={"messages": messages})

    def invoke(self, *, input, config):
        with self._critical_lock:
            self._critical_active += 1
            self.max_critical_active = max(
                self.max_critical_active, self._critical_active
            )
        self.invoke_thread_ids.append(threading.get_ident())
        # Simulate slow sync graph call to expose lost-update races.
        self._simulate_sync_work()
        thread_id = self._extract_thread_id(config)
        new_messages = list(input.get("messages", []))
        ai_reply = AIMessage(
            content=f"ack:{new_messages[-1].content}", id=f"ai-{len(new_messages)}"
        )
        new_messages.append(ai_reply)
        with self._state_lock:
            self._state[thread_id] = new_messages
            result = {"messages": [ai_reply]}
        with self._critical_lock:
            self._critical_active -= 1
        return result

    def state_messages(self, thread_id: str) -> list:
        with self._state_lock:
            return list(self._state.get(thread_id, []))


@pytest.mark.asyncio
async def test_execute_chat_serializes_same_session_and_avoids_message_loss(
    monkeypatch,
):
    fake_graph = _FakeChatGraph()
    main_thread_id = threading.get_ident()
    reset_session_locks()

    session = SimpleNamespace(model_override=None, save=AsyncMock())
    monkeypatch.setattr(chat_router, "chat_graph", fake_graph)
    monkeypatch.setattr(chat_router.ChatSession, "get", AsyncMock(return_value=session))

    async def _send(message: str):
        return await chat_router.execute_chat(
            chat_router.ExecuteChatRequest(
                session_id="s1",
                message=message,
                context={"sources": [], "notes": []},
            )
        )

    try:
        await asyncio.gather(_send("A"), _send("B"))
    finally:
        reset_session_locks()

    final_messages = fake_graph.state_messages("chat_session:s1")
    human_contents = [
        msg.content for msg in final_messages if isinstance(msg, HumanMessage)
    ]
    assert set(human_contents) == {"A", "B"}
    assert all(
        thread_id != main_thread_id for thread_id in fake_graph.invoke_thread_ids
    )


@pytest.mark.asyncio
async def test_execute_chat_serializes_checkpoint_critical_section_across_sessions(
    monkeypatch,
):
    fake_graph = _FakeChatGraph()
    reset_session_locks()

    session = SimpleNamespace(model_override=None, save=AsyncMock())
    monkeypatch.setattr(chat_router, "chat_graph", fake_graph)
    monkeypatch.setattr(chat_router.ChatSession, "get", AsyncMock(return_value=session))

    async def _send(session_id: str, message: str):
        return await chat_router.execute_chat(
            chat_router.ExecuteChatRequest(
                session_id=session_id,
                message=message,
                context={"sources": [], "notes": []},
            )
        )

    try:
        await asyncio.gather(_send("s1", "A"), _send("s2", "B"))
    finally:
        reset_session_locks()

    assert len(fake_graph.invoke_thread_ids) == 2
