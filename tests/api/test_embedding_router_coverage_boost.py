import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from packages.core.application.models import EmbedRequest
from services.api.routers import embedding as embedding_router


def _stub_embedding_commands_import(monkeypatch: pytest.MonkeyPatch) -> None:
    commands_pkg = types.ModuleType("commands")
    commands_pkg.__path__ = []  # mark as package
    embedding_commands_module = types.ModuleType(
        "packages.core.application.commands.embedding_commands"
    )
    monkeypatch.setitem(sys.modules, "commands", commands_pkg)
    monkeypatch.setitem(
        sys.modules,
        "packages.core.application.commands.embedding_commands",
        embedding_commands_module,
    )


@pytest.mark.asyncio
async def test_embed_content_returns_400_without_embedding_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        embedding_router.model_manager,
        "get_embedding_model",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        await embedding_router.embed_content(
            EmbedRequest(item_id="source:1", item_type="source", async_processing=False)
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_embed_content_validates_item_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        embedding_router.model_manager,
        "get_embedding_model",
        AsyncMock(return_value=object()),
    )

    with pytest.raises(HTTPException) as exc_info:
        await embedding_router.embed_content(
            EmbedRequest(
                item_id="source:1", item_type="invalid", async_processing=False
            )
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_embed_content_source_missing_returns_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        embedding_router.model_manager,
        "get_embedding_model",
        AsyncMock(return_value=object()),
    )
    monkeypatch.setattr(embedding_router.Source, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await embedding_router.embed_content(
            EmbedRequest(
                item_id="source:missing", item_type="source", async_processing=False
            )
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Source not found"


@pytest.mark.asyncio
async def test_embed_content_note_missing_returns_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        embedding_router.model_manager,
        "get_embedding_model",
        AsyncMock(return_value=object()),
    )
    monkeypatch.setattr(embedding_router.Note, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await embedding_router.embed_content(
            EmbedRequest(
                item_id="note:missing", item_type="note", async_processing=False
            )
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Note not found"


@pytest.mark.asyncio
async def test_embed_content_async_source_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_embedding_commands_import(monkeypatch)
    monkeypatch.setattr(
        embedding_router.model_manager,
        "get_embedding_model",
        AsyncMock(return_value=object()),
    )
    submit_mock = AsyncMock(return_value="command:embed:source:1")
    monkeypatch.setattr(
        embedding_router.CommandService, "submit_command_job", submit_mock
    )

    response = await embedding_router.embed_content(
        EmbedRequest(item_id="source:1", item_type="SOURCE", async_processing=True)
    )

    assert response.success is True
    assert response.command_id == "command:embed:source:1"
    assert response.item_type == "source"
    args = submit_mock.await_args.args
    assert args[1] == "embed_source"
    assert args[2] == {"source_id": "source:1"}


@pytest.mark.asyncio
async def test_embed_content_async_note_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_embedding_commands_import(monkeypatch)
    monkeypatch.setattr(
        embedding_router.model_manager,
        "get_embedding_model",
        AsyncMock(return_value=object()),
    )
    submit_mock = AsyncMock(return_value="command:embed:note:1")
    monkeypatch.setattr(
        embedding_router.CommandService, "submit_command_job", submit_mock
    )

    response = await embedding_router.embed_content(
        EmbedRequest(item_id="note:1", item_type="note", async_processing=True)
    )

    assert response.success is True
    assert response.command_id == "command:embed:note:1"
    args = submit_mock.await_args.args
    assert args[1] == "embed_note"
    assert args[2] == {"note_id": "note:1"}


@pytest.mark.asyncio
async def test_embed_content_sync_source_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        embedding_router.model_manager,
        "get_embedding_model",
        AsyncMock(return_value=object()),
    )
    source_item = SimpleNamespace(
        vectorize=AsyncMock(return_value="command:source:sync")
    )
    monkeypatch.setattr(
        embedding_router.Source, "get", AsyncMock(return_value=source_item)
    )

    response = await embedding_router.embed_content(
        EmbedRequest(item_id="source:1", item_type="source", async_processing=False)
    )

    assert response.success is True
    assert response.message == "Source embedding job submitted"
    assert response.command_id == "command:source:sync"
    source_item.vectorize.assert_awaited_once()


@pytest.mark.asyncio
async def test_embed_content_sync_note_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        embedding_router.model_manager,
        "get_embedding_model",
        AsyncMock(return_value=object()),
    )
    note_item = SimpleNamespace(save=AsyncMock(return_value="command:note:sync"))
    monkeypatch.setattr(embedding_router.Note, "get", AsyncMock(return_value=note_item))

    response = await embedding_router.embed_content(
        EmbedRequest(item_id="note:1", item_type="note", async_processing=False)
    )

    assert response.success is True
    assert response.message == "Note embedding job submitted"
    assert response.command_id == "command:note:sync"
    note_item.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_embed_content_wraps_unexpected_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        embedding_router.model_manager,
        "get_embedding_model",
        AsyncMock(return_value=object()),
    )
    monkeypatch.setattr(
        embedding_router.Source,
        "get",
        AsyncMock(side_effect=RuntimeError("db offline")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await embedding_router.embed_content(
            EmbedRequest(item_id="source:1", item_type="source")
        )

    assert exc_info.value.status_code == 500
    assert "Error embedding content: db offline" == exc_info.value.detail
