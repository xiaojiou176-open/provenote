from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

from packages.core.podcasts import paths as podcast_paths_module
from services.api import podcast_service as podcast_service_module
from services.api.routers import podcasts as podcasts_router


def _episode(
    *,
    episode_id: str,
    command: object,
    audio_file: str | None,
    detail: dict | None = None,
    detail_exc: Exception | None = None,
) -> SimpleNamespace:
    async def _get_job_detail() -> dict:
        if detail_exc:
            raise detail_exc
        return detail or {"status": "completed", "error_message": None}

    return SimpleNamespace(
        id=episode_id,
        name=f"name-{episode_id}",
        episode_profile={"name": "ep"},
        speaker_profile={"name": "sp"},
        briefing="brief",
        content="content",
        transcript={"t": 1},
        outline={"o": 1},
        created="2026-01-01",
        command=command,
        audio_file=audio_file,
        get_job_detail=AsyncMock(side_effect=_get_job_detail),
        delete=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_podcasts_generate_and_status_error_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = podcasts_router.PodcastGenerationRequest(
        episode_profile="ep",
        speaker_profile="sp",
        episode_name="n1",
        content="body",
    )

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "submit_generation_job",
        AsyncMock(return_value="command:1"),
    )
    result = await podcasts_router.generate_podcast(request, idempotency_key="idem-1")
    assert result.job_id == "command:1"

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "submit_generation_job",
        AsyncMock(side_effect=RuntimeError("submit failed")),
    )
    with pytest.raises(HTTPException) as gen_exc:
        await podcasts_router.generate_podcast(request, idempotency_key=None)
    assert gen_exc.value.status_code == 500

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_job_status",
        AsyncMock(side_effect=RuntimeError("offline")),
    )
    with pytest.raises(HTTPException) as status_exc:
        await podcasts_router.get_podcast_job_status("command:404")
    assert status_exc.value.status_code == 500


@pytest.mark.asyncio
async def test_list_and_get_podcast_episode_branches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    podcast_output_dir = (tmp_path / "podcasts" / "episodes").resolve()
    podcast_output_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        podcast_service_module,
        "PODCAST_EPISODES_OUTPUT_DIR",
        podcast_output_dir,
    )
    monkeypatch.setattr(
        podcast_paths_module,
        "PODCAST_EPISODES_OUTPUT_DIR",
        podcast_output_dir,
    )

    audio_file = podcast_output_dir / "done" / "ep.mp3"
    audio_file.parent.mkdir(parents=True, exist_ok=True)
    audio_file.write_bytes(b"audio")

    episodes = [
        _episode(episode_id="skip", command=None, audio_file=None),
        _episode(
            episode_id="unknown",
            command="cmd:1",
            audio_file=None,
            detail_exc=RuntimeError("status err"),
        ),
        _episode(
            episode_id="done",
            command=None,
            audio_file=str(audio_file),
            detail={"status": "completed", "error_message": None},
        ),
        _episode(
            episode_id="unsafe",
            command=None,
            audio_file=str(tmp_path / "outside.mp3"),
            detail={"status": "completed", "error_message": None},
        ),
    ]
    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "list_episodes",
        AsyncMock(return_value=episodes),
    )

    listed = await podcasts_router.list_podcast_episodes()
    assert len(listed) == 3
    assert listed[0].job_status == "unknown"
    assert listed[1].audio_url == "/api/podcasts/episodes/done/audio"
    assert listed[1].audio_file == "done/ep.mp3"
    assert listed[2].audio_file is None
    assert listed[2].audio_url is None

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(return_value=episodes[2]),
    )
    got = await podcasts_router.get_podcast_episode("done")
    assert got.job_status == "completed"
    assert got.audio_url == "/api/podcasts/episodes/done/audio"
    assert got.audio_file == "done/ep.mp3"

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(
            return_value=_episode(episode_id="raw", command=None, audio_file=None)
        ),
    )
    got_unknown = await podcasts_router.get_podcast_episode("raw")
    assert got_unknown.job_status == "unknown"

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "list_episodes",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    with pytest.raises(HTTPException) as list_exc:
        await podcasts_router.list_podcast_episodes()
    assert list_exc.value.status_code == 500

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(side_effect=RuntimeError("missing")),
    )
    with pytest.raises(HTTPException) as get_exc:
        await podcasts_router.get_podcast_episode("404")
    assert get_exc.value.status_code == 404


@pytest.mark.asyncio
async def test_stream_retry_and_delete_podcast_branches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    podcast_output_dir = (tmp_path / "podcasts" / "episodes").resolve()
    podcast_output_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        podcast_service_module,
        "PODCAST_EPISODES_OUTPUT_DIR",
        podcast_output_dir,
    )
    monkeypatch.setattr(
        podcast_paths_module,
        "PODCAST_EPISODES_OUTPUT_DIR",
        podcast_output_dir,
    )

    audio_file = podcast_output_dir / "a1" / "audio.mp3"
    audio_file.parent.mkdir(parents=True, exist_ok=True)
    audio_file.write_bytes(b"a")

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(
            return_value=_episode(
                episode_id="a1", command=None, audio_file=str(audio_file)
            )
        ),
    )
    streamed = await podcasts_router.stream_podcast_episode_audio("a1")
    assert isinstance(streamed, FileResponse)

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(
            return_value=_episode(episode_id="a2", command=None, audio_file=None)
        ),
    )
    with pytest.raises(HTTPException) as no_audio_exc:
        await podcasts_router.stream_podcast_episode_audio("a2")
    assert no_audio_exc.value.detail == "Episode has no audio file"

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(
            return_value=_episode(
                episode_id="a3",
                command=None,
                audio_file=str(podcast_output_dir / "a3" / "missing.mp3"),
            )
        ),
    )
    with pytest.raises(HTTPException) as missing_audio_exc:
        await podcasts_router.stream_podcast_episode_audio("a3")
    assert missing_audio_exc.value.detail == "Audio file not found on disk"

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(
            return_value=_episode(
                episode_id="a3-traversal",
                command=None,
                audio_file="../outside.mp3",
            )
        ),
    )
    with pytest.raises(HTTPException) as traversal_audio_exc:
        await podcasts_router.stream_podcast_episode_audio("a3-traversal")
    assert traversal_audio_exc.value.detail == "Audio file not found on disk"

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(side_effect=HTTPException(status_code=404, detail="x")),
    )
    with pytest.raises(HTTPException) as passthrough_exc:
        await podcasts_router.stream_podcast_episode_audio("a4")
    assert passthrough_exc.value.status_code == 404

    failed_ep = _episode(
        episode_id="r1",
        command="cmd",
        audio_file=str(audio_file),
        detail={"status": "failed", "error_message": "x"},
    )
    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(return_value=failed_ep),
    )
    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "submit_generation_job",
        AsyncMock(return_value="command:new"),
    )
    ok_retry = await podcasts_router.retry_podcast_episode(
        "r1", idempotency_key="idem-x"
    )
    assert ok_retry["job_id"] == "command:new"

    outside_retry_audio = tmp_path / "outside-retry.mp3"
    outside_retry_audio.write_bytes(b"outside")
    failed_ep_outside_audio = _episode(
        episode_id="r1-outside",
        command="cmd",
        audio_file=str(outside_retry_audio),
        detail={"status": "failed", "error_message": "x"},
    )
    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(return_value=failed_ep_outside_audio),
    )
    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "submit_generation_job",
        AsyncMock(return_value="command:new-outside"),
    )
    outside_retry = await podcasts_router.retry_podcast_episode(
        "r1-outside", idempotency_key="idem-y"
    )
    assert outside_retry["job_id"] == "command:new-outside"
    assert outside_retry_audio.exists()

    not_failed_ep = _episode(
        episode_id="r2",
        command="cmd",
        audio_file=None,
        detail={"status": "completed", "error_message": None},
    )
    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(return_value=not_failed_ep),
    )
    with pytest.raises(HTTPException) as state_exc:
        await podcasts_router.retry_podcast_episode("r2", idempotency_key=None)
    assert state_exc.value.status_code == 400

    no_profile_ep = _episode(
        episode_id="r3",
        command="cmd",
        audio_file=None,
        detail={"status": "failed", "error_message": "x"},
    )
    no_profile_ep.episode_profile = {}
    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(return_value=no_profile_ep),
    )
    with pytest.raises(HTTPException) as profile_exc:
        await podcasts_router.retry_podcast_episode("r3", idempotency_key=None)
    assert profile_exc.value.status_code == 400

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(side_effect=RuntimeError("oops")),
    )
    with pytest.raises(HTTPException) as retry_exc:
        await podcasts_router.retry_podcast_episode("r4", idempotency_key=None)
    assert retry_exc.value.status_code == 500

    deletable = _episode(
        episode_id="d1",
        command=None,
        audio_file=str(audio_file),
        detail={"status": "failed", "error_message": "x"},
    )
    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(return_value=deletable),
    )
    deleted = await podcasts_router.delete_podcast_episode("d1")
    assert deleted["episode_id"] == "d1"

    outside_delete_audio = tmp_path / "outside-delete.mp3"
    outside_delete_audio.write_bytes(b"outside")
    unsafe_deletable = _episode(
        episode_id="d1-unsafe",
        command=None,
        audio_file=str(outside_delete_audio),
        detail={"status": "failed", "error_message": "x"},
    )
    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(return_value=unsafe_deletable),
    )
    deleted_unsafe = await podcasts_router.delete_podcast_episode("d1-unsafe")
    assert deleted_unsafe["episode_id"] == "d1-unsafe"
    assert outside_delete_audio.exists()

    monkeypatch.setattr(
        podcasts_router.PodcastService,
        "get_episode",
        AsyncMock(side_effect=RuntimeError("delete err")),
    )
    with pytest.raises(HTTPException) as del_exc:
        await podcasts_router.delete_podcast_episode("d2")
    assert del_exc.value.status_code == 500
