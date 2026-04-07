from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from packages.core.application.models import (
    NotebookCreate,
    NotebookUpdate,
    SettingsUpdate,
)
from packages.core.domain.transformation import Transformation
from packages.core.exceptions import InvalidInputError
from services.api.routers import notebooks as notebooks_router
from services.api.routers import settings as settings_router
from services.api.transformations_service import TransformationsService


@pytest.fixture
def transformation_payload() -> dict[str, object]:
    return {
        "id": "transformation:1",
        "name": "normalize",
        "title": "Normalize",
        "description": "normalize text",
        "prompt": "do normalize",
        "apply_default": True,
        "created": "2026-01-01T00:00:00Z",
        "updated": "2026-01-02T00:00:00Z",
    }


def test_transformations_service_get_all_and_single_branches(
    monkeypatch: pytest.MonkeyPatch,
    transformation_payload: dict[str, object],
) -> None:
    service = TransformationsService()

    monkeypatch.setattr(
        "services.api.transformations_service.api_client.get_transformations",
        lambda: [transformation_payload],
    )
    monkeypatch.setattr(
        "services.api.transformations_service.api_client.get_transformation",
        lambda _id: [transformation_payload],
    )

    all_items = service.get_all_transformations()
    assert len(all_items) == 1
    assert all_items[0].id == "transformation:1"
    assert all_items[0].created.isoformat() == "2026-01-01T00:00:00+00:00"

    single_item = service.get_transformation("transformation:1")
    assert single_item.id == "transformation:1"
    assert single_item.updated.isoformat() == "2026-01-02T00:00:00+00:00"


def test_transformations_service_create_update_delete_execute_branches(
    monkeypatch: pytest.MonkeyPatch,
    transformation_payload: dict[str, object],
) -> None:
    service = TransformationsService()

    created_payload = dict(transformation_payload, id="transformation:2")
    updated_payload = dict(transformation_payload, updated="2026-02-01T00:00:00Z")

    monkeypatch.setattr(
        "services.api.transformations_service.api_client.create_transformation",
        lambda **_kwargs: created_payload,
    )
    monkeypatch.setattr(
        "services.api.transformations_service.api_client.update_transformation",
        lambda _id, **_kwargs: [updated_payload],
    )

    delete_calls: list[str] = []

    def _delete_transformation(transformation_id: str) -> None:
        delete_calls.append(transformation_id)

    monkeypatch.setattr(
        "services.api.transformations_service.api_client.delete_transformation",
        _delete_transformation,
    )

    monkeypatch.setattr(
        "services.api.transformations_service.api_client.execute_transformation",
        lambda **kwargs: {
            "ok": True,
            "transformation_id": kwargs["transformation_id"],
            "model_id": kwargs["model_id"],
        },
    )

    created = service.create_transformation(
        name="normalize",
        title="Normalize",
        description="normalize text",
        prompt="do normalize",
        apply_default=False,
    )
    assert created.id == "transformation:2"

    to_update = Transformation(
        name="n",
        title="t",
        description="d",
        prompt="p",
        apply_default=False,
    )
    to_update.id = "transformation:1"

    updated = service.update_transformation(to_update)
    assert updated.updated.isoformat() == "2026-02-01T00:00:00+00:00"

    result = service.execute_transformation(
        transformation_id="transformation:1",
        input_text="hello",
        model_id="model:1",
    )
    assert result == {
        "ok": True,
        "transformation_id": "transformation:1",
        "model_id": "model:1",
    }

    assert service.delete_transformation("transformation:1") is True
    assert delete_calls == ["transformation:1"]


def test_transformations_service_update_requires_id() -> None:
    service = TransformationsService()
    transformation = Transformation(
        name="n",
        title="t",
        description="d",
        prompt="p",
        apply_default=False,
    )

    with pytest.raises(ValueError, match="Transformation ID is required for update"):
        service.update_transformation(transformation)


@pytest.mark.asyncio
async def test_parse_notebook_order_valid_and_invalid_branches() -> None:
    assert notebooks_router._parse_notebook_order("name asc") == ("name", "asc")
    assert notebooks_router._parse_notebook_order("updated") == ("updated", "desc")

    with pytest.raises(HTTPException) as bad_field:
        notebooks_router._parse_notebook_order("title asc")
    assert bad_field.value.status_code == 400

    with pytest.raises(HTTPException) as bad_direction:
        notebooks_router._parse_notebook_order("name upward")
    assert bad_direction.value.status_code == 400


@pytest.mark.asyncio
async def test_get_notebooks_success_with_filter_and_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query_mock = AsyncMock(
        return_value=[
            {
                "id": "notebook:1",
                "name": "N1",
                "description": "desc",
                "archived": True,
                "created": "2026-01-01",
                "updated": "2026-01-02",
                "source_count": 2,
                "note_count": 3,
            }
        ]
    )
    monkeypatch.setattr(notebooks_router, "repo_query", query_mock)

    response = await notebooks_router.get_notebooks(archived=True, order_by="name asc")

    assert len(response) == 1
    assert response[0].source_count == 2
    assert response[0].note_count == 3

    query, params = query_mock.await_args.args
    assert "WHERE archived = $archived" in query
    assert "ORDER BY name ASC" in query
    assert params == {"archived": True}


@pytest.mark.asyncio
async def test_notebook_router_exception_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # get_notebooks wraps unexpected errors
    monkeypatch.setattr(
        notebooks_router,
        "repo_query",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    with pytest.raises(HTTPException) as fetch_exc:
        await notebooks_router.get_notebooks(archived=None, order_by="updated desc")
    assert fetch_exc.value.status_code == 500
    assert "Error fetching notebooks: db down" == fetch_exc.value.detail

    # get_notebook_delete_preview returns 404 when notebook missing
    monkeypatch.setattr(notebooks_router.Notebook, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as preview_missing:
        await notebooks_router.get_notebook_delete_preview("notebook:404")
    assert preview_missing.value.status_code == 404

    # get_notebook returns 404 when query is empty
    monkeypatch.setattr(notebooks_router, "repo_query", AsyncMock(return_value=[]))
    with pytest.raises(HTTPException) as notebook_missing:
        await notebooks_router.get_notebook("notebook:404")
    assert notebook_missing.value.status_code == 404


@pytest.mark.asyncio
async def test_update_notebook_fallback_and_error_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notebook = SimpleNamespace(
        id="notebook:1",
        name="old",
        description="old desc",
        archived=False,
        created="2026-01-01",
        updated="2026-01-02",
        save=AsyncMock(),
    )
    monkeypatch.setattr(
        notebooks_router.Notebook, "get", AsyncMock(return_value=notebook)
    )
    monkeypatch.setattr(notebooks_router, "repo_query", AsyncMock(return_value=[]))

    fallback = await notebooks_router.update_notebook(
        "notebook:1",
        NotebookUpdate(name="new", description="new desc", archived=True),
    )
    assert fallback.name == "new"
    assert fallback.archived is True
    assert fallback.source_count == 0

    monkeypatch.setattr(
        notebooks_router.Notebook,
        "get",
        AsyncMock(side_effect=InvalidInputError("bad notebook")),
    )
    with pytest.raises(HTTPException) as invalid_input_exc:
        await notebooks_router.update_notebook("notebook:1", NotebookUpdate(name="x"))
    assert invalid_input_exc.value.status_code == 400
    assert invalid_input_exc.value.detail == "bad notebook"


@pytest.mark.asyncio
async def test_notebook_source_linking_idempotent_and_create_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        notebooks_router.Notebook,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="notebook:1")),
    )
    monkeypatch.setattr(
        notebooks_router.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1")),
    )

    # Existing relationship branch: no RELATE call
    existing_only = AsyncMock(return_value=[{"id": "reference:1"}])
    monkeypatch.setattr(notebooks_router, "repo_query", existing_only)
    response = await notebooks_router.add_source_to_notebook("notebook:1", "source:1")
    assert response["message"] == "Source linked to notebook successfully"
    assert existing_only.await_count == 1

    # Missing relationship branch: executes RELATE call
    relate_branch = AsyncMock(side_effect=[[], [{"id": "reference:new"}]])
    monkeypatch.setattr(notebooks_router, "repo_query", relate_branch)
    await notebooks_router.add_source_to_notebook("notebook:1", "source:1")
    assert relate_branch.await_count == 2
    assert "RELATE" in relate_branch.await_args_list[1].args[0]


@pytest.mark.asyncio
async def test_delete_notebook_success_and_error_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notebook = SimpleNamespace(
        delete=AsyncMock(
            return_value={
                "deleted_notes": 5,
                "deleted_sources": 2,
                "unlinked_sources": 1,
            }
        )
    )
    monkeypatch.setattr(
        notebooks_router.Notebook, "get", AsyncMock(return_value=notebook)
    )

    response = await notebooks_router.delete_notebook("notebook:1", True)
    assert response.deleted_notes == 5
    assert response.deleted_sources == 2
    assert response.unlinked_sources == 1

    monkeypatch.setattr(
        notebooks_router.Notebook,
        "get",
        AsyncMock(side_effect=RuntimeError("delete backend down")),
    )
    with pytest.raises(HTTPException) as exc_info:
        await notebooks_router.delete_notebook("notebook:1", False)
    assert exc_info.value.status_code == 500
    assert "Error deleting notebook: delete backend down" == exc_info.value.detail


@pytest.mark.asyncio
async def test_settings_router_success_and_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(
        default_content_processing_engine_doc="auto",
        default_content_processing_engine_url="auto",
        default_embedding_option="ask",
        auto_delete_files="no",
        youtube_preferred_languages=["en"],
        update=AsyncMock(),
    )
    monkeypatch.setattr(
        settings_router.ContentSettings,
        "get_instance",
        AsyncMock(return_value=settings),
    )

    fetched = await settings_router.get_settings()
    assert fetched.default_content_processing_engine_doc == "auto"

    updated = await settings_router.update_settings(
        SettingsUpdate(
            default_content_processing_engine_doc="docling",
            default_content_processing_engine_url="jina",
            default_embedding_option="always",
            auto_delete_files="yes",
            youtube_preferred_languages=["zh", "en"],
        )
    )
    assert updated.default_content_processing_engine_doc == "docling"
    assert updated.default_content_processing_engine_url == "jina"
    assert updated.default_embedding_option == "always"
    assert updated.auto_delete_files == "yes"
    assert updated.youtube_preferred_languages == ["zh", "en"]

    monkeypatch.setattr(
        settings_router.ContentSettings,
        "get_instance",
        AsyncMock(side_effect=RuntimeError("settings offline")),
    )
    with pytest.raises(HTTPException) as get_exc:
        await settings_router.get_settings()
    assert get_exc.value.status_code == 500
    assert get_exc.value.detail == "Error fetching settings"

    monkeypatch.setattr(
        settings_router.ContentSettings,
        "get_instance",
        AsyncMock(
            return_value=SimpleNamespace(
                update=AsyncMock(side_effect=InvalidInputError("invalid setting"))
            )
        ),
    )
    with pytest.raises(HTTPException) as update_invalid:
        await settings_router.update_settings(SettingsUpdate())
    assert update_invalid.value.status_code == 400
    assert update_invalid.value.detail == "invalid setting"


@pytest.mark.asyncio
async def test_settings_update_reraises_http_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(
        default_content_processing_engine_doc="auto",
        default_content_processing_engine_url="auto",
        default_embedding_option="ask",
        auto_delete_files="no",
        youtube_preferred_languages=["en"],
        update=AsyncMock(side_effect=HTTPException(status_code=409, detail="conflict")),
    )
    monkeypatch.setattr(
        settings_router.ContentSettings,
        "get_instance",
        AsyncMock(return_value=settings),
    )

    with pytest.raises(HTTPException) as exc_info:
        await settings_router.update_settings(SettingsUpdate())

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "conflict"


@pytest.mark.asyncio
async def test_create_notebook_invalid_input_and_generic_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _InvalidNotebook:
        def __init__(self, **_kwargs) -> None:
            raise InvalidInputError("bad create")

    monkeypatch.setattr(notebooks_router, "Notebook", _InvalidNotebook)

    with pytest.raises(HTTPException) as invalid_exc:
        await notebooks_router.create_notebook(
            NotebookCreate(name="n", description="d")
        )
    assert invalid_exc.value.status_code == 400
    assert invalid_exc.value.detail == "bad create"

    class _ExplodingNotebook:
        def __init__(self, **_kwargs) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr(notebooks_router, "Notebook", _ExplodingNotebook)

    with pytest.raises(HTTPException) as generic_exc:
        await notebooks_router.create_notebook(
            NotebookCreate(name="n", description="d")
        )
    assert generic_exc.value.status_code == 500
    assert generic_exc.value.detail == "Error creating notebook: boom"
