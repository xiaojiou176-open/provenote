from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

from packages.core.ai.model_strategy import GEMINI_MODEL_PRO_31
from packages.core.auditable.coverage_validator import build_coverage_report
from packages.core.auditable.dedup_engine import build_dedup_entries
from packages.core.auditable.markdown_renderer import render_markdown
from packages.core.auditable.paragraph_indexer import index_source_paragraphs
from packages.core.auditable.schemas import (
    AuditableBuildResult,
    AuditableClaim,
    AuditableLLMOutput,
    AuditableMetrics,
    AuditableSection,
    CoverageJSON,
    DedupEntry,
    DedupJSON,
    SourceParagraph,
)


@dataclass(frozen=True)
class CoreParagraph:
    pid: str
    text: str


@dataclass(frozen=True)
class AppendixEntry:
    pid: str
    text: str
    status: str
    duplicate_of: Optional[str] = None
    similarity: Optional[float] = None


@dataclass(frozen=True)
class LegacyAuditableBuildResult:
    model: str
    language: str
    near_dedup_threshold: float
    total_paragraphs: int
    unique_paragraphs: int
    duplicate_exact_count: int
    duplicate_near_count: int
    coverage_ratio: float
    pid_sequence: list[str]
    missing_pids: list[str]
    core: list[CoreParagraph]
    appendix: list[AppendixEntry]
    markdown: str

    def core_as_dict(self) -> list[dict]:
        return [asdict(item) for item in self.core]

    def appendix_as_dict(self) -> list[dict]:
        return [asdict(item) for item in self.appendix]


# Backward-compatibility helpers used by existing tests/integrations


def split_paragraphs_with_pid(text: str) -> list[CoreParagraph]:
    paragraphs = index_source_paragraphs(text)
    return [CoreParagraph(pid=p.pid, text=p.raw_text) for p in paragraphs]


def compute_coverage(
    expected_pids: list[str], observed_pids: list[str]
) -> tuple[float, list[str]]:
    if not expected_pids:
        return 1.0, []
    expected_set = set(expected_pids)
    observed_set = set(observed_pids)
    missing = sorted(expected_set - observed_set)
    ratio = (len(expected_set) - len(missing)) / len(expected_set)
    return ratio, missing


def _build_sections_and_claims(
    source_paragraphs: list[SourceParagraph],
    dedup_entries: list[DedupEntry],
    llm_output: Optional[AuditableLLMOutput] = None,
) -> tuple[list[AuditableSection], list[AuditableClaim], list[str]]:
    if llm_output:
        return llm_output.sections, llm_output.claims, llm_output.unclassified_pids

    core_entries = [entry for entry in dedup_entries if entry.status == "core"]

    section = AuditableSection(
        title="Core Deduplicated Findings",
        bullets=[entry.text for entry in core_entries],
        source_pids=[entry.pid for entry in core_entries],
    )
    claims = [
        AuditableClaim(text=entry.text, source_pids=[entry.pid])
        for entry in core_entries
    ]

    core_pid_set = {entry.pid for entry in core_entries}
    all_pid_set = {paragraph.pid for paragraph in source_paragraphs}
    unclassified = sorted(all_pid_set - core_pid_set)

    return ([section] if section.bullets else []), claims, unclassified


def _build_metrics(
    coverage_json: CoverageJSON,
    dedup_json: DedupJSON,
    claims: list[AuditableClaim],
) -> AuditableMetrics:
    uncited_claims = sum(1 for claim in claims if not claim.source_pids)
    return AuditableMetrics(
        coverage_rate=coverage_json.coverage_rate,
        missing_count=len(coverage_json.missing_pids),
        duplicate_count=len(coverage_json.duplicate_pids),
        uncited_claims_count=uncited_claims,
        dedup_group_count=dedup_json.group_count,
        unknown_pid_count=len(coverage_json.unknown_pids),
        unclassified_count=len(coverage_json.unclassified_pids),
    )


def build_auditable_artifact(
    text: str,
    *,
    model_id: str = GEMINI_MODEL_PRO_31,
    language: str = "zh-CN",
    near_dedup_threshold: float = 0.97,
    llm_output: Optional[AuditableLLMOutput] = None,
) -> AuditableBuildResult:
    source_paragraphs = index_source_paragraphs(text)
    return build_auditable_artifact_from_paragraphs(
        source_paragraphs,
        model_id=model_id,
        language=language,
        near_dedup_threshold=near_dedup_threshold,
        llm_output=llm_output,
        title="Auditable Long Text Run",
    )


def build_auditable_artifact_from_paragraphs(
    source_paragraphs: list[SourceParagraph],
    *,
    model_id: str = GEMINI_MODEL_PRO_31,
    language: str = "zh-CN",
    near_dedup_threshold: float = 0.97,
    llm_output: Optional[AuditableLLMOutput] = None,
    title: str = "Auditable Long Text Run",
) -> AuditableBuildResult:
    if not source_paragraphs:
        raise ValueError("Source text does not contain any non-empty paragraph")

    dedup_entries, dedup_json = build_dedup_entries(
        source_paragraphs, near_dedup_threshold
    )
    sections, claims, unclassified_pids = _build_sections_and_claims(
        source_paragraphs, dedup_entries, llm_output
    )

    expected_pids = [paragraph.pid for paragraph in source_paragraphs]
    coverage_json = build_coverage_report(
        expected_pids=expected_pids,
        claims=claims,
        dedup_entries=dedup_entries,
        unclassified_pids=unclassified_pids,
    )
    metrics = _build_metrics(
        coverage_json=coverage_json, dedup_json=dedup_json, claims=claims
    )

    result_markdown = render_markdown(
        title=title,
        sections=sections,
        claims=claims,
        dedup_json=dedup_json,
        coverage_json=coverage_json,
        dedup_entries=dedup_entries,
    )

    return AuditableBuildResult(
        model_id=model_id,
        language=language,
        near_dedup_threshold=near_dedup_threshold,
        source_paragraphs=source_paragraphs,
        sections=sections,
        claims=claims,
        dedup_entries=dedup_entries,
        metrics=metrics,
        coverage_json=coverage_json,
        dedup_json=dedup_json,
        result_markdown=result_markdown,
    )


def build_auditable_markdown(
    text: str,
    *,
    model: str = GEMINI_MODEL_PRO_31,
    language: str = "zh-CN",
    near_dedup_threshold: float = 0.97,
) -> LegacyAuditableBuildResult:
    """Backward-compatible wrapper kept for existing tests/integrations."""
    artifact = build_auditable_artifact(
        text,
        model_id=model,
        language=language,
        near_dedup_threshold=near_dedup_threshold,
    )

    core = [
        CoreParagraph(pid=entry.pid, text=entry.text)
        for entry in artifact.dedup_entries
        if entry.status == "core"
    ]
    appendix = [
        AppendixEntry(
            pid=entry.pid,
            text=entry.text,
            status=entry.status,
            duplicate_of=entry.duplicate_of,
            similarity=entry.similarity,
        )
        for entry in artifact.dedup_entries
    ]

    return LegacyAuditableBuildResult(
        model=artifact.model_id,
        language=artifact.language,
        near_dedup_threshold=artifact.near_dedup_threshold,
        total_paragraphs=len(artifact.source_paragraphs),
        unique_paragraphs=len(core),
        duplicate_exact_count=len(
            [a for a in appendix if a.status == "duplicate_exact"]
        ),
        duplicate_near_count=len([a for a in appendix if a.status == "duplicate_near"]),
        coverage_ratio=artifact.coverage_json.coverage_rate,
        pid_sequence=[paragraph.pid for paragraph in artifact.source_paragraphs],
        missing_pids=artifact.coverage_json.missing_pids,
        core=core,
        appendix=appendix,
        markdown=artifact.result_markdown,
    )
