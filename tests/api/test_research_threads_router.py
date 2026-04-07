from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from packages.core.application.models import (
    ResearchThreadCreateRequest,
    ResearchThreadEntryRequest,
)
from packages.core.exceptions import InvalidInputError, NotFoundError
from services.api.routers import research_threads as research_threads_router


@pytest.mark.asyncio
async def test_research_threads_router_calls_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        research_threads_router.research_thread_service,
        "create_thread",
        AsyncMock(
            return_value={
                "id": "research_thread:1",
                "notebook_id": "notebook:1",
                "title": "Insight thread",
                "seed_kind": "insight",
                "source_ids": ["source:1"],
                "note_ids": [],
                "entries": [],
                "entry_count": 0,
                "created": "2026-01-01T00:00:00+00:00",
                "updated": "2026-01-01T00:00:00+00:00",
            }
        ),
    )
    monkeypatch.setattr(
        research_threads_router.research_thread_service,
        "list_threads_by_notebook",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        research_threads_router.research_thread_service,
        "create_draft_from_thread",
        AsyncMock(return_value={"id": "draft:1"}),
    )
    monkeypatch.setattr(
        research_threads_router.research_thread_service,
        "append_entry",
        AsyncMock(
            return_value={
                "id": "research_thread:1",
                "notebook_id": "notebook:1",
                "title": "Insight thread",
                "seed_kind": "insight",
                "source_ids": ["source:1", "source:2"],
                "note_ids": [],
                "entries": [{"content": "old"}, {"content": "new"}],
                "entry_count": 2,
                "created": "2026-01-01T00:00:00+00:00",
                "updated": "2026-01-01T00:00:00+00:00",
            }
        ),
    )

    created = await research_threads_router.create_research_thread(
        "notebook:1",
        ResearchThreadCreateRequest(
            title="Insight thread",
            seed_kind="insight",
            insight_id="source_insight:1",
            insight_type="summary",
        ),
    )
    listed = await research_threads_router.list_research_threads("notebook:1")
    appended = await research_threads_router.append_research_thread_entry(
        "research_thread:1",
        ResearchThreadEntryRequest(
            entry_type="search_result",
            title="Result",
            content="new",
            source_ids=["source:2"],
        ),
    )
    draft = await research_threads_router.create_draft_from_thread("research_thread:1")

    assert created["id"] == "research_thread:1"
    assert created["seed_kind"] == "insight"
    assert listed == []
    assert appended["entry_count"] == 2
    assert draft["id"] == "draft:1"


@pytest.mark.asyncio
async def test_research_threads_router_maps_domain_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        research_threads_router.research_thread_service,
        "create_thread",
        AsyncMock(side_effect=InvalidInputError("bad thread")),
    )
    monkeypatch.setattr(
        research_threads_router.research_thread_service,
        "get_thread",
        AsyncMock(side_effect=NotFoundError("missing thread")),
    )

    with pytest.raises(HTTPException) as create_exc:
        await research_threads_router.create_research_thread(
            "notebook:1",
            ResearchThreadCreateRequest(title="Bad", seed_kind="search"),
        )
    with pytest.raises(HTTPException) as get_exc:
        await research_threads_router.get_research_thread("research_thread:404")

    assert create_exc.value.status_code == 400
    assert get_exc.value.status_code == 404


def test_research_thread_request_requires_insight_id_for_insight_seed() -> None:
    with pytest.raises(ValueError, match="insight_id is required"):
        ResearchThreadCreateRequest(title="Insight thread", seed_kind="insight")
