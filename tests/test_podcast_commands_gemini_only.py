from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from packages.core.application.commands.podcast_commands import (
    PodcastGenerationInput,
    generate_podcast_command,
)
from packages.core.podcasts import paths as podcast_paths_module
from packages.core.podcasts.models import EpisodeProfile, SpeakerProfile
from services.api import podcast_service as podcast_service_module


@pytest.mark.asyncio
async def test_generate_podcast_command_rejects_non_google_profile_provider() -> None:
    episode_profile = EpisodeProfile(
        name="legacy-profile",
        description="legacy",
        speaker_config="speaker-1",
        outline_provider="anthropic",
        outline_model="claude-3-5-haiku-latest",
        transcript_provider="google",
        transcript_model="gemini-2.5-flash",
        default_briefing="brief",
        num_segments=5,
    )
    speaker_profile = SpeakerProfile(
        name="speaker-1",
        description="speaker",
        tts_provider="google",
        tts_model="gemini-2.5-flash-preview-tts",
        speakers=[
            {
                "name": "Host",
                "voice_id": "voice123",
                "backstory": "host",
                "personality": "clear",
            }
        ],
    )

    with (
        patch(
            "packages.core.application.commands.podcast_commands.EpisodeProfile.get_by_name",
            new=AsyncMock(return_value=episode_profile),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.SpeakerProfile.get_by_name",
            new=AsyncMock(return_value=speaker_profile),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.create_podcast",
            new=AsyncMock(),
        ),
    ):
        with pytest.raises(
            ValueError, match="Only 'google' is allowed in Gemini-only mode"
        ):
            await generate_podcast_command(
                PodcastGenerationInput(
                    episode_profile="legacy-profile",
                    speaker_profile="speaker-1",
                    episode_name="episode-1",
                    content="content",
                )
            )


@pytest.mark.asyncio
async def test_generate_podcast_command_sanitizes_episode_name_and_audio_path(
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

    episode_profile = EpisodeProfile(
        name="google-ep",
        description="google",
        speaker_config="speaker-1",
        outline_provider="google",
        outline_model="gemini-2.5-pro",
        transcript_provider="google",
        transcript_model="gemini-2.5-flash",
        default_briefing="brief",
        num_segments=5,
    )
    speaker_profile = SpeakerProfile(
        name="speaker-1",
        description="speaker",
        tts_provider="google",
        tts_model="gemini-2.5-flash-preview-tts",
        speakers=[
            {
                "name": "Host",
                "voice_id": "voice123",
                "backstory": "host",
                "personality": "clear",
            }
        ],
    )
    create_podcast_mock = AsyncMock(
        return_value={
            "final_output_file_path": str(
                podcast_output_dir / "escape_episode" / "episode.mp3"
            ),
            "transcript": {"lines": []},
            "outline": {"sections": []},
        }
    )

    with (
        patch(
            "packages.core.application.commands.podcast_commands.EpisodeProfile.get_by_name",
            new=AsyncMock(return_value=episode_profile),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.SpeakerProfile.get_by_name",
            new=AsyncMock(return_value=speaker_profile),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.repo_query",
            new=AsyncMock(
                side_effect=[
                    [episode_profile.model_dump()],
                    [speaker_profile.model_dump()],
                ]
            ),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.PodcastEpisode.save",
            new=AsyncMock(),
        ),
        patch("packages.core.application.commands.podcast_commands.configure"),
        patch(
            "packages.core.application.commands.podcast_commands.create_podcast",
            new=create_podcast_mock,
        ),
    ):
        result = await generate_podcast_command(
            PodcastGenerationInput(
                episode_profile="google-ep",
                speaker_profile="speaker-1",
                episode_name="../../escape episode",
                content="content",
            )
        )

    create_call = create_podcast_mock.await_args.kwargs
    assert create_call["episode_name"] == "escape_episode"
    assert Path(create_call["output_dir"]).is_relative_to(podcast_output_dir)
    assert result.audio_file_path == "escape_episode/episode.mp3"
