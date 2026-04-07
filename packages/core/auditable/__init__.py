from packages.core.auditable.coverage_validator import build_coverage_report
from packages.core.auditable.dedup_engine import build_dedup_entries
from packages.core.auditable.markdown_renderer import render_markdown
from packages.core.auditable.paragraph_indexer import (
    index_source_paragraphs,
    normalize_whitespace,
    split_paragraphs,
)
from packages.core.auditable.pipeline import (
    AppendixEntry,
    CoreParagraph,
    LegacyAuditableBuildResult,
    build_auditable_artifact,
    build_auditable_artifact_from_paragraphs,
    build_auditable_markdown,
    compute_coverage,
    split_paragraphs_with_pid,
)
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

__all__ = [
    "AppendixEntry",
    "AuditableBuildResult",
    "AuditableClaim",
    "AuditableLLMOutput",
    "AuditableMetrics",
    "AuditableSection",
    "CoreParagraph",
    "CoverageJSON",
    "DedupEntry",
    "DedupJSON",
    "LegacyAuditableBuildResult",
    "SourceParagraph",
    "build_auditable_artifact",
    "build_auditable_artifact_from_paragraphs",
    "build_auditable_markdown",
    "build_coverage_report",
    "build_dedup_entries",
    "compute_coverage",
    "index_source_paragraphs",
    "normalize_whitespace",
    "render_markdown",
    "split_paragraphs",
    "split_paragraphs_with_pid",
]
