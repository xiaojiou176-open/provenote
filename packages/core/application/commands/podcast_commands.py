import time
from typing import Optional

from pydantic import BaseModel
from surreal_commands import CommandInput, CommandOutput, command

from packages.core.application.command_service import (
    RETRY_POLICY_SINGLE_ATTEMPT,
    CommandService,
)
from packages.core.database.repository import ensure_record_id, repo_query
from packages.core.observability import bind_observability_context
from packages.core.observability.logger import logger
from packages.core.podcasts.models import EpisodeProfile, PodcastEpisode, SpeakerProfile
from packages.core.podcasts.paths import (
    build_podcast_episode_output_dir,
    resolve_podcast_output_path,
    to_podcast_audio_identifier,
)

try:
    from podcast_creator import configure, create_podcast
except ImportError as e:
    logger.error(f"Failed to import podcast_creator: {e}")
    raise ValueError("podcast_creator library not available")

SUPPORTED_PROVIDER = "google"


def _normalize_provider(provider: str) -> str:
    return provider.strip().lower().replace("-", "_")


def _assert_google_provider(provider: str, field_name: str) -> None:
    normalized = _normalize_provider(provider)
    if normalized != SUPPORTED_PROVIDER:
        raise ValueError(
            f"Unsupported provider '{provider}' for {field_name}. "
            f"Only '{SUPPORTED_PROVIDER}' is allowed in Gemini-only mode."
        )


def full_model_dump(model):
    if isinstance(model, BaseModel):
        return model.model_dump()
    elif isinstance(model, dict):
        return {k: full_model_dump(v) for k, v in model.items()}
    elif isinstance(model, list):
        return [full_model_dump(item) for item in model]
    else:
        return model


class PodcastGenerationInput(CommandInput):
    episode_profile: str
    speaker_profile: str
    episode_name: str
    content: str
    draft_id: Optional[str] = None
    briefing_suffix: Optional[str] = None


class PodcastGenerationOutput(CommandOutput):
    success: bool
    episode_id: Optional[str] = None
    audio_file_path: Optional[str] = None
    transcript: Optional[dict] = None
    outline: Optional[dict] = None
    processing_time: float
    error_message: Optional[str] = None


@command("generate_podcast", app="open_notebook", retry=RETRY_POLICY_SINGLE_ATTEMPT)
async def generate_podcast_command(
    input_data: PodcastGenerationInput,
) -> PodcastGenerationOutput:
    """
    Real podcast generation using podcast-creator library with Episode Profiles
    """
    start_time = time.time()
    command_id = (
        str(input_data.execution_context.command_id)
        if input_data.execution_context
        else "unknown"
    )

    with bind_observability_context(
        command_id=command_id,
        job_kind="generate_podcast",
    ):
        try:
            logger.info(
                f"Starting podcast generation for episode: {input_data.episode_name}"
            )
            logger.info(f"Using episode profile: {input_data.episode_profile}")

            episode_profile = await EpisodeProfile.get_by_name(
                input_data.episode_profile
            )
            if not episode_profile:
                raise ValueError(
                    f"Episode profile '{input_data.episode_profile}' not found"
                )

            speaker_profile = await SpeakerProfile.get_by_name(
                episode_profile.speaker_config
            )
            if not speaker_profile:
                raise ValueError(
                    f"Speaker profile '{episode_profile.speaker_config}' not found"
                )

            _assert_google_provider(
                episode_profile.outline_provider, "outline_provider"
            )
            _assert_google_provider(
                episode_profile.transcript_provider, "transcript_provider"
            )
            _assert_google_provider(speaker_profile.tts_provider, "tts_provider")

            logger.info(f"Loaded episode profile: {episode_profile.name}")
            logger.info(f"Loaded speaker profile: {speaker_profile.name}")

            episode_profiles = await repo_query("SELECT * FROM episode_profile")
            speaker_profiles = await repo_query("SELECT * FROM speaker_profile")

            episode_profiles_dict = {
                profile["name"]: profile for profile in episode_profiles
            }
            speaker_profiles_dict = {
                profile["name"]: profile for profile in speaker_profiles
            }

            briefing = episode_profile.default_briefing
            if input_data.briefing_suffix:
                briefing += f"\n\nAdditional instructions: {input_data.briefing_suffix}"

            episode = PodcastEpisode(
                name=input_data.episode_name,
                episode_profile=full_model_dump(episode_profile.model_dump()),
                speaker_profile=full_model_dump(speaker_profile.model_dump()),
                command=ensure_record_id(input_data.execution_context.command_id)
                if input_data.execution_context
                else None,
                briefing=briefing,
                content=input_data.content,
                audio_file=None,
                transcript=None,
                outline=None,
            )
            await episode.save()

            configure("speakers_config", {"profiles": speaker_profiles_dict})
            configure("episode_config", {"profiles": episode_profiles_dict})

            logger.info("Configured podcast-creator with episode and speaker profiles")
            logger.info(f"Generated briefing (length: {len(briefing)} chars)")

            safe_episode_name, output_dir = build_podcast_episode_output_dir(
                input_data.episode_name
            )
            output_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Created output directory: {output_dir}")
            logger.info("Starting podcast generation with podcast-creator...")

            result = await create_podcast(
                content=input_data.content,
                briefing=briefing,
                episode_name=safe_episode_name,
                output_dir=str(output_dir),
                speaker_config=speaker_profile.name,
                episode_profile=episode_profile.name,
            )

            audio_file_path = result.get("final_output_file_path") if result else None
            audio_file_identifier = None
            if audio_file_path:
                normalized_audio_path = resolve_podcast_output_path(
                    str(audio_file_path)
                )
                audio_file_identifier = to_podcast_audio_identifier(
                    normalized_audio_path
                )

            episode.audio_file = audio_file_identifier
            episode.transcript = {
                "transcript": full_model_dump(result["transcript"]) if result else None
            }
            episode.outline = full_model_dump(result["outline"]) if result else None
            await episode.save()

            processing_time = time.time() - start_time
            logger.info(
                f"Successfully generated podcast episode: {episode.id} in {processing_time:.2f}s"
            )

            return PodcastGenerationOutput(
                success=True,
                episode_id=str(episode.id),
                audio_file_path=audio_file_identifier,
                transcript={"transcript": full_model_dump(result["transcript"])}
                if result.get("transcript")
                else None,
                outline=full_model_dump(result["outline"])
                if result.get("outline")
                else None,
                processing_time=processing_time,
            )

        except ValueError as e:
            if input_data.execution_context:
                await CommandService.record_command_failure_event(
                    str(input_data.execution_context.command_id),
                    app="open_notebook",
                    name="generate_podcast",
                    error_message=str(e),
                )
            raise

        except Exception as e:
            logger.error(f"Podcast generation failed: {e}")
            logger.exception(e)
            if input_data.execution_context:
                await CommandService.record_command_failure_event(
                    str(input_data.execution_context.command_id),
                    app="open_notebook",
                    name="generate_podcast",
                    error_message=str(e),
                )

            error_msg = str(e)
            if "Invalid json output" in error_msg or "Expecting value" in error_msg:
                error_msg += (
                    "\n\nNOTE: Verify your profile models are Gemini-compatible and return "
                    "valid JSON for outline/transcript generation."
                )

            raise RuntimeError(error_msg) from e
