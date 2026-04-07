from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


def _policy_stub(**overrides):
    state = {
        "language": ["google"],
        "embedding": ["google"],
        "speech_to_text": ["google"],
        "text_to_speech": ["google"],
    }
    state.update(overrides)
    policy = SimpleNamespace()
    policy.update = AsyncMock()
    policy.as_dict = lambda: dict(state)
    return policy, state


def test_get_policy_returns_500_when_backend_raises(api_client) -> None:
    with patch(
        "services.api.routers.providers.get_provider_policy",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ):
        response = api_client.get("/api/providers/policy")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_update_policy_success_with_normalized_provider_values(api_client) -> None:
    policy, state = _policy_stub()
    with patch(
        "services.api.routers.providers.get_provider_policy",
        new=AsyncMock(return_value=policy),
    ):
        response = api_client.put(
            "/api/providers/policy",
            json={
                "language": [" Google "],
                "embedding": ["gOOgle"],
            },
        )

    assert response.status_code == 200
    assert response.json()["language"] == ["google"]
    assert response.json()["embedding"] == ["google"]
    assert state["language"] == ["google"]
    assert state["embedding"] == ["google"]
    policy.update.assert_awaited_once()


def test_update_policy_returns_500_when_update_fails(api_client) -> None:
    policy, _ = _policy_stub()
    policy.update = AsyncMock(side_effect=RuntimeError("write failed"))
    with patch(
        "services.api.routers.providers.get_provider_policy",
        new=AsyncMock(return_value=policy),
    ):
        response = api_client.put(
            "/api/providers/policy",
            json={"language": ["google"]},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_bootstrap_diagnostics_adds_fully_configured_suggestion(api_client) -> None:
    defaults = SimpleNamespace(
        default_chat_model="gemini-3.1-pro-preview",
        default_transformation_model="gemini-3.1-pro-preview",
        default_tools_model="gemini-3.1-pro-preview",
        large_context_model="gemini-3.1-pro-preview",
        default_embedding_model="gemini-embedding-001",
        default_text_to_speech_model="gemini-tts",
        default_speech_to_text_model="gemini-stt",
    )
    with (
        patch(
            "services.api.routers.providers.probe_startup_gemini_model",
            new=AsyncMock(
                return_value={
                    "model_probe_result": {
                        "provider": "google",
                        "success": True,
                    },
                    "blocked_reason": None,
                    "remediation": [],
                }
            ),
        ),
        patch(
            "services.api.routers.providers.Credential.get_by_provider",
            new=AsyncMock(return_value=[SimpleNamespace(id="credential:google")]),
        ),
        patch(
            "services.api.routers.providers.DefaultModels.get_instance",
            new=AsyncMock(return_value=defaults),
        ),
    ):
        response = api_client.get("/api/providers/policy/bootstrap-diagnostics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["missing_credentials"] == []
    assert payload["missing_default_model_slots"] == []
    assert payload["suggestions"] == [
        "Provider policy is fully configured for runtime."
    ]


def test_bootstrap_diagnostics_returns_500_on_probe_error(api_client) -> None:
    with patch(
        "services.api.routers.providers.probe_startup_gemini_model",
        new=AsyncMock(side_effect=OSError("network down")),
    ):
        response = api_client.get("/api/providers/policy/bootstrap-diagnostics")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
