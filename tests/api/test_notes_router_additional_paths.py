from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from packages.core.exceptions import InvalidInputError


def _note_stub() -> SimpleNamespace:
    return SimpleNamespace(
        id="note:1",
        title="title",
        content="content",
        note_type="human",
        created="2026-01-01T00:00:00Z",
        updated="2026-01-01T00:00:00Z",
        save=AsyncMock(return_value="command:note"),
        delete=AsyncMock(return_value=None),
        add_to_notebook=AsyncMock(return_value=None),
    )


def test_get_notes_by_notebook_success(api_client) -> None:
    notebook = SimpleNamespace(
        get_notes=AsyncMock(return_value=[_note_stub()]),
    )
    with patch(
        "packages.core.domain.notebook.Notebook.get",
        new=AsyncMock(return_value=notebook),
    ):
        response = api_client.get("/api/notes?notebook_id=notebook:1")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == "note:1"


def test_get_notes_returns_500_on_unexpected_error(api_client) -> None:
    with patch(
        "services.api.routers.notes.Note.get_all",
        new=AsyncMock(side_effect=RuntimeError("db down")),
    ):
        response = api_client.get("/api/notes")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_create_note_returns_404_when_notebook_missing(api_client) -> None:
    with patch(
        "packages.core.domain.notebook.Notebook.get",
        new=AsyncMock(return_value=None),
    ):
        response = api_client.post(
            "/api/notes",
            json={
                "title": "x",
                "content": "y",
                "note_type": "human",
                "notebook_id": "notebook:missing",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Notebook not found"


def test_create_note_accepts_null_note_type(api_client) -> None:
    note = _note_stub()
    with patch("services.api.routers.notes.Note", return_value=note):
        response = api_client.post(
            "/api/notes",
            json={
                "title": "manual",
                "content": "body",
                "note_type": None,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "title"
    assert payload["note_type"] == "human"


def test_get_note_returns_404_when_missing(api_client) -> None:
    with patch("services.api.routers.notes.Note.get", new=AsyncMock(return_value=None)):
        response = api_client.get("/api/notes/note:missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"


def test_update_note_returns_404_when_missing(api_client) -> None:
    with patch("services.api.routers.notes.Note.get", new=AsyncMock(return_value=None)):
        response = api_client.put("/api/notes/note:missing", json={"title": "new"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"


def test_update_note_maps_invalid_input_to_400(api_client) -> None:
    note = _note_stub()
    note.save = AsyncMock(side_effect=InvalidInputError("bad payload"))
    with patch("services.api.routers.notes.Note.get", new=AsyncMock(return_value=note)):
        response = api_client.put("/api/notes/note:1", json={"title": "new"})

    assert response.status_code == 400
    assert response.json()["detail"] == "bad payload"


def test_delete_note_success(api_client) -> None:
    note = _note_stub()
    with patch("services.api.routers.notes.Note.get", new=AsyncMock(return_value=note)):
        response = api_client.delete("/api/notes/note:1")

    assert response.status_code == 200
    assert response.json() == {"message": "Note deleted successfully"}
    note.delete.assert_awaited_once()


def test_delete_note_returns_500_on_unexpected_error(api_client) -> None:
    note = _note_stub()
    note.delete = AsyncMock(side_effect=RuntimeError("delete failed"))
    with patch("services.api.routers.notes.Note.get", new=AsyncMock(return_value=note)):
        response = api_client.delete("/api/notes/note:1")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
