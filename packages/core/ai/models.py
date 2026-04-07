import os
from typing import Any, ClassVar, Dict, Optional, Union

from esperanto import (
    AIFactory,
    EmbeddingModel,
    LanguageModel,
    SpeechToTextModel,
    TextToSpeechModel,
)

from packages.core.ai.key_provider import (
    get_provisioned_provider_config,
    provision_provider_keys,
)
from packages.core.ai.model_strategy import GEMINI_EMBEDDING_MODEL
from packages.core.ai.provider_policy import get_provider_chain_for_model_type
from packages.core.database.repository import ensure_record_id, repo_query
from packages.core.domain.base import ObjectModel, RecordModel
from packages.core.exceptions import ConfigurationError
from packages.core.observability.logger import logger

ModelType = Union[LanguageModel, EmbeddingModel, SpeechToTextModel, TextToSpeechModel]


def _classify_fallback_reason(exc: Exception) -> str:
    message = str(exc).lower()
    if "rate" in message and "limit" in message:
        return "rate_limit"
    if "timeout" in message or "connection" in message or "network" in message:
        return "network"
    if "unsupported" in message or "not implemented" in message:
        return "unsupported"
    if any(code in message for code in ("500", "502", "503", "504")):
        return "provider_5xx"
    if "not found" in message or "no model configured" in message:
        return "not_configured"
    return "unknown"


class Model(ObjectModel):
    table_name: ClassVar[str] = "model"
    nullable_fields: ClassVar[set[str]] = {"credential"}
    name: str
    provider: str
    type: str
    credential: Optional[str] = None

    @classmethod
    async def get_models_by_type(cls, model_type):
        models = await repo_query(
            "SELECT * FROM model WHERE type=$model_type;", {"model_type": model_type}
        )
        return [Model(**model) for model in models]

    @classmethod
    async def get_by_credential(cls, credential_id: str):
        """Get all models linked to a specific credential."""
        models = await repo_query(
            "SELECT * FROM model WHERE credential=$cred_id;",
            {"cred_id": ensure_record_id(credential_id)},
        )
        return [Model(**model) for model in models]

    def _prepare_save_data(self) -> Dict[str, Any]:
        data = super()._prepare_save_data()
        if data.get("credential"):
            data["credential"] = ensure_record_id(data["credential"])
        return data

    async def get_credential_obj(self):
        """Get the Credential object linked to this model, if any."""
        if not self.credential:
            return None
        from packages.core.domain.credential import Credential

        try:
            return await Credential.get(self.credential)
        except Exception:
            logger.warning(
                f"Could not load credential {self.credential} for model {self.id}"
            )
            return None


class DefaultModels(RecordModel):
    record_id: ClassVar[str] = "open_notebook:default_models"
    default_chat_model: Optional[str] = None
    default_transformation_model: Optional[str] = None
    large_context_model: Optional[str] = None
    default_text_to_speech_model: Optional[str] = None
    default_speech_to_text_model: Optional[str] = None
    # default_vision_model: Optional[str]
    default_embedding_model: Optional[str] = None
    default_tools_model: Optional[str] = None

    @classmethod
    async def get_instance(cls) -> "DefaultModels":
        """Always fetch fresh defaults from database (override parent caching behavior)"""
        result = await repo_query(
            "SELECT * FROM ONLY $record_id",
            {"record_id": ensure_record_id(cls.record_id)},
        )

        if result:
            if isinstance(result, list) and len(result) > 0:
                data = result[0]
            elif isinstance(result, dict):
                data = result
            else:
                data = {}
        else:
            data = {}

        # Create new instance with fresh data (bypass singleton cache)
        instance = object.__new__(cls)
        object.__setattr__(instance, "__dict__", {})
        super(RecordModel, instance).__init__(**data)
        return instance


class ModelManager:
    def __init__(self):
        pass  # No caching needed

    async def get_model(self, model_id: str, **kwargs) -> Optional[ModelType]:
        """Get a model by ID. Esperanto will cache the actual model instance."""
        if not model_id:
            return None

        try:
            model: Model = await Model.get(model_id)
        except Exception:
            raise ConfigurationError(f"Model with ID {model_id} not found")

        if not model.type or model.type not in [
            "language",
            "embedding",
            "speech_to_text",
            "text_to_speech",
        ]:
            raise ConfigurationError(f"Invalid model type: {model.type}")
        normalized_provider = model.provider.lower().replace("-", "_")
        if normalized_provider != "google":
            raise ConfigurationError(
                f"Provider '{model.provider}' is not supported in Gemini-only runtime mode"
            )

        # Build config from credential if linked, otherwise fall back to provisioned runtime config
        config: dict = {}
        if model.credential:
            credential = await model.get_credential_obj()
            if credential:
                config = credential.to_esperanto_config()
                logger.debug(
                    f"Using credential '{credential.name}' for model {model.name}"
                )
            else:
                logger.warning(
                    f"Model {model.id} has credential {model.credential} but it could not be loaded. "
                    f"Falling back to provisioned runtime config."
                )
                await provision_provider_keys(model.provider)
                config = get_provisioned_provider_config(model.provider)
        else:
            # No credential linked - use provisioned runtime config fallback
            await provision_provider_keys(model.provider)
            config = get_provisioned_provider_config(model.provider)

        # Merge any additional kwargs (e.g. temperature)
        config.update(kwargs)

        # Normalize provider name: DB stores underscores but Esperanto expects hyphens
        provider = model.provider.replace("_", "-")

        # Create model based on type (Esperanto will cache the instance)
        if model.type == "language":
            return AIFactory.create_language(
                model_name=model.name,
                provider=provider,
                config=config,
            )
        elif model.type == "embedding":
            return AIFactory.create_embedding(
                model_name=model.name,
                provider=provider,
                config=config,
            )
        elif model.type == "speech_to_text":
            return AIFactory.create_speech_to_text(
                model_name=model.name,
                provider=provider,
                config=config,
            )
        elif model.type == "text_to_speech":
            return AIFactory.create_text_to_speech(
                model_name=model.name,
                provider=provider,
                config=config,
            )
        else:
            raise ConfigurationError(f"Invalid model type: {model.type}")

    async def get_defaults(self) -> DefaultModels:
        """Get the default models configuration from database"""
        defaults = await DefaultModels.get_instance()
        if not defaults:
            raise RuntimeError("Failed to load default models configuration")
        return defaults

    async def get_speech_to_text(self, **kwargs) -> Optional[SpeechToTextModel]:
        """Get the default speech-to-text model"""
        model = await self.get_default_model("speech_to_text", **kwargs)
        assert model is None or isinstance(model, SpeechToTextModel), (
            f"Expected SpeechToTextModel but got {type(model)}"
        )
        return model

    async def get_text_to_speech(self, **kwargs) -> Optional[TextToSpeechModel]:
        """Get the default text-to-speech model"""
        model = await self.get_default_model("text_to_speech", **kwargs)
        assert model is None or isinstance(model, TextToSpeechModel), (
            f"Expected TextToSpeechModel but got {type(model)}"
        )
        return model

    async def get_embedding_model(self, **kwargs) -> Optional[EmbeddingModel]:
        """Get the default embedding model"""
        model = await self.get_default_model("embedding", **kwargs)
        assert model is None or isinstance(model, EmbeddingModel), (
            f"Expected EmbeddingModel but got {type(model)}"
        )
        return model

    async def _runtime_fallback_embedding_model(
        self, **kwargs
    ) -> Optional[EmbeddingModel]:
        """
        Build a runtime fallback embedding model when DB defaults are missing.

        This keeps Gemini-only runtime usable for /api/embed in fresh environments
        before users explicitly assign default models in Settings.
        """
        try:
            provider = "google"
            model_name = os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL)
            await provision_provider_keys(provider)
            config = get_provisioned_provider_config(provider)
            config.update(kwargs)
            model = AIFactory.create_embedding(
                model_name=model_name,
                provider=provider,
                config=config,
            )
            logger.warning(
                "Using runtime fallback embedding model='{}' provider='{}' (no DB default embedding model configured)",
                model_name,
                provider,
            )
            return model
        except Exception as exc:
            logger.warning(
                "Runtime fallback embedding model creation failed detail='{}'",
                str(exc),
            )
            return None

    @staticmethod
    def _default_model_id_for_type(
        defaults: DefaultModels, model_type: str
    ) -> Optional[str]:
        if model_type == "chat":
            return defaults.default_chat_model
        if model_type == "transformation":
            return defaults.default_transformation_model or defaults.default_chat_model
        if model_type == "tools":
            return defaults.default_tools_model or defaults.default_chat_model
        if model_type == "embedding":
            return defaults.default_embedding_model
        if model_type == "text_to_speech":
            return defaults.default_text_to_speech_model
        if model_type == "speech_to_text":
            return defaults.default_speech_to_text_model
        if model_type == "large_context":
            return defaults.large_context_model
        return None

    async def get_default_model(self, model_type: str, **kwargs) -> Optional[ModelType]:
        """
        Get the default model for a specific type.

        Args:
            model_type: The type of model to retrieve (e.g., 'chat', 'embedding', etc.)
            **kwargs: Additional arguments to pass to the model constructor
        """
        defaults = await self.get_defaults()
        model_id = self._default_model_id_for_type(defaults, model_type)

        if not model_id:
            logger.warning(
                f"No default model configured for type '{model_type}'. "
                f"Please go to Settings → Models and set a default model."
            )
        else:
            try:
                return await self.get_model(model_id, **kwargs)
            except (ValueError, ConfigurationError) as e:
                reason_code = _classify_fallback_reason(e)
                logger.warning(
                    "Primary model load failed type='{}' model_id='{}' reason_code='{}' detail='{}'. "
                    "Attempting provider fallback chain.",
                    model_type,
                    model_id,
                    reason_code,
                    str(e),
                )

        # Gemini-only provider chain
        fallback_type = (
            "language"
            if model_type in {"chat", "transformation", "tools", "large_context"}
            else model_type
        )
        provider_chain = await get_provider_chain_for_model_type(fallback_type)
        try:
            candidate_models = await repo_query(
                "SELECT id, provider, name FROM model WHERE type=$model_type ORDER BY provider, name",
                {"model_type": fallback_type},
            )
        except (RuntimeError, ValueError, TypeError, OSError) as exc:
            logger.warning(
                "Fallback lookup failed type='{}' detail='{}'",
                model_type,
                str(exc),
            )
            return None
        if not candidate_models:
            if model_type == "embedding":
                return await self._runtime_fallback_embedding_model(**kwargs)
            return None

        by_provider: dict[str, list[str]] = {}
        for item in candidate_models:
            provider = str(item.get("provider", "")).lower().replace("-", "_")
            item_id = item.get("id")
            if not provider or not item_id:
                continue
            by_provider.setdefault(provider, []).append(item_id)

        for provider in provider_chain:
            for candidate_id in by_provider.get(provider, []):
                if candidate_id == model_id:
                    continue
                try:
                    model = await self.get_model(candidate_id, **kwargs)
                    if model is not None:
                        logger.warning(
                            "Using fallback model type='{}' provider='{}' model_id='{}'",
                            model_type,
                            provider,
                            candidate_id,
                        )
                        return model
                except (ValueError, ConfigurationError) as exc:
                    logger.debug(
                        "Fallback candidate failed type='{}' provider='{}' model_id='{}' reason_code='{}' detail='{}'",
                        model_type,
                        provider,
                        candidate_id,
                        _classify_fallback_reason(exc),
                        str(exc),
                    )
                    continue

        if model_type == "embedding":
            return await self._runtime_fallback_embedding_model(**kwargs)
        return None


model_manager = ModelManager()
