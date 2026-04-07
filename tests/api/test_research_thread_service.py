from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from packages.core.application.models import (
    ResearchThreadCreateRequest,
    ResearchThreadEntryRequest,
)
from packages.core.database.repository import ensure_record_id
from packages.core.exceptions import InvalidInputError, NotFoundError
from services.api import research_thread_service as research_thread_service_module


@pytest.mark.asyncio
async def test_create_and_list_research_threads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_create_mock = AsyncMock(
        return_value=[
            {
                "id": "research_thread:1",
                "notebook": "notebook:1",
                "title": "Insight thread",
                "seed_kind": "insight",
                "source_ids": ["source:1"],
                "note_ids": [],
                "entries": [{"content": "answer"}],
                "created": "2026-01-01T00:00:00+00:00",
                "updated": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    monkeypatch.setattr(
        research_thread_service_module.research_thread_service,
        "_get_notebook_or_raise",
        AsyncMock(return_value=SimpleNamespace(id="notebook:1")),
    )
    monkeypatch.setattr(
        research_thread_service_module,
        "repo_create",
        repo_create_mock,
    )
    monkeypatch.setattr(
        research_thread_service_module.ResearchThread,
        "list_by_notebook",
        AsyncMock(
            return_value=[
                SimpleNamespace(
                    model_dump=lambda: {
                        "id": "research_thread:1",
                        "notebook": "notebook:1",
                        "title": "Insight thread",
                        "seed_kind": "insight",
                        "source_ids": ["source:1"],
                        "note_ids": [],
                        "entries": [{"content": "answer"}],
                        "created": "2026-01-01T00:00:00+00:00",
                        "updated": "2026-01-01T00:00:00+00:00",
                    }
                )
            ]
        ),
    )

    created = (
        await research_thread_service_module.research_thread_service.create_thread(
            "notebook:1",
            ResearchThreadCreateRequest(
                title="Insight thread",
                seed_kind="insight",
                question="Continue researching this summary",
                answer="Key insight",
                insight_id="source_insight:1",
                insight_type="summary",
                source_ids=["source:1"],
            ),
        )
    )
    listed = await research_thread_service_module.research_thread_service.list_threads_by_notebook(
        "notebook:1"
    )

    assert created.id == "research_thread:1"
    assert created.seed_kind == "insight"
    assert created.entry_count == 1
    assert listed[0].id == "research_thread:1"
    assert listed[0].seed_kind == "insight"
    persisted = repo_create_mock.await_args.args[1]
    assert persisted["seed_kind"] == "insight"
    assert persisted["entries"][0]["entry_type"] == "insight_snapshot"
    assert (
        persisted["entries"][0]["metadata"]["question"]
        == "Continue researching this summary"
    )
    assert persisted["entries"][0]["metadata"]["search_results"] == []
    assert persisted["entries"][0]["metadata"]["insight_id"] == "source_insight:1"
    assert persisted["entries"][0]["metadata"]["insight_type"] == "summary"


@pytest.mark.asyncio
async def test_get_append_and_create_draft_from_thread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        research_thread_service_module,
        "repo_query",
        AsyncMock(
            side_effect=[
                [
                    {
                        "id": "research_thread:1",
                        "notebook": "notebook:1",
                        "title": "Thread One",
                        "seed_kind": "search",
                        "source_ids": ["source:1", "source:2"],
                        "note_ids": ["note:1"],
                        "entries": [{"content": "first"}, {"content": "second"}],
                        "created": "2026-01-01T00:00:00+00:00",
                        "updated": "2026-01-01T00:00:00+00:00",
                    }
                ],
                [
                    {
                        "id": "research_thread:1",
                        "notebook": "notebook:1",
                        "title": "Thread One",
                        "seed_kind": "search",
                        "source_ids": ["source:1", "source:2"],
                        "note_ids": ["note:1"],
                        "entries": [{"content": "first"}, {"content": "second"}],
                        "created": "2026-01-01T00:00:00+00:00",
                        "updated": "2026-01-01T00:00:00+00:00",
                    }
                ],
            ]
        ),
    )
    monkeypatch.setattr(
        research_thread_service_module.research_thread_service,
        "get_thread",
        AsyncMock(
            side_effect=[
                research_thread_service_module.ResearchThreadResponse(
                    id="research_thread:1",
                    notebook_id="notebook:1",
                    title="Thread One",
                    seed_kind="search",
                    source_ids=["source:1"],
                    note_ids=[],
                    entries=[{"content": "first"}],
                    entry_count=1,
                    created="2026-01-01T00:00:00+00:00",
                    updated="2026-01-01T00:00:00+00:00",
                ),
                research_thread_service_module.ResearchThreadResponse(
                    id="research_thread:1",
                    notebook_id="notebook:1",
                    title="Thread One",
                    seed_kind="search",
                    source_ids=["source:1"],
                    note_ids=["note:1"],
                    entries=[{"content": "first"}],
                    entry_count=1,
                    created="2026-01-01T00:00:00+00:00",
                    updated="2026-01-01T00:00:00+00:00",
                ),
                research_thread_service_module.ResearchThreadResponse(
                    id="research_thread:1",
                    notebook_id="notebook:1",
                    title="Thread One",
                    seed_kind="search",
                    source_ids=["source:1"],
                    note_ids=["note:1"],
                    entries=[{"content": "first"}],
                    entry_count=1,
                    created="2026-01-01T00:00:00+00:00",
                    updated="2026-01-01T00:00:00+00:00",
                ),
            ]
        ),
    )
    monkeypatch.setattr(
        research_thread_service_module.draft_service,
        "create_draft",
        AsyncMock(return_value=SimpleNamespace(id="draft:1")),
    )

    got = await research_thread_service_module.research_thread_service.get_thread(
        "research_thread:1"
    )
    updated = await research_thread_service_module.research_thread_service.append_entry(
        "research_thread:1",
        ResearchThreadEntryRequest(
            entry_type="answer_snapshot",
            title="A2",
            content="second",
            source_ids=["source:2"],
            note_ids=["note:1"],
        ),
    )
    draft = await research_thread_service_module.research_thread_service.create_draft_from_thread(
        "research_thread:1"
    )

    assert got.id == "research_thread:1"
    assert updated.entry_count == 2
    assert draft.id == "draft:1"
    research_thread_service_module.draft_service.create_draft.assert_awaited_once()
    create_args = research_thread_service_module.draft_service.create_draft.await_args
    assert create_args.args[0] == "notebook:1"
    assert create_args.args[1].thread_ids == ["research_thread:1"]
    append_payload = research_thread_service_module.repo_query.await_args.args[1][
        "data"
    ]
    assert [item.table_name for item in append_payload["source_ids"]] == [
        "source",
        "source",
    ]
    assert [str(item.id) for item in append_payload["source_ids"]] == ["1", "2"]
    assert [item.table_name for item in append_payload["note_ids"]] == ["note"]
    assert [str(item.id) for item in append_payload["note_ids"]] == ["1"]


@pytest.mark.asyncio
async def test_create_draft_from_thread_requires_source_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        research_thread_service_module.research_thread_service,
        "get_thread",
        AsyncMock(
            return_value=research_thread_service_module.ResearchThreadResponse(
                id="research_thread:1",
                notebook_id="notebook:1",
                title="Thread One",
                seed_kind="search",
                source_ids=[],
                note_ids=[],
                entries=[],
                entry_count=0,
                created="2026-01-01T00:00:00+00:00",
                updated="2026-01-01T00:00:00+00:00",
            )
        ),
    )

    with pytest.raises(
        InvalidInputError, match="Research thread must include at least one source"
    ):
        await research_thread_service_module.research_thread_service.create_draft_from_thread(
            "research_thread:1"
        )


@pytest.mark.asyncio
async def test_get_thread_raises_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        research_thread_service_module,
        "repo_query",
        AsyncMock(return_value=[]),
    )

    with pytest.raises(NotFoundError, match="Research thread not found"):
        await research_thread_service_module.research_thread_service.get_thread(
            "research_thread:404"
        )
