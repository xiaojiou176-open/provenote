from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def client(api_client):
    """Use shared authenticated client from tests/conftest.py."""
    return api_client


class TestModelCreation:
    @pytest.mark.asyncio
    @patch("packages.core.database.repository.repo_query")
    @patch("services.api.routers.models.Model.save")
    async def test_create_duplicate_google_model_returns_400(
        self, mock_save, mock_repo_query, client
    ):
        mock_repo_query.return_value = [
            {
                "id": "model:123",
                "name": "gemini-3.1-pro-preview",
                "provider": "google",
                "type": "language",
            }
        ]

        response = client.post(
            "/api/models",
            json={
                "name": "gemini-3.1-pro-preview",
                "provider": "google",
                "type": "language",
            },
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    @patch("packages.core.database.repository.repo_query")
    async def test_create_non_google_model_rejected(self, mock_repo_query, client):
        mock_repo_query.return_value = []
        response = client.post(
            "/api/models",
            json={
                "name": "claude-3-5-sonnet",
                "provider": "anthropic",
                "type": "language",
            },
        )
        assert response.status_code == 400
        assert "Only 'google'" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("packages.core.database.repository.repo_query")
    async def test_create_google_model_with_different_type_allowed(
        self, mock_repo_query, client
    ):
        from packages.core.ai.models import Model

        mock_repo_query.return_value = []
        with patch.object(Model, "save", new_callable=AsyncMock):
            response = client.post(
                "/api/models",
                json={
                    "name": "gemini-embedding-001",
                    "provider": "google",
                    "type": "embedding",
                },
            )

        assert response.status_code == 200


class TestModelsProviderAvailability:
    @patch(
        "services.api.routers.models._check_provider_has_credential",
        new_callable=AsyncMock,
    )
    def test_provider_available_when_google_credential_exists(
        self, mock_has_credential, client
    ):
        mock_has_credential.return_value = True

        response = client.get("/api/models/providers")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] == ["google"]
        assert "google" not in data["unavailable"]
        assert sorted(data["supported_types"]["google"]) == sorted(
            ["language", "embedding", "speech_to_text", "text_to_speech"]
        )

    @patch(
        "services.api.routers.models._check_provider_has_credential",
        new_callable=AsyncMock,
    )
    def test_provider_unavailable_without_google_credential(
        self, mock_has_credential, client
    ):
        mock_has_credential.return_value = False

        response = client.get("/api/models/providers")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] == []
        assert data["unavailable"] == ["google"]
        assert data["supported_types"] == {}


class TestDefaultModelValidation:
    @patch(
        "services.api.routers.models.DefaultModels.get_instance", new_callable=AsyncMock
    )
    @patch("services.api.routers.models.repo_query", new_callable=AsyncMock)
    def test_update_defaults_rejects_wrong_model_type(
        self, mock_repo_query, mock_get_defaults, client
    ):
        defaults = SimpleNamespace(
            default_chat_model=None,
            default_transformation_model=None,
            default_tools_model=None,
            large_context_model=None,
            default_text_to_speech_model=None,
            default_speech_to_text_model=None,
            default_embedding_model=None,
            update=AsyncMock(),
        )
        mock_get_defaults.return_value = defaults
        mock_repo_query.return_value = [
            {
                "id": "model:embed",
                "provider": "google",
                "type": "embedding",
                "name": "gemini-embedding-001",
            }
        ]

        response = client.put(
            "/api/models/defaults",
            json={"default_chat_model": "model:embed"},
        )
        assert response.status_code == 400
        assert "expected 'language'" in response.json()["detail"]

    @patch(
        "services.api.routers.models.DefaultModels.get_instance", new_callable=AsyncMock
    )
    @patch("services.api.routers.models.repo_query", new_callable=AsyncMock)
    def test_update_defaults_rejects_non_google_provider(
        self, mock_repo_query, mock_get_defaults, client
    ):
        defaults = SimpleNamespace(
            default_chat_model=None,
            default_transformation_model=None,
            default_tools_model=None,
            large_context_model=None,
            default_text_to_speech_model=None,
            default_speech_to_text_model=None,
            default_embedding_model=None,
            update=AsyncMock(),
        )
        mock_get_defaults.return_value = defaults
        mock_repo_query.return_value = [
            {
                "id": "model:chat",
                "provider": "anthropic",
                "type": "language",
                "name": "claude-3-5-sonnet",
            }
        ]

        response = client.put(
            "/api/models/defaults",
            json={"default_chat_model": "model:chat"},
        )
        assert response.status_code == 400
        assert "only 'google'" in response.json()["detail"]


class TestModelManagerProvisionedFallback:
    @pytest.mark.asyncio
    @patch("packages.core.ai.models.Model.get", new_callable=AsyncMock)
    @patch("packages.core.ai.models.AIFactory.create_language")
    @patch("packages.core.ai.models.provision_provider_keys", new_callable=AsyncMock)
    @patch("packages.core.ai.models.get_provisioned_provider_config")
    async def test_fallback_uses_provisioned_cache_without_linked_credential(
        self,
        mock_get_provisioned_provider_config,
        mock_provision_provider_keys,
        mock_create_language,
        mock_model_get,
    ):
        from packages.core.ai.models import ModelManager

        mock_model_get.return_value = SimpleNamespace(
            id="model:test",
            name="gemini-3.1-pro-preview",
            provider="google",
            type="language",
            credential=None,
        )
        mock_get_provisioned_provider_config.return_value = {
            "api_key": "db-key",
            "base_url": "https://example.invalid",
        }
        expected_model = object()
        mock_create_language.return_value = expected_model

        manager = ModelManager()
        result = await manager.get_model(
            "model:test", api_key="runtime-override", temperature=0.2
        )

        assert result is expected_model
        mock_provision_provider_keys.assert_awaited_once_with("google")
        mock_get_provisioned_provider_config.assert_called_once_with("google")


class TestModelManagerProviderFallback:
    @pytest.mark.asyncio
    async def test_get_default_model_falls_back_to_next_google_model(self):
        from packages.core.ai.models import ModelManager
        from packages.core.exceptions import ConfigurationError

        manager = ModelManager()
        manager.get_defaults = AsyncMock(
            return_value=SimpleNamespace(
                default_chat_model="model:google-primary",
                default_transformation_model=None,
                default_tools_model=None,
                large_context_model=None,
                default_embedding_model=None,
                default_text_to_speech_model=None,
                default_speech_to_text_model=None,
            )
        )

        model_calls = []

        async def fake_get_model(model_id: str, **kwargs):
            model_calls.append(model_id)
            if model_id == "model:google-primary":
                raise ConfigurationError("rate limit")
            if model_id == "model:google-secondary":
                return SimpleNamespace(id=model_id)
            raise ConfigurationError("not found")

        manager.get_model = AsyncMock(side_effect=fake_get_model)

        with (
            patch(
                "packages.core.ai.models.get_provider_chain_for_model_type",
                new=AsyncMock(return_value=["google"]),
            ),
            patch(
                "packages.core.ai.models.repo_query",
                new=AsyncMock(
                    return_value=[
                        {"id": "model:google-primary", "provider": "google"},
                        {"id": "model:google-secondary", "provider": "google"},
                    ]
                ),
            ),
        ):
            resolved = await manager.get_default_model("chat")

        assert getattr(resolved, "id", None) == "model:google-secondary"
        assert model_calls == ["model:google-primary", "model:google-secondary"]


class TestAutoAssignDefaults:
    @patch(
        "services.api.routers.models.DefaultModels.get_instance", new_callable=AsyncMock
    )
    @patch("services.api.routers.models.repo_query", new_callable=AsyncMock)
    def test_auto_assign_defaults_uses_primary_secondary_language_policy(
        self, mock_repo_query, mock_get_defaults, client
    ):
        defaults = SimpleNamespace(
            default_chat_model=None,
            default_transformation_model=None,
            default_tools_model=None,
            large_context_model=None,
            default_text_to_speech_model="model:tts-existing",
            default_speech_to_text_model="model:stt-existing",
            default_embedding_model=None,
            update=AsyncMock(),
        )
        mock_get_defaults.return_value = defaults
        mock_repo_query.return_value = [
            {
                "id": "model:pro",
                "name": "gemini-3.1-pro-preview",
                "provider": "google",
                "type": "language",
            },
            {
                "id": "model:flash",
                "name": "gemini-3-flash-preview",
                "provider": "google",
                "type": "language",
            },
            {
                "id": "model:embed",
                "name": "gemini-embedding-001",
                "provider": "google",
                "type": "embedding",
            },
        ]

        response = client.post("/api/models/auto-assign")
        assert response.status_code == 200
        payload = response.json()

        assert payload["assigned"]["default_chat_model"] == "model:pro"
        assert payload["assigned"]["large_context_model"] == "model:pro"
        assert payload["assigned"]["default_transformation_model"] == "model:flash"
        assert payload["assigned"]["default_tools_model"] == "model:flash"
        assert payload["assigned"]["default_embedding_model"] == "model:embed"
        assert "default_text_to_speech_model" in payload["skipped"]
        assert "default_speech_to_text_model" in payload["skipped"]

        defaults.update.assert_awaited_once()


class TestProviderQueryIndexCompatibility:
    @pytest.mark.asyncio
    @patch("packages.core.database.repository.repo_query", new_callable=AsyncMock)
    @patch("services.api.routers.models.Model.save", new_callable=AsyncMock)
    async def test_create_model_duplicate_check_uses_index_friendly_provider_filter(
        self, mock_model_save, mock_repo_query
    ):
        from packages.core.application.models import ModelCreate
        from services.api.routers.models import create_model

        mock_repo_query.return_value = []
        response = await create_model(
            ModelCreate(
                name="gemini-3.1-pro-preview",
                provider="google",
                type="language",
            )
        )

        assert response.provider == "google"
        query = mock_repo_query.call_args.args[0]
        params = mock_repo_query.call_args.args[1]
        assert "provider = $provider" in query
        assert "string::lowercase(provider)" not in query
        assert params["provider"] == "google"
        mock_model_save.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        "services.api.routers.models.DefaultModels.get_instance", new_callable=AsyncMock
    )
    @patch("services.api.routers.models.repo_query", new_callable=AsyncMock)
    async def test_auto_assign_uses_provider_equality_filter(
        self, mock_repo_query, mock_get_defaults
    ):
        from services.api.routers.models import auto_assign_defaults

        defaults = SimpleNamespace(
            default_chat_model="model:existing",
            default_transformation_model="model:existing",
            default_tools_model="model:existing",
            large_context_model="model:existing",
            default_text_to_speech_model="model:existing",
            default_speech_to_text_model="model:existing",
            default_embedding_model="model:existing",
            update=AsyncMock(),
        )
        mock_get_defaults.return_value = defaults
        mock_repo_query.return_value = []

        response = await auto_assign_defaults()
        assert response.assigned == {}
        query = mock_repo_query.call_args.args[0]
        params = mock_repo_query.call_args.args[1]
        assert "WHERE provider = $provider" in query
        assert "string::lowercase(provider)" not in query
        assert params["provider"] == "google"
