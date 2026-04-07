from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.api import draft_service as draft_service_module
from services.api import podcast_service as podcast_service_module


@pytest.mark.asyncio
async def test_verify_draft_updates_status_and_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        draft_service_module.draft_service,
        "get_draft",
        AsyncMock(
            return_value=SimpleNamespace(
                id="draft:1",
                title="Notebook Draft",
                version=2,
                result_markdown="# Draft",
                metrics=SimpleNamespace(model_dump=lambda: {"coverage_rate": 1.0}),
            )
        ),
    )
    repo_query_mock = AsyncMock(
        return_value=[
            {
                "id": "draft:1",
                "notebook": "notebook:1",
                "title": "Notebook Draft",
                "status": "verified",
                "model_id": "model-draft",
                "language": "zh-CN",
                "near_dedup_threshold": 0.97,
                "source_ids": ["source:1"],
                "note_ids": [],
                "thread_ids": [],
                "version": 2,
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
                "verified_brief_snapshot": {"draft_id": "draft:1"},
                "created": "2026-01-01T00:00:00+00:00",
                "updated": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    monkeypatch.setattr(draft_service_module, "repo_query", repo_query_mock)

    response = await draft_service_module.draft_service.verify_draft("draft:1")

    assert response.status == "verified"
    payload = repo_query_mock.await_args.args[1]["data"]
    assert payload["status"] == "verified"
    assert payload["verified_brief_snapshot"]["draft_id"] == "draft:1"


@pytest.mark.asyncio
async def test_submit_generation_job_prefers_draft_markdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        podcast_service_module.EpisodeProfile,
        "get_by_name",
        AsyncMock(
            return_value=SimpleNamespace(name="Episode", speaker_config="Speaker")
        ),
    )
    monkeypatch.setattr(
        podcast_service_module.SpeakerProfile,
        "get_by_name",
        AsyncMock(return_value=SimpleNamespace(name="Speaker")),
    )
    monkeypatch.setattr(
        podcast_service_module.Draft,
        "get",
        AsyncMock(
            return_value=SimpleNamespace(
                id="draft:1",
                title="Notebook Draft",
                version=3,
                status="verified",
                result_markdown="# Verified Draft",
                verified_brief_snapshot={"draft_id": "draft:1"},
            )
        ),
    )
    submit_mock = AsyncMock(return_value="job-1")
    monkeypatch.setattr(
        podcast_service_module.CommandService,
        "submit_command_job",
        submit_mock,
    )

    job_id = await podcast_service_module.PodcastService.submit_generation_job(
        episode_profile_name="Episode",
        speaker_profile_name="Speaker",
        episode_name="Weekly Brief",
        draft_id="draft:1",
    )

    assert job_id == "job-1"
    payload = submit_mock.await_args.kwargs["command_args"]
    assert payload["draft_id"] == "draft:1"
    assert payload["content"] == "# Verified Draft"
    assert "Verified draft: Notebook Draft (v3)" in payload["briefing_suffix"]
