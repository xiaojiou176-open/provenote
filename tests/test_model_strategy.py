from packages.core.ai.model_strategy import (
    GEMINI_COMPUTER_USE_MODEL,
    GEMINI_DEFAULT_FAST_PATH_MODEL,
    GEMINI_LANGUAGE_MODEL_PRIORITY,
    GEMINI_MODEL_FLASH_25,
    GEMINI_MODEL_FLASH_30,
    GEMINI_MODEL_PRO_30,
    GEMINI_MODEL_PRO_31,
)


def test_computer_use_model_tracks_highest_quality_default() -> None:
    assert GEMINI_COMPUTER_USE_MODEL == GEMINI_MODEL_PRO_31


def test_fast_path_default_model_tracks_stable_supported_runtime() -> None:
    assert GEMINI_DEFAULT_FAST_PATH_MODEL == GEMINI_MODEL_FLASH_25


def test_language_model_priority_order_and_uniqueness() -> None:
    assert GEMINI_LANGUAGE_MODEL_PRIORITY == (
        GEMINI_MODEL_PRO_31,
        GEMINI_MODEL_PRO_30,
        GEMINI_MODEL_FLASH_30,
    )
    assert len(set(GEMINI_LANGUAGE_MODEL_PRIORITY)) == 3
