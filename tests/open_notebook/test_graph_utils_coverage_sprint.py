from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from packages.core.utils import graph_utils


@pytest.mark.asyncio
async def test_get_session_message_count_returns_length() -> None:
    class _Graph:
        def get_state(self, *, config):
            assert config.get("configurable", {}).get("thread_id") == "session-1"
            return SimpleNamespace(values={"messages": ["a", "b", "c"]})

    count = await graph_utils.get_session_message_count(_Graph(), "session-1")
    assert count == 3


@pytest.mark.asyncio
async def test_get_session_message_count_returns_zero_without_messages() -> None:
    class _Graph:
        def get_state(self, *, config):
            _ = config
            return SimpleNamespace(values={})

    count = await graph_utils.get_session_message_count(_Graph(), "session-2")
    assert count == 0


@pytest.mark.asyncio
async def test_get_session_message_count_logs_warning_on_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Graph:
        def get_state(self, *, config):
            _ = config
            raise RuntimeError("state unavailable")

    warning_mock = MagicMock()
    monkeypatch.setattr(graph_utils.logger, "warning", warning_mock)

    count = await graph_utils.get_session_message_count(_Graph(), "session-3")

    assert count == 0
    warning_mock.assert_called_once()
    assert "session-3" in warning_mock.call_args.args[0]
