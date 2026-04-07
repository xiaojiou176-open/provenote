import io
import json
import zipfile
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from packages.core.application.models import DraftCreateRequest, DraftRerunRequest
from packages.core.exceptions import InvalidInputError
from services.api import draft_service as draft_service_module


@pytest.mark.asyncio
async def test_create_draft_persists_graph_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notebook = SimpleNamespace(name="Alpha Notebook")
    source = SimpleNamespace(id="source:1", title="Alpha", full_text="First paragraph")
    repo_create_mock = AsyncMock(
        return_value=[
            {
                "id": "draft:1",
                "notebook": "notebook:1",
                "title": "Alpha Draft",
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
                "result_markdown": "# Alpha Draft",
                "source_paragraphs": [{"pid": "S001-P000001"}],
                "sections": [],
                "claims": [],
                "dedup_entries": [],
                "created": "2026-01-01T00:00:00+00:00",
                "updated": "2026-01-01T00:00:00+00:00",
            }
        ]
    )

    monkeypatch.setattr(
        draft_service_module.draft_service,
        "_get_notebook_or_raise",
        AsyncMock(return_value=notebook),
    )
    monkeypatch.setattr(
        draft_service_module.draft_service,
        "_resolve_selected_sources",
        AsyncMock(return_value=[source]),
    )
    monkeypatch.setattr(
        draft_service_module.notebook_draft_graph,
        "ainvoke",
        AsyncMock(
            return_value={
                "output": {
                    "model_id": "model-draft",
                    "language": "zh-CN",
                    "near_dedup_threshold": 0.97,
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
                    "result_markdown": "# Alpha Draft",
                    "source_paragraphs": [{"pid": "S001-P000001"}],
                    "sections": [],
                    "claims": [],
                    "dedup_entries": [],
                }
            }
        ),
    )
    monkeypatch.setattr(draft_service_module, "repo_create", repo_create_mock)

    response = await draft_service_module.draft_service.create_draft(
        "notebook:1",
        DraftCreateRequest(
            title="Alpha Draft",
            source_ids=["source:1"],
            thread_ids=["thread-1"],
        ),
    )

    assert response.id == "draft:1"
    assert response.title == "Alpha Draft"
    assert response.source_ids == ["source:1"]
    persisted = repo_create_mock.await_args.args[1]
    assert persisted["title"] == "Alpha Draft"
    assert str(persisted["source_ids"][0]).startswith("source:")
    assert "1" in str(persisted["source_ids"][0])
    assert str(persisted["thread_ids"][0]).startswith("research_thread:")
    assert "thread-1" in str(persisted["thread_ids"][0])


@pytest.mark.asyncio
async def test_resolve_selected_sources_refetches_full_source_when_notebook_view_is_lightweight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lightweight_source = SimpleNamespace(id="source:1", full_text=None)
    notebook = SimpleNamespace(get_sources=AsyncMock(return_value=[lightweight_source]))

    monkeypatch.setattr(
        draft_service_module.draft_service,
        "_get_notebook_or_raise",
        AsyncMock(return_value=notebook),
    )
    full_source = SimpleNamespace(
        id="source:1",
        full_text="Recovered source body",
    )
    monkeypatch.setattr(
        draft_service_module.Source,
        "get",
        AsyncMock(return_value=full_source),
    )

    resolved = await draft_service_module.draft_service._resolve_selected_sources(
        "notebook:1",
        ["source:1"],
    )

    assert resolved == [full_source]
    draft_service_module.Source.get.assert_awaited_once_with("source:1")


@pytest.mark.asyncio
async def test_create_draft_rejects_sources_outside_notebook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notebook = SimpleNamespace(
        get_sources=AsyncMock(
            return_value=[SimpleNamespace(id="source:1", title="Alpha")]
        )
    )
    monkeypatch.setattr(
        draft_service_module.draft_service,
        "_get_notebook_or_raise",
        AsyncMock(return_value=notebook),
    )

    with pytest.raises(
        InvalidInputError, match="Draft sources must belong to the notebook"
    ):
        await draft_service_module.draft_service._resolve_selected_sources(
            "notebook:1", ["source:2"]
        )


def test_to_response_normalizes_missing_timestamps_to_empty_strings() -> None:
    response = draft_service_module.draft_service._to_response(
        {
            "id": "draft:missing-time",
            "notebook": "notebook:1",
            "title": "Draft",
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
            "created": None,
            "updated": None,
        }
    )

    assert response.created == ""
    assert response.updated == ""


def test_to_response_treats_stringified_none_timestamps_as_empty_strings() -> None:
    response = draft_service_module.draft_service._to_response(
        {
            "id": "draft:string-none",
            "notebook": "notebook:1",
            "title": "Draft",
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
            "created": "None",
            "updated": "null",
        }
    )

    assert response.created == ""
    assert response.updated == ""


@pytest.mark.asyncio
async def test_rerun_draft_creates_child_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_create_mock = AsyncMock(
        return_value=[
            {
                "id": "draft:2",
                "notebook": "notebook:1",
                "title": "Alpha Draft",
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
                "result_markdown": "# Alpha Draft",
                "source_paragraphs": [],
                "sections": [],
                "claims": [],
                "dedup_entries": [],
                "created": "2026-01-01T00:00:00+00:00",
                "updated": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    monkeypatch.setattr(
        draft_service_module.draft_service,
        "get_draft",
        AsyncMock(
            return_value=SimpleNamespace(
                id="draft:1",
                notebook_id="notebook:1",
                title="Alpha Draft",
                source_ids=["source:1"],
                note_ids=[],
                thread_ids=[],
                model_id="model-draft",
                language="zh-CN",
                near_dedup_threshold=0.97,
                version=1,
            )
        ),
    )
    monkeypatch.setattr(
        draft_service_module.draft_service,
        "_build_draft_record",
        AsyncMock(return_value={"title": "Alpha Draft", "version": 2}),
    )
    monkeypatch.setattr(draft_service_module, "repo_create", repo_create_mock)

    response = await draft_service_module.draft_service.rerun_draft(
        "draft:1",
        DraftRerunRequest(),
    )

    assert response.id == "draft:2"
    assert response.parent_draft_id == "draft:1"
    draft_service_module.draft_service._build_draft_record.assert_awaited_once()
    build_kwargs = (
        draft_service_module.draft_service._build_draft_record.await_args.kwargs
    )
    assert build_kwargs["parent_draft_id"] == "draft:1"
    assert build_kwargs["version"] == 2


@pytest.mark.asyncio
async def test_draft_service_helpers_cover_query_and_verify_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert draft_service_module.DraftService._normalize_note_id("abc") == "note:abc"
    assert (
        draft_service_module.DraftService._normalize_thread_id("session-1")
        == "research_thread:session-1"
    )
    assert (
        draft_service_module.DraftService._record_to_string({"id": "draft:1"})
        == "draft:1"
    )
    assert draft_service_module.DraftService._record_list_to_strings("draft:1") == [
        "draft:1"
    ]

    monkeypatch.setattr(
        draft_service_module.draft_service,
        "_get_notebook_or_raise",
        AsyncMock(return_value=SimpleNamespace(id="notebook:1")),
    )
    monkeypatch.setattr(
        draft_service_module.Draft,
        "list_by_notebook",
        AsyncMock(
            return_value=[
                SimpleNamespace(
                    model_dump=lambda: {
                        "id": "draft:1",
                        "notebook": "notebook:1",
                        "title": "Alpha Draft",
                        "status": "completed",
                        "model_id": "model-draft",
                        "language": "zh-CN",
                        "near_dedup_threshold": 0.97,
                        "source_ids": ["source:1"],
                        "note_ids": [],
                        "thread_ids": [],
                        "version": 1,
                        "metrics": {"coverage_rate": 0.5},
                        "coverage_json": {
                            "coverage_rate": 0.5,
                            "missing_pids": [],
                            "duplicate_pids": [],
                            "unknown_pids": [],
                            "unclassified_pids": [],
                        },
                        "dedup_json": {"group_count": 0},
                        "result_markdown": "# Draft",
                        "source_paragraphs": [],
                        "sections": [],
                        "claims": [],
                        "dedup_entries": [],
                        "created": "2026-01-01T00:00:00+00:00",
                        "updated": "2026-01-01T00:00:00+00:00",
                    }
                )
            ]
        ),
    )
    monkeypatch.setattr(
        draft_service_module,
        "repo_query",
        AsyncMock(
            side_effect=[
                [
                    {
                        "id": "draft:2",
                        "notebook": "notebook:1",
                        "title": "Beta Draft",
                        "status": "completed",
                        "model_id": "model-draft",
                        "language": "zh-CN",
                        "near_dedup_threshold": 0.97,
                        "source_ids": ["source:2"],
                        "note_ids": [],
                        "thread_ids": [],
                        "version": 1,
                        "metrics": {"coverage_rate": 1.0},
                        "coverage_json": {
                            "coverage_rate": 1.0,
                            "missing_pids": [],
                            "duplicate_pids": [],
                            "unknown_pids": [],
                            "unclassified_pids": [],
                        },
                        "dedup_json": {"group_count": 0},
                        "result_markdown": "# Draft",
                        "source_paragraphs": [],
                        "sections": [],
                        "claims": [],
                        "dedup_entries": [],
                        "created": "2026-01-01T00:00:00+00:00",
                        "updated": "2026-01-01T00:00:00+00:00",
                    }
                ],
                [
                    {
                        "id": "draft:2",
                        "notebook": "notebook:1",
                        "title": "Beta Draft",
                        "status": "completed",
                        "model_id": "model-draft",
                        "language": "zh-CN",
                        "near_dedup_threshold": 0.97,
                        "source_ids": ["source:2"],
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
                        "coverage_json": {
                            "coverage_rate": 1.0,
                            "missing_pids": [],
                            "duplicate_pids": [],
                            "unknown_pids": [],
                            "unclassified_pids": [],
                        },
                        "dedup_json": {"group_count": 0},
                        "result_markdown": "# Draft",
                        "source_paragraphs": [],
                        "sections": [],
                        "claims": [],
                        "dedup_entries": [],
                        "created": "2026-01-01T00:00:00+00:00",
                        "updated": "2026-01-01T00:00:00+00:00",
                    }
                ],
                [
                    {
                        "id": "draft:2",
                        "notebook": "notebook:1",
                        "title": "Beta Draft",
                        "status": "verified",
                        "model_id": "model-draft",
                        "language": "zh-CN",
                        "near_dedup_threshold": 0.97,
                        "source_ids": ["source:2"],
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
                        "coverage_json": {
                            "coverage_rate": 1.0,
                            "missing_pids": [],
                            "duplicate_pids": [],
                            "unknown_pids": [],
                            "unclassified_pids": [],
                        },
                        "dedup_json": {"group_count": 0},
                        "result_markdown": "# Draft",
                        "source_paragraphs": [],
                        "sections": [],
                        "claims": [],
                        "dedup_entries": [],
                        "verified_brief_snapshot": {"draft_id": "draft:2"},
                        "created": "2026-01-01T00:00:00+00:00",
                        "updated": "2026-01-01T00:00:00+00:00",
                    }
                ],
                [
                    {
                        "id": "draft:2",
                        "notebook": "notebook:1",
                        "title": "Beta Draft",
                        "status": "verified",
                        "model_id": "model-draft",
                        "language": "zh-CN",
                        "near_dedup_threshold": 0.97,
                        "source_ids": ["source:2"],
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
                        "coverage_json": {
                            "coverage_rate": 1.0,
                            "missing_pids": [],
                            "duplicate_pids": [],
                            "unknown_pids": [],
                            "unclassified_pids": [],
                        },
                        "dedup_json": {"group_count": 0},
                        "result_markdown": "# Draft",
                        "source_paragraphs": [],
                        "sections": [],
                        "claims": [],
                        "dedup_entries": [],
                        "verified_brief_snapshot": {"draft_id": "draft:2"},
                        "created": "2026-01-01T00:00:00+00:00",
                        "updated": "2026-01-01T00:00:00+00:00",
                    }
                ],
            ]
        ),
    )

    listed = await draft_service_module.draft_service.list_drafts_by_notebook(
        "notebook:1"
    )
    got = await draft_service_module.draft_service.get_draft("draft:2")
    markdown = await draft_service_module.draft_service.get_markdown("draft:2")
    verified = await draft_service_module.draft_service.verify_draft("draft:2")

    assert listed[0].id == "draft:1"
    assert got.id == "draft:2"
    assert markdown == "# Draft"
    assert verified.status == "verified"
    verify_payload = draft_service_module.repo_query.await_args_list[3].args[1]["data"]
    assert verify_payload["verified_brief_snapshot"]["draft_id"] == "draft:2"
    assert verify_payload["verified_brief_snapshot"]["title"] == "Beta Draft"
    assert verify_payload["verified_brief_snapshot"]["version"] == 1
    assert verify_payload["verified_brief_snapshot"]["result_markdown"] == "# Draft"
    assert verify_payload["verified_brief_snapshot"]["metrics"]["coverage_rate"] == 1.0
    assert verify_payload["verified_brief_snapshot"]["metrics"]["missing_count"] == 0


@pytest.mark.asyncio
async def test_get_export_bundle_packages_markdown_metadata_and_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draft = SimpleNamespace(
        id="draft:bundle",
        notebook_id="notebook:1",
        title="Bundle Draft",
        status="verified",
        model_id="model-draft",
        language="en-US",
        near_dedup_threshold=0.97,
        source_ids=["source:1"],
        note_ids=[],
        thread_ids=["research_thread:1"],
        version=3,
        parent_draft_id="draft:2",
        metrics=SimpleNamespace(model_dump=lambda: {"coverage_rate": 0.88}),
        coverage_json={"coverage_rate": 0.88},
        dedup_json={"group_count": 1},
        result_markdown="# Bundle Draft",
        source_paragraphs=[{"pid": "S001-P000001"}],
        sections=[{"title": "Summary", "source_pids": ["S001-P000001"]}],
        claims=[{"text": "Claim", "source_pids": ["S001-P000001"]}],
        dedup_entries=[],
        verified_brief_snapshot={"draft_id": "draft:bundle", "version": 3},
        created="2026-01-01T00:00:00+00:00",
        updated="2026-01-01T00:00:00+00:00",
    )
    monkeypatch.setattr(
        draft_service_module.draft_service,
        "get_draft",
        AsyncMock(return_value=draft),
    )
    monkeypatch.setattr(
        draft_service_module.Source,
        "get",
        AsyncMock(
            return_value=SimpleNamespace(
                title="Source One",
                topics=["alpha"],
                embedded=True,
                insights_count=2,
            )
        ),
    )

    filename, payload = await draft_service_module.draft_service.get_export_bundle(
        "draft:bundle"
    )

    assert filename.endswith(".zip")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = set(archive.namelist())
        assert {
            "draft.md",
            "metadata.json",
            "metrics.json",
            "pid_summary.json",
            "source_manifest.json",
            "sections.json",
            "claims.json",
            "coverage.json",
            "dedup.json",
            "verified_snapshot.json",
            "README.txt",
        }.issubset(members)
        assert archive.read("draft.md").decode("utf-8") == "# Bundle Draft"
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        assert metadata["draft_id"] == "draft:bundle"
        assert metadata["version"] == 3
        source_manifest = json.loads(
            archive.read("source_manifest.json").decode("utf-8")
        )
        assert source_manifest == [
            {
                "id": "source:1",
                "title": "Source One",
                "topics": ["alpha"],
                "embedded": True,
                "insights_count": 2,
            }
        ]
        pid_summary = json.loads(archive.read("pid_summary.json").decode("utf-8"))
        assert pid_summary["claim_pids"] == ["S001-P000001"]
        assert pid_summary["section_pids"] == ["S001-P000001"]


@pytest.mark.asyncio
async def test_draft_service_notebook_lookup_and_get_raise_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        draft_service_module.Notebook, "get", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(draft_service_module, "repo_query", AsyncMock(return_value=[]))

    with pytest.raises(draft_service_module.NotFoundError, match="Notebook not found"):
        await draft_service_module.draft_service._get_notebook_or_raise("notebook:404")
    with pytest.raises(draft_service_module.NotFoundError, match="Draft not found"):
        await draft_service_module.draft_service.get_draft("draft:404")
