from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.responses import Response

from packages.core.application.models import DraftCreateRequest, DraftRerunRequest
from packages.core.exceptions import InvalidInputError, NotFoundError
from services.api.routers import drafts as drafts_router


@pytest.mark.asyncio
async def test_drafts_router_calls_service_and_returns_markdown_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        drafts_router.draft_service,
        "create_draft",
        AsyncMock(
            return_value={
                "id": "draft:1",
                "notebook_id": "notebook:1",
                "title": "Notebook Draft",
                "status": "completed",
                "model_id": "model-draft",
                "language": "zh-CN",
                "near_dedup_threshold": 0.97,
                "source_ids": ["source:1"],
                "note_ids": [],
                "thread_ids": [],
                "version": 1,
                "metrics": {
                    "coverage_rate": 1.0,
                    "missing_count": 0,
                    "duplicate_count": 0,
                    "uncited_claims_count": 0,
                    "dedup_group_count": 0,
                    "unknown_pid_count": 0,
                    "unclassified_count": 0,
                },
                "coverage_json": {},
                "dedup_json": {},
                "result_markdown": "# Draft",
                "source_paragraphs": [],
                "sections": [],
                "claims": [],
                "dedup_entries": [],
                "verified_brief_snapshot": None,
                "created": "2026-01-01T00:00:00+00:00",
                "updated": "2026-01-01T00:00:00+00:00",
            }
        ),
    )
    monkeypatch.setattr(
        drafts_router.draft_service,
        "list_drafts_by_notebook",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        drafts_router.draft_service,
        "get_draft",
        AsyncMock(
            return_value={
                "id": "draft:1",
                "notebook_id": "notebook:1",
                "title": "Notebook Draft",
                "status": "completed",
                "model_id": "model-draft",
                "language": "zh-CN",
                "near_dedup_threshold": 0.97,
                "source_ids": ["source:1"],
                "note_ids": [],
                "thread_ids": [],
                "version": 1,
                "metrics": {
                    "coverage_rate": 1.0,
                    "missing_count": 0,
                    "duplicate_count": 0,
                    "uncited_claims_count": 0,
                    "dedup_group_count": 0,
                    "unknown_pid_count": 0,
                    "unclassified_count": 0,
                },
                "coverage_json": {},
                "dedup_json": {},
                "result_markdown": "# Draft",
                "source_paragraphs": [],
                "sections": [],
                "claims": [],
                "dedup_entries": [],
                "verified_brief_snapshot": None,
                "created": "2026-01-01T00:00:00+00:00",
                "updated": "2026-01-01T00:00:00+00:00",
            }
        ),
    )
    monkeypatch.setattr(
        drafts_router.draft_service,
        "rerun_draft",
        AsyncMock(
            return_value={
                "id": "draft:2",
                "notebook_id": "notebook:1",
                "title": "Notebook Draft",
                "status": "completed",
                "model_id": "model-draft",
                "language": "zh-CN",
                "near_dedup_threshold": 0.97,
                "source_ids": ["source:1"],
                "note_ids": [],
                "thread_ids": [],
                "version": 2,
                "parent_draft_id": "draft:1",
                "metrics": {
                    "coverage_rate": 1.0,
                    "missing_count": 0,
                    "duplicate_count": 0,
                    "uncited_claims_count": 0,
                    "dedup_group_count": 0,
                    "unknown_pid_count": 0,
                    "unclassified_count": 0,
                },
                "coverage_json": {},
                "dedup_json": {},
                "result_markdown": "# Draft",
                "source_paragraphs": [],
                "sections": [],
                "claims": [],
                "dedup_entries": [],
                "verified_brief_snapshot": None,
                "created": "2026-01-01T00:00:00+00:00",
                "updated": "2026-01-01T00:00:00+00:00",
            }
        ),
    )
    monkeypatch.setattr(
        drafts_router.draft_service,
        "get_markdown",
        AsyncMock(return_value="# Notebook Draft"),
    )
    monkeypatch.setattr(
        drafts_router.draft_service,
        "get_export_bundle",
        AsyncMock(return_value=("bundle.zip", b"zip-bytes")),
    )
    monkeypatch.setattr(
        drafts_router.draft_service,
        "verify_draft",
        AsyncMock(
            return_value={
                "id": "draft:2",
                "notebook_id": "notebook:1",
                "title": "Notebook Draft",
                "status": "verified",
                "model_id": "model-draft",
                "language": "zh-CN",
                "near_dedup_threshold": 0.97,
                "source_ids": ["source:1"],
                "note_ids": [],
                "thread_ids": [],
                "version": 2,
                "parent_draft_id": "draft:1",
                "metrics": {
                    "coverage_rate": 1.0,
                    "missing_count": 0,
                    "duplicate_count": 0,
                    "uncited_claims_count": 0,
                    "dedup_group_count": 0,
                    "unknown_pid_count": 0,
                    "unclassified_count": 0,
                },
                "coverage_json": {},
                "dedup_json": {},
                "result_markdown": "# Draft",
                "source_paragraphs": [],
                "sections": [],
                "claims": [],
                "dedup_entries": [],
                "verified_brief_snapshot": {"draft_id": "draft:2", "version": 2},
                "created": "2026-01-01T00:00:00+00:00",
                "updated": "2026-01-01T00:00:00+00:00",
            }
        ),
    )

    created = await drafts_router.create_draft(
        "notebook:1",
        DraftCreateRequest(source_ids=["source:1"]),
    )
    listed = await drafts_router.list_notebook_drafts("notebook:1")
    fetched = await drafts_router.get_draft("draft:1")
    rerun = await drafts_router.rerun_draft("draft:1", DraftRerunRequest())
    verified = await drafts_router.verify_draft("draft:2")
    markdown = await drafts_router.get_draft_markdown("draft:1")
    bundle = await drafts_router.get_draft_bundle("draft:1")

    assert created["id"] == "draft:1"
    assert listed == []
    assert fetched["title"] == "Notebook Draft"
    assert rerun["parent_draft_id"] == "draft:1"
    assert verified["status"] == "verified"
    assert verified["verified_brief_snapshot"]["version"] == 2
    assert isinstance(markdown, Response)
    assert markdown.body == b"# Notebook Draft"
    assert (
        'attachment; filename="draft-draft_1.md"'
        == markdown.headers["Content-Disposition"]
    )
    assert isinstance(bundle, Response)
    assert bundle.body == b"zip-bytes"
    assert bundle.headers["Content-Disposition"] == 'attachment; filename="bundle.zip"'
    assert bundle.media_type == "application/zip"


@pytest.mark.asyncio
async def test_drafts_router_maps_domain_errors_to_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        drafts_router.draft_service,
        "create_draft",
        AsyncMock(side_effect=InvalidInputError("bad draft")),
    )
    monkeypatch.setattr(
        drafts_router.draft_service,
        "get_draft",
        AsyncMock(side_effect=NotFoundError("missing draft")),
    )

    with pytest.raises(HTTPException) as create_exc:
        await drafts_router.create_draft(
            "notebook:1",
            DraftCreateRequest(source_ids=["source:1"]),
        )
    with pytest.raises(HTTPException) as get_exc:
        await drafts_router.get_draft("draft:404")

    assert create_exc.value.status_code == 400
    assert get_exc.value.status_code == 404
