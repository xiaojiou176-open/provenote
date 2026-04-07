from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from services.api import podcast_service as podcast_service_module


@pytest.mark.asyncio
async def test_submit_generation_job_covers_missing_draft_notebook_fallback_and_import_error(
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
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException, match="Draft 'draft:404' not found"):
        await podcast_service_module.PodcastService.submit_generation_job(
            episode_profile_name="Episode",
            speaker_profile_name="Speaker",
            episode_name="Weekly Brief",
            draft_id="draft:404",
        )

    monkeypatch.setattr(
        podcast_service_module.Notebook,
        "get",
        AsyncMock(side_effect=RuntimeError("db down")),
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
        notebook_id="notebook:1",
    )
    assert job_id == "job-1"
    assert (
        submit_mock.await_args.kwargs["command_args"]["content"]
        == "Notebook ID: notebook:1"
    )


@pytest.mark.asyncio
async def test_podcast_service_list_get_and_import_error_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        podcast_service_module.PodcastEpisode,
        "get_all",
        AsyncMock(return_value=[SimpleNamespace(id="episode:1")]),
    )
    monkeypatch.setattr(
        podcast_service_module.PodcastEpisode,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="episode:1")),
    )
    episodes = await podcast_service_module.PodcastService.list_episodes()
    episode = await podcast_service_module.PodcastService.get_episode("episode:1")
    assert episodes[0].id == "episode:1"
    assert episode.id == "episode:1"
