"""Credential and provider policy API schemas."""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ApiKeyStatusResponse(BaseModel):
    """Response showing which providers are configured and their source."""

    configured: Dict[str, bool] = Field(
        ..., description="Map of provider name to whether it is configured"
    )
    source: Dict[str, Literal["environment", "none"]] = Field(
        ...,
        description="Map of provider name to configuration source (environment or none)",
    )
    legacy_env_detected: Dict[str, bool] = Field(
        ...,
        description="Map of provider name to whether legacy provider ENV variables are present",
    )
    encryption_configured: bool = Field(
        ...,
        description="Whether OPEN_NOTEBOOK_ENCRYPTION_KEY is set (required to store keys in database)",
    )
    policy_effective: Dict[
        Literal["language", "embedding", "speech_to_text", "text_to_speech"], bool
    ] = Field(
        default_factory=dict,
        description="Whether each modality has at least one configured provider in policy chain",
    )
    policy_active_provider: Dict[
        Literal["language", "embedding", "speech_to_text", "text_to_speech"],
        Optional[str],
    ] = Field(
        default_factory=dict,
        description="Currently active provider per modality according to policy chain",
    )
    policy_blockers: Dict[
        Literal["language", "embedding", "speech_to_text", "text_to_speech"],
        Optional[str],
    ] = Field(
        default_factory=dict,
        description="Blocking reason per modality when policy is not effective",
    )
    provider_capabilities: Dict[str, Dict[str, Dict[str, str]]] = Field(
        default_factory=dict,
        description=(
            "Provider capability matrix by modality. "
            "Each modality contains {status: supported|preview|unsupported, detail: string}."
        ),
    )


class ProviderPolicyResponse(BaseModel):
    """Provider fallback policy for each modality."""

    language: List[str] = Field(..., description="Provider order for language models")
    embedding: List[str] = Field(..., description="Provider order for embedding models")
    speech_to_text: List[str] = Field(
        ..., description="Provider order for speech-to-text models"
    )
    text_to_speech: List[str] = Field(
        ..., description="Provider order for text-to-speech models"
    )


class ProviderPolicyUpdateRequest(BaseModel):
    """Partial update request for provider fallback policy."""

    language: Optional[List[str]] = None
    embedding: Optional[List[str]] = None
    speech_to_text: Optional[List[str]] = None
    text_to_speech: Optional[List[str]] = None


class ProviderBootstrapDiagnosticsResponse(BaseModel):
    """Runtime readiness diagnostics for Gemini-only policy."""

    missing_credentials: List[str] = Field(
        default_factory=list,
        description="Providers missing credentials for policy execution",
    )
    missing_default_model_slots: List[str] = Field(
        default_factory=list,
        description="Default model slots not configured yet",
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Actionable remediation suggestions",
    )


class TestConnectionResponse(BaseModel):
    """Response from testing a provider connection."""

    provider: str = Field(..., description="Provider name that was tested")
    success: bool = Field(..., description="Whether connection test succeeded")
    message: str = Field(..., description="Result message with details")


class MigrationResult(BaseModel):
    """Response from migration operations."""

    message: str = Field(..., description="Summary message")
    migrated: List[str] = Field(
        default_factory=list, description="Providers successfully migrated"
    )
    skipped: List[str] = Field(
        default_factory=list, description="Providers skipped (already in DB)"
    )
    errors: List[str] = Field(
        default_factory=list, description="Migration errors by provider"
    )


class CreateCredentialRequest(BaseModel):
    """Request to create a new credential."""

    name: str = Field(..., description="Credential name")
    provider: str = Field(
        ..., description="Provider name (Gemini-only runtime supports 'google')"
    )
    modalities: List[str] = Field(
        default_factory=list,
        description="Supported modalities (language, embedding, text_to_speech, speech_to_text)",
    )
    api_key: Optional[str] = Field(None, description="API key (stored encrypted)")
    base_url: Optional[str] = Field(None, description="Base URL")
    endpoint: Optional[str] = Field(None, description="Endpoint URL (Azure)")
    api_version: Optional[str] = Field(None, description="API version (Azure)")
    endpoint_llm: Optional[str] = Field(None, description="LLM endpoint")
    endpoint_embedding: Optional[str] = Field(None, description="Embedding endpoint")
    endpoint_stt: Optional[str] = Field(None, description="STT endpoint")
    endpoint_tts: Optional[str] = Field(None, description="TTS endpoint")
    project: Optional[str] = Field(None, description="Project ID (Vertex)")
    location: Optional[str] = Field(None, description="Location (Vertex)")
    credentials_path: Optional[str] = Field(
        None, description="Credentials file path (Vertex)"
    )


class UpdateCredentialRequest(BaseModel):
    """Request to update an existing credential."""

    name: Optional[str] = Field(None, description="Credential name")
    modalities: Optional[List[str]] = Field(None, description="Supported modalities")
    api_key: Optional[str] = Field(None, description="API key (stored encrypted)")
    base_url: Optional[str] = Field(None, description="Base URL")
    endpoint: Optional[str] = Field(None, description="Endpoint URL")
    api_version: Optional[str] = Field(None, description="API version")
    endpoint_llm: Optional[str] = Field(None, description="LLM endpoint")
    endpoint_embedding: Optional[str] = Field(None, description="Embedding endpoint")
    endpoint_stt: Optional[str] = Field(None, description="STT endpoint")
    endpoint_tts: Optional[str] = Field(None, description="TTS endpoint")
    project: Optional[str] = Field(None, description="Project ID")
    location: Optional[str] = Field(None, description="Location")
    credentials_path: Optional[str] = Field(None, description="Credentials path")


class CredentialResponse(BaseModel):
    """Response for a credential (never includes api_key)."""

    id: str
    name: str
    provider: str
    modalities: List[str]
    base_url: Optional[str] = None
    endpoint: Optional[str] = None
    api_version: Optional[str] = None
    endpoint_llm: Optional[str] = None
    endpoint_embedding: Optional[str] = None
    endpoint_stt: Optional[str] = None
    endpoint_tts: Optional[str] = None
    project: Optional[str] = None
    location: Optional[str] = None
    credentials_path: Optional[str] = None
    has_api_key: bool = False
    created: str
    updated: str
    model_count: int = 0


class CredentialDeleteResponse(BaseModel):
    """Response for credential deletion."""

    message: str
    deleted_models: int = 0


class DiscoveredModelResponse(BaseModel):
    """A model discovered from a provider."""

    name: str
    provider: str
    model_type: Optional[str] = None
    description: Optional[str] = None


class DiscoverModelsResponse(BaseModel):
    """Response from model discovery."""

    credential_id: str
    provider: str
    discovered: List[DiscoveredModelResponse]


class RegisterModelData(BaseModel):
    """A model to register with user-specified type."""

    name: str
    provider: str
    model_type: str  # Required: user specifies the type


class RegisterModelsRequest(BaseModel):
    """Request to register discovered models."""

    models: List[RegisterModelData]


class RegisterModelsResponse(BaseModel):
    """Response from model registration."""

    created: int
    existing: int
