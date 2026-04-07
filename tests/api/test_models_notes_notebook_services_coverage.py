from __future__ import annotations

import pytest

from packages.core.ai.models import DefaultModels
from packages.core.domain.notebook import Note, Notebook
from services.api.models_service import ModelsService
from services.api.notebook_service import NotebookService
from services.api.notes_service import NotesService


def _model_payload(model_id: str = "model:1") -> dict:
    return {
        "id": model_id,
        "name": "gemini-3.1-pro",
        "provider": "google",
        "type": "language",
        "created": "2026-01-01T00:00:00+00:00",
        "updated": "2026-01-02T00:00:00+00:00",
    }


def _defaults_payload() -> dict:
    return {
        "default_chat_model": "model:chat",
        "default_transformation_model": "model:transform",
        "large_context_model": "model:large",
        "default_text_to_speech_model": "model:tts",
        "default_speech_to_text_model": "model:stt",
        "default_embedding_model": "model:embed",
        "default_tools_model": "model:tools",
    }


def _note_payload(note_id: str = "note:1") -> dict:
    return {
        "id": note_id,
        "title": "t",
        "content": "c",
        "note_type": "human",
        "created": "2026-01-01T00:00:00+00:00",
        "updated": "2026-01-02T00:00:00+00:00",
    }


def _notebook_payload(notebook_id: str = "notebook:1") -> dict:
    return {
        "id": notebook_id,
        "name": "nb",
        "description": "desc",
        "archived": False,
        "created": "2026-01-01T00:00:00+00:00",
        "updated": "2026-01-02T00:00:00+00:00",
    }


def test_models_service_get_all_models_maps_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str | None] = {"model_type": None}

    def fake_get_models(model_type: str | None = None):
        captured["model_type"] = model_type
        return [_model_payload()]

    monkeypatch.setattr(
        "services.api.models_service.api_client.get_models",
        fake_get_models,
    )

    models = ModelsService().get_all_models(model_type="language")

    assert captured["model_type"] == "language"
    assert len(models) == 1
    assert models[0].id == "model:1"
    assert models[0].name == "gemini-3.1-pro"


@pytest.mark.parametrize(
    "raw_response", [_model_payload("model:2"), [_model_payload("model:3")]]
)
def test_models_service_create_model_accepts_dict_or_list_response(
    monkeypatch: pytest.MonkeyPatch, raw_response: dict | list[dict]
) -> None:
    monkeypatch.setattr(
        "services.api.models_service.api_client.create_model",
        lambda name, provider, model_type: raw_response,
    )

    model = ModelsService().create_model("x", "google", "language")

    assert model.id in {"model:2", "model:3"}
    assert model.provider == "google"


@pytest.mark.parametrize("raw_response", [_defaults_payload(), [_defaults_payload()]])
def test_models_service_get_default_models_accepts_dict_or_list_response(
    monkeypatch: pytest.MonkeyPatch, raw_response: dict | list[dict]
) -> None:
    monkeypatch.setattr(
        "services.api.models_service.api_client.get_default_models",
        lambda: raw_response,
    )

    defaults = ModelsService().get_default_models()

    assert defaults.default_chat_model == "model:chat"
    assert defaults.default_embedding_model == "model:embed"


def test_models_service_update_default_models_returns_updated_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "services.api.models_service.api_client.update_default_models",
        lambda **kwargs: _defaults_payload(),
    )
    defaults = DefaultModels(default_chat_model="old")

    updated = ModelsService().update_default_models(defaults)

    assert updated is defaults
    assert updated.default_chat_model == "model:chat"
    assert updated.default_tools_model == "model:tools"


def test_models_service_delete_model_success_and_error_propagation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "services.api.models_service.api_client.delete_model",
        lambda _: None,
    )
    assert ModelsService().delete_model("model:1") is True

    def raise_runtime_error(_: str) -> None:
        raise RuntimeError("delete failed")

    monkeypatch.setattr(
        "services.api.models_service.api_client.delete_model",
        raise_runtime_error,
    )
    with pytest.raises(RuntimeError, match="delete failed"):
        ModelsService().delete_model("model:1")


def test_notes_service_get_all_notes_maps_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str | None] = {"notebook_id": None}

    def fake_get_notes(notebook_id: str | None = None):
        captured["notebook_id"] = notebook_id
        return [_note_payload()]

    monkeypatch.setattr(
        "services.api.notes_service.api_client.get_notes", fake_get_notes
    )

    notes = NotesService().get_all_notes(notebook_id="notebook:1")

    assert captured["notebook_id"] == "notebook:1"
    assert len(notes) == 1
    assert notes[0].id == "note:1"
    assert notes[0].content == "c"


@pytest.mark.parametrize(
    "raw_response", [_note_payload("note:2"), [_note_payload("note:3")]]
)
def test_notes_service_get_note_accepts_dict_or_list_response(
    monkeypatch: pytest.MonkeyPatch, raw_response: dict | list[dict]
) -> None:
    monkeypatch.setattr(
        "services.api.notes_service.api_client.get_note", lambda _: raw_response
    )

    note = NotesService().get_note("note:x")

    assert note.id in {"note:2", "note:3"}


@pytest.mark.parametrize(
    "raw_response", [_note_payload("note:4"), [_note_payload("note:5")]]
)
def test_notes_service_create_note_accepts_dict_or_list_response(
    monkeypatch: pytest.MonkeyPatch, raw_response: dict | list[dict]
) -> None:
    monkeypatch.setattr(
        "services.api.notes_service.api_client.create_note",
        lambda **kwargs: raw_response,
    )

    created = NotesService().create_note(
        content="hello", title="title", note_type="human"
    )

    assert created.id in {"note:4", "note:5"}
    assert created.title == "t"


def test_notes_service_update_note_uses_empty_id_fallback_and_updates_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict = {}

    def fake_update_note(note_id: str, **updates):
        called["note_id"] = note_id
        called["updates"] = updates
        return {
            **_note_payload("note:updated"),
            "title": "new title",
            "content": "new content",
            "note_type": "ai",
        }

    monkeypatch.setattr(
        "services.api.notes_service.api_client.update_note", fake_update_note
    )
    note = Note(title="old", content="old", note_type="human")

    updated = NotesService().update_note(note)

    assert called["note_id"] == ""
    assert called["updates"] == {
        "title": "old",
        "content": "old",
        "note_type": "human",
    }
    assert updated is note
    assert note.title == "new title"
    assert note.note_type == "ai"


def test_notes_service_delete_note_and_error_propagation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "services.api.notes_service.api_client.delete_note", lambda _: None
    )
    assert NotesService().delete_note("note:1") is True

    def raise_value_error(_: str) -> None:
        raise ValueError("invalid note id")

    monkeypatch.setattr(
        "services.api.notes_service.api_client.delete_note", raise_value_error
    )
    with pytest.raises(ValueError, match="invalid note id"):
        NotesService().delete_note("bad")


def test_notebook_service_get_all_notebooks_maps_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str] = {}

    def fake_get_notebooks(order_by: str = "updated desc"):
        captured["order_by"] = order_by
        return [_notebook_payload()]

    monkeypatch.setattr(
        "services.api.notebook_service.api_client.get_notebooks", fake_get_notebooks
    )

    notebooks = NotebookService().get_all_notebooks(order_by="created asc")

    assert captured["order_by"] == "created asc"
    assert len(notebooks) == 1
    assert notebooks[0].id == "notebook:1"


@pytest.mark.parametrize(
    "raw_response", [_notebook_payload("notebook:2"), [_notebook_payload("notebook:3")]]
)
def test_notebook_service_get_notebook_accepts_dict_or_list_response(
    monkeypatch: pytest.MonkeyPatch, raw_response: dict | list[dict]
) -> None:
    monkeypatch.setattr(
        "services.api.notebook_service.api_client.get_notebook", lambda _: raw_response
    )

    notebook = NotebookService().get_notebook("notebook:x")

    expected_id = (
        raw_response["id"] if isinstance(raw_response, dict) else raw_response[0]["id"]
    )
    assert notebook.id == expected_id


@pytest.mark.parametrize(
    "raw_response", [_notebook_payload("notebook:4"), [_notebook_payload("notebook:5")]]
)
def test_notebook_service_create_notebook_accepts_dict_or_list_response(
    monkeypatch: pytest.MonkeyPatch, raw_response: dict | list[dict]
) -> None:
    monkeypatch.setattr(
        "services.api.notebook_service.api_client.create_notebook",
        lambda *_: raw_response,
    )

    created = NotebookService().create_notebook(name="nb", description="desc")

    assert created.id in {"notebook:4", "notebook:5"}


def test_notebook_service_update_notebook_uses_empty_id_fallback_and_updates_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict = {}

    def fake_update_notebook(notebook_id: str, **updates):
        called["notebook_id"] = notebook_id
        called["updates"] = updates
        return {
            **_notebook_payload("notebook:updated"),
            "name": "new name",
            "description": "new desc",
            "archived": True,
        }

    monkeypatch.setattr(
        "services.api.notebook_service.api_client.update_notebook", fake_update_notebook
    )
    notebook = Notebook(name="old", description="old desc", archived=False)

    updated = NotebookService().update_notebook(notebook)

    assert called["notebook_id"] == ""
    assert called["updates"] == {
        "name": "old",
        "description": "old desc",
        "archived": False,
    }
    assert updated is notebook
    assert notebook.name == "new name"
    assert notebook.archived is True


def test_notebook_service_delete_notebook_and_error_propagation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict = {}

    def fake_delete_notebook(notebook_id: str) -> None:
        called["notebook_id"] = notebook_id

    monkeypatch.setattr(
        "services.api.notebook_service.api_client.delete_notebook", fake_delete_notebook
    )
    notebook = Notebook(name="to delete")

    assert NotebookService().delete_notebook(notebook) is True
    assert called["notebook_id"] == ""

    def raise_runtime_error(_: str) -> None:
        raise RuntimeError("delete notebook failed")

    monkeypatch.setattr(
        "services.api.notebook_service.api_client.delete_notebook", raise_runtime_error
    )
    with pytest.raises(RuntimeError, match="delete notebook failed"):
        NotebookService().delete_notebook(notebook)
