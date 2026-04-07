from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from packages.core.application.models import (
    AskRequest,
    NoteUpdate,
    RebuildRequest,
    SearchRequest,
)
from packages.core.exceptions import DatabaseOperationError, InvalidInputError
from services.api.routers import embedding_rebuild as embedding_rebuild_router
from services.api.routers import notes as notes_router
from services.api.routers import search as search_router


class AsyncCallStub:
    """Lightweight async spy to avoid AsyncMock unawaited coroutine warnings."""

    def __init__(
        self,
        *,
        return_value: object = None,
        side_effect: object = None,
    ) -> None:
        self.return_value = return_value
        self.side_effect = side_effect
        self.await_count = 0
        self.await_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
        self._iterable_side_effect = (
            iter(side_effect) if isinstance(side_effect, list) else None
        )

    async def __call__(self, *args: object, **kwargs: object) -> object:
        self.await_count += 1
        self.await_calls.append((args, kwargs))

        if self._iterable_side_effect is not None:
            value = next(self._iterable_side_effect)
            if isinstance(value, Exception):
                raise value
            return value

        if isinstance(self.side_effect, Exception):
            raise self.side_effect

        if callable(self.side_effect):
            return self.side_effect(*args, **kwargs)

        return self.return_value

    def assert_awaited_once(self) -> None:
        assert self.await_count == 1

    def assert_not_awaited(self) -> None:
        assert self.await_count == 0


@pytest.mark.asyncio
async def test_search_vector_success_with_explicit_embedding_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = SearchRequest(
        query="q",
        type="vector",
        limit=2,
        search_sources=True,
        search_notes=False,
        minimum_score=0.3,
    )

    async def _fake_get_defaults() -> SimpleNamespace:
        return SimpleNamespace(default_embedding_model="model:embed")

    async def _fake_get_model(_model_id: str) -> SimpleNamespace:
        return SimpleNamespace(id="model:embed", type="embedding")

    async def _fake_get_runtime_model(_model_id: str) -> object:
        return object()

    vector_calls: list[dict[str, object]] = []

    async def _fake_vector_search(**kwargs: object) -> list[dict[str, str]]:
        vector_calls.append(kwargs)
        return [{"id": "r1"}, {"id": "r2"}]

    monkeypatch.setattr(search_router.DefaultModels, "get_instance", _fake_get_defaults)
    monkeypatch.setattr(search_router.Model, "get", _fake_get_model)
    monkeypatch.setattr(
        search_router.model_manager, "get_model", _fake_get_runtime_model
    )
    monkeypatch.setattr(search_router, "vector_search", _fake_vector_search)

    response = await search_router.search_knowledge_base(request)

    assert response.total_count == 2
    assert response.results == [{"id": "r1"}, {"id": "r2"}]
    assert vector_calls == [
        {
            "keyword": "q",
            "results": 2,
            "source": True,
            "note": False,
            "minimum_score": 0.3,
        }
    ]


@pytest.mark.asyncio
async def test_search_vector_rejects_invalid_default_embedding_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = SearchRequest(query="q", type="vector")

    async def _fake_get_defaults() -> SimpleNamespace:
        return SimpleNamespace(default_embedding_model="model:embed")

    async def _fake_get_model(_model_id: str) -> None:
        return None

    monkeypatch.setattr(search_router.DefaultModels, "get_instance", _fake_get_defaults)
    monkeypatch.setattr(search_router.Model, "get", _fake_get_model)

    with pytest.raises(HTTPException) as exc_info:
        await search_router.search_knowledge_base(request)

    assert exc_info.value.status_code == 400
    assert "Default embedding model is invalid" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_search_vector_rejects_unavailable_embedding_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = SearchRequest(query="q", type="vector")

    async def _fake_get_defaults() -> SimpleNamespace:
        return SimpleNamespace(default_embedding_model="model:embed")

    async def _fake_get_model(_model_id: str) -> SimpleNamespace:
        return SimpleNamespace(id="model:embed", type="embedding")

    async def _missing_runtime_model(_model_id: str) -> None:
        return None

    monkeypatch.setattr(search_router.DefaultModels, "get_instance", _fake_get_defaults)
    monkeypatch.setattr(search_router.Model, "get", _fake_get_model)
    monkeypatch.setattr(
        search_router.model_manager, "get_model", _missing_runtime_model
    )

    with pytest.raises(HTTPException) as exc_info:
        await search_router.search_knowledge_base(request)

    assert exc_info.value.status_code == 400
    assert "Configured embedding model is unavailable" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_search_text_invalid_input_maps_to_400(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _failing_text_search(**_kwargs: object) -> None:
        raise InvalidInputError("invalid query")

    monkeypatch.setattr(search_router, "text_search", _failing_text_search)

    with pytest.raises(HTTPException) as exc_info:
        await search_router.search_knowledge_base(SearchRequest(query="?", type="text"))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "invalid query"


@pytest.mark.asyncio
async def test_search_text_database_error_maps_to_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _failing_text_search(**_kwargs: object) -> None:
        raise DatabaseOperationError("db unavailable")

    monkeypatch.setattr(search_router, "text_search", _failing_text_search)

    with pytest.raises(HTTPException) as exc_info:
        await search_router.search_knowledge_base(SearchRequest(query="x", type="text"))

    assert exc_info.value.status_code == 500
    assert "Search failed" == exc_info.value.detail


@pytest.mark.asyncio
async def test_stream_ask_response_handles_chunks_after_final_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_astream(*_args, **_kwargs):
        yield {"write_final_answer": {"final_answer": "final"}}
        yield {"provide_answer": {"answers": ["late-answer"]}}

    monkeypatch.setattr(search_router.ask_graph, "astream", _fake_astream)

    strategy_model = SimpleNamespace(id="m1")
    answer_model = SimpleNamespace(id="m2")
    final_model = SimpleNamespace(id="m3")

    chunks: list[dict[str, str]] = []
    async for chunk in search_router.stream_ask_response(
        "q", strategy_model, answer_model, final_model
    ):
        chunks.append(json.loads(chunk.removeprefix("data: ").strip()))

    assert [c["type"] for c in chunks] == ["final_answer", "answer", "complete"]
    assert chunks[-1]["final_answer"] == "final"


@pytest.mark.asyncio
async def test_ask_endpoint_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _failing_model_resolver(
        *_args: object, **_kwargs: object
    ) -> tuple[object, object, object]:
        raise RuntimeError("resolver boom")

    monkeypatch.setattr(search_router, "_resolve_ask_models", _failing_model_resolver)

    with pytest.raises(HTTPException) as exc_info:
        await search_router.ask_knowledge_base(
            AskRequest(
                question="q",
                strategy_model="s",
                answer_model="a",
                final_answer_model="f",
            )
        )

    assert exc_info.value.status_code == 500
    assert "Ask operation failed" == exc_info.value.detail


@pytest.mark.asyncio
async def test_ask_simple_returns_final_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    models = (
        SimpleNamespace(id="s", type="language"),
        SimpleNamespace(id="a", type="language"),
        SimpleNamespace(id="f", type="language"),
    )

    async def _resolve_models(
        *_args: object, **_kwargs: object
    ) -> tuple[SimpleNamespace, SimpleNamespace, SimpleNamespace]:
        return models

    async def _require_embedding_model(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(search_router, "_resolve_ask_models", _resolve_models)
    monkeypatch.setattr(
        search_router,
        "_require_explicit_embedding_model",
        _require_embedding_model,
    )

    async def _fake_astream(*_args, **_kwargs):
        yield {"write_final_answer": {"final_answer": "Answer"}}

    monkeypatch.setattr(search_router.ask_graph, "astream", _fake_astream)

    response = await search_router.ask_knowledge_base_simple(
        AskRequest(
            question="What?",
            strategy_model="s",
            answer_model="a",
            final_answer_model="f",
        )
    )

    assert response.answer == "Answer"
    assert response.question == "What?"


@pytest.mark.asyncio
async def test_ask_simple_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _failing_model_resolver(
        *_args: object, **_kwargs: object
    ) -> tuple[object, object, object]:
        raise RuntimeError("simple boom")

    monkeypatch.setattr(search_router, "_resolve_ask_models", _failing_model_resolver)

    with pytest.raises(HTTPException) as exc_info:
        await search_router.ask_knowledge_base_simple(
            AskRequest(
                question="q",
                strategy_model="s",
                answer_model="a",
                final_answer_model="f",
            )
        )

    assert exc_info.value.status_code == 500
    assert "Ask operation failed" == exc_info.value.detail


@pytest.mark.asyncio
async def test_start_rebuild_existing_mode_mixed_result_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        embedding_rebuild_router,
        "repo_query",
        AsyncCallStub(side_effect=[[5], [{"count": 2}], [9]]),
    )
    submit_mock = AsyncCallStub(return_value="cmd:existing:mix")
    monkeypatch.setattr(
        embedding_rebuild_router.CommandService,
        "submit_command_job",
        submit_mock,
    )

    response = await embedding_rebuild_router.start_rebuild(
        RebuildRequest(
            mode="existing",
            include_sources=True,
            include_notes=True,
            include_insights=True,
        )
    )

    assert response.command_id == "cmd:existing:mix"
    assert response.total_items == 16
    submit_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_rebuild_with_all_includes_disabled_skips_count_queries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_query_mock = AsyncCallStub()
    monkeypatch.setattr(embedding_rebuild_router, "repo_query", repo_query_mock)
    monkeypatch.setattr(
        embedding_rebuild_router.CommandService,
        "submit_command_job",
        AsyncCallStub(return_value="cmd:none"),
    )

    response = await embedding_rebuild_router.start_rebuild(
        RebuildRequest(
            mode="all",
            include_sources=False,
            include_notes=False,
            include_insights=False,
        )
    )

    assert response.total_items == 0
    repo_query_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_rebuild_status_without_result_dict_skips_progress_and_stats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status = SimpleNamespace(
        status="running",
        result=None,
        created="2026-03-01T00:00:00Z",
        updated="2026-03-01T00:00:10Z",
    )
    monkeypatch.setattr(
        embedding_rebuild_router,
        "get_command_status",
        AsyncCallStub(return_value=status),
    )

    response = await embedding_rebuild_router.get_rebuild_status("cmd:none")

    assert response.progress is None
    assert response.stats is None
    assert response.started_at == "2026-03-01T00:00:00Z"
    assert response.completed_at == "2026-03-01T00:00:10Z"


@pytest.mark.asyncio
async def test_get_rebuild_status_without_progress_keys_sets_only_stats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status = SimpleNamespace(
        status="running",
        result={"sources_submitted": 3, "failed_submissions": 1},
        created=None,
        updated=None,
    )
    monkeypatch.setattr(
        embedding_rebuild_router,
        "get_command_status",
        AsyncCallStub(return_value=status),
    )

    response = await embedding_rebuild_router.get_rebuild_status("cmd:stats")

    assert response.progress is None
    assert response.stats.sources == 3
    assert response.stats.failed == 1
    assert response.stats.notes == 0
    assert response.stats.insights == 0


@pytest.mark.asyncio
async def test_get_note_success_returns_response_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    note = SimpleNamespace(
        id="note:ok",
        title="T",
        content="C",
        note_type="human",
        created="2026-03-01T00:00:00Z",
        updated="2026-03-01T00:01:00Z",
    )
    monkeypatch.setattr(notes_router.Note, "get", AsyncCallStub(return_value=note))

    response = await notes_router.get_note("note:ok")

    assert response.id == "note:ok"
    assert response.title == "T"
    assert response.content == "C"


@pytest.mark.asyncio
async def test_update_note_success_updates_content_and_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    note = SimpleNamespace(
        id="note:1",
        title="old",
        content="old content",
        note_type="human",
        created="2026-03-01T00:00:00Z",
        updated="2026-03-01T00:01:00Z",
        save=AsyncCallStub(return_value="cmd:update"),
    )
    monkeypatch.setattr(notes_router.Note, "get", AsyncCallStub(return_value=note))

    response = await notes_router.update_note(
        "note:1", NoteUpdate(content="new content", note_type="ai")
    )

    assert note.content == "new content"
    assert note.note_type == "ai"
    assert response.command_id == "cmd:update"


@pytest.mark.asyncio
async def test_update_note_unexpected_error_maps_to_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    note = SimpleNamespace(
        id="note:1",
        title="t",
        content="c",
        note_type="human",
        created="2026-03-01T00:00:00Z",
        updated="2026-03-01T00:01:00Z",
        save=AsyncCallStub(side_effect=RuntimeError("save failed")),
    )
    monkeypatch.setattr(notes_router.Note, "get", AsyncCallStub(return_value=note))

    with pytest.raises(HTTPException) as exc_info:
        await notes_router.update_note("note:1", NoteUpdate(title="next"))

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Error updating note: save failed"
