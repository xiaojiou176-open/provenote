"""
Credentials Service

Business logic for managing AI provider credentials.
Extracted from the credentials router to follow the service layer pattern.

All functions raise ValueError for business errors (router converts to HTTPException).
"""

import ipaddress
import socket
from typing import Dict, List
from urllib.parse import urlparse

from packages.core.ai.google_genai_adapter import (
    build_google_capability_matrix,
    list_google_models,
    test_google_connection,
)
from packages.core.ai.connection_tester import _safe_public_error_message
from packages.core.ai.model_strategy import GEMINI_MODEL_FLASH_30
from packages.core.ai.provider_policy import evaluate_policy_effectiveness
from packages.core.application.models import CredentialResponse
from packages.core.database.repository import repo_query
from packages.core.domain.credential import Credential
from packages.core.observability.logger import logger
from packages.core.settings import detect_legacy_provider_env, read_env
from packages.core.utils.encryption import get_secret_from_env

# =============================================================================
# Constants
# =============================================================================

PROVIDER_ENV_CONFIG: Dict[str, dict] = {
    "google": {
        "required": ["GEMINI_API_KEY"],
        "optional": ["GEMINI_MODEL"],
    },
}

PROVIDER_MODALITIES: Dict[str, List[str]] = {
    "google": ["language", "embedding", "speech_to_text", "text_to_speech"],
}


# =============================================================================
# URL Validation (SSRF protection)
# =============================================================================


def validate_url(url: str, provider: str) -> None:
    """
    Validate URL format for API endpoints.

    This is a self-hosted application, so we allow:
    - Private IPs (10.x, 172.16-31.x, 192.168.x) for self-hosted services
    - Localhost for local services (Ollama, LM Studio, etc.)

    We only block:
    - Invalid schemes (must be http or https)
    - Malformed URLs
    - Link-local addresses (169.254.x.x) - used for cloud metadata endpoints
    - Hostnames that resolve to link-local addresses

    Args:
        url: The URL to validate
        provider: The provider name (for logging/context)

    Raises:
        ValueError: If the URL is invalid
    """
    if not url or not url.strip():
        return  # Empty URLs handled elsewhere

    try:
        parsed = urlparse(url.strip())

        # Validate scheme - only http/https allowed
        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"Invalid URL scheme: '{parsed.scheme}'. Only http and https are allowed."
            )

        # Extract hostname
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("Invalid URL: hostname could not be determined.")

        # Try to parse as IP address to check for dangerous addresses
        try:
            ip = ipaddress.ip_address(hostname)

            # Block link-local addresses (169.254.x.x) - used for cloud metadata
            # These are dangerous as they can expose cloud instance credentials
            if ip.is_link_local:
                raise ValueError(
                    "Link-local addresses (169.254.x.x) are not allowed for security reasons. "
                    "These addresses are used for cloud metadata endpoints."
                )

            # Block IPv4-mapped IPv6 addresses pointing to link-local
            # e.g. ::ffff:169.254.169.254 bypasses IPv6 is_link_local check
            if (
                hasattr(ip, "ipv4_mapped")
                and ip.ipv4_mapped
                and ip.ipv4_mapped.is_link_local
            ):
                raise ValueError(
                    "Link-local addresses (169.254.x.x) are not allowed for security reasons. "
                    "These addresses are used for cloud metadata endpoints."
                )

        except ValueError as ve:
            # Re-raise our own ValueErrors
            if "Link-local" in str(ve) or "Invalid URL" in str(ve):
                raise
            # Not an IP address, it's a hostname - need to resolve and check
            try:
                # Resolve hostname to IP address
                resolved_ips = socket.getaddrinfo(hostname, None)
                for family, _, _, _, sockaddr in resolved_ips:
                    ip_addr = sockaddr[0]
                    try:
                        parsed_ip = ipaddress.ip_address(ip_addr)
                        if parsed_ip.is_link_local:
                            raise ValueError(
                                f"Hostname '{hostname}' resolves to a link-local address (169.254.x.x) which is not allowed for security reasons. "
                                "These addresses are used for cloud metadata endpoints."
                            )
                        # Block IPv4-mapped IPv6 addresses pointing to link-local
                        if (
                            hasattr(parsed_ip, "ipv4_mapped")
                            and parsed_ip.ipv4_mapped
                            and parsed_ip.ipv4_mapped.is_link_local
                        ):
                            raise ValueError(
                                f"Hostname '{hostname}' resolves to a link-local address (169.254.x.x) which is not allowed for security reasons. "
                                "These addresses are used for cloud metadata endpoints."
                            )
                    except ValueError as inner_ve:
                        if "link-local" in str(inner_ve).lower() or "Link-local" in str(
                            inner_ve
                        ):
                            raise
                        # Skip non-IP addresses (e.g., IPv6 zones)
                        continue
            except socket.gaierror:
                # Could not resolve hostname - allow it since the URL may be
                # valid in the deployment environment (e.g., Azure endpoints,
                # internal DNS names). We only block link-local addresses.
                pass

    except ValueError:
        raise
    except Exception:
        raise ValueError("Invalid URL format. Check server logs for details.")


# =============================================================================
# Helpers
# =============================================================================


def require_encryption_key() -> None:
    """Raise ValueError if encryption key is not configured."""
    if not get_secret_from_env("OPEN_NOTEBOOK_ENCRYPTION_KEY"):
        raise ValueError(
            "Encryption key not configured. "
            "Set OPEN_NOTEBOOK_ENCRYPTION_KEY to enable storing API keys."
        )


def credential_to_response(
    cred: Credential, model_count: int = 0
) -> CredentialResponse:
    """Convert a Credential domain object to API response."""
    return CredentialResponse(
        id=cred.id or "",
        name=cred.name,
        provider=cred.provider,
        modalities=cred.modalities,
        base_url=cred.base_url,
        endpoint=cred.endpoint,
        api_version=cred.api_version,
        endpoint_llm=cred.endpoint_llm,
        endpoint_embedding=cred.endpoint_embedding,
        endpoint_stt=cred.endpoint_stt,
        endpoint_tts=cred.endpoint_tts,
        project=cred.project,
        location=cred.location,
        credentials_path=cred.credentials_path,
        has_api_key=cred.api_key is not None,
        created=str(cred.created) if cred.created else "",
        updated=str(cred.updated) if cred.updated else "",
        model_count=model_count,
    )


# =============================================================================
# Service Functions
# =============================================================================


async def get_provider_status() -> dict:
    """
    Get configuration status: encryption key status, and per-provider
    configured/source information.
    """
    encryption_configured = bool(get_secret_from_env("OPEN_NOTEBOOK_ENCRYPTION_KEY"))

    configured: Dict[str, bool] = {}
    source: Dict[str, str] = {}
    legacy_env_detected: Dict[str, bool] = detect_legacy_provider_env()

    for provider in PROVIDER_ENV_CONFIG:
        env_configured = False
        if provider == "google":
            env_configured = bool(read_env("GEMINI_API_KEY", ""))

        try:
            db_credentials = await Credential.get_by_provider(provider)
            db_configured = len(db_credentials) > 0
        except Exception:
            db_configured = False

        configured[provider] = env_configured or db_configured
        source[provider] = "environment" if env_configured else "none"
        legacy_env_detected.setdefault(provider, False)

    policy_effectiveness = await evaluate_policy_effectiveness(configured)
    try:
        google_models = await repo_query(
            "SELECT name FROM model WHERE provider = 'google' AND name != NONE",
            {},
        )
    except (RuntimeError, ValueError, TypeError, OSError):
        google_models = []
    google_model_names = [
        str(item.get("name", "")) for item in google_models if item.get("name")
    ]
    provider_capabilities = {
        "google": build_google_capability_matrix(google_model_names),
    }

    return {
        "configured": configured,
        "source": source,
        "legacy_env_detected": legacy_env_detected,
        "encryption_configured": encryption_configured,
        "policy_effective": policy_effectiveness["effective"],
        "policy_active_provider": policy_effectiveness["active_provider"],
        "policy_blockers": policy_effectiveness["blocking_reason"],
        "provider_capabilities": provider_capabilities,
    }


async def test_credential(credential_id: str) -> dict:
    """
    Test connection using a credential's configuration.

    Returns dict with provider, success, message keys.
    """
    provider = "unknown"
    try:
        cred = await Credential.get(credential_id)
        provider = cred.provider.lower()
        if provider != "google":
            return {
                "provider": provider,
                "success": False,
                "message": "Only Google provider is supported in Gemini-only mode",
            }

        config = cred.to_esperanto_config()
        success, message = await test_google_connection(
            config.get("api_key", ""),
            GEMINI_MODEL_FLASH_30,
        )
        return {
            "provider": provider,
            "success": success,
            "message": message if success else _safe_public_error_message(message),
        }

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            return {
                "provider": provider,
                "success": False,
                "message": "Invalid API key",
            }
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            return {
                "provider": provider,
                "success": False,
                "message": "API key lacks required permissions",
            }
        elif "rate" in error_msg.lower() and "limit" in error_msg.lower():
            return {
                "provider": provider,
                "success": True,
                "message": "Rate limited - but connection works",
            }
        elif "not found" in error_msg.lower() and "model" in error_msg.lower():
            return {
                "provider": provider,
                "success": True,
                "message": "API key valid (test model not available)",
            }
        else:
            logger.debug(f"Test connection error for credential {credential_id}: {e}")
            return {
                "provider": provider,
                "success": False,
                "message": _safe_public_error_message(error_msg),
            }


async def discover_with_config(provider: str, config: dict) -> List[dict]:
    """
    Discover models using explicit config instead of env vars.

    Returns model names only — no type classification.
    The user chooses the model type when registering.
    """
    provider = provider.strip().lower().replace("-", "_")
    if provider != "google":
        logger.warning(f"Rejected non-google provider discovery request: {provider}")
        return []

    models = await list_google_models(config.get("api_key", ""))
    return [
        {
            "name": str(item.get("name", "")),
            "provider": "google",
            "description": item.get("description"),
        }
        for item in models
        if item.get("name")
    ]


async def register_models(credential_id: str, models_data: list) -> dict:
    """
    Register discovered models and link them to a credential.

    Args:
        credential_id: The credential ID to link models to
        models_data: List of dicts with name, provider, model_type

    Returns:
        dict with created and existing counts
    """
    cred = await Credential.get(credential_id)
    if cred.provider.lower() != "google":
        raise ValueError("Only Google credential model registration is supported")

    from packages.core.ai.models import Model
    from packages.core.database.repository import repo_query

    # Batch fetch existing models for this provider
    existing_models = await repo_query(
        "SELECT string::lowercase(name) as name, string::lowercase(type) as type FROM model "
        "WHERE provider = $provider",
        {"provider": cred.provider.lower().replace("-", "_")},
    )
    existing_keys = {(m["name"], m["type"]) for m in existing_models}

    created = 0
    existing = 0

    for model_data in models_data:
        model_provider = (
            (model_data.provider or cred.provider).lower().replace("-", "_")
        )
        if model_provider != "google":
            raise ValueError("Only Google provider models can be registered")
        key = (model_data.name.lower(), model_data.model_type.lower())
        if key in existing_keys:
            existing += 1
            continue

        new_model = Model(
            name=model_data.name,
            provider=model_provider,
            type=model_data.model_type,
            credential=cred.id,
        )
        await new_model.save()
        created += 1

    return {"created": created, "existing": existing}
