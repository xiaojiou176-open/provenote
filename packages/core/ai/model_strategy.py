"""Centralized Gemini model strategy defaults for runtime governance."""

from __future__ import annotations

GEMINI_MODEL_PRO_31 = "gemini-3.1-pro"
GEMINI_MODEL_PRO_30 = "gemini-3.0-pro"
GEMINI_MODEL_FLASH_30 = "gemini-3.0-flash"
GEMINI_MODEL_FLASH_25 = "gemini-2.5-flash"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
GEMINI_DEFAULT_FAST_PATH_MODEL = GEMINI_MODEL_FLASH_25

# Use the strongest default for computer-use style long-horizon plans.
GEMINI_COMPUTER_USE_MODEL = GEMINI_MODEL_PRO_31

# Ordered policy: high quality -> balanced -> low latency.
GEMINI_LANGUAGE_MODEL_PRIORITY: tuple[str, ...] = (
    GEMINI_MODEL_PRO_31,
    GEMINI_MODEL_PRO_30,
    GEMINI_MODEL_FLASH_30,
)
