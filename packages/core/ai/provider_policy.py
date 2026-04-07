"""Provider policy management for Gemini-only runtime behavior."""

from __future__ import annotations

from typing import Dict, Iterable, List, Literal, TypedDict, cast

from pydantic import Field, field_validator

from packages.core.domain.base import RecordModel
from packages.core.observability.logger import logger

PolicyModality = Literal["language", "embedding", "speech_to_text", "text_to_speech"]

MODEL_TYPE_TO_MODALITY: dict[str, PolicyModality] = {
    "chat": "language",
    "transformation": "language",
    "tools": "language",
    "large_context": "language",
    "language": "language",
    "embedding": "embedding",
    "speech_to_text": "speech_to_text",
    "text_to_speech": "text_to_speech",
}

DEFAULT_PROVIDER_CHAIN: list[str] = ["google"]


class PolicyEffectiveness(TypedDict):
    effective: dict[PolicyModality, bool]
    active_provider: dict[PolicyModality, str | None]
    blocking_reason: dict[PolicyModality, str | None]


def _normalize_provider_name(provider: str) -> str:
    return provider.strip().lower().replace("-", "_")


def _normalize_chain(values: Iterable[str] | None) -> list[str]:
    """Normalize and enforce Gemini-only provider chain."""
    if values is None:
        return DEFAULT_PROVIDER_CHAIN.copy()
    for raw in values:
        provider = _normalize_provider_name(raw)
        if provider == "google":
            return DEFAULT_PROVIDER_CHAIN.copy()
    return DEFAULT_PROVIDER_CHAIN.copy()


class ProviderPolicy(RecordModel):
    """Runtime provider routing policy."""

    record_id = "open_notebook:provider_policy"
    language: List[str] = Field(default_factory=lambda: DEFAULT_PROVIDER_CHAIN.copy())
    embedding: List[str] = Field(default_factory=lambda: DEFAULT_PROVIDER_CHAIN.copy())
    speech_to_text: List[str] = Field(
        default_factory=lambda: DEFAULT_PROVIDER_CHAIN.copy()
    )
    text_to_speech: List[str] = Field(
        default_factory=lambda: DEFAULT_PROVIDER_CHAIN.copy()
    )

    @field_validator(
        "language",
        "embedding",
        "speech_to_text",
        "text_to_speech",
        mode="before",
    )
    @classmethod
    def normalize_policy_chain(cls, value: object) -> list[str]:
        if value is None:
            return DEFAULT_PROVIDER_CHAIN.copy()
        if isinstance(value, str):
            return _normalize_chain([value])
        if isinstance(value, (list, tuple, set)):
            return _normalize_chain([str(item) for item in value])
        return DEFAULT_PROVIDER_CHAIN.copy()

    def chain_for(self, modality: PolicyModality) -> list[str]:
        chain = getattr(self, modality, DEFAULT_PROVIDER_CHAIN.copy())
        return _normalize_chain(chain)

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "language": self.chain_for("language"),
            "embedding": self.chain_for("embedding"),
            "speech_to_text": self.chain_for("speech_to_text"),
            "text_to_speech": self.chain_for("text_to_speech"),
        }


async def get_provider_policy() -> ProviderPolicy:
    try:
        return cast(ProviderPolicy, await ProviderPolicy.get_instance())
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        logger.warning(
            f"Failed to load provider policy from database, using defaults: {exc}"
        )
        return ProviderPolicy()


def resolve_modality(model_type: str) -> PolicyModality:
    return MODEL_TYPE_TO_MODALITY.get(model_type, "language")


async def get_provider_chain_for_model_type(model_type: str) -> list[str]:
    policy = await get_provider_policy()
    return policy.chain_for(resolve_modality(model_type))


async def evaluate_policy_effectiveness(
    configured: Dict[str, bool],
) -> PolicyEffectiveness:
    policy = await get_provider_policy()
    result: PolicyEffectiveness = {
        "effective": {},
        "active_provider": {},
        "blocking_reason": {},
    }

    for modality in ("language", "embedding", "speech_to_text", "text_to_speech"):
        chain = policy.chain_for(modality)
        active = next(
            (provider for provider in chain if configured.get(provider, False)), None
        )
        is_effective = active is not None
        result["effective"][modality] = is_effective
        result["active_provider"][modality] = active
        result["blocking_reason"][modality] = (
            None
            if is_effective
            else f"No configured provider available in chain: {', '.join(chain)}"
        )

    return result
