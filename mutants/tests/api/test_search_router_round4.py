import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from packages.core.application.models import AskRequest, SearchRequest
from services.api.routers import search as search_router


class AsyncCallStub:
    def __init__(
        self,
        *,
        return_value: object = None,
        side_effect: object = None,
    ) -> None:
        self.return_value = return_value
        self.side_effect = side_effect
        self.await_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    async def __call__(self, *args: object, **kwargs: object) -> object:
        self.await_calls.append((args, kwargs))
        if isinstance(self.side_effect, Exception):
            raise self.side_effect
        if callable(self.side_effect):
            return self.side_effect(*args, **kwargs)
        return self.return_value

    def assert_awaited_once_with(self, **expected_kwargs: object) -> None:
        assert len(self.await_calls) == 1
        _, kwargs = self.await_calls[0]
        assert kwargs == expected_kwargs


@pytest.mark.asyncio
async def test_search_vector_requires_embedding_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = SearchRequest(
        query="q",
        type="vector",
        limit=5,
        search_sources=True,
        search_notes=True,
        minimum_score=0.2,
    )

    monkey_defaults = SimpleNamespace(default_embedding_model=None)
    monkeypatch.setattr(
        search_router.DefaultModels,
        "get_instance",
        AsyncCallStub(return_value=monkey_defaults),
    )

    with pytest.raises(HTTPException) as exc_info:
        await search_router.search_knowledge_base(request)

    assert exc_info.value.status_code == 400
    assert "Embedding model is not configured" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_search_text_returns_empty_payload_when_backend_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = SearchRequest(
        query="hello",
        type="text",
        limit=3,
        search_sources=False,
        search_notes=True,
        minimum_score=0.2,
    )
    text_search_mock = AsyncCallStub(return_value=None)
    monkeypatch.setattr(search_router, "text_search", text_search_mock)

    response = await search_router.search_knowledge_base(request)

    assert response.results == []
    assert response.total_count == 0
    assert response.search_type == "text"
    text_search_mock.assert_awaited_once_with(
        keyword="hello",
        results=3,
        source=False,
        note=True,
    )


@pytest.mark.asyncio
async def test_search_text_wraps_unexpected_backend_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = SearchRequest(
        query="hello",
        type="text",
        limit=3,
        search_sources=False,
        search_notes=True,
        minimum_score=0.2,
    )
    monkeypatch.setattr(
        search_router,
        "text_search",
        AsyncCallStub(side_effect=RuntimeError("db exploded")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await search_router.search_knowledge_base(request)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Search failed"


@pytest.mark.asyncio
async def test_stream_ask_response_streams_all_event_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    strategy = SimpleNamespace(
        reasoning="r",
        searches=[SimpleNamespace(term="alpha", instructions="find alpha")],
    )

    async def _fake_astream(*_args, **_kwargs):
        yield {"agent": {"strategy": strategy}}
        yield {"provide_answer": {"answers": ["A1"]}}
        yield {"write_final_answer": {"final_answer": "FINAL"}}

    monkeypatch.setattr(search_router.ask_graph, "astream", _fake_astream)

    strategy_model = SimpleNamespace(id="m-strategy")
    answer_model = SimpleNamespace(id="m-answer")
    final_model = SimpleNamespace(id="m-final")

    chunks: list[str] = []
    async for chunk in search_router.stream_ask_response(
        "question", strategy_model, answer_model, final_model
    ):
        chunks.append(chunk)

    events = [
        json.loads(chunk.removeprefix("data: ").strip())
        for chunk in chunks
        if chunk.startswith("data: ")
    ]
    assert [event["type"] for event in events] == [
        "strategy",
        "answer",
        "final_answer",
        "complete",
    ]
    assert events[-1]["final_answer"] == "FINAL"


@pytest.mark.asyncio
async def test_stream_ask_response_emits_error_event_on_graph_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _failing_astream(*_args, **_kwargs):
        raise RuntimeError("graph failure")
        yield  # pragma: no cover

    monkeypatch.setattr(search_router.ask_graph, "astream", _failing_astream)

    strategy_model = SimpleNamespace(id="m-strategy")
    answer_model = SimpleNamespace(id="m-answer")
    final_model = SimpleNamespace(id="m-final")

    chunks: list[str] = []
    async for chunk in search_router.stream_ask_response(
        "question", strategy_model, answer_model, final_model
    ):
        chunks.append(chunk)

    events = [
        json.loads(chunk.removeprefix("data: ").strip())
        for chunk in chunks
        if chunk.startswith("data: ")
    ]
    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert isinstance(events[0]["message"], str)
    assert events[0]["message"]


@pytest.mark.asyncio
async def test_ask_simple_raises_when_no_final_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = SimpleNamespace(id="model-id", type="language")
    monkeypatch.setattr(search_router.Model, "get", AsyncCallStub(return_value=model))
    monkeypatch.setattr(
        search_router,
        "_require_explicit_embedding_model",
        AsyncCallStub(return_value=None),
    )

    async def _fake_astream(*_args, **_kwargs):
        yield {"agent": {"strategy": {"reasoning": "r", "searches": []}}}

    monkeypatch.setattr(search_router.ask_graph, "astream", _fake_astream)

    request = AskRequest(
        question="q",
        strategy_model="s",
        answer_model="a",
        final_answer_model="f",
    )
    with pytest.raises(HTTPException) as exc_info:
        await search_router.ask_knowledge_base_simple(request)

    assert exc_info.value.status_code == 500
    assert "No answer generated" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_ask_endpoint_returns_400_for_missing_strategy_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(search_router.Model, "get", AsyncCallStub(return_value=None))
    request = AskRequest(
        question="q",
        strategy_model="missing-strategy",
        answer_model="a",
        final_answer_model="f",
    )

    with pytest.raises(HTTPException) as exc_info:
        await search_router.ask_knowledge_base(request)

    assert exc_info.value.status_code == 400
    assert "Strategy model missing-strategy not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_ask_endpoint_rejects_non_language_strategy_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    non_language_model = SimpleNamespace(id="model:embed", type="embedding")
    monkeypatch.setattr(
        search_router.Model, "get", AsyncCallStub(return_value=non_language_model)
    )
    request = AskRequest(
        question="q",
        strategy_model="model:embed",
        answer_model="a",
        final_answer_model="f",
    )

    with pytest.raises(HTTPException) as exc_info:
        await search_router.ask_knowledge_base(request)

    assert exc_info.value.status_code == 400
    assert "must be a language model" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_ask_endpoint_uses_sse_media_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    strategy_model = SimpleNamespace(id="m-strategy", type="language")
    answer_model = SimpleNamespace(id="m-answer", type="language")
    final_model = SimpleNamespace(id="m-final", type="language")
    monkeypatch.setattr(
        search_router,
        "_resolve_ask_models",
        AsyncCallStub(return_value=(strategy_model, answer_model, final_model)),
    )
    monkeypatch.setattr(
        search_router,
        "_require_explicit_embedding_model",
        AsyncCallStub(return_value=None),
    )

    async def _fake_stream(*_args, **_kwargs):
        yield "data: {}\n\n"

    monkeypatch.setattr(search_router, "stream_ask_response", _fake_stream)

    response = await search_router.ask_knowledge_base(
        AskRequest(
            question="q",
            strategy_model="s",
            answer_model="a",
            final_answer_model="f",
        )
    )
    assert response.media_type == "text/event-stream"
