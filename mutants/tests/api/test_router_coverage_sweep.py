import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pydantic.root_model as pydantic_root_model
import pytest
from fastapi import HTTPException

from packages.core.application.models import (
    CreateCredentialRequest,
    CreateSourceInsightRequest,
    EmbedRequest,
    RebuildRequest,
    RegisterModelData,
    RegisterModelsRequest,
    SourceCreate,
    SourceInsightResponse,
    SourceUpdate,
    UpdateCredentialRequest,
)

embedding_stub = types.ModuleType("packages.core.utils.embedding")
embedding_stub.generate_embedding = lambda *args, **kwargs: None
embedding_stub.generate_embeddings = lambda *args, **kwargs: []
embedding_stub.mean_pool_embeddings = lambda *args, **kwargs: []
sys.modules.setdefault("packages.core.utils.embedding", embedding_stub)

from services.api.routers import embedding as embedding_router
from services.api.routers import embedding_rebuild as embedding_rebuild_router
from services.api.routers import sources as sources_router

sys.modules.setdefault("pydantic.root_model", pydantic_root_model)
from services.api.routers import credentials as credentials_router


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
            EmbedRequest(item_id="x", item_type="invalid", async_processing=False)
        )

    assert exc_info.value.status_code == 400
    assert "either 'source' or 'note'" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_embed_content_async_queue_failure_returns_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        embedding_router.model_manager,
        "get_embedding_model",
        AsyncMock(return_value=object()),
    )
    monkeypatch.setattr(
        embedding_router.CommandService,
        "submit_command_job",
        AsyncMock(side_effect=RuntimeError("queue unavailable")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await embedding_router.embed_content(
            EmbedRequest(item_id="source:1", item_type="source", async_processing=True)
        )

    assert exc_info.value.status_code == 500
    assert "Failed to queue embedding" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_embed_content_async_source_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    assert args[0] == "open_notebook"
    assert args[1] == "embed_source"
    assert args[2] == {"source_id": "source:1"}


@pytest.mark.asyncio
async def test_embed_content_async_note_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
            EmbedRequest(item_id="source:missing", item_type="source")
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
            EmbedRequest(item_id="note:missing", item_type="note")
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Note not found"


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


@pytest.mark.asyncio
async def test_start_rebuild_aggregates_counts_from_mixed_result_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_query_mock = AsyncMock(
        side_effect=[
            [{"count": 2}],
            [3],
            [{"count": 4}],
        ]
    )
    submit_mock = AsyncMock(return_value="cmd:rebuild:1")
    monkeypatch.setattr(embedding_rebuild_router, "repo_query", repo_query_mock)
    monkeypatch.setattr(
        embedding_rebuild_router.CommandService, "submit_command_job", submit_mock
    )

    response = await embedding_rebuild_router.start_rebuild(
        RebuildRequest(
            mode="all", include_sources=True, include_notes=True, include_insights=True
        )
    )

    assert response.command_id == "cmd:rebuild:1"
    assert response.total_items == 9
    submit_payload = submit_mock.await_args.args[2]
    assert submit_payload["mode"] == "all"
    assert submit_payload["include_sources"] is True


@pytest.mark.asyncio
async def test_start_rebuild_wraps_query_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        embedding_rebuild_router,
        "repo_query",
        AsyncMock(side_effect=RuntimeError("count failure")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await embedding_rebuild_router.start_rebuild(
            RebuildRequest(mode="existing", include_sources=True, include_notes=False)
        )

    assert exc_info.value.status_code == 500
    assert "Failed to start rebuild operation" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_rebuild_status_returns_404_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        embedding_rebuild_router,
        "get_command_status",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        await embedding_rebuild_router.get_rebuild_status("cmd:missing")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_rebuild_status_builds_progress_stats_and_error_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status = SimpleNamespace(
        status="failed",
        result={
            "total_items": 10,
            "jobs_submitted": 4,
            "sources_submitted": 1,
            "notes_submitted": 2,
            "insights_submitted": 1,
            "failed_submissions": 2,
            "error_message": "submission timeout",
        },
        created="2026-02-28T00:00:00Z",
        updated="2026-02-28T00:01:00Z",
    )
    monkeypatch.setattr(
        embedding_rebuild_router,
        "get_command_status",
        AsyncMock(return_value=status),
    )

    response = await embedding_rebuild_router.get_rebuild_status("cmd:1")

    assert response.status == "failed"
    assert response.progress.percentage == 40.0
    assert response.stats.failed == 2
    assert response.error_message == "submission timeout"


@pytest.mark.asyncio
async def test_get_rebuild_status_handles_zero_total_without_division_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status = SimpleNamespace(
        status="running",
        result={"total_items": 0, "jobs_submitted": 9},
        created=None,
        updated=None,
    )
    monkeypatch.setattr(
        embedding_rebuild_router,
        "get_command_status",
        AsyncMock(return_value=status),
    )

    response = await embedding_rebuild_router.get_rebuild_status("cmd:2")

    assert response.progress.percentage == 0


@pytest.mark.asyncio
async def test_get_rebuild_status_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        embedding_rebuild_router,
        "get_command_status",
        AsyncMock(side_effect=RuntimeError("status backend down")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await embedding_rebuild_router.get_rebuild_status("cmd:err")

    assert exc_info.value.status_code == 500
    assert "Failed to get rebuild status" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_sources_rejects_invalid_sort_by() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await sources_router.get_sources(sort_by="title", sort_order="desc")

    assert exc_info.value.status_code == 400
    assert "sort_by" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_sources_rejects_invalid_sort_order() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await sources_router.get_sources(sort_by="created", sort_order="up")

    assert exc_info.value.status_code == 400
    assert "sort_order" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_sources_returns_404_when_notebook_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sources_router.Notebook, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.get_sources(
            notebook_id="notebook:missing",
            sort_by="updated",
            sort_order="desc",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Notebook not found"


@pytest.mark.asyncio
async def test_get_sources_wraps_repo_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router,
        "repo_query",
        AsyncMock(side_effect=RuntimeError("query failed")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.get_sources(
            notebook_id=None,
            sort_by="updated",
            sort_order="desc",
        )

    assert exc_info.value.status_code == 500
    assert "Error fetching sources: query failed" == exc_info.value.detail


@pytest.mark.asyncio
async def test_get_source_degrades_status_to_unknown_when_status_lookup_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SimpleNamespace(
        id="source:1",
        command="command:1",
        get_status=AsyncMock(side_effect=RuntimeError("status timeout")),
        get_processing_progress=AsyncMock(return_value={"processed": 1}),
        get_embedded_chunks=AsyncMock(return_value=3),
    )
    monkeypatch.setattr(sources_router.Source, "get", AsyncMock(return_value=source))
    monkeypatch.setattr(sources_router, "repo_query", AsyncMock(return_value=["nb:1"]))
    monkeypatch.setattr(sources_router, "is_source_file_available", lambda _: True)
    monkeypatch.setattr(
        sources_router,
        "build_source_response",
        lambda *args, **kwargs: {
            "status": kwargs["status"],
            "command_id": kwargs["command_id"],
            "notebooks": kwargs["notebooks"],
        },
    )

    response = await sources_router.get_source("source:1")

    assert response["status"] == "unknown"
    assert response["command_id"] == "command:1"
    assert response["notebooks"] == ["nb:1"]


@pytest.mark.asyncio
async def test_get_source_status_returns_legacy_message_when_no_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SimpleNamespace(command=None)
    monkeypatch.setattr(sources_router.Source, "get", AsyncMock(return_value=source))

    response = await sources_router.get_source_status("source:legacy")

    assert response.status is None
    assert "Legacy source" in response.message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expected_message"),
    [
        ("completed", "Source processing completed successfully"),
        ("failed", "Source processing failed"),
        ("running", "Source processing in progress"),
        ("queued", "Source processing queued"),
        ("unknown", "Source processing status unknown"),
        ("paused", "Source processing status: paused"),
    ],
)
async def test_get_source_status_maps_status_messages(
    monkeypatch: pytest.MonkeyPatch, status: str, expected_message: str
) -> None:
    source = SimpleNamespace(
        command="command:1",
        get_status=AsyncMock(return_value=status),
        get_processing_progress=AsyncMock(return_value={"step": "x"}),
    )
    monkeypatch.setattr(sources_router.Source, "get", AsyncMock(return_value=source))

    response = await sources_router.get_source_status("source:1")

    assert response.status == status
    assert response.message == expected_message
    assert response.command_id == "command:1"


@pytest.mark.asyncio
async def test_get_source_status_degrades_to_unknown_on_status_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SimpleNamespace(
        command="command:1",
        get_status=AsyncMock(side_effect=RuntimeError("status rpc down")),
        get_processing_progress=AsyncMock(return_value=None),
    )
    monkeypatch.setattr(sources_router.Source, "get", AsyncMock(return_value=source))

    response = await sources_router.get_source_status("source:1")

    assert response.status == "unknown"
    assert response.message == "Failed to retrieve processing status"


@pytest.mark.asyncio
async def test_update_source_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router,
        "update_source_service",
        AsyncMock(side_effect=RuntimeError("write failed")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.update_source("source:1", SourceUpdate(title="new"))

    assert exc_info.value.status_code == 500
    assert "Error updating source: write failed" == exc_info.value.detail


@pytest.mark.asyncio
async def test_delete_source_returns_404_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sources_router.Source, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.delete_source("source:missing")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_source_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router.Source, "get", AsyncMock(side_effect=RuntimeError("db broken"))
    )

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.delete_source("source:1")

    assert exc_info.value.status_code == 500
    assert "Error deleting source: db broken" == exc_info.value.detail


@pytest.mark.asyncio
async def test_create_source_insight_returns_404_for_missing_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sources_router.Source, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.create_source_insight(
            "source:missing",
            CreateSourceInsightRequest(transformation_id="transformation:1"),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Source not found"


@pytest.mark.asyncio
async def test_create_source_insight_returns_404_for_missing_transformation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1")),
    )
    monkeypatch.setattr(
        sources_router.Transformation,
        "get",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.create_source_insight(
            "source:1",
            CreateSourceInsightRequest(transformation_id="transformation:missing"),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Transformation not found"


@pytest.mark.asyncio
async def test_create_source_insight_wraps_submission_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1")),
    )
    monkeypatch.setattr(
        sources_router.Transformation,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="transformation:1")),
    )
    monkeypatch.setattr(
        sources_router.CommandService,
        "submit_command_job",
        AsyncMock(side_effect=RuntimeError("queue error")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.create_source_insight(
            "source:1",
            CreateSourceInsightRequest(transformation_id="transformation:1"),
        )

    assert exc_info.value.status_code == 500
    assert "Error starting insight generation: queue error" == exc_info.value.detail


def test_credentials_provider_normalization_and_guard() -> None:
    assert credentials_router._normalize_provider(" GOOGLE-API ") == "google_api"

    assert credentials_router._assert_google_provider("Google") == "google"
    with pytest.raises(HTTPException) as exc_info:
        credentials_router._assert_google_provider("openai")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_list_credentials_invalid_provider_is_wrapped_as_500() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await credentials_router.list_credentials(provider="openai")

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to list credentials"


@pytest.mark.asyncio
async def test_create_credential_returns_400_when_encryption_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        credentials_router,
        "require_encryption_key",
        lambda: (_ for _ in ()).throw(ValueError("missing encryption key")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await credentials_router.create_credential(
            CreateCredentialRequest(
                name="cred",
                provider="google",
                modalities=["language"],
            )
        )

    assert exc_info.value.status_code == 400
    assert "missing encryption key" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_credential_returns_400_on_invalid_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(credentials_router, "require_encryption_key", lambda: None)
    monkeypatch.setattr(
        credentials_router,
        "validate_url",
        lambda *_: (_ for _ in ()).throw(ValueError("invalid base_url")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await credentials_router.create_credential(
            CreateCredentialRequest(
                name="cred",
                provider="google",
                modalities=[],
                base_url="not-a-url",
            )
        )

    assert exc_info.value.status_code == 400
    assert "invalid base_url" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_credential_returns_400_on_invalid_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(credentials_router, "require_encryption_key", lambda: None)
    monkeypatch.setattr(
        credentials_router,
        "validate_url",
        lambda *_: (_ for _ in ()).throw(ValueError("invalid endpoint")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await credentials_router.update_credential(
            "cred:1", UpdateCredentialRequest(endpoint="bad")
        )

    assert exc_info.value.status_code == 400
    assert "invalid endpoint" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_credential_preserves_http_exception_from_provider_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(credentials_router, "require_encryption_key", lambda: None)
    monkeypatch.setattr(credentials_router, "validate_url", lambda *_: None)
    monkeypatch.setattr(
        credentials_router.Credential,
        "get",
        AsyncMock(return_value=SimpleNamespace(provider="openai")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await credentials_router.update_credential(
            "cred:1",
            UpdateCredentialRequest(),
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_delete_credential_returns_409_when_linked_models_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    linked_model = SimpleNamespace(id="model:1", provider="google", name="gemini")
    cred = SimpleNamespace(
        provider="google",
        get_linked_models=AsyncMock(return_value=[linked_model]),
    )
    monkeypatch.setattr(
        credentials_router.Credential, "get", AsyncMock(return_value=cred)
    )

    with pytest.raises(HTTPException) as exc_info:
        await credentials_router.delete_credential(
            "cred:1",
            delete_models=False,
            migrate_to=None,
        )

    assert exc_info.value.status_code == 409
    assert "linked model" in exc_info.value.detail["message"]


@pytest.mark.asyncio
async def test_delete_credential_migrates_linked_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model_1 = SimpleNamespace(id="model:1", credential=None, save=AsyncMock())
    model_2 = SimpleNamespace(id="model:2", credential=None, save=AsyncMock())
    source_cred = SimpleNamespace(
        provider="google",
        id="cred:source",
        get_linked_models=AsyncMock(return_value=[model_1, model_2]),
        delete=AsyncMock(),
    )
    target_cred = SimpleNamespace(id="cred:target")

    monkeypatch.setattr(
        credentials_router.Credential,
        "get",
        AsyncMock(side_effect=[source_cred, target_cred]),
    )

    response = await credentials_router.delete_credential(
        "cred:source",
        migrate_to="cred:target",
    )

    assert response.deleted_models == 0
    assert model_1.credential == "cred:target"
    assert model_2.credential == "cred:target"
    model_1.save.assert_awaited_once()
    model_2.save.assert_awaited_once()
    source_cred.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_credential_deletes_linked_models_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model_1 = SimpleNamespace(delete=AsyncMock())
    model_2 = SimpleNamespace(delete=AsyncMock())
    cred = SimpleNamespace(
        provider="google",
        get_linked_models=AsyncMock(return_value=[model_1, model_2]),
        delete=AsyncMock(),
    )
    monkeypatch.setattr(
        credentials_router.Credential, "get", AsyncMock(return_value=cred)
    )

    response = await credentials_router.delete_credential(
        "cred:1",
        delete_models=True,
        migrate_to=None,
    )

    assert response.deleted_models == 2
    model_1.delete.assert_awaited_once()
    model_2.delete.assert_awaited_once()
    cred.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_discover_models_for_credential_wraps_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        credentials_router.Credential,
        "get",
        AsyncMock(return_value=SimpleNamespace(provider="openai")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await credentials_router.discover_models_for_credential("cred:1")

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to discover models"


@pytest.mark.asyncio
async def test_register_models_for_credential_wraps_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        credentials_router.Credential,
        "get",
        AsyncMock(return_value=SimpleNamespace(provider="google")),
    )
    monkeypatch.setattr(
        credentials_router,
        "register_models",
        AsyncMock(side_effect=RuntimeError("registry unavailable")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await credentials_router.register_models_for_credential(
            "cred:1",
            RegisterModelsRequest(models=[]),
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to register models"


@pytest.mark.asyncio
async def test_get_sources_success_without_notebook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = {"id": "source:1"}
    monkeypatch.setattr(sources_router, "repo_query", AsyncMock(return_value=[row]))
    monkeypatch.setattr(
        sources_router, "build_source_list_response", lambda item: {"id": item["id"]}
    )

    result = await sources_router.get_sources(
        notebook_id=None,
        sort_by="updated",
        sort_order="asc",
    )

    assert result == [{"id": "source:1"}]


@pytest.mark.asyncio
async def test_get_sources_success_with_notebook_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router.Notebook,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="nb:1")),
    )
    monkeypatch.setattr(
        sources_router, "ensure_record_id", lambda value: f"RID:{value}"
    )
    repo_query_mock = AsyncMock(return_value=[])
    monkeypatch.setattr(sources_router, "repo_query", repo_query_mock)

    result = await sources_router.get_sources(
        notebook_id="nb:1", sort_by="created", sort_order="desc"
    )

    assert result == []
    query_params = repo_query_mock.await_args.args[1]
    assert query_params["notebook_id"] == "RID:nb:1"


@pytest.mark.asyncio
async def test_create_source_delegates_to_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_data = SourceCreate(type="text", content="hello")
    service_mock = AsyncMock(return_value={"id": "source:1"})
    monkeypatch.setattr(sources_router, "create_source_service", service_mock)

    response = await sources_router.create_source((source_data, None))

    assert response == {"id": "source:1"}
    assert service_mock.await_count == 1


@pytest.mark.asyncio
async def test_create_source_json_delegates_to_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service_mock = AsyncMock(return_value={"id": "source:2"})
    monkeypatch.setattr(sources_router, "create_source_service", service_mock)
    source_data = SourceCreate(type="text", content="json payload")

    response = await sources_router.create_source_json(source_data)

    assert response == {"id": "source:2"}
    assert service_mock.await_args.args[1] is None


@pytest.mark.asyncio
async def test_get_source_returns_404_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sources_router.Source, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.get_source("source:missing")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Source not found"


@pytest.mark.asyncio
async def test_get_source_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router.Source,
        "get",
        AsyncMock(side_effect=RuntimeError("storage down")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.get_source("source:broken")

    assert exc_info.value.status_code == 500
    assert "Error fetching source: storage down" == exc_info.value.detail


@pytest.mark.asyncio
async def test_check_source_file_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router,
        "resolve_source_file",
        AsyncMock(return_value=("/tmp/x", "x.txt")),
    )

    response = await sources_router.check_source_file("source:1")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_check_source_file_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router,
        "resolve_source_file",
        AsyncMock(side_effect=RuntimeError("disk error")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.check_source_file("source:1")

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to verify file"


@pytest.mark.asyncio
async def test_download_source_file_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router,
        "resolve_source_file",
        AsyncMock(return_value=("/tmp/x", "x.txt")),
    )

    response = await sources_router.download_source_file("source:1")

    assert response.filename == "x.txt"


@pytest.mark.asyncio
async def test_download_source_file_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router,
        "resolve_source_file",
        AsyncMock(side_effect=RuntimeError("missing file")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.download_source_file("source:1")

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to download source file"


@pytest.mark.asyncio
async def test_get_source_status_returns_404_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sources_router.Source, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.get_source_status("source:404")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_source_status_wraps_outer_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router.Source,
        "get",
        AsyncMock(side_effect=RuntimeError("status service unavailable")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.get_source_status("source:err")

    assert exc_info.value.status_code == 500
    assert (
        "Error fetching source status: status service unavailable"
        == exc_info.value.detail
    )


@pytest.mark.asyncio
async def test_retry_source_processing_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    retry_mock = AsyncMock(return_value={"id": "source:1"})
    monkeypatch.setattr(sources_router, "retry_source_processing_service", retry_mock)

    response = await sources_router.retry_source_processing("source:1")

    assert response == {"id": "source:1"}
    retry_mock.assert_awaited_once_with("source:1")


@pytest.mark.asyncio
async def test_get_source_insights_returns_404_when_source_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sources_router.Source, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.get_source_insights("source:404")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_source_insights_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    insight = SimpleNamespace(
        id="insight:1",
        insight_type="summary",
        content="content",
        created="2026-02-01",
        updated="2026-02-02",
    )
    source = SimpleNamespace(get_insights=AsyncMock(return_value=[insight]))
    monkeypatch.setattr(sources_router.Source, "get", AsyncMock(return_value=source))

    result = await sources_router.get_source_insights("source:1")

    assert isinstance(result[0], SourceInsightResponse)
    assert result[0].insight_type == "summary"


@pytest.mark.asyncio
async def test_get_source_insights_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router.Source,
        "get",
        AsyncMock(side_effect=RuntimeError("insight query failed")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await sources_router.get_source_insights("source:1")

    assert exc_info.value.status_code == 500
    assert "Error fetching insights: insight query failed" == exc_info.value.detail


@pytest.mark.asyncio
async def test_create_source_insight_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1")),
    )
    monkeypatch.setattr(
        sources_router.Transformation,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="transformation:1")),
    )
    monkeypatch.setattr(
        sources_router.CommandService,
        "submit_command_job",
        AsyncMock(return_value="cmd:run:1"),
    )

    response = await sources_router.create_source_insight(
        "source:1",
        CreateSourceInsightRequest(transformation_id="transformation:1"),
    )

    assert response.status == "pending"
    assert response.command_id == "cmd:run:1"


@pytest.mark.asyncio
async def test_get_credentials_status_success_and_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        credentials_router,
        "get_provider_status",
        AsyncMock(return_value={"configured": {"google": True}}),
    )
    ok_response = await credentials_router.get_status()
    assert ok_response["configured"]["google"] is True

    monkeypatch.setattr(
        credentials_router,
        "get_provider_status",
        AsyncMock(side_effect=RuntimeError("status failure")),
    )
    with pytest.raises(HTTPException) as exc_info:
        await credentials_router.get_status()
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_list_credentials_success_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cred_a = SimpleNamespace(get_linked_models=AsyncMock(return_value=[1, 2]))
    cred_b = SimpleNamespace(get_linked_models=AsyncMock(return_value=[]))
    get_by_provider_mock = AsyncMock(side_effect=[[cred_a, cred_b], [cred_a]])
    monkeypatch.setattr(
        credentials_router.Credential, "get_by_provider", get_by_provider_mock
    )
    monkeypatch.setattr(
        credentials_router,
        "credential_to_response",
        lambda cred, count: {"count": count},
    )

    all_result = await credentials_router.list_credentials(provider=None)
    by_provider_result = await credentials_router.list_credentials(provider="google")

    assert all_result == [{"count": 2}, {"count": 0}]
    assert by_provider_result == [{"count": 2}]


@pytest.mark.asyncio
async def test_list_credentials_by_provider_success_and_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cred = SimpleNamespace(get_linked_models=AsyncMock(return_value=[]))
    monkeypatch.setattr(
        credentials_router.Credential,
        "get_by_provider",
        AsyncMock(return_value=[cred]),
    )
    monkeypatch.setattr(
        credentials_router,
        "credential_to_response",
        lambda cred, count: {"count": count},
    )

    ok = await credentials_router.list_credentials_by_provider("google")
    assert ok == [{"count": 0}]

    monkeypatch.setattr(
        credentials_router.Credential,
        "get_by_provider",
        AsyncMock(side_effect=RuntimeError("provider lookup failed")),
    )
    with pytest.raises(HTTPException) as exc_info:
        await credentials_router.list_credentials_by_provider("google")
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_create_credential_success_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCredential:
        def __init__(self, **kwargs):
            self.id = "cred:1"
            self.name = kwargs["name"]
            self.provider = kwargs["provider"]
            self.modalities = kwargs["modalities"]

        async def save(self) -> None:
            return None

    monkeypatch.setattr(credentials_router, "require_encryption_key", lambda: None)
    monkeypatch.setattr(credentials_router, "validate_url", lambda *_: None)
    monkeypatch.setattr(credentials_router, "Credential", FakeCredential)
    monkeypatch.setattr(
        credentials_router,
        "credential_to_response",
        lambda cred, count: {
            "id": cred.id,
            "provider": cred.provider,
            "model_count": count,
        },
    )

    response = await credentials_router.create_credential(
        CreateCredentialRequest(
            name="my-cred",
            provider="GOOGLE",
            modalities=["language"],
            api_key="secret",
        )
    )

    assert response["id"] == "cred:1"
    assert response["provider"] == "google"


@pytest.mark.asyncio
async def test_get_credential_success_and_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cred = SimpleNamespace(
        provider="google",
        get_linked_models=AsyncMock(return_value=[1]),
    )
    monkeypatch.setattr(
        credentials_router.Credential, "get", AsyncMock(return_value=cred)
    )
    monkeypatch.setattr(
        credentials_router,
        "credential_to_response",
        lambda cred, count: {"count": count},
    )
    response = await credentials_router.get_credential("cred:1")
    assert response == {"count": 1}

    monkeypatch.setattr(
        credentials_router.Credential,
        "get",
        AsyncMock(side_effect=RuntimeError("missing")),
    )
    with pytest.raises(HTTPException) as exc_info:
        await credentials_router.get_credential("cred:missing")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_credential_success_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cred = SimpleNamespace(
        provider="google",
        name="old",
        modalities=["language"],
        api_key=None,
        base_url="https://old.example",
        endpoint="https://old-endpoint.example",
        api_version="v1",
        endpoint_llm=None,
        endpoint_embedding=None,
        endpoint_stt=None,
        endpoint_tts=None,
        project=None,
        location=None,
        credentials_path=None,
        save=AsyncMock(),
        get_linked_models=AsyncMock(return_value=[1, 2, 3]),
    )
    monkeypatch.setattr(credentials_router, "require_encryption_key", lambda: None)
    monkeypatch.setattr(credentials_router, "validate_url", lambda *_: None)
    monkeypatch.setattr(
        credentials_router.Credential, "get", AsyncMock(return_value=cred)
    )
    monkeypatch.setattr(
        credentials_router,
        "credential_to_response",
        lambda cred, count: {
            "name": cred.name,
            "count": count,
            "base_url": cred.base_url,
        },
    )

    response = await credentials_router.update_credential(
        "cred:1",
        UpdateCredentialRequest(name="new", base_url=""),
    )

    assert response["name"] == "new"
    assert response["base_url"] is None
    assert response["count"] == 3
    cred.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_credential_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cred = SimpleNamespace(
        provider="google",
        get_linked_models=AsyncMock(return_value=[]),
        delete=AsyncMock(side_effect=RuntimeError("delete failed")),
    )
    monkeypatch.setattr(
        credentials_router.Credential, "get", AsyncMock(return_value=cred)
    )

    with pytest.raises(HTTPException) as exc_info:
        await credentials_router.delete_credential("cred:1", migrate_to=None)

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_test_credential_endpoint_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc_mock = AsyncMock(
        return_value={"provider": "google", "success": True, "message": "ok"}
    )
    monkeypatch.setattr(credentials_router, "svc_test_credential", svc_mock)

    response = await credentials_router.test_credential("cred:1")

    assert response == {
        "provider": "google",
        "success": True,
        "message": "Connection test succeeded.",
    }
    svc_mock.assert_awaited_once_with("cred:1")


@pytest.mark.asyncio
async def test_discover_models_for_credential_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cred = SimpleNamespace(
        id="cred:1",
        provider="google",
        to_esperanto_config=lambda: {"api_key": "x"},
    )
    monkeypatch.setattr(
        credentials_router.Credential, "get", AsyncMock(return_value=cred)
    )
    monkeypatch.setattr(
        credentials_router,
        "discover_with_config",
        AsyncMock(
            return_value=[
                {"name": "gemini-3.1-pro", "provider": "google", "description": "desc"}
            ]
        ),
    )

    response = await credentials_router.discover_models_for_credential("cred:1")

    assert response.provider == "google"
    assert response.discovered[0].name == "gemini-3.1-pro"


@pytest.mark.asyncio
async def test_register_models_for_credential_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        credentials_router.Credential,
        "get",
        AsyncMock(return_value=SimpleNamespace(provider="google")),
    )
    monkeypatch.setattr(
        credentials_router,
        "register_models",
        AsyncMock(return_value={"created": 1, "existing": 0}),
    )

    response = await credentials_router.register_models_for_credential(
        "cred:1",
        RegisterModelsRequest(
            models=[
                RegisterModelData(
                    name="gemini-3.1-pro",
                    provider="google",
                    model_type="language",
                )
            ]
        ),
    )

    assert response.created == 1
    assert response.existing == 0
