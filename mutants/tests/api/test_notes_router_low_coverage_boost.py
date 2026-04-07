from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from packages.core.exceptions import InvalidInputError


def test_get_notes_all_success(api_client) -> None:
    note = SimpleNamespace(
        id="note:1",
        title="n1",
        content="c1",
        note_type="human",
        created="2026-01-01T00:00:00Z",
        updated="2026-01-01T00:01:00Z",
    )
    with patch(
        "services.api.routers.notes.Note.get_all", new=AsyncMock(return_value=[note])
    ):
        response = api_client.get("/api/notes")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "note:1"
    assert body[0]["content"] == "c1"


def test_get_notes_by_notebook_not_found(api_client) -> None:
    with patch(
        "packages.core.domain.notebook.Notebook.get", new=AsyncMock(return_value=None)
    ):
        response = api_client.get("/api/notes?notebook_id=notebook:missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Notebook not found"


def test_create_note_ai_autogenerates_title(api_client) -> None:
    mock_note = AsyncMock()
    mock_note.id = "note:ai"
    mock_note.title = "AI Generated"
    mock_note.content = "Long AI summary"
    mock_note.note_type = "ai"
    mock_note.created = "2026-01-01T00:00:00Z"
    mock_note.updated = "2026-01-01T00:00:00Z"
    mock_note.save.return_value = "command:embed:ai"

    with (
        patch("services.api.routers.notes.Note", return_value=mock_note),
        patch(
            "packages.core.graphs.prompt.graph.ainvoke",
            new=AsyncMock(return_value={"output": "AI Generated"}),
        ) as mock_prompt,
    ):
        response = api_client.post(
            "/api/notes",
            json={"content": "Long AI summary", "note_type": "ai", "title": None},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "AI Generated"
    assert data["command_id"] == "command:embed:ai"
    mock_prompt.assert_awaited_once()


def test_create_note_invalid_note_type_returns_400(api_client) -> None:
    response = api_client.post(
        "/api/notes", json={"content": "x", "note_type": "machine"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "note_type must be 'human' or 'ai'"


def test_create_note_add_to_notebook_failure_rolls_back(api_client) -> None:
    mock_note = AsyncMock()
    mock_note.id = "note:rollback"
    mock_note.title = "Rollback"
    mock_note.content = "c"
    mock_note.note_type = "human"
    mock_note.created = "2026-01-01T00:00:00Z"
    mock_note.updated = "2026-01-01T00:00:00Z"
    mock_note.save.return_value = "command:rollback"
    mock_note.add_to_notebook.side_effect = RuntimeError("link failed")

    with (
        patch("services.api.routers.notes.Note", return_value=mock_note),
        patch(
            "packages.core.domain.notebook.Notebook.get",
            new=AsyncMock(return_value=SimpleNamespace(id="notebook:1")),
        ),
    ):
        response = api_client.post(
            "/api/notes",
            json={
                "content": "c",
                "note_type": "human",
                "notebook_id": "notebook:1",
            },
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    mock_note.delete.assert_awaited_once()


def test_create_note_invalid_input_error_returns_400(api_client) -> None:
    mock_note = AsyncMock()
    mock_note.save.side_effect = InvalidInputError("invalid content")

    with patch("services.api.routers.notes.Note", return_value=mock_note):
        response = api_client.post(
            "/api/notes", json={"content": "x", "note_type": "human"}
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid content"


def test_get_note_unexpected_error_returns_500(api_client) -> None:
    with patch(
        "services.api.routers.notes.Note.get",
        new=AsyncMock(side_effect=RuntimeError("db down")),
    ):
        response = api_client.get("/api/notes/note:err")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_update_note_invalid_type_returns_400(api_client) -> None:
    mock_note = AsyncMock()
    mock_note.id = "note:1"
    mock_note.title = "t"
    mock_note.content = "c"
    mock_note.note_type = "human"
    mock_note.created = "2026-01-01T00:00:00Z"
    mock_note.updated = "2026-01-01T00:00:00Z"

    with patch(
        "services.api.routers.notes.Note.get", new=AsyncMock(return_value=mock_note)
    ):
        response = api_client.put(
            "/api/notes/note:1", json={"note_type": "invalid_type"}
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "note_type must be 'human' or 'ai'"


def test_delete_note_not_found_returns_404(api_client) -> None:
    with patch("services.api.routers.notes.Note.get", new=AsyncMock(return_value=None)):
        response = api_client.delete("/api/notes/note:missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"
