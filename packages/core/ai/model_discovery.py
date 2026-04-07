"""
Model Discovery - Gemini-only runtime model discovery.

This module discovers available Google Gemini models from configured
credentials and can optionally register discovered models in the database.
"""

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Dict, List, Optional, Tuple

from packages.core.ai.google_genai_adapter import list_google_models
from packages.core.ai.key_provider import get_api_key
from packages.core.ai.models import Model
from packages.core.database.repository import repo_query
from packages.core.observability.logger import logger


@dataclass
class DiscoveredModel:
    """Represents a model discovered from a provider."""

    name: str
    provider: str
    model_type: str  # language, embedding, speech_to_text, text_to_speech
    description: Optional[str] = None


async def discover_google_models() -> List[DiscoveredModel]:
    """Fetch available models from Google Gemini API."""
    api_key = await get_api_key("google")
    if not api_key:
        return []

    try:
        discovered = await list_google_models(api_key)
        return [
            DiscoveredModel(
                name=str(item.get("name", "")),
                provider="google",
                model_type=str(item.get("model_type", "language")),
                description=(
                    str(item.get("description"))
                    if item.get("description") is not None
                    else None
                ),
            )
            for item in discovered
            if item.get("name")
        ]
    except Exception as exc:
        logger.exception(
            "Failed to discover Google models via google-genai error_type={}",
            type(exc).__name__,
        )
        return []


PROVIDER_DISCOVERY_FUNCTIONS = {
    "google": discover_google_models,
}


async def discover_provider_models(provider: str) -> List[DiscoveredModel]:
    """
    Discover available models for a specific provider.

    Args:
        provider: Provider name (google)

    Returns:
        List of discovered models
    """
    discover_func = PROVIDER_DISCOVERY_FUNCTIONS.get(provider)
    if discover_func is None:
        logger.warning(
            f"No discovery function for provider: {provider}. "
            "Gemini-only runtime supports only 'google'."
        )
        return []

    return await discover_func()


async def sync_provider_models(
    provider: str, auto_register: bool = True
) -> Tuple[int, int, int]:
    """
    Sync models for a provider: discover and optionally register in database.

    Args:
        provider: Provider name
        auto_register: If True, automatically create Model records in database

    Returns:
        Tuple of (discovered_count, new_count, existing_count)
    """
    provider_normalized = provider.strip().lower().replace("-", "_")
    discovered = await discover_provider_models(provider_normalized)
    discovered_count = len(discovered)
    new_count = 0
    existing_count = 0

    if not auto_register:
        return discovered_count, 0, 0

    if not discovered:
        return 0, 0, 0

    # Batch fetch existing models to avoid N+1 query pattern
    try:
        existing_models = await repo_query(
            "SELECT string::lowercase(name) as name, string::lowercase(type) as type FROM model "
            "WHERE provider = $provider",
            {"provider": provider_normalized},
        )
        # Create a set of (name, type) tuples for O(1) lookup
        existing_keys = set()
        for m in existing_models:
            existing_keys.add((m.get("name", ""), m.get("type", "")))
    except Exception as exc:
        logger.exception(
            "Failed to fetch existing models provider={} error_type={}",
            provider_normalized,
            type(exc).__name__,
        )
        existing_keys = set()

    for model in discovered:
        model_key = (model.name.lower(), model.model_type.lower())

        # Check if model already exists using pre-fetched data
        if model_key in existing_keys:
            existing_count += 1
            continue

        # Create new model
        try:
            new_model = Model(
                name=model.name,
                provider=model.provider,
                type=model.model_type,
            )
            await new_model.save()
            new_count += 1
            logger.info(
                f"Registered new model: {model.provider}/{model.name} ({model.model_type})"
            )
        except Exception as exc:
            logger.exception(
                "Failed to register model provider={} model={} type={} error_type={}",
                model.provider,
                model.name,
                model.model_type,
                type(exc).__name__,
            )

    logger.info(
        f"Synced {provider}: {discovered_count} discovered, "
        f"{new_count} new, {existing_count} existing"
    )
    return discovered_count, new_count, existing_count


async def sync_all_providers() -> Dict[str, Tuple[int, int, int]]:
    """
    Sync models for all configured providers.

    Returns:
        Dict mapping provider names to (discovered, new, existing) tuples
    """
    results: Dict[str, Tuple[int, int, int]] = {}

    # Run discovery for all providers in parallel
    tasks: List[Awaitable[Tuple[int, int, int]]] = []
    providers = list(PROVIDER_DISCOVERY_FUNCTIONS.keys())

    for provider in providers:
        tasks.append(sync_provider_models(provider, auto_register=True))

    task_results = await asyncio.gather(*tasks, return_exceptions=True)

    for provider, result in zip(providers, task_results):
        if isinstance(result, BaseException):
            logger.error(
                "Error syncing provider={} error_type={}",
                provider,
                type(result).__name__,
            )
            results[provider] = (0, 0, 0)
        else:
            results[provider] = result

    return results


async def get_provider_model_count(provider: str) -> Dict[str, int]:
    """
    Get count of registered models for a provider, grouped by type.

    Args:
        provider: Provider name (case-insensitive)

    Returns:
        Dict mapping model type to count
    """
    provider_normalized = provider.strip().lower().replace("-", "_")
    result = await repo_query(
        "SELECT type, count() as count FROM model WHERE provider = $provider GROUP BY type",
        {"provider": provider_normalized},
    )

    counts = {
        "language": 0,
        "embedding": 0,
        "speech_to_text": 0,
        "text_to_speech": 0,
    }

    for row in result:
        model_type = row.get("type")
        count = row.get("count", 0)
        if model_type in counts:
            counts[model_type] = count

    return counts
