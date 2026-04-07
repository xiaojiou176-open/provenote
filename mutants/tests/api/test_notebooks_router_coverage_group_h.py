from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from packages.core.application.models import NotebookCreate, NotebookUpdate
from packages.core.exceptions import InvalidInputError
from services.api.routers import notebooks as notebooks_router


@pytest.mark.asyncio
async def test_notebooks_additional_router_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _NotebookCtor:
        def __init__(self, name: str, description: str) -> None:
            self.id = "notebook:1"
            self.name = name
            self.description = description
            self.archived = False
            self.created = "2026-01-01"
            self.updated = "2026-01-02"
            self.save = AsyncMock()

    monkeypatch.setattr(notebooks_router, "Notebook", _NotebookCtor)
    created = await notebooks_router.create_notebook(
        NotebookCreate(name="n1", description="d1")
    )
    assert created.id == "notebook:1"

    class _BadNotebookCtor:
        def __init__(self, *_args, **_kwargs) -> None:
            raise InvalidInputError("bad notebook")

    monkeypatch.setattr(notebooks_router, "Notebook", _BadNotebookCtor)
    with pytest.raises(HTTPException) as create_bad:
        await notebooks_router.create_notebook(
            NotebookCreate(name="n2", description="d2")
        )
    assert create_bad.value.status_code == 400

    monkeypatch.setattr(
        notebooks_router,
        "Notebook",
        SimpleNamespace(get=AsyncMock()),
    )
    monkeypatch.setattr(
        notebooks_router.Notebook,
        "get",
        AsyncMock(
            return_value=SimpleNamespace(
                id="notebook:1",
                name="N",
                get_delete_preview=AsyncMock(
                    return_value={
                        "note_count": 2,
                        "exclusive_source_count": 1,
                        "shared_source_count": 3,
                    }
                ),
            )
        ),
    )
    preview = await notebooks_router.get_notebook_delete_preview("notebook:1")
    assert preview.note_count == 2

    monkeypatch.setattr(
        notebooks_router.Notebook,
        "get",
        AsyncMock(side_effect=RuntimeError("preview down")),
    )
    with pytest.raises(HTTPException) as preview_exc:
        await notebooks_router.get_notebook_delete_preview("notebook:1")
    assert preview_exc.value.status_code == 500

    monkeypatch.setattr(
        notebooks_router,
        "repo_query",
        AsyncMock(
            return_value=[
                {
                    "id": "notebook:1",
                    "name": "N",
                    "description": "D",
                    "archived": False,
                    "created": "2026-01-01",
                    "updated": "2026-01-02",
                    "source_count": 8,
                    "note_count": 9,
                }
            ]
        ),
    )
    got = await notebooks_router.get_notebook("notebook:1")
    assert got.source_count == 8

    notebook = SimpleNamespace(
        id="notebook:1",
        name="old",
        description="old",
        archived=False,
        created="2026-01-01",
        updated="2026-01-02",
        save=AsyncMock(),
    )
    monkeypatch.setattr(
        notebooks_router.Notebook, "get", AsyncMock(return_value=notebook)
    )
    monkeypatch.setattr(
        notebooks_router,
        "repo_query",
        AsyncMock(
            return_value=[
                {
                    "id": "notebook:1",
                    "name": "new",
                    "description": "new",
                    "archived": True,
                    "created": "2026-01-01",
                    "updated": "2026-01-03",
                    "source_count": 5,
                    "note_count": 6,
                }
            ]
        ),
    )
    updated = await notebooks_router.update_notebook(
        "notebook:1",
        NotebookUpdate(name="new", description="new", archived=True),
    )
    assert updated.note_count == 6

    monkeypatch.setattr(notebooks_router.Notebook, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as link_404:
        await notebooks_router.add_source_to_notebook("notebook:404", "source:1")
    assert link_404.value.status_code == 404

    monkeypatch.setattr(
        notebooks_router.Notebook,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="notebook:1")),
    )
    monkeypatch.setattr(notebooks_router.Source, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as source_404:
        await notebooks_router.add_source_to_notebook("notebook:1", "source:404")
    assert source_404.value.status_code == 404

    monkeypatch.setattr(notebooks_router.Notebook, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as remove_404:
        await notebooks_router.remove_source_from_notebook("notebook:404", "source:1")
    assert remove_404.value.status_code == 404

    monkeypatch.setattr(
        notebooks_router.Notebook,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="notebook:1")),
    )
    monkeypatch.setattr(
        notebooks_router,
        "repo_query",
        AsyncMock(side_effect=RuntimeError("rm failed")),
    )
    with pytest.raises(HTTPException) as remove_500:
        await notebooks_router.remove_source_from_notebook("notebook:1", "source:1")
    assert remove_500.value.status_code == 500

    monkeypatch.setattr(notebooks_router.Notebook, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as delete_404:
        await notebooks_router.delete_notebook("notebook:404", False)
    assert delete_404.value.status_code == 404
