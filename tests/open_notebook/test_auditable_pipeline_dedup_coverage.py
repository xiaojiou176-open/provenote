from __future__ import annotations

import hashlib
from collections import Counter

import pytest

from packages.core.auditable import dedup_engine, pipeline
from packages.core.auditable.schemas import (
    AuditableClaim,
    AuditableLLMOutput,
    AuditableSection,
    CoverageJSON,
    DedupEntry,
    DedupJSON,
    SourceParagraph,
)


def _make_paragraph(
    pid: str, order: int, text: str, *, canonical: str | None = None
) -> SourceParagraph:
    canonical_text = canonical or text.lower().strip()
    return SourceParagraph(
        pid=pid,
        order=order,
        raw_text=text,
        canonical_text=canonical_text,
        canonical_hash=hashlib.sha256(canonical_text.encode("utf-8")).hexdigest(),
    )


def test_to_features_handles_empty_short_and_trigram_inputs() -> None:
    assert dedup_engine._to_features("") == Counter()
    assert dedup_engine._to_features("Ab") == Counter({"ab": 1})
    assert dedup_engine._to_features("ABCD") == Counter({"abc": 1, "bcd": 1})


def test_cosine_similarity_handles_empty_zero_norm_and_identical_vectors() -> None:
    assert dedup_engine._cosine_similarity(Counter(), Counter({"abc": 1})) == 0.0
    assert (
        dedup_engine._cosine_similarity(Counter({"abc": 0}), Counter({"abc": 1})) == 0.0
    )
    assert dedup_engine._cosine_similarity(
        Counter({"abc": 1}), Counter({"abc": 1})
    ) == pytest.approx(1.0)
    assert (
        dedup_engine._cosine_similarity(Counter({"abc": 1}), Counter({"xyz": 1})) == 0.0
    )


def test_build_dedup_entries_returns_empty_payload_for_empty_input() -> None:
    dedup_entries, dedup_json = dedup_engine.build_dedup_entries([], near_threshold=0.9)

    assert dedup_entries == []
    assert dedup_json.exact_groups == []
    assert dedup_json.near_groups == []
    assert dedup_json.group_count == 0


def test_build_dedup_entries_marks_exact_and_near_duplicates() -> None:
    core = _make_paragraph("P000001", 1, "Alpha beta gamma.")
    exact_duplicate = _make_paragraph(
        "P000002",
        2,
        "ALPHA beta gamma.  ",
        canonical=core.canonical_text,
    )
    near_duplicate = _make_paragraph("P000003", 3, "Alpha beta gammaa.")
    far_paragraph = _make_paragraph("P000004", 4, "Completely unrelated sentence.")

    dedup_entries, dedup_json = dedup_engine.build_dedup_entries(
        [core, exact_duplicate, near_duplicate, far_paragraph],
        near_threshold=0.7,
    )

    entry_by_pid = {entry.pid: entry for entry in dedup_entries}

    assert entry_by_pid["P000001"].status == "core"
    assert entry_by_pid["P000002"].status == "duplicate_exact"
    assert entry_by_pid["P000002"].duplicate_of == "P000001"
    assert entry_by_pid["P000003"].status == "duplicate_near"
    assert entry_by_pid["P000003"].duplicate_of == "P000001"
    assert entry_by_pid["P000003"].similarity > 0.7
    assert entry_by_pid["P000004"].status == "core"

    assert dedup_json.group_count == 2
    assert dedup_json.exact_groups == [
        {"canonical_pid": "P000001", "member_pids": ["P000002"]}
    ]
    assert dedup_json.near_groups[0]["canonical_pid"] == "P000001"
    assert dedup_json.near_groups[0]["member_pids"] == ["P000003"]


def test_split_and_coverage_helpers_cover_empty_and_partial_observations() -> None:
    paragraphs = pipeline.split_paragraphs_with_pid("First para.\n\nSecond para.")
    assert [item.pid for item in paragraphs] == ["P000001", "P000002"]

    assert pipeline.compute_coverage([], ["P000001"]) == (1.0, [])

    ratio, missing = pipeline.compute_coverage(
        ["P000001", "P000002", "P000003"],
        ["P000003", "P000001"],
    )
    assert ratio == pytest.approx(2 / 3)
    assert missing == ["P000002"]


def test_build_sections_claims_and_metrics_cover_fallback_and_llm_paths() -> None:
    source_paragraphs = [
        _make_paragraph("P000001", 1, "Core paragraph."),
        _make_paragraph("P000002", 2, "Second paragraph."),
    ]

    fallback_sections, fallback_claims, fallback_unclassified = (
        pipeline._build_sections_and_claims(
            source_paragraphs,
            [DedupEntry(pid="P000001", text="Core paragraph.", status="core")],
            llm_output=None,
        )
    )
    assert fallback_sections[0].title == "Core Deduplicated Findings"
    assert [claim.text for claim in fallback_claims] == ["Core paragraph."]
    assert fallback_unclassified == ["P000002"]

    llm_output = AuditableLLMOutput(
        sections=[
            AuditableSection(
                title="LLM section", bullets=["Summary"], source_pids=["P000001"]
            )
        ],
        claims=[AuditableClaim(text="Claim", source_pids=["P000001"])],
        unclassified_pids=["P999999"],
    )
    llm_sections, llm_claims, llm_unclassified = pipeline._build_sections_and_claims(
        source_paragraphs,
        [DedupEntry(pid="P000001", text="Core paragraph.", status="core")],
        llm_output=llm_output,
    )
    assert llm_sections == llm_output.sections
    assert llm_claims == llm_output.claims
    assert llm_unclassified == ["P999999"]

    metrics = pipeline._build_metrics(
        coverage_json=CoverageJSON(
            total_pids=2,
            covered_pids=2,
            coverage_rate=1.0,
            missing_pids=[],
            duplicate_pids=["P000001"],
            unknown_pids=[],
            unclassified_pids=["P999999"],
        ),
        dedup_json=DedupJSON(group_count=3),
        claims=[
            AuditableClaim(text="Cited", source_pids=["P000001"]),
            AuditableClaim(text="Uncited", source_pids=[]),
        ],
    )
    assert metrics.duplicate_count == 1
    assert metrics.uncited_claims_count == 1
    assert metrics.dedup_group_count == 3
    assert metrics.unclassified_count == 1


def test_build_auditable_artifact_and_legacy_wrapper_cover_end_to_end_paths() -> None:
    text = (
        "Alpha beta gamma.\n\n"
        "Alpha beta gamma.\n\n"
        "Alpha beta gammaa.\n\n"
        "Completely unrelated sentence."
    )

    artifact = pipeline.build_auditable_artifact(
        text,
        model_id="gemini-test",
        language="en",
        near_dedup_threshold=0.7,
    )
    assert artifact.model_id == "gemini-test"
    assert artifact.language == "en"
    assert any(entry.status == "duplicate_exact" for entry in artifact.dedup_entries)
    assert any(entry.status == "duplicate_near" for entry in artifact.dedup_entries)
    assert "## Coverage Report" in artifact.result_markdown
    assert artifact.metrics.dedup_group_count >= 1

    legacy = pipeline.build_auditable_markdown(
        text,
        model="legacy-model",
        language="en",
        near_dedup_threshold=0.7,
    )
    assert legacy.model == "legacy-model"
    assert legacy.language == "en"
    assert len(legacy.pid_sequence) == legacy.total_paragraphs
    assert len(legacy.core_as_dict()) == legacy.unique_paragraphs
    assert any(
        item["status"] == "duplicate_exact" for item in legacy.appendix_as_dict()
    )


def test_build_auditable_artifact_rejects_empty_source_text() -> None:
    with pytest.raises(ValueError, match="non-empty paragraph"):
        pipeline.build_auditable_artifact(" \n\n\t")
