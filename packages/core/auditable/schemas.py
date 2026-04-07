from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SourceParagraph(BaseModel):
    pid: str
    order: int
    raw_text: str
    canonical_text: str
    canonical_hash: str
    source_id: Optional[str] = None
    source_title: Optional[str] = None


class DedupEntry(BaseModel):
    pid: str
    text: str
    status: Literal["core", "duplicate_exact", "duplicate_near"]
    duplicate_of: Optional[str] = None
    similarity: Optional[float] = None


class AuditableSection(BaseModel):
    title: str
    bullets: list[str]
    source_pids: list[str] = Field(default_factory=list)


class AuditableClaim(BaseModel):
    text: str
    source_pids: list[str]


class AuditableLLMOutput(BaseModel):
    sections: list[AuditableSection]
    claims: list[AuditableClaim]
    dedup_groups: list[dict[str, Any]] = Field(default_factory=list)
    unclassified_pids: list[str] = Field(default_factory=list)


class CoverageJSON(BaseModel):
    total_pids: int
    covered_pids: int
    coverage_rate: float
    missing_pids: list[str] = Field(default_factory=list)
    duplicate_pids: list[str] = Field(default_factory=list)
    unknown_pids: list[str] = Field(default_factory=list)
    unclassified_pids: list[str] = Field(default_factory=list)


class DedupJSON(BaseModel):
    exact_groups: list[dict[str, Any]] = Field(default_factory=list)
    near_groups: list[dict[str, Any]] = Field(default_factory=list)
    group_count: int = 0


class AuditableMetrics(BaseModel):
    coverage_rate: float
    missing_count: int
    duplicate_count: int
    uncited_claims_count: int
    dedup_group_count: int
    unknown_pid_count: int
    unclassified_count: int


class AuditableBuildResult(BaseModel):
    model_id: str
    language: str
    near_dedup_threshold: float
    source_paragraphs: list[SourceParagraph]
    sections: list[AuditableSection]
    claims: list[AuditableClaim]
    dedup_entries: list[DedupEntry]
    metrics: AuditableMetrics
    coverage_json: CoverageJSON
    dedup_json: DedupJSON
    result_markdown: str
