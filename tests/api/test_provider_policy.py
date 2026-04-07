from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from packages.core.ai.provider_policy import (
    ProviderPolicy,
    evaluate_policy_effectiveness,
    get_provider_chain_for_model_type,
    get_provider_policy,
    resolve_modality,
)


def test_provider_policy_enforces_google_only_chain() -> None:
    ProviderPolicy.clear_instance()
    policy = ProviderPolicy(
        language=["anthropic", "google", "mistral"],
        embedding=["voyage"],
    )

    assert policy.language == ["google"]
    assert policy.embedding == ["google"]
    assert policy.speech_to_text == ["google"]
    assert policy.text_to_speech == ["google"]


def test_provider_policy_normalizer_handles_none_string_and_invalid_types() -> None:
    assert ProviderPolicy.normalize_policy_chain(None) == ["google"]
    assert ProviderPolicy.normalize_policy_chain(" google ") == ["google"]
    assert ProviderPolicy.normalize_policy_chain(123) == ["google"]


def test_provider_policy_as_dict_returns_normalized_google_only_chains() -> None:
    policy = ProviderPolicy(
        language=["google"],
        embedding=["other"],
        speech_to_text=None,
        text_to_speech={"google"},
    )

    assert policy.as_dict() == {
        "language": ["google"],
        "embedding": ["google"],
        "speech_to_text": ["google"],
        "text_to_speech": ["google"],
    }


@pytest.mark.asyncio
async def test_evaluate_policy_effectiveness_requires_google_configuration() -> None:
    ProviderPolicy.clear_instance()
    configured = {"google": False, "anthropic": True}
    with patch(
        "packages.core.ai.provider_policy.get_provider_policy",
        new=AsyncMock(return_value=ProviderPolicy()),
    ):
        result = await evaluate_policy_effectiveness(configured)

    assert result["effective"]["language"] is False
    assert result["active_provider"]["language"] is None
    assert "google" in (result["blocking_reason"]["language"] or "")


@pytest.mark.asyncio
async def test_get_provider_policy_falls_back_to_default_on_load_error() -> None:
    with (
        patch(
            "packages.core.ai.provider_policy.ProviderPolicy.get_instance",
            new=AsyncMock(side_effect=RuntimeError("db unavailable")),
        ),
        patch("packages.core.ai.provider_policy.logger.warning") as warning_mock,
    ):
        policy = await get_provider_policy()

    assert isinstance(policy, ProviderPolicy)
    assert policy.as_dict()["language"] == ["google"]
    warning_mock.assert_called_once()


@pytest.mark.asyncio
async def test_get_provider_chain_for_unknown_model_type_defaults_to_language_chain() -> (
    None
):
    with patch(
        "packages.core.ai.provider_policy.get_provider_policy",
        new=AsyncMock(return_value=ProviderPolicy(language=["google"])),
    ):
        chain = await get_provider_chain_for_model_type("unknown")

    assert resolve_modality("unknown") == "language"
    assert chain == ["google"]


def test_get_provider_policy_endpoint_returns_google_only_chain(api_client) -> None:
    fake_policy = SimpleNamespace(
        as_dict=lambda: {
            "language": ["google"],
            "embedding": ["google"],
            "speech_to_text": ["google"],
            "text_to_speech": ["google"],
        }
    )
    with patch(
        "services.api.routers.providers.get_provider_policy",
        new=AsyncMock(return_value=fake_policy),
    ):
        response = api_client.get("/api/providers/policy")

    assert response.status_code == 200
    assert response.json()["language"] == ["google"]


def test_update_provider_policy_endpoint_rejects_non_google_chain(api_client) -> None:
    policy = ProviderPolicy()
    policy.update = AsyncMock()
    with patch(
        "services.api.routers.providers.get_provider_policy",
        new=AsyncMock(return_value=policy),
    ):
        response = api_client.put(
            "/api/providers/policy",
            json={"language": ["anthropic"]},
        )

    assert response.status_code == 400
    assert "Only 'google'" in response.json()["detail"]


def test_policy_bootstrap_diagnostics_endpoint_reports_missing_state(
    api_client,
) -> None:
    defaults = SimpleNamespace(
        default_chat_model="",
        default_transformation_model="",
        default_tools_model="",
        large_context_model="",
        default_embedding_model="",
        default_text_to_speech_model="",
        default_speech_to_text_model="",
    )

    with (
        patch(
            "services.api.routers.providers.probe_startup_gemini_model",
            new=AsyncMock(
                return_value={
                    "model_probe_result": {
                        "provider": "google",
                        "model": "gemini-3.1-pro-preview",
                        "success": False,
                        "message": "No Google API key configured",
                        "key_source": "none",
                    },
                    "blocked_reason": "missing_google_api_key",
                    "remediation": ["Set GEMINI_API_KEY."],
                }
            ),
        ),
        patch(
            "services.api.routers.providers.Credential.get_by_provider",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "services.api.routers.providers.DefaultModels.get_instance",
            new=AsyncMock(return_value=defaults),
        ),
    ):
        response = api_client.get("/api/providers/policy/bootstrap-diagnostics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["model_probe_result"]["success"] is False
    assert payload["blocked_reason"] == "missing_google_api_key"
    assert payload["remediation"] == [
        "Set GEMINI_API_KEY, or add a Google credential in Settings -> API Keys.",
        "Restart the API after credentials are configured.",
    ]
    assert payload["missing_credentials"] == ["google"]
    assert "default_chat_model" in payload["missing_default_model_slots"]
