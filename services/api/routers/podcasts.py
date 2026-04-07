from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from packages.core.observability.logger import logger
from services.api.podcast_service import (
    PodcastGenerationRequest,
    PodcastGenerationResponse,
    PodcastService,
    resolve_podcast_output_path,
    to_podcast_audio_identifier,
)

router = APIRouter()


class PodcastEpisodeResponse(BaseModel):
    id: str
    name: str
    episode_profile: dict
    speaker_profile: dict
    briefing: str
    audio_file: Optional[str] = None
    audio_url: Optional[str] = None
    transcript: Optional[dict] = None
    outline: Optional[dict] = None
    created: Optional[str] = None
    job_status: Optional[str] = None
    error_message: Optional[str] = None


def _safe_audio_reference(audio_file: str) -> tuple[Optional[str], Optional[Path]]:
    try:
        audio_identifier = to_podcast_audio_identifier(audio_file)
        return audio_identifier, resolve_podcast_output_path(audio_identifier)
    except ValueError as exc:
        logger.warning(f"Ignoring unsafe podcast audio path '{audio_file}': {exc}")
        return None, None


@router.post("/podcasts/generate", response_model=PodcastGenerationResponse)
async def generate_podcast(
    request: PodcastGenerationRequest,
    idempotency_key: Optional[str] = Header(
        default=None, alias="Idempotency-Key", convert_underscores=False
    ),
):
    """
    Generate a podcast episode using Episode Profiles.
    Returns immediately with job ID for status tracking.
    """
    try:
        job_id = await PodcastService.submit_generation_job(
            episode_profile_name=request.episode_profile,
            speaker_profile_name=request.speaker_profile,
            episode_name=request.episode_name,
            draft_id=request.draft_id,
            notebook_id=request.notebook_id,
            content=request.content,
            briefing_suffix=request.briefing_suffix,
            idempotency_key=idempotency_key,
        )

        return PodcastGenerationResponse(
            job_id=job_id,
            status="submitted",
            message=f"Podcast generation started for episode '{request.episode_name}'",
            episode_profile=request.episode_profile,
            episode_name=request.episode_name,
        )

    except Exception as e:
        logger.error(f"Error generating podcast: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate podcast")


@router.get("/podcasts/jobs/{job_id}")
async def get_podcast_job_status(job_id: str):
    """Get the status of a podcast generation job"""
    try:
        status_data = await PodcastService.get_job_status(job_id)
        return status_data

    except Exception as e:
        logger.error(f"Error fetching podcast job status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch job status")


@router.get("/podcasts/episodes", response_model=List[PodcastEpisodeResponse])
async def list_podcast_episodes():
    """List all podcast episodes"""
    try:
        episodes = await PodcastService.list_episodes()

        response_episodes = []
        for episode in episodes:
            # Skip incomplete episodes without command or audio
            if not episode.command and not episode.audio_file:
                continue

            # Get job status and error message if available
            job_status = None
            error_message = None
            if episode.command:
                try:
                    detail = await episode.get_job_detail()
                    job_status = detail["status"]
                    error_message = detail["error_message"]
                except Exception:
                    job_status = "unknown"
            else:
                # No command but has audio file = completed import
                job_status = "completed"

            audio_url = None
            audio_file = None
            if episode.audio_file:
                audio_file, audio_path = _safe_audio_reference(episode.audio_file)
                if audio_path and audio_path.exists():
                    audio_url = f"/api/podcasts/episodes/{episode.id}/audio"

            response_episodes.append(
                PodcastEpisodeResponse(
                    id=str(episode.id),
                    name=episode.name,
                    episode_profile=episode.episode_profile,
                    speaker_profile=episode.speaker_profile,
                    briefing=episode.briefing,
                    audio_file=audio_file,
                    audio_url=audio_url,
                    transcript=episode.transcript,
                    outline=episode.outline,
                    created=str(episode.created) if episode.created else None,
                    job_status=job_status,
                    error_message=error_message,
                )
            )

        return response_episodes

    except Exception as e:
        logger.error(f"Error listing podcast episodes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list podcast episodes")


@router.get("/podcasts/episodes/{episode_id}", response_model=PodcastEpisodeResponse)
async def get_podcast_episode(episode_id: str):
    """Get a specific podcast episode"""
    try:
        episode = await PodcastService.get_episode(episode_id)

        # Get job status and error message if available
        job_status = None
        error_message = None
        if episode.command:
            try:
                detail = await episode.get_job_detail()
                job_status = detail["status"]
                error_message = detail["error_message"]
            except Exception:
                job_status = "unknown"
        else:
            # No command but has audio file = completed import
            job_status = "completed" if episode.audio_file else "unknown"

        audio_url = None
        audio_file = None
        if episode.audio_file:
            audio_file, audio_path = _safe_audio_reference(episode.audio_file)
            if audio_path and audio_path.exists():
                audio_url = f"/api/podcasts/episodes/{episode.id}/audio"

        return PodcastEpisodeResponse(
            id=str(episode.id),
            name=episode.name,
            episode_profile=episode.episode_profile,
            speaker_profile=episode.speaker_profile,
            briefing=episode.briefing,
            audio_file=audio_file,
            audio_url=audio_url,
            transcript=episode.transcript,
            outline=episode.outline,
            created=str(episode.created) if episode.created else None,
            job_status=job_status,
            error_message=error_message,
        )

    except Exception as e:
        logger.error(f"Error fetching podcast episode: {str(e)}")
        raise HTTPException(status_code=404, detail="Episode not found")


@router.get("/podcasts/episodes/{episode_id}/audio")
async def stream_podcast_episode_audio(episode_id: str):
    """Stream the audio file associated with a podcast episode"""
    try:
        episode = await PodcastService.get_episode(episode_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching podcast episode for audio: {str(e)}")
        raise HTTPException(status_code=404, detail="Episode not found")

    if not episode.audio_file:
        raise HTTPException(status_code=404, detail="Episode has no audio file")

    try:
        audio_path = resolve_podcast_output_path(episode.audio_file)
    except ValueError as exc:
        logger.warning(f"Unsafe audio path for episode {episode_id}: {exc}")
        raise HTTPException(
            status_code=404, detail="Audio file not found on disk"
        ) from exc

    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=audio_path.name,
    )


@router.post("/podcasts/episodes/{episode_id}/retry")
async def retry_podcast_episode(
    episode_id: str,
    idempotency_key: Optional[str] = Header(
        default=None, alias="Idempotency-Key", convert_underscores=False
    ),
):
    """Retry a failed podcast episode by deleting it and submitting a new job"""
    try:
        episode = await PodcastService.get_episode(episode_id)

        # Validate episode is in a failed state
        detail = await episode.get_job_detail()
        if detail["status"] not in ("failed", "error"):
            raise HTTPException(
                status_code=400,
                detail=f"Episode is not in a failed state (current: {detail['status']})",
            )

        # Extract params for re-submission
        ep_profile_name = episode.episode_profile.get("name")
        sp_profile_name = episode.speaker_profile.get("name")
        episode_name = episode.name
        content = episode.content

        if not ep_profile_name or not sp_profile_name:
            raise HTTPException(
                status_code=400,
                detail="Cannot retry: episode or speaker profile name missing from stored data",
            )

        retry_idempotency_key = idempotency_key or f"podcast-retry:{episode.id}"

        # Submit a new job first, then cleanup old failed record.
        job_id = await PodcastService.submit_generation_job(
            episode_profile_name=ep_profile_name,
            speaker_profile_name=sp_profile_name,
            episode_name=episode_name,
            content=content,
            idempotency_key=retry_idempotency_key,
        )

        # Delete audio file if any
        if episode.audio_file:
            try:
                audio_path = resolve_podcast_output_path(episode.audio_file)
            except ValueError as exc:
                logger.warning(
                    f"Refused to delete unsafe audio path for episode {episode.id}: {exc}"
                )
            else:
                if audio_path.exists():
                    try:
                        audio_path.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to delete audio file {audio_path}: {e}")

        # Best-effort cleanup of failed episode record.
        try:
            await episode.delete()
        except Exception as e:
            logger.warning(f"Failed to delete failed episode {episode.id}: {e}")

        return {"job_id": job_id, "message": "Retry submitted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying podcast episode: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retry episode")


@router.delete("/podcasts/episodes/{episode_id}")
async def delete_podcast_episode(episode_id: str):
    """Delete a podcast episode and its associated audio file"""
    try:
        # Get the episode first to check if it exists and get the audio file path
        episode = await PodcastService.get_episode(episode_id)

        # Delete the physical audio file if it exists
        if episode.audio_file:
            try:
                audio_path = resolve_podcast_output_path(episode.audio_file)
            except ValueError as exc:
                logger.warning(
                    f"Refused to delete unsafe audio path for episode {episode_id}: {exc}"
                )
            else:
                if audio_path.exists():
                    try:
                        audio_path.unlink()
                        logger.info(f"Deleted audio file: {audio_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete audio file {audio_path}: {e}")

        # Delete the episode from the database
        await episode.delete()

        logger.info(f"Deleted podcast episode: {episode_id}")
        return {"message": "Episode deleted successfully", "episode_id": episode_id}

    except Exception as e:
        logger.error(f"Error deleting podcast episode: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete episode")
