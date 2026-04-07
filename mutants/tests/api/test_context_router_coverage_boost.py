from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from packages.core.application.models import ContextConfig, ContextRequest
from packages.core.exceptions import InvalidInputError
from services.api.routers import context as context_router


@pytest.mark.asyncio
async def test_get_notebook_context_returns_404_when_notebook_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(context_router.Notebook, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await context_router.get_notebook_context(
            "nb-missing",
            ContextRequest(notebook_id="nb-missing", context_config=None),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Notebook not found"


@pytest.mark.asyncio
async def test_get_notebook_context_with_context_config_covers_status_and_error_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notebook = SimpleNamespace(id="notebook:1")
    monkeypatch.setattr(
        context_router.Notebook, "get", AsyncMock(return_value=notebook)
    )

    source_short = SimpleNamespace(
        get_context=AsyncMock(return_value={"id": "source:s2", "mode": "short"})
    )
    source_long = SimpleNamespace(
        get_context=AsyncMock(return_value={"id": "source:s3", "mode": "long"})
    )
    source_raise = SimpleNamespace(
        get_context=AsyncMock(side_effect=RuntimeError("boom"))
    )

    async def _fake_source_get(source_id: str):
        mapping = {
            "source:s2": source_short,
            "source:s3": source_long,
            "source:s5": source_raise,
        }
        if source_id == "source:s4":
            raise RuntimeError("source lookup failed")
        return mapping[source_id]

    source_get_mock = AsyncMock(side_effect=_fake_source_get)
    monkeypatch.setattr(context_router.Source, "get", source_get_mock)

    note_good = SimpleNamespace(
        get_context=lambda *, context_size: {"id": "note:n1", "mode": context_size}
    )
    note_raise = SimpleNamespace(
        get_context=lambda *, context_size: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    async def _fake_note_get(note_id: str):
        mapping = {
            "note:n1": note_good,
            "note:n2": None,
            "note:n3": note_raise,
            "note:n4": note_good,
        }
        return mapping[note_id]

    note_get_mock = AsyncMock(side_effect=_fake_note_get)
    monkeypatch.setattr(context_router.Note, "get", note_get_mock)

    captured = {"input": None}

    def _fake_token_count(content: str) -> int:
        captured["input"] = content
        return 123

    monkeypatch.setattr(context_router, "token_count", _fake_token_count)

    request = ContextRequest(
        notebook_id="notebook:1",
        context_config=ContextConfig(
            sources={
                "s1": "not in context",
                "s2": "insights only",
                "source:s3": "full content",
                "s4": "insights only",
                "s5": "insights only",
                "s6": "unknown",
            },
            notes={
                "n0": "not in context",
                "n1": "full content",
                "n2": "full content",
                "n3": "full content",
                "n4": "insights only",
            },
        ),
    )

    response = await context_router.get_notebook_context("notebook:1", request)

    assert [call.args[0] for call in source_get_mock.await_args_list] == [
        "source:s2",
        "source:s3",
        "source:s4",
        "source:s5",
        "source:s6",
    ]
    assert source_short.get_context.await_args.kwargs["context_size"] == "short"
    assert source_long.get_context.await_args.kwargs["context_size"] == "long"
    assert source_raise.get_context.await_args.kwargs["context_size"] == "short"
    assert [call.args[0] for call in note_get_mock.await_args_list] == [
        "note:n1",
        "note:n2",
        "note:n3",
        "note:n4",
    ]

    assert response.sources == [
        {"id": "source:s2", "mode": "short"},
        {"id": "source:s3", "mode": "long"},
    ]
    assert response.notes == [{"id": "note:n1", "mode": "long"}]
    assert response.total_tokens == 123
    assert "source:s2" in captured["input"]
    assert "note:n1" in captured["input"]


@pytest.mark.asyncio
async def test_get_notebook_context_with_context_config_empty_payload_has_zero_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notebook = SimpleNamespace(id="notebook:2")
    monkeypatch.setattr(
        context_router.Notebook, "get", AsyncMock(return_value=notebook)
    )

    token_count_mock = MagicMock(return_value=999)
    monkeypatch.setattr(context_router, "token_count", token_count_mock)

    request = ContextRequest(
        notebook_id="notebook:2",
        context_config=ContextConfig(sources={}, notes={}),
    )

    response = await context_router.get_notebook_context("notebook:2", request)

    assert response.sources == []
    assert response.notes == []
    assert response.total_tokens == 0
    token_count_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_notebook_context_default_branch_uses_short_context_and_skips_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    good_source = SimpleNamespace(
        get_context=AsyncMock(return_value={"id": "source:ok", "mode": "short"})
    )
    bad_source = SimpleNamespace(
        id="source:bad",
        get_context=AsyncMock(side_effect=RuntimeError("source context error")),
    )

    good_note = SimpleNamespace(
        get_context=lambda *, context_size: {"id": "note:ok", "mode": context_size}
    )
    bad_note = SimpleNamespace(
        id="note:bad",
        get_context=lambda *, context_size: (_ for _ in ()).throw(
            RuntimeError("note context error")
        ),
    )

    notebook = SimpleNamespace(
        get_sources=AsyncMock(return_value=[good_source, bad_source]),
        get_notes=AsyncMock(return_value=[good_note, bad_note]),
    )
    monkeypatch.setattr(
        context_router.Notebook, "get", AsyncMock(return_value=notebook)
    )

    token_count_mock = MagicMock(return_value=77)
    monkeypatch.setattr(context_router, "token_count", token_count_mock)

    response = await context_router.get_notebook_context(
        "nb-default",
        ContextRequest(notebook_id="nb-default", context_config=None),
    )

    assert response.sources == [{"id": "source:ok", "mode": "short"}]
    assert response.notes == [{"id": "note:ok", "mode": "short"}]
    assert response.total_tokens == 77
    assert good_source.get_context.await_args.kwargs["context_size"] == "short"
    token_count_mock.assert_called_once()


@pytest.mark.asyncio
async def test_get_notebook_context_wraps_invalid_input_error_as_400(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        context_router.Notebook,
        "get",
        AsyncMock(side_effect=InvalidInputError("invalid notebook id")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await context_router.get_notebook_context(
            "nb-invalid",
            ContextRequest(notebook_id="nb-invalid", context_config=None),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "invalid notebook id"


@pytest.mark.asyncio
async def test_get_notebook_context_wraps_unexpected_error_as_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        context_router.Notebook,
        "get",
        AsyncMock(side_effect=RuntimeError("db down")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await context_router.get_notebook_context(
            "nb-error",
            ContextRequest(notebook_id="nb-error", context_config=None),
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Error getting context: db down"
