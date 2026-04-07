from unittest.mock import AsyncMock, patch

import pytest

from packages.core.ai.connection_tester import (
    DEFAULT_STARTUP_GEMINI_MODEL,
    GEMINI_MODEL_FLASH_25,
    probe_startup_gemini_model,
)


def test_default_startup_gemini_model_tracks_stable_fast_path() -> None:
    assert DEFAULT_STARTUP_GEMINI_MODEL == GEMINI_MODEL_FLASH_25


@pytest.mark.asyncio
async def test_probe_startup_gemini_model_blocks_without_api_key() -> None:
    with patch(
        "packages.core.ai.connection_tester._resolve_google_api_key",
        new=AsyncMock(return_value=(None, "none")),
    ):
        result = await probe_startup_gemini_model("gemini-3.1-pro-preview")

    assert result["model_probe_result"]["success"] is False
    assert result["blocked_reason"] == "missing_google_api_key"
    assert "GEMINI_API_KEY" in result["remediation"][0]


@pytest.mark.asyncio
async def test_probe_startup_gemini_model_blocks_when_model_unavailable() -> None:
    with (
        patch(
            "packages.core.ai.connection_tester._resolve_google_api_key",
            new=AsyncMock(return_value=("sk-test", "environment:GEMINI_API_KEY")),
        ),
        patch(
            "packages.core.ai.connection_tester.test_google_connection",
            new=AsyncMock(
                return_value=(True, "API key valid (test model not available)")
            ),
        ),
    ):
        result = await probe_startup_gemini_model("gemini-3.1-pro-preview")

    assert result["model_probe_result"]["success"] is False
    assert result["blocked_reason"] == "gemini_model_unavailable"


@pytest.mark.asyncio
async def test_probe_startup_gemini_model_passes_on_success() -> None:
    with (
        patch(
            "packages.core.ai.connection_tester._resolve_google_api_key",
            new=AsyncMock(return_value=("sk-test", "database:credential")),
        ),
        patch(
            "packages.core.ai.connection_tester.test_google_connection",
            new=AsyncMock(return_value=(True, "Connection successful")),
        ),
    ):
        result = await probe_startup_gemini_model("gemini-3.1-pro-preview")

    assert result["model_probe_result"]["success"] is True
    assert result["blocked_reason"] is None


@pytest.mark.asyncio
async def test_probe_startup_gemini_model_falls_back_when_default_model_is_unavailable() -> (
    None
):
    with (
        patch(
            "packages.core.ai.connection_tester._resolve_google_api_key",
            new=AsyncMock(return_value=("sk-test", "environment:GEMINI_API_KEY")),
        ),
        patch(
            "packages.core.ai.connection_tester.read_env",
            side_effect=lambda key, default=None: (
                "" if key == "GEMINI_MODEL" else default
            ),
        ),
        patch(
            "packages.core.ai.connection_tester.test_google_connection",
            new=AsyncMock(
                side_effect=[
                    (True, "API key valid (test model not available)"),
                    (True, "Connection successful"),
                ]
            ),
        ) as connection_mock,
    ):
        result = await probe_startup_gemini_model()

    assert result["model_probe_result"]["success"] is True
    assert result["model_probe_result"]["model"] == "gemini-2.5-pro"
    assert result["blocked_reason"] is None
    assert connection_mock.await_count == 2
