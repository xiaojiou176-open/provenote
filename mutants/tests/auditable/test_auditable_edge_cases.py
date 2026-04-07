from collections import Counter

import pytest

from packages.core.auditable.dedup_engine import (
    _cosine_similarity,
    _to_features,
    build_dedup_entries,
)
from packages.core.auditable.markdown_renderer import render_markdown
from packages.core.auditable.pipeline import (
    build_auditable_artifact,
    build_auditable_markdown,
    compute_coverage,
)
from packages.core.auditable.schemas import (
    AuditableClaim,
    AuditableLLMOutput,
    AuditableSection,
    CoverageJSON,
    DedupEntry,
    DedupJSON,
)


def test_to_features_handles_empty_and_short_text():
    assert _to_features("") == Counter()
    assert _to_features("ab") == Counter({"ab": 1})


def test_cosine_similarity_handles_empty_and_zero_norm_vectors():
    assert _cosine_similarity(Counter(), Counter({"abc": 1})) == 0.0
    assert _cosine_similarity(Counter({"abc": 1}), Counter()) == 0.0

    # Counter allows zero values; this forces the zero-norm branch.
    assert _cosine_similarity(Counter({"abc": 0}), Counter({"abc": 1})) == 0.0


def test_build_dedup_entries_handles_empty_input():
    dedup_entries, dedup_json = build_dedup_entries([], near_threshold=0.97)

    assert dedup_entries == []
    assert dedup_json.exact_groups == []
    assert dedup_json.near_groups == []
    assert dedup_json.group_count == 0


def test_compute_coverage_returns_full_ratio_when_no_expected_pids():
    ratio, missing = compute_coverage(expected_pids=[], observed_pids=["P000001"])

    assert ratio == 1.0
    assert missing == []


def test_build_auditable_markdown_raises_for_empty_input():
    with pytest.raises(ValueError, match="does not contain any non-empty paragraph"):
        build_auditable_markdown("  \n\n   ")


def test_build_auditable_artifact_uses_llm_output_sections_claims_and_unclassified():
    llm_output = AuditableLLMOutput(
        sections=[
            AuditableSection(
                title="Summary",
                bullets=["Point A"],
                source_pids=["P000001"],
            )
        ],
        claims=[AuditableClaim(text="Claim A", source_pids=["P000001"])],
        unclassified_pids=["P000002"],
    )

    result = build_auditable_artifact(
        "第一段\n\n第二段",
        llm_output=llm_output,
    )

    assert result.sections == llm_output.sections
    assert result.claims == llm_output.claims
    assert result.metrics.unclassified_count == 1
    assert result.coverage_json.unclassified_pids == ["P000002"]


def test_build_auditable_artifact_tracks_uncited_duplicate_and_unknown_claim_metrics():
    llm_output = AuditableLLMOutput(
        sections=[
            AuditableSection(
                title="Summary",
                bullets=["Point A"],
                source_pids=["P000001"],
            )
        ],
        claims=[
            AuditableClaim(text="Known claim", source_pids=["P000001", "P000001"]),
            AuditableClaim(text="Unknown pid claim", source_pids=["P999999"]),
            AuditableClaim(text="Uncited claim", source_pids=[]),
        ],
        unclassified_pids=["P000002", "P000002"],
    )

    result = build_auditable_artifact("第一段\n\n第二段", llm_output=llm_output)

    assert result.metrics.uncited_claims_count == 1
    assert result.metrics.duplicate_count == 1
    assert result.metrics.unknown_pid_count == 1
    assert result.metrics.missing_count == 0
    assert result.metrics.unclassified_count == 1
    assert result.coverage_json.duplicate_pids == ["P000001"]
    assert result.coverage_json.unknown_pids == ["P999999"]
    assert result.coverage_json.unclassified_pids == ["P000002"]
    assert "### Claims" in result.result_markdown
    assert "- Unknown pid claim [[P999999]]" in result.result_markdown
    assert "- Uncited claim" in result.result_markdown


def test_legacy_result_dict_helpers_return_serializable_items():
    legacy = build_auditable_markdown("第一段\n\n第二段")

    assert legacy.core_as_dict()
    assert set(legacy.core_as_dict()[0].keys()) == {"pid", "text"}
    assert legacy.appendix_as_dict()
    assert {"pid", "text", "status", "duplicate_of", "similarity"}.issubset(
        legacy.appendix_as_dict()[0].keys()
    )


def test_render_markdown_fallback_sections_and_no_claims():
    markdown = render_markdown(
        title="Run",
        sections=[],
        claims=[],
        dedup_json=DedupJSON(exact_groups=[], near_groups=[], group_count=0),
        coverage_json=CoverageJSON(
            total_pids=1,
            covered_pids=1,
            coverage_rate=1.0,
            missing_pids=[],
            duplicate_pids=[],
            unknown_pids=[],
            unclassified_pids=[],
        ),
        dedup_entries=[
            DedupEntry(
                pid="P000001",
                text="Paragraph",
                status="core",
                duplicate_of=None,
                similarity=None,
            )
        ],
    )

    assert "- No structured sections available" in markdown
    assert "### Claims" not in markdown
    assert "| - | - | no dedup groups |" in markdown


def test_render_markdown_formats_near_group_similarity_and_claim_refs():
    markdown = render_markdown(
        title="Run",
        sections=[
            AuditableSection(
                title="Section A",
                bullets=["Bullet A"],
                source_pids=["P000001", "P000002"],
            )
        ],
        claims=[AuditableClaim(text="Claim A", source_pids=["P000001"])],
        dedup_json=DedupJSON(
            exact_groups=[],
            near_groups=[
                {
                    "canonical_pid": "P000001",
                    "member_pids": ["P000002"],
                    "evidence": [{"pid": "P000002", "similarity": 0.98765}],
                }
            ],
            group_count=1,
        ),
        coverage_json=CoverageJSON(
            total_pids=2,
            covered_pids=2,
            coverage_rate=1.0,
            missing_pids=[],
            duplicate_pids=[],
            unknown_pids=[],
            unclassified_pids=[],
        ),
        dedup_entries=[
            DedupEntry(
                pid="P000001",
                text="Paragraph A",
                status="core",
                duplicate_of=None,
                similarity=None,
            ),
            DedupEntry(
                pid="P000002",
                text="Paragraph B",
                status="duplicate_near",
                duplicate_of="P000001",
                similarity=0.98765,
            ),
        ],
    )

    assert "- Bullet A [[P000001]][[P000002]]" in markdown
    assert "- Claim A [[P000001]]" in markdown
    assert "| P000001 | P000002 | near (P000002:0.9877) |" in markdown
