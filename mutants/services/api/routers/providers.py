"""Provider policy API endpoints."""

from fastapi import APIRouter, HTTPException

from packages.core.ai.connection_tester import (
    _resolve_startup_gemini_model,
    _safe_public_error_message,
    probe_startup_gemini_model,
)
from packages.core.ai.models import DefaultModels
from packages.core.ai.provider_policy import get_provider_policy
from packages.core.application.models import (
    ProviderPolicyResponse,
    ProviderPolicyUpdateRequest,
)
from packages.core.domain.credential import Credential
from packages.core.observability.logger import logger

router = APIRouter(prefix="/providers", tags=["providers"])
SUPPORTED_PROVIDER = "google"


def _to_response(policy) -> ProviderPolicyResponse:
    return ProviderPolicyResponse(**policy.as_dict())


@router.get("/policy", response_model=ProviderPolicyResponse)
async def get_policy():
    """Get provider policy used for modality routing and fallback."""
    try:
        policy = await get_provider_policy()
        return _to_response(policy)
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        logger.error(
            "Provider policy fetch failed error_type={}",
            type(exc).__name__,
        )
        raise HTTPException(status_code=500, detail="Failed to fetch provider policy")


@router.put("/policy", response_model=ProviderPolicyResponse)
async def update_policy(request: ProviderPolicyUpdateRequest):
    """Update provider policy (Gemini-only)."""
    try:
        payload = request.model_dump(exclude_none=True)
        for key, providers in payload.items():
            if any(
                (provider or "").strip().lower().replace("-", "_") != SUPPORTED_PROVIDER
                for provider in providers
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"Only '{SUPPORTED_PROVIDER}' provider is supported by policy endpoint.",
                )

        policy = await get_provider_policy()
        for key, value in payload.items():
            setattr(policy, key, value)
        await policy.update()
        return _to_response(policy)
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        logger.error(
            "Provider policy update failed error_type={}",
            type(exc).__name__,
        )
        raise HTTPException(status_code=500, detail="Failed to update provider policy")


@router.get("/policy/bootstrap-diagnostics")
async def get_policy_bootstrap_diagnostics():
    """Get startup diagnostics for Gemini-only readiness."""
    try:
        probe_result = await probe_startup_gemini_model()
        missing_credentials: list[str] = []
        credentials = await Credential.get_by_provider(SUPPORTED_PROVIDER)
        if not credentials:
            missing_credentials.append(SUPPORTED_PROVIDER)

        defaults = await DefaultModels.get_instance()
        missing_default_model_slots: list[str] = []
        required_slots = [
            "default_chat_model",
            "default_transformation_model",
            "default_tools_model",
            "large_context_model",
            "default_embedding_model",
            "default_text_to_speech_model",
            "default_speech_to_text_model",
        ]
        for slot in required_slots:
            if not getattr(defaults, slot, None):
                missing_default_model_slots.append(slot)

        model_probe = probe_result.get("model_probe_result", {})
        success = bool(model_probe.get("success", False))
        blocked_reason = None
        if missing_credentials:
            blocked_reason = "missing_google_api_key"
        elif not success:
            blocked_reason = "gemini_model_probe_failed"
        if success:
            public_message = "Connection test succeeded."
        elif missing_credentials:
            public_message = "No Google API key configured"
        else:
            public_message = "Connection test failed. Check provider configuration and server logs."

        safe_remediation: list[str] = []
        if missing_credentials:
            safe_remediation = [
                "Set GEMINI_API_KEY, or add a Google credential in Settings -> API Keys.",
                "Restart the API after credentials are configured.",
            ]
        elif not success:
            safe_remediation = [
                "Verify Google API key permissions and network access to Gemini API.",
                "Re-run connection test in Settings -> API Keys and restart the API.",
            ]
        suggestions: list[str] = list(safe_remediation)
        if missing_credentials:
            suggestions.append(
                "Add missing provider credentials in Settings → API Keys: "
                + ", ".join(missing_credentials)
            )
        if missing_default_model_slots:
            suggestions.append(
                "Assign missing default models in Settings → Models: "
                + ", ".join(missing_default_model_slots)
            )
        if not suggestions:
            suggestions.append("Provider policy is fully configured for runtime.")
        key_source = "none" if missing_credentials else "unknown"
        return {
            "model_probe_result": {
                "provider": SUPPORTED_PROVIDER,
                "model": _resolve_startup_gemini_model(),
                "success": success,
                "message": public_message,
                "key_source": key_source,
            },
            "blocked_reason": blocked_reason,
            "remediation": safe_remediation,
            "missing_credentials": missing_credentials,
            "missing_default_model_slots": missing_default_model_slots,
            "suggestions": suggestions,
        }
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        logger.error(
            "Provider bootstrap diagnostics failed error_type={}",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=500, detail="Failed to build bootstrap diagnostics"
        )
