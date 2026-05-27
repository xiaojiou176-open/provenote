"""Worker adapter for surreal-commands integration."""

import os

from packages.core.application.commands.embedding_commands import (
    embed_insight_command,
    embed_note_command,
    embed_source_command,
    rebuild_embeddings_command,
)
from packages.core.application.commands.example_commands import (
    analyze_data_command,
    process_text_command,
)
from packages.core.application.commands.podcast_commands import generate_podcast_command
from packages.core.application.commands.source_commands import process_source_command
from packages.core.observability.logger import configure_process_logging

configure_process_logging(
    service="notebooklab-worker",
    component="services.worker.runner",
    domain="worker",
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    serialize=os.getenv("LOG_JSON", "").strip().lower() in {"1", "true", "yes", "on"},
)

__all__ = [
    # Embedding commands
    "embed_note_command",
    "embed_insight_command",
    "embed_source_command",
    "rebuild_embeddings_command",
    # Other commands
    "generate_podcast_command",
    "process_source_command",
    "process_text_command",
    "analyze_data_command",
]
