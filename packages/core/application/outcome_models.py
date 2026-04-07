from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from packages.core.ai.model_strategy import GEMINI_DEFAULT_FAST_PATH_MODEL


class SourceProcessingReportResponse(BaseModel):
    source_id: str = Field(..., description="Source ID")
    source_type: str = Field(..., description="Source type")
    title: Optional[str] = Field(None, description="Source title")
    processing_status: Optional[str] = Field(
        None, description="Current processing status"
    )
    processing_message: str = Field(
        ..., description="Human-readable processing summary"
    )
    processing_engine: Optional[str] = Field(
        None, description="Detected processing engine if available"
    )
    extracted_length: int = Field(
        ..., description="Extracted text length in characters"
    )
    paragraph_count: int = Field(..., description="Extracted paragraph count")
    embedded: bool = Field(..., description="Whether embeddings exist")
    embedded_chunks: int = Field(..., description="Number of embedded chunks")
    insights_count: int = Field(..., description="Insight count for this source")
    has_file: bool = Field(..., description="Whether this source has a file payload")
    file_available: Optional[bool] = Field(
        None, description="Whether the original uploaded file is still available"
    )
    command_id: Optional[str] = Field(None, description="Last processing command ID")
    processing_info: Optional[Dict[str, Any]] = Field(
        None, description="Detailed backend processing metadata"
    )


class AuditableRunCreateRequest(BaseModel):
    model_id: str = Field(
        GEMINI_DEFAULT_FAST_PATH_MODEL, description="Model name for auditable run"
    )
    language: str = Field("zh-CN", description="Target language")
    near_dedup_threshold: float = Field(
        0.97, ge=0.0, le=1.0, description="Near-duplicate threshold"
    )


class AuditableMetrics(BaseModel):
    coverage_rate: float
    missing_count: int
    duplicate_count: int
    uncited_claims_count: int
    dedup_group_count: int
    unknown_pid_count: int
    unclassified_count: int


class AuditableRunResponse(BaseModel):
    id: str
    source_id: str
    status: Literal["queued", "running", "completed", "failed"]
    model_id: str
    language: str
    near_dedup_threshold: float
    metrics: AuditableMetrics
    coverage_json: Dict[str, Any]
    dedup_json: Dict[str, Any]
    result_markdown: str
    source_paragraphs: List[Dict[str, Any]] = Field(default_factory=list)
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    dedup_entries: List[Dict[str, Any]] = Field(default_factory=list)
    created: str
    updated: str


class AuditableBatchRequest(BaseModel):
    source_ids: List[str] = Field(..., min_length=1, description="Source ID list")
    model_id: str = Field(
        GEMINI_DEFAULT_FAST_PATH_MODEL, description="Model name for auditable run"
    )
    language: str = Field("zh-CN", description="Target language")
    near_dedup_threshold: float = Field(
        0.97, ge=0.0, le=1.0, description="Near-duplicate threshold"
    )

    @field_validator("source_ids")
    @classmethod
    def validate_source_ids(cls, value: List[str]) -> List[str]:
        normalized = [item.strip() for item in value if item and item.strip()]
        if not normalized:
            raise ValueError("source_ids cannot be empty")
        return normalized


class AuditableBatchResponse(BaseModel):
    run_ids: List[str]


class AuditableRepairRequest(BaseModel):
    target_index: int = Field(..., ge=0, description="Claim or section index to repair")
    model_id: Optional[str] = Field(
        None, description="Optional model override for targeted repair"
    )


class DraftCreateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Optional draft title")
    source_ids: List[str] = Field(
        ..., min_length=1, description="Source IDs to include in the draft"
    )
    note_ids: List[str] = Field(
        default_factory=list,
        description="Optional note IDs reserved for future draft enrichment",
    )
    thread_ids: List[str] = Field(
        default_factory=list,
        description="Optional research thread IDs reserved for future draft enrichment",
    )
    model_id: str = Field(
        GEMINI_DEFAULT_FAST_PATH_MODEL,
        description="Model name for notebook draft generation",
    )
    language: str = Field("zh-CN", description="Target language")
    near_dedup_threshold: float = Field(
        0.97, ge=0.0, le=1.0, description="Near-duplicate threshold"
    )

    @field_validator("source_ids")
    @classmethod
    def validate_source_ids(cls, value: List[str]) -> List[str]:
        normalized = [item.strip() for item in value if item and item.strip()]
        if not normalized:
            raise ValueError("source_ids cannot be empty")
        return normalized

    @field_validator("note_ids", "thread_ids")
    @classmethod
    def validate_optional_ids(cls, value: List[str]) -> List[str]:
        return [item.strip() for item in value if item and item.strip()]


class DraftRerunRequest(BaseModel):
    title: Optional[str] = Field(None, description="Optional replacement title")
    source_ids: Optional[List[str]] = Field(
        None, description="Optional replacement source IDs"
    )
    note_ids: Optional[List[str]] = Field(
        None, description="Optional replacement note IDs"
    )
    thread_ids: Optional[List[str]] = Field(
        None, description="Optional replacement thread IDs"
    )
    model_id: Optional[str] = Field(None, description="Optional replacement model ID")
    language: Optional[str] = Field(None, description="Optional replacement language")
    near_dedup_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Optional replacement dedup threshold"
    )

    @field_validator("source_ids", "note_ids", "thread_ids")
    @classmethod
    def validate_optional_id_lists(
        cls, value: Optional[List[str]]
    ) -> Optional[List[str]]:
        if value is None:
            return None
        normalized = [item.strip() for item in value if item and item.strip()]
        if not normalized:
            raise ValueError("replacement ID lists cannot be empty when provided")
        return normalized


class DraftResponse(BaseModel):
    id: str
    notebook_id: str
    title: str
    status: Literal["queued", "running", "completed", "failed", "verified"]
    model_id: str
    language: str
    near_dedup_threshold: float
    source_ids: List[str] = Field(default_factory=list)
    note_ids: List[str] = Field(default_factory=list)
    thread_ids: List[str] = Field(default_factory=list)
    version: int = Field(..., description="Draft version number")
    parent_draft_id: Optional[str] = Field(
        None, description="Parent draft ID when this draft is a rerun revision"
    )
    metrics: AuditableMetrics
    coverage_json: Dict[str, Any]
    dedup_json: Dict[str, Any]
    result_markdown: str
    source_paragraphs: List[Dict[str, Any]] = Field(default_factory=list)
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    dedup_entries: List[Dict[str, Any]] = Field(default_factory=list)
    verified_brief_snapshot: Optional[Dict[str, Any]] = None
    created: str
    updated: str


class ResearchThreadCreateRequest(BaseModel):
    title: str = Field(..., description="Research thread title")
    seed_kind: Literal["search", "ask", "notebook_chat", "insight"] = Field(
        ..., description="Canonical seed type for the thread"
    )
    source_ids: List[str] = Field(
        default_factory=list, description="Attached source IDs"
    )
    note_ids: List[str] = Field(default_factory=list, description="Attached note IDs")
    question: Optional[str] = Field(None, description="Question or query text")
    answer: Optional[str] = Field(None, description="Saved answer text")
    insight_id: Optional[str] = Field(
        None, description="Origin source insight ID for insight-seeded threads"
    )
    insight_type: Optional[str] = Field(
        None, description="Origin insight type for insight-seeded threads"
    )
    search_results: List[Dict[str, Any]] = Field(
        default_factory=list, description="Saved search result snapshots"
    )

    @model_validator(mode="after")
    def validate_insight_seed_requires_provenance(
        self,
    ) -> "ResearchThreadCreateRequest":
        if self.seed_kind == "insight" and not (self.insight_id or "").strip():
            raise ValueError("insight_id is required when seed_kind='insight'")
        return self


class ResearchThreadEntryRequest(BaseModel):
    entry_type: Literal[
        "search_result", "answer_snapshot", "note_snapshot", "insight_snapshot"
    ] = Field(..., description="Entry type")
    title: Optional[str] = Field(None, description="Entry title")
    content: str = Field(..., description="Entry content")
    source_ids: List[str] = Field(
        default_factory=list, description="Related source IDs"
    )
    note_ids: List[str] = Field(default_factory=list, description="Related note IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Entry metadata")


class ResearchThreadResponse(BaseModel):
    id: str
    notebook_id: str
    title: str
    seed_kind: Literal["search", "ask", "notebook_chat", "insight"]
    source_ids: List[str] = Field(default_factory=list)
    note_ids: List[str] = Field(default_factory=list)
    entries: List[Dict[str, Any]] = Field(default_factory=list)
    entry_count: int = 0
    created: str
    updated: str
