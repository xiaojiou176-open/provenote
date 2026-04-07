import traceback
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from packages.core.ai.connection_tester import test_individual_model
from packages.core.ai.key_provider import provision_provider_keys
from packages.core.ai.model_discovery import (
    discover_provider_models,
    get_provider_model_count,
    sync_all_providers,
    sync_provider_models,
)
from packages.core.ai.model_strategy import (
    GEMINI_EMBEDDING_MODEL,
    GEMINI_LANGUAGE_MODEL_PRIORITY,
)
from packages.core.ai.models import DefaultModels, Model
from packages.core.application.models import (
    DefaultModelsResponse,
    ModelCreate,
    ModelResponse,
    ProviderAvailabilityResponse,
)
from packages.core.database.repository import ensure_record_id, repo_query
from packages.core.domain.credential import Credential
from packages.core.exceptions import InvalidInputError
from packages.core.observability.logger import logger

router = APIRouter()
SUPPORTED_PROVIDER = "google"


# =============================================================================
# Model Discovery Response Models
# =============================================================================


class ProviderDiscoveredModelResponse(BaseModel):
    """Response model for a provider discovery result."""

    name: str
    provider: str
    model_type: str
    description: Optional[str] = None


class ProviderSyncResponse(BaseModel):
    """Response model for provider sync operation."""

    provider: str
    discovered: int
    new: int
    existing: int


class AllProvidersSyncResponse(BaseModel):
    """Response model for syncing all providers."""

    results: Dict[str, ProviderSyncResponse]
    total_discovered: int
    total_new: int


class ProviderModelCountResponse(BaseModel):
    """Response model for provider model counts."""

    provider: str
    counts: Dict[str, int]
    total: int


class AutoAssignResult(BaseModel):
    """Response model for auto-assign operation."""

    assigned: Dict[str, str]  # slot_name -> model_id
    skipped: List[str]  # slots already assigned
    missing: List[str]  # slots with no available models


class ModelTestResponse(BaseModel):
    """Response model for individual model test."""

    success: bool
    message: str
    details: Optional[str] = None


PRIMARY_LANGUAGE_MODEL = GEMINI_LANGUAGE_MODEL_PRIORITY[0]
SECONDARY_LANGUAGE_MODEL = GEMINI_LANGUAGE_MODEL_PRIORITY[1]
TERTIARY_LANGUAGE_MODEL = GEMINI_LANGUAGE_MODEL_PRIORITY[2]
DEFAULT_EMBEDDING_MODEL = GEMINI_EMBEDDING_MODEL

DEFAULT_SLOT_POLICY: Dict[str, Dict[str, List[str] | str]] = {
    "default_chat_model": {
        "type": "language",
        "preferred": [
            PRIMARY_LANGUAGE_MODEL,
            SECONDARY_LANGUAGE_MODEL,
            TERTIARY_LANGUAGE_MODEL,
        ],
    },
    "default_transformation_model": {
        "type": "language",
        "preferred": [
            SECONDARY_LANGUAGE_MODEL,
            TERTIARY_LANGUAGE_MODEL,
            PRIMARY_LANGUAGE_MODEL,
        ],
    },
    "default_tools_model": {
        "type": "language",
        "preferred": [
            SECONDARY_LANGUAGE_MODEL,
            TERTIARY_LANGUAGE_MODEL,
            PRIMARY_LANGUAGE_MODEL,
        ],
    },
    "large_context_model": {
        "type": "language",
        "preferred": [
            PRIMARY_LANGUAGE_MODEL,
            SECONDARY_LANGUAGE_MODEL,
            TERTIARY_LANGUAGE_MODEL,
        ],
    },
    "default_embedding_model": {
        "type": "embedding",
        "preferred": [
            DEFAULT_EMBEDDING_MODEL,
        ],
    },
    "default_text_to_speech_model": {
        "type": "text_to_speech",
        "preferred": [
            "gemini-2.5-flash-preview-tts",
            "gemini-tts",
            "tts",
        ],
    },
    "default_speech_to_text_model": {
        "type": "speech_to_text",
        "preferred": [
            TERTIARY_LANGUAGE_MODEL,
            "transcribe",
            "speech",
            "audio",
        ],
    },
}

SLOT_TYPE_MAP = {
    slot: str(config["type"]) for slot, config in DEFAULT_SLOT_POLICY.items()
}


def _normalize_model_name_for_policy(name: str) -> str:
    normalized = name.strip().lower()
    normalized = normalized.replace("-preview", "")
    normalized = normalized.replace("-experimental", "")
    normalized = normalized.replace("-exp", "")
    normalized = normalized.replace("gemini-3.0-", "gemini-3-")
    return normalized


def _policy_name_variants(preferred_name: str) -> set[str]:
    variants = {_normalize_model_name_for_policy(preferred_name)}
    if "gemini-3.0-" in preferred_name.lower():
        variants.add(
            _normalize_model_name_for_policy(
                preferred_name.lower().replace("gemini-3.0-", "gemini-3-")
            )
        )
    return {item for item in variants if item}


def _normalize_provider(provider: str) -> str:
    return provider.strip().lower().replace("-", "_")


def _assert_google_provider(provider: str) -> str:
    normalized = _normalize_provider(provider)
    if normalized != SUPPORTED_PROVIDER:
        raise HTTPException(
            status_code=400,
            detail=f"Only '{SUPPORTED_PROVIDER}' provider is supported in Gemini-only mode.",
        )
    return normalized


async def _check_provider_has_credential(provider: str) -> bool:
    """Check if a provider has any credentials configured in the database."""
    if _normalize_provider(provider) != SUPPORTED_PROVIDER:
        return False
    try:
        credentials = await Credential.get_by_provider(SUPPORTED_PROVIDER)
        return len(credentials) > 0
    except Exception:
        pass
    return False


@router.get("/models", response_model=List[ModelResponse])
async def get_models(
    type: Optional[str] = Query(None, description="Filter by model type"),
):
    """Get all configured models with optional type filtering."""
    try:
        if type:
            models = await Model.get_models_by_type(type)
        else:
            models = await Model.get_all()

        return [
            ModelResponse(
                id=model.id,
                name=model.name,
                provider=model.provider,
                type=model.type,
                credential=model.credential,
                created=str(model.created),
                updated=str(model.updated),
            )
            for model in models
        ]
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


@router.post("/models", response_model=ModelResponse)
async def create_model(model_data: ModelCreate):
    """Create a new model configuration."""
    try:
        # Validate model type
        valid_types = ["language", "embedding", "text_to_speech", "speech_to_text"]
        if model_data.type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model type. Must be one of: {valid_types}",
            )
        model_provider = _assert_google_provider(model_data.provider)

        # Check for duplicate model name under the same provider and type (case-insensitive)
        from packages.core.database.repository import repo_query

        existing = await repo_query(
            "SELECT * FROM model WHERE provider = $provider AND string::lowercase(name) = $name AND string::lowercase(type) = $type LIMIT 1",
            {
                "provider": model_provider,
                "name": model_data.name.lower(),
                "type": model_data.type.lower(),
            },
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model_data.name}' already exists for provider '{model_data.provider}' with type '{model_data.type}'",
            )

        new_model = Model(
            name=model_data.name,
            provider=model_provider,
            type=model_data.type,
            credential=model_data.credential,
        )
        await new_model.save()

        return ModelResponse(
            id=new_model.id or "",
            name=new_model.name,
            provider=new_model.provider,
            type=new_model.type,
            credential=new_model.credential,
            created=str(new_model.created),
            updated=str(new_model.updated),
        )
    except HTTPException:
        raise
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating model: {str(e)}")


@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """Delete a model configuration."""
    try:
        model = await Model.get(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        await model.delete()

        return {"message": "Model deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting model: {str(e)}")


@router.post("/models/{model_id}/test", response_model=ModelTestResponse)
async def test_model(model_id: str):
    """Test if a specific model is correctly configured and functional."""
    try:
        model = await Model.get(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Model not found")

    try:
        success, message = await test_individual_model(model)
        return ModelTestResponse(success=success, message=message)
    except Exception as e:
        logger.error(f"Error testing model {model_id}: {traceback.format_exc()}")
        return ModelTestResponse(
            success=False,
            message=str(e)[:200],
        )


@router.get("/models/defaults", response_model=DefaultModelsResponse)
async def get_default_models():
    """Get default model assignments."""
    try:
        defaults = await DefaultModels.get_instance()

        return DefaultModelsResponse(
            default_chat_model=defaults.default_chat_model,  # type: ignore[attr-defined]
            default_transformation_model=defaults.default_transformation_model,  # type: ignore[attr-defined]
            large_context_model=defaults.large_context_model,  # type: ignore[attr-defined]
            default_text_to_speech_model=defaults.default_text_to_speech_model,  # type: ignore[attr-defined]
            default_speech_to_text_model=defaults.default_speech_to_text_model,  # type: ignore[attr-defined]
            default_embedding_model=defaults.default_embedding_model,  # type: ignore[attr-defined]
            default_tools_model=defaults.default_tools_model,  # type: ignore[attr-defined]
        )
    except Exception as e:
        logger.error(f"Error fetching default models: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching default models: {str(e)}"
        )


@router.put("/models/defaults", response_model=DefaultModelsResponse)
async def update_default_models(defaults_data: DefaultModelsResponse):
    """Update default model assignments."""
    try:
        defaults = await DefaultModels.get_instance()
        payload = defaults_data.model_dump(exclude_none=True)
        for slot_name, model_id in payload.items():
            expected_type = SLOT_TYPE_MAP.get(slot_name)
            if not expected_type:
                continue
            try:
                model_record_id = ensure_record_id(model_id)
            except Exception as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid model id '{model_id}' for slot '{slot_name}': {exc}",
                ) from exc
            record = await repo_query(
                "SELECT id, provider, type, name FROM $model_id",
                {"model_id": model_record_id},
            )
            if not record:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{model_id}' does not exist for slot '{slot_name}'.",
                )
            model_record = record[0]
            provider = _normalize_provider(str(model_record.get("provider", "")))
            model_type = str(model_record.get("type", "")).lower()
            if provider != SUPPORTED_PROVIDER:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Model '{model_id}' belongs to provider '{provider}', "
                        f"but only '{SUPPORTED_PROVIDER}' is allowed."
                    ),
                )
            if model_type != expected_type:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Model '{model_id}' has type '{model_type}', expected "
                        f"'{expected_type}' for slot '{slot_name}'."
                    ),
                )
            setattr(defaults, slot_name, model_id)

        await defaults.update()

        # No cache refresh needed - next access will fetch fresh data from DB

        return DefaultModelsResponse(
            default_chat_model=defaults.default_chat_model,  # type: ignore[attr-defined]
            default_transformation_model=defaults.default_transformation_model,  # type: ignore[attr-defined]
            large_context_model=defaults.large_context_model,  # type: ignore[attr-defined]
            default_text_to_speech_model=defaults.default_text_to_speech_model,  # type: ignore[attr-defined]
            default_speech_to_text_model=defaults.default_speech_to_text_model,  # type: ignore[attr-defined]
            default_embedding_model=defaults.default_embedding_model,  # type: ignore[attr-defined]
            default_tools_model=defaults.default_tools_model,  # type: ignore[attr-defined]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating default models: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating default models: {str(e)}"
        )


@router.get("/models/providers", response_model=ProviderAvailabilityResponse)
async def get_provider_availability():
    """Get provider availability based on database credentials only."""
    try:
        has_google = await _check_provider_has_credential(SUPPORTED_PROVIDER)
        available_providers = [SUPPORTED_PROVIDER] if has_google else []
        unavailable_providers = [] if has_google else [SUPPORTED_PROVIDER]
        supported_types: dict[str, list[str]] = {}
        if has_google:
            supported_types[SUPPORTED_PROVIDER] = [
                "language",
                "embedding",
                "speech_to_text",
                "text_to_speech",
            ]

        return ProviderAvailabilityResponse(
            available=available_providers,
            unavailable=unavailable_providers,
            supported_types=supported_types,
        )
    except Exception as e:
        logger.error(f"Error checking provider availability: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error checking provider availability: {str(e)}"
        )


# =============================================================================
# Model Discovery Endpoints
# =============================================================================


@router.get(
    "/models/discover/{provider}", response_model=List[ProviderDiscoveredModelResponse]
)
async def discover_models(provider: str):
    """
    Discover available models from a provider without registering them.

    This endpoint queries the provider's API to list available models
    but does not save them to the database. Use the sync endpoint
    to both discover and register models.
    """
    try:
        provider = _assert_google_provider(provider)
        # Provision DB-stored credentials into env vars before discovery
        await provision_provider_keys(provider)
        discovered = await discover_provider_models(provider)
        return [
            ProviderDiscoveredModelResponse(
                name=m.name,
                provider=m.provider,
                model_type=m.model_type,
                description=m.description,
            )
            for m in discovered
        ]
    except Exception as e:
        logger.error(f"Error discovering models for {provider}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error discovering models. Check server logs for details.",
        )


@router.post("/models/sync/{provider}", response_model=ProviderSyncResponse)
async def sync_models(provider: str):
    """
    Sync models for a specific provider.

    Discovers available models from the provider's API and registers
    any new models in the database. Existing models are skipped.

    Returns counts of discovered, new, and existing models.
    """
    try:
        provider = _assert_google_provider(provider)
        # Provision DB-stored credentials into env vars before discovery
        await provision_provider_keys(provider)
        discovered, new, existing = await sync_provider_models(
            provider, auto_register=True
        )
        return ProviderSyncResponse(
            provider=provider,
            discovered=discovered,
            new=new,
            existing=existing,
        )
    except Exception as e:
        logger.error(f"Error syncing models for {provider}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error syncing models. Check server logs for details.",
        )


@router.post("/models/sync", response_model=AllProvidersSyncResponse)
async def sync_all_models():
    """
    Sync models for all configured providers.

    Discovers and registers models from all providers that have
    valid API keys configured. This is useful for initial setup
    or periodic refresh of available models.
    """
    try:
        results = await sync_all_providers()

        response_results = {}
        total_discovered = 0
        total_new = 0

        for provider, (discovered, new, existing) in results.items():
            response_results[provider] = ProviderSyncResponse(
                provider=provider,
                discovered=discovered,
                new=new,
                existing=existing,
            )
            total_discovered += discovered
            total_new += new

        return AllProvidersSyncResponse(
            results=response_results,
            total_discovered=total_discovered,
            total_new=total_new,
        )
    except Exception as e:
        logger.error(f"Error syncing all models: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error syncing all models: {str(e)}"
        )


@router.get("/models/count/{provider}", response_model=ProviderModelCountResponse)
async def get_model_count(provider: str):
    """
    Get count of registered models for a provider, grouped by type.

    Returns counts for each model type (language, embedding,
    speech_to_text, text_to_speech) as well as total count.
    """
    try:
        provider = _assert_google_provider(provider)
        counts = await get_provider_model_count(provider)
        total = sum(counts.values())
        return ProviderModelCountResponse(
            provider=provider,
            counts=counts,
            total=total,
        )
    except Exception as e:
        logger.error(f"Error getting model count for {provider}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting model count: {str(e)}"
        )


@router.get("/models/by-provider/{provider}", response_model=List[ModelResponse])
async def get_models_by_provider(provider: str):
    """
    Get all registered models for a specific provider.

    Returns models from the database that belong to the specified provider.
    """
    try:
        provider = _assert_google_provider(provider)
        models = await repo_query(
            "SELECT * FROM model WHERE provider = $provider ORDER BY type, name",
            {"provider": provider},
        )

        return [
            ModelResponse(
                id=model.get("id", ""),
                name=model.get("name", ""),
                provider=model.get("provider", ""),
                type=model.get("type", ""),
                credential=model.get("credential"),
                created=str(model.get("created", "")),
                updated=str(model.get("updated", "")),
            )
            for model in models
        ]
    except Exception as e:
        logger.error(f"Error fetching models for {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


@router.post("/models/auto-assign", response_model=AutoAssignResult)
async def auto_assign_defaults():
    """
    Auto-assign default models based on Gemini slot policy.

    Returns:
        - assigned: Dict of slot names to assigned model IDs
        - skipped: List of slots that already have models assigned
        - missing: List of slots with no available models
    """
    try:
        defaults = await DefaultModels.get_instance()
        all_models = await repo_query(
            "SELECT id, name, provider, type FROM model "
            "WHERE provider = $provider ORDER BY name",
            {"provider": SUPPORTED_PROVIDER},
        )

        models_by_type: Dict[str, List[Dict]] = {
            "language": [],
            "embedding": [],
            "text_to_speech": [],
            "speech_to_text": [],
        }
        for model in all_models:
            model_type = str(model.get("type", "")).lower()
            if model_type in models_by_type:
                models_by_type[model_type].append(model)

        assigned: Dict[str, str] = {}
        skipped: List[str] = []
        missing: List[str] = []

        for slot_name, slot_policy in DEFAULT_SLOT_POLICY.items():
            current_value = getattr(defaults, slot_name, None)
            if current_value:
                skipped.append(slot_name)
                continue

            model_type = str(slot_policy["type"])
            preferred_names = [str(item) for item in slot_policy["preferred"]]  # type: ignore[index]
            candidates = models_by_type.get(model_type, [])
            if not candidates:
                missing.append(f"{slot_name}:missing_{model_type}_model")
                continue

            selected: Optional[Dict] = None
            for preferred in preferred_names:
                variants = _policy_name_variants(preferred)
                selected = next(
                    (
                        model
                        for model in candidates
                        if _normalize_model_name_for_policy(str(model.get("name", "")))
                        in variants
                    ),
                    None,
                )
                if selected:
                    break
            if not selected:
                for preferred in preferred_names:
                    variants = _policy_name_variants(preferred)
                    selected = next(
                        (
                            model
                            for model in candidates
                            if any(
                                variant
                                in _normalize_model_name_for_policy(
                                    str(model.get("name", ""))
                                )
                                for variant in variants
                            )
                        ),
                        None,
                    )
                    if selected:
                        break
            if not selected:
                selected = candidates[0]

            model_id = str(selected.get("id", ""))
            if not model_id:
                missing.append(f"{slot_name}:invalid_model_record")
                continue
            setattr(defaults, slot_name, model_id)
            assigned[slot_name] = model_id

        if assigned:
            await defaults.update()

        return AutoAssignResult(assigned=assigned, skipped=skipped, missing=missing)

    except Exception as e:
        logger.error(f"Error auto-assigning defaults: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error auto-assigning defaults: {str(e)}"
        )
