"""Canonical podcast output path helpers."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from packages.core.config import DATA_FOLDER

PODCAST_EPISODES_OUTPUT_DIR = (Path(DATA_FOLDER) / "podcasts" / "episodes").resolve()
_INVALID_EPISODE_PATH_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_MAX_SAFE_EPISODE_NAME_LENGTH = 120


def sanitize_episode_name(episode_name: str) -> str:
    candidate = episode_name.strip()
    if not candidate:
        raise ValueError("Episode name cannot be empty")

    candidate = candidate.replace("/", "_").replace("\\", "_")
    candidate = _INVALID_EPISODE_PATH_CHARS.sub("_", candidate).strip("._-")
    if not candidate or candidate in {".", ".."}:
        raise ValueError("Episode name contains no safe filesystem characters")

    return candidate[:_MAX_SAFE_EPISODE_NAME_LENGTH]


def _coerce_path(path_or_uri: str | Path) -> Path:
    if isinstance(path_or_uri, Path):
        return path_or_uri

    if path_or_uri.startswith("file://"):
        parsed = urlparse(path_or_uri)
        return Path(unquote(parsed.path))

    return Path(path_or_uri)


def resolve_podcast_output_path(path_or_uri: str | Path) -> Path:
    candidate = _coerce_path(path_or_uri)
    if not candidate.is_absolute():
        candidate = PODCAST_EPISODES_OUTPUT_DIR / candidate

    resolved = candidate.resolve(strict=False)
    if resolved == PODCAST_EPISODES_OUTPUT_DIR or not resolved.is_relative_to(
        PODCAST_EPISODES_OUTPUT_DIR
    ):
        raise ValueError("Path escapes podcasts output directory")

    return resolved


def build_podcast_episode_output_dir(episode_name: str) -> tuple[str, Path]:
    safe_episode_name = sanitize_episode_name(episode_name)
    output_dir = resolve_podcast_output_path(safe_episode_name)
    return safe_episode_name, output_dir


def to_podcast_audio_identifier(path_or_uri: str | Path) -> str:
    resolved = resolve_podcast_output_path(path_or_uri)
    return resolved.relative_to(PODCAST_EPISODES_OUTPUT_DIR).as_posix()
