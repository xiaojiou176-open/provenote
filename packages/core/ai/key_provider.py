"""API key helpers backed by database credentials."""

from typing import Optional

from packages.core.domain.credential import Credential
from packages.core.observability.logger import logger

# =============================================================================
# Provider Registration
# =============================================================================
SIMPLE_PROVIDERS = ("google",)

_PROVISIONED_PROVIDER_CONFIG: dict[str, dict[str, str]] = {}


def _normalize_provider(provider: str) -> str:
    """Normalize provider name to internal snake_case."""
    return provider.lower().replace("-", "_")


def _cache_provider_config(provider: str, cred: Optional[Credential]) -> bool:
    """Store provider config in in-memory runtime cache (no global ENV writes)."""
    normalized_provider = _normalize_provider(provider)
    if not cred:
        _PROVISIONED_PROVIDER_CONFIG.pop(normalized_provider, None)
        return False

    raw_config = cred.to_esperanto_config()
    config = {k: str(v) for k, v in raw_config.items() if v is not None}
    if not config:
        _PROVISIONED_PROVIDER_CONFIG.pop(normalized_provider, None)
        return False

    _PROVISIONED_PROVIDER_CONFIG[normalized_provider] = config
    logger.debug("Cached runtime provider config for {}", normalized_provider)
    return True


def get_provisioned_provider_config(provider: str) -> dict[str, str]:
    """Return in-memory provisioned provider config for current process."""
    return dict(_PROVISIONED_PROVIDER_CONFIG.get(_normalize_provider(provider), {}))


async def _get_default_credential(provider: str) -> Optional[Credential]:
    """Get the first credential for a provider from the database."""
    try:
        credentials = await Credential.get_by_provider(provider)
        if credentials:
            return credentials[0]
    except Exception as e:
        logger.debug(f"Could not load credential from database for {provider}: {e}")
    return None


async def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for a provider from database credentials only.

    Args:
        provider: Provider name (runtime uses "google" for Gemini).

    Returns:
        API key string or None if not configured
    """
    cred = await _get_default_credential(provider)
    if cred and cred.api_key:
        logger.debug(f"Using {provider} API key from Credential")
        return cred.api_key.get_secret_value()

    return None


async def _provision_simple_provider(provider: str) -> bool:
    """
    Cache provider config for a simple provider from DB config.

    Returns:
        True if config was cached from database, False otherwise
    """
    provider_lower = provider.lower()
    if provider_lower not in SIMPLE_PROVIDERS:
        return False

    cred = await _get_default_credential(provider_lower)
    return _cache_provider_config(provider_lower, cred)


async def provision_provider_keys(provider: str) -> bool:
    """
    Provision provider config from database into runtime in-memory cache.

    This function checks if the provider has a Credential record stored in the
    database and caches the corresponding runtime config. This avoids mutating
    process-global environment variables with sensitive values.

    Args:
        provider: Provider name. In current Gemini-only runtime mode,
                  only "google" is supported.

    Returns:
        True if any provider config values were cached from database, False otherwise

    Example:
        # Before provisioning a model, ensure DB credential config is cached
        await provision_provider_keys("google")
        model = AIFactory.create_language(
            model_name="gemini-3.0-flash",
            provider="google",
        )
    """
    # Normalize provider name
    provider_lower = _normalize_provider(provider)

    if provider_lower != "google":
        logger.warning(
            "Provision request for unsupported provider '{}' was ignored in Gemini-only mode.",
            provider_lower,
        )
        return False

    return await _provision_simple_provider(provider_lower)


async def provision_all_keys() -> dict[str, bool]:
    """
    Provision runtime provider config cache from database for all providers.

    NOTE: This function is deprecated for request-time use because it can leave
    stale cache entries after key deletion. Configs should only be provisioned at startup
    or via provision_provider_keys() for specific providers.

    Useful at application startup to load all DB-stored provider configs.

    Returns:
        Dict mapping provider names to whether keys were set from DB
    """
    results: dict[str, bool] = {}

    # Simple providers
    for provider in SIMPLE_PROVIDERS:
        results[provider] = await provision_provider_keys(provider)

    return results
