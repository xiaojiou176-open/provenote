from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from langchain_core.messages import HumanMessage

from packages.core.application.models import DefaultModelsResponse, ModelCreate
from packages.core.exceptions import InvalidInputError, NotFoundError
from services.api.routers import chat as chat_router
from services.api.routers import models as models_router


class _NullAsyncLock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_models_get_models_success_and_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model_row = SimpleNamespace(
        id="model:1",
        name="gemini-3.1-pro",
        provider="google",
        type="language",
        credential=None,
        created="2026-02-01",
        updated="2026-02-02",
    )
    monkeypatch.setattr(
        models_router.Model, "get_all", AsyncMock(return_value=[model_row])
    )
    response = await models_router.get_models(type=None)
    assert len(response) == 1
    assert response[0].name == "gemini-3.1-pro"

    monkeypatch.setattr(
        models_router.Model,
        "get_models_by_type",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    with pytest.raises(HTTPException) as exc_info:
        await models_router.get_models(type="language")
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_models_create_model_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(HTTPException) as invalid_type:
        await models_router.create_model(
            ModelCreate(name="x", provider="google", type="invalid", credential=None)
        )
    assert invalid_type.value.status_code == 400

    with pytest.raises(HTTPException) as invalid_provider:
        await models_router.create_model(
            ModelCreate(name="x", provider="openai", type="language", credential=None)
        )
    assert invalid_provider.value.status_code == 400

    monkeypatch.setattr(
        "packages.core.database.repository.repo_query",
        AsyncMock(return_value=[{"id": "model:dup"}]),
    )
    with pytest.raises(HTTPException) as duplicate:
        await models_router.create_model(
            ModelCreate(name="dup", provider="google", type="language", credential=None)
        )
    assert duplicate.value.status_code == 400

    monkeypatch.setattr(
        "packages.core.database.repository.repo_query", AsyncMock(return_value=[])
    )

    class _InvalidModel:
        def __init__(self, **kwargs):
            self.id = ""
            self.name = kwargs["name"]
            self.provider = kwargs["provider"]
            self.type = kwargs["type"]
            self.credential = kwargs.get("credential")
            self.created = "c"
            self.updated = "u"

        async def save(self) -> None:
            raise InvalidInputError("invalid model payload")

    monkeypatch.setattr(models_router, "Model", _InvalidModel)
    with pytest.raises(HTTPException) as invalid_input:
        await models_router.create_model(
            ModelCreate(name="bad", provider="google", type="language", credential=None)
        )
    assert invalid_input.value.status_code == 400

    class _GoodModel(_InvalidModel):
        async def save(self) -> None:
            self.id = "model:new"

    monkeypatch.setattr(models_router, "Model", _GoodModel)
    created = await models_router.create_model(
        ModelCreate(name="ok", provider=" Google ", type="language", credential=None)
    )
    assert created.id == "model:new"
    assert created.provider == "google"


@pytest.mark.asyncio
async def test_models_delete_and_test_model_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(models_router.Model, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as not_found:
        await models_router.delete_model("missing")
    assert not_found.value.status_code == 404

    model = SimpleNamespace(delete=AsyncMock(side_effect=RuntimeError("delete failed")))
    monkeypatch.setattr(models_router.Model, "get", AsyncMock(return_value=model))
    with pytest.raises(HTTPException) as delete_500:
        await models_router.delete_model("model:1")
    assert delete_500.value.status_code == 500

    good_model = SimpleNamespace(delete=AsyncMock(return_value=None))
    monkeypatch.setattr(models_router.Model, "get", AsyncMock(return_value=good_model))
    deleted = await models_router.delete_model("model:ok")
    assert deleted["message"] == "Model deleted successfully"

    monkeypatch.setattr(
        models_router.Model, "get", AsyncMock(side_effect=RuntimeError("boom"))
    )
    with pytest.raises(HTTPException) as test_model_not_found:
        await models_router.test_model("model:missing")
    assert test_model_not_found.value.status_code == 404

    model_for_test = SimpleNamespace(id="model:1")
    monkeypatch.setattr(
        models_router.Model, "get", AsyncMock(return_value=model_for_test)
    )
    monkeypatch.setattr(
        models_router, "test_individual_model", AsyncMock(return_value=(True, "ok"))
    )
    test_ok = await models_router.test_model("model:1")
    assert test_ok.success is True
    assert test_ok.message == "ok"

    monkeypatch.setattr(
        models_router,
        "test_individual_model",
        AsyncMock(side_effect=RuntimeError("timeout while probing")),
    )
    test_fail = await models_router.test_model("model:1")
    assert test_fail.success is False
    assert "timeout while probing" in test_fail.message


@pytest.mark.asyncio
async def test_models_defaults_provider_discovery_and_auto_assign(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    defaults = SimpleNamespace(
        default_chat_model=None,
        default_transformation_model=None,
        large_context_model=None,
        default_text_to_speech_model=None,
        default_speech_to_text_model=None,
        default_embedding_model=None,
        default_tools_model="model:keep",
        update=AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        models_router.DefaultModels, "get_instance", AsyncMock(return_value=defaults)
    )

    got_defaults = await models_router.get_default_models()
    assert got_defaults.default_tools_model == "model:keep"

    monkeypatch.setattr(
        models_router, "ensure_record_id", lambda raw: f"normalized:{raw}"
    )
    monkeypatch.setattr(
        models_router,
        "repo_query",
        AsyncMock(
            return_value=[
                {
                    "id": "model:language",
                    "provider": "google",
                    "type": "language",
                    "name": "gemini-3.1-pro",
                }
            ]
        ),
    )
    updated = await models_router.update_default_models(
        DefaultModelsResponse(default_chat_model="model:language")
    )
    assert updated.default_chat_model == "model:language"

    monkeypatch.setattr(
        models_router,
        "ensure_record_id",
        lambda raw: (_ for _ in ()).throw(ValueError("bad id")),
    )
    with pytest.raises(HTTPException) as bad_model_id:
        await models_router.update_default_models(
            DefaultModelsResponse(default_chat_model="broken")
        )
    assert bad_model_id.value.status_code == 400

    monkeypatch.setattr(models_router, "ensure_record_id", lambda raw: raw)
    monkeypatch.setattr(models_router, "repo_query", AsyncMock(return_value=[]))
    with pytest.raises(HTTPException) as model_missing:
        await models_router.update_default_models(
            DefaultModelsResponse(default_chat_model="model:missing")
        )
    assert model_missing.value.status_code == 400

    monkeypatch.setattr(
        models_router,
        "repo_query",
        AsyncMock(
            return_value=[{"provider": "openai", "type": "language", "name": "gpt"}]
        ),
    )
    with pytest.raises(HTTPException) as provider_mismatch:
        await models_router.update_default_models(
            DefaultModelsResponse(default_chat_model="model:x")
        )
    assert provider_mismatch.value.status_code == 400

    monkeypatch.setattr(
        models_router,
        "repo_query",
        AsyncMock(
            return_value=[{"provider": "google", "type": "embedding", "name": "x"}]
        ),
    )
    with pytest.raises(HTTPException) as type_mismatch:
        await models_router.update_default_models(
            DefaultModelsResponse(default_chat_model="model:x")
        )
    assert type_mismatch.value.status_code == 400

    monkeypatch.setattr(
        models_router, "_check_provider_has_credential", AsyncMock(return_value=True)
    )
    availability = await models_router.get_provider_availability()
    assert availability.available == ["google"]
    assert "google" in availability.supported_types

    monkeypatch.setattr(
        models_router,
        "_check_provider_has_credential",
        AsyncMock(side_effect=RuntimeError("db fail")),
    )
    with pytest.raises(HTTPException) as provider_500:
        await models_router.get_provider_availability()
    assert provider_500.value.status_code == 500

    monkeypatch.setattr(
        models_router, "provision_provider_keys", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(
        models_router,
        "discover_provider_models",
        AsyncMock(
            return_value=[
                SimpleNamespace(
                    name="gemini-3.1-pro",
                    provider="google",
                    model_type="language",
                    description="pro",
                )
            ]
        ),
    )
    discovered = await models_router.discover_models("Google")
    assert discovered[0].provider == "google"

    with pytest.raises(HTTPException) as discover_bad_provider:
        await models_router.discover_models("openai")
    assert discover_bad_provider.value.status_code == 500

    monkeypatch.setattr(
        models_router, "sync_provider_models", AsyncMock(return_value=(10, 2, 8))
    )
    synced = await models_router.sync_models("google")
    assert synced.new == 2

    monkeypatch.setattr(
        models_router,
        "sync_provider_models",
        AsyncMock(side_effect=RuntimeError("sync failed")),
    )
    with pytest.raises(HTTPException) as sync_500:
        await models_router.sync_models("google")
    assert sync_500.value.status_code == 500

    monkeypatch.setattr(
        models_router,
        "sync_all_providers",
        AsyncMock(return_value={"google": (3, 1, 2)}),
    )
    all_synced = await models_router.sync_all_models()
    assert all_synced.total_discovered == 3
    assert all_synced.total_new == 1

    monkeypatch.setattr(
        models_router,
        "sync_all_providers",
        AsyncMock(side_effect=RuntimeError("all failed")),
    )
    with pytest.raises(HTTPException) as all_sync_500:
        await models_router.sync_all_models()
    assert all_sync_500.value.status_code == 500

    monkeypatch.setattr(
        models_router,
        "get_provider_model_count",
        AsyncMock(return_value={"language": 2, "embedding": 1}),
    )
    counts = await models_router.get_model_count("google")
    assert counts.total == 3

    monkeypatch.setattr(
        models_router,
        "get_provider_model_count",
        AsyncMock(side_effect=RuntimeError("count failed")),
    )
    with pytest.raises(HTTPException) as count_500:
        await models_router.get_model_count("google")
    assert count_500.value.status_code == 500

    monkeypatch.setattr(
        models_router,
        "repo_query",
        AsyncMock(
            return_value=[
                {
                    "id": "model:1",
                    "name": "gemini-3.1-pro",
                    "provider": "google",
                    "type": "language",
                    "created": "c",
                    "updated": "u",
                }
            ]
        ),
    )
    by_provider = await models_router.get_models_by_provider("google")
    assert by_provider[0].id == "model:1"

    monkeypatch.setattr(
        models_router, "repo_query", AsyncMock(side_effect=RuntimeError("query failed"))
    )
    with pytest.raises(HTTPException) as provider_models_500:
        await models_router.get_models_by_provider("google")
    assert provider_models_500.value.status_code == 500

    monkeypatch.setattr(
        models_router,
        "repo_query",
        AsyncMock(
            return_value=[
                {
                    "id": "model:lang",
                    "name": models_router.PRIMARY_LANGUAGE_MODEL,
                    "provider": "google",
                    "type": "language",
                },
                {
                    "id": "model:embed",
                    "name": models_router.DEFAULT_EMBEDDING_MODEL,
                    "provider": "google",
                    "type": "embedding",
                },
                {
                    "id": "model:tts",
                    "name": "my-tts-model",
                    "provider": "google",
                    "type": "text_to_speech",
                },
                {
                    "id": "",
                    "name": "speech-model",
                    "provider": "google",
                    "type": "speech_to_text",
                },
            ]
        ),
    )
    auto_assign = await models_router.auto_assign_defaults()
    assert "default_tools_model" in auto_assign.skipped
    assert "default_transformation_model" in auto_assign.assigned
    assert any(
        item.startswith("default_speech_to_text_model:") for item in auto_assign.missing
    )
    defaults.update.assert_awaited()

    monkeypatch.setattr(
        models_router,
        "repo_query",
        AsyncMock(side_effect=RuntimeError("auto assign failed")),
    )
    with pytest.raises(HTTPException) as auto_assign_500:
        await models_router.auto_assign_defaults()
    assert auto_assign_500.value.status_code == 500


@pytest.mark.asyncio
async def test_chat_sessions_crud_and_error_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(chat_router.Notebook, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as sessions_404:
        await chat_router.get_sessions("notebook:missing")
    assert sessions_404.value.status_code == 500

    session_1 = SimpleNamespace(
        id="chat_session:1",
        title=None,
        created="c1",
        updated="u1",
        model_override=None,
    )
    session_2 = SimpleNamespace(
        id="chat_session:2",
        title="Named",
        created="c2",
        updated="u2",
        model_override="m2",
    )
    notebook = SimpleNamespace(
        get_chat_sessions=AsyncMock(return_value=[session_1, session_2])
    )
    monkeypatch.setattr(chat_router.Notebook, "get", AsyncMock(return_value=notebook))
    monkeypatch.setattr(
        chat_router, "get_session_message_count", AsyncMock(side_effect=[1, 3])
    )
    sessions = await chat_router.get_sessions("notebook:1")
    assert [item.message_count for item in sessions] == [1, 3]
    assert sessions[0].title == "Untitled Session"

    monkeypatch.setattr(
        chat_router.Notebook, "get", AsyncMock(side_effect=NotFoundError("missing"))
    )
    with pytest.raises(HTTPException) as sessions_nf:
        await chat_router.get_sessions("notebook:missing")
    assert sessions_nf.value.status_code == 404

    monkeypatch.setattr(
        chat_router.Notebook, "get", AsyncMock(side_effect=RuntimeError("db down"))
    )
    with pytest.raises(HTTPException) as sessions_500:
        await chat_router.get_sessions("notebook:1")
    assert sessions_500.value.status_code == 500

    create_session_obj = SimpleNamespace(
        id="chat_session:new",
        title="Created",
        created="c",
        updated="u",
        model_override="m",
        save=AsyncMock(return_value=None),
        relate_to_notebook=AsyncMock(return_value=None),
    )
    monkeypatch.setattr(chat_router.Notebook, "get", AsyncMock(return_value=object()))
    monkeypatch.setattr(chat_router, "ChatSession", lambda **_: create_session_obj)
    created = await chat_router.create_session(
        chat_router.CreateSessionRequest(
            notebook_id="notebook:1", title="Created", model_override="m"
        )
    )
    assert created.id == "chat_session:new"
    assert created.model_override == "m"

    failing_session = SimpleNamespace(
        save=AsyncMock(side_effect=RuntimeError("save failed")),
        relate_to_notebook=AsyncMock(return_value=None),
        delete=AsyncMock(return_value=None),
    )
    monkeypatch.setattr(chat_router, "ChatSession", lambda **_: failing_session)
    with pytest.raises(HTTPException) as create_500:
        await chat_router.create_session(
            chat_router.CreateSessionRequest(notebook_id="notebook:1")
        )
    assert create_500.value.status_code == 500


@pytest.mark.asyncio
async def test_chat_get_update_delete_execute_and_context_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _immediate_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(chat_router.asyncio, "to_thread", _immediate_to_thread)

    session = SimpleNamespace(
        id="chat_session:1",
        title="S1",
        created="c",
        updated="u",
        model_override=None,
        save=AsyncMock(return_value=None),
        delete=AsyncMock(return_value=None),
    )
    monkeypatch.setattr(chat_router.ChatSession, "get", AsyncMock(return_value=session))
    monkeypatch.setattr(
        chat_router,
        "chat_graph",
        SimpleNamespace(
            get_state=lambda *, config: SimpleNamespace(
                values={
                    "messages": [
                        SimpleNamespace(id="m1", type="human", content="hi"),
                        object(),
                    ]
                }
            ),
            invoke=lambda *, input, config: {
                "messages": [
                    SimpleNamespace(id="a1", type="ai", content="ok"),
                    object(),
                ]
            },
        ),
    )
    monkeypatch.setattr(chat_router, "ensure_record_id", lambda value: value)
    monkeypatch.setattr(
        chat_router, "repo_query", AsyncMock(return_value=[{"out": "notebook:1"}])
    )
    got = await chat_router.get_session("1")
    assert got.notebook_id == "notebook:1"
    assert got.message_count == 2
    assert got.messages[1].type == "unknown"

    monkeypatch.setattr(
        chat_router, "repo_query", AsyncMock(side_effect=RuntimeError("query failed"))
    )
    with pytest.raises(HTTPException) as get_session_500:
        await chat_router.get_session("1")
    assert get_session_500.value.status_code == 500

    monkeypatch.setattr(chat_router.ChatSession, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as session_404:
        await chat_router.get_session("missing")
    assert session_404.value.status_code == 500

    updated_session = SimpleNamespace(
        id="chat_session:2",
        title="Old",
        created="c2",
        updated="u2",
        model_override=None,
        save=AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        chat_router.ChatSession, "get", AsyncMock(return_value=updated_session)
    )
    monkeypatch.setattr(chat_router, "repo_query", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        chat_router, "get_session_message_count", AsyncMock(return_value=7)
    )
    updated = await chat_router.update_session(
        "2", chat_router.UpdateSessionRequest(title="New", model_override="model-x")
    )
    assert updated.title == "New"
    assert updated.model_override == "model-x"
    assert updated.message_count == 7

    monkeypatch.setattr(
        chat_router.ChatSession,
        "get",
        AsyncMock(side_effect=RuntimeError("lookup failed")),
    )
    with pytest.raises(HTTPException) as update_500:
        await chat_router.update_session(
            "2", chat_router.UpdateSessionRequest(title="x")
        )
    assert update_500.value.status_code == 500

    monkeypatch.setattr(chat_router.ChatSession, "get", AsyncMock(return_value=session))
    deleted = await chat_router.delete_session("1")
    assert deleted.success is True
    session.delete.assert_awaited()

    monkeypatch.setattr(chat_router.ChatSession, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as delete_404:
        await chat_router.delete_session("missing")
    assert delete_404.value.status_code == 500

    monkeypatch.setattr(
        chat_router.ChatSession, "get", AsyncMock(side_effect=RuntimeError("db broken"))
    )
    with pytest.raises(HTTPException) as delete_500:
        await chat_router.delete_session("x")
    assert delete_500.value.status_code == 500

    monkeypatch.setattr(chat_router.ChatSession, "get", AsyncMock(return_value=session))
    monkeypatch.setattr(
        chat_router, "get_session_lock", AsyncMock(return_value=_NullAsyncLock())
    )
    executed = await chat_router.execute_chat(
        chat_router.ExecuteChatRequest(
            session_id="s1",
            message="hello",
            context={"sources": [], "notes": []},
        )
    )
    assert executed.messages[0].type == "ai"
    assert executed.messages[1].type == "unknown"

    monkeypatch.setattr(
        chat_router,
        "chat_graph",
        SimpleNamespace(
            get_state=lambda *, config: SimpleNamespace(values=[]),
            invoke=lambda *, input, config: (_ for _ in ()).throw(
                RuntimeError("invoke failed")
            ),
        ),
    )
    with pytest.raises(HTTPException) as execute_500:
        await chat_router.execute_chat(
            chat_router.ExecuteChatRequest(
                session_id="s1", message="x", context={"sources": [], "notes": []}
            )
        )
    assert execute_500.value.status_code == 500

    monkeypatch.setattr(
        chat_router.ChatSession, "get", AsyncMock(side_effect=NotFoundError("missing"))
    )
    with pytest.raises(HTTPException) as execute_404:
        await chat_router.execute_chat(
            chat_router.ExecuteChatRequest(
                session_id="s1", message="x", context={"sources": [], "notes": []}
            )
        )
    assert execute_404.value.status_code == 404

    monkeypatch.setattr(chat_router.Notebook, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as context_404:
        await chat_router.build_context(
            chat_router.BuildContextRequest(notebook_id="nb:404", context_config={})
        )
    assert context_404.value.status_code == 404

    source_ok = SimpleNamespace(get_context=AsyncMock(return_value={"id": "source:1"}))
    source_bad = SimpleNamespace(
        id="source:bad", get_context=AsyncMock(side_effect=RuntimeError("source err"))
    )
    note_ok = SimpleNamespace(
        id="note:1",
        get_context=lambda *, context_size: {"id": "note:1", "size": context_size},
    )
    note_bad = SimpleNamespace(
        id="note:2",
        get_context=lambda *, context_size: (_ for _ in ()).throw(
            RuntimeError("note err")
        ),
    )
    notebook = SimpleNamespace(
        get_sources=AsyncMock(return_value=[source_ok, source_bad]),
        get_notes=AsyncMock(return_value=[note_ok, note_bad]),
    )
    monkeypatch.setattr(chat_router.Notebook, "get", AsyncMock(return_value=notebook))
    context = await chat_router.build_context(
        chat_router.BuildContextRequest(notebook_id="nb:1", context_config={})
    )
    assert len(context.context["sources"]) == 1
    assert len(context.context["notes"]) == 1
    assert context.char_count > 0

    monkeypatch.setattr(
        chat_router.Notebook, "get", AsyncMock(side_effect=RuntimeError("ctx boom"))
    )
    with pytest.raises(HTTPException) as context_500:
        await chat_router.build_context(
            chat_router.BuildContextRequest(notebook_id="nb:1", context_config={})
        )
    assert context_500.value.status_code == 500

    with pytest.raises(HTTPException):
        await chat_router.update_session("missing", chat_router.UpdateSessionRequest())
