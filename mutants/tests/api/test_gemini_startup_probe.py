from unittest.mock import AsyncMock, patch

import pytest

from packages.core.ai.connection_tester import probe_startup_gemini_model


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
