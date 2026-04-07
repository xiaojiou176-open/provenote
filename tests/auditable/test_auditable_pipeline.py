from packages.core.auditable import (
    build_auditable_markdown,
    compute_coverage,
    split_paragraphs_with_pid,
)


def test_pid_continuity():
    text = "第一段\n\n第二段\n\n第三段"
    paragraphs = split_paragraphs_with_pid(text)

    assert [item.pid for item in paragraphs] == ["P000001", "P000002", "P000003"]


def test_coverage_ratio_is_100_percent():
    text = "甲段内容\n\n乙段内容\n\n丙段内容"
    result = build_auditable_markdown(text)

    assert result.coverage_ratio == 1.0
    assert result.missing_pids == []
    assert result.total_paragraphs == 3
    assert result.unique_paragraphs == 3


def test_missing_pid_detection():
    ratio, missing = compute_coverage(
        expected_pids=["P000001", "P000002", "P000003"],
        observed_pids=["P000001", "P000003"],
    )

    assert ratio == 2 / 3
    assert missing == ["P000002"]


def test_coverage_computation_uses_pid_set_semantics():
    ratio, missing = compute_coverage(
        expected_pids=["P000001", "P000001", "P000002"],
        observed_pids=["P000001", "P000001"],
    )

    assert ratio == 0.5
    assert missing == ["P000002"]


def test_exact_and_near_duplicate_detection():
    source_text = (
        "This is a long paragraph used for near duplicate detection with stable "
        "tokens and structure 12345.\n\n"
        "This is a long paragraph used for near duplicate detection with stable "
        "tokens and structure 12345.\n\n"
        "This is a long paragraph used for near duplicate detection with stable "
        "tokens and structure 12346."
    )

    result = build_auditable_markdown(source_text, near_dedup_threshold=0.97)

    assert result.total_paragraphs == 3
    assert result.unique_paragraphs == 1
    assert result.duplicate_exact_count == 1
    assert result.duplicate_near_count == 1
    assert [item.status for item in result.appendix] == [
        "core",
        "duplicate_exact",
        "duplicate_near",
    ]
    assert result.appendix[1].duplicate_of == "P000001"
    assert result.appendix[2].duplicate_of == "P000001"
    assert result.appendix[2].similarity >= 0.97
    assert "| Canonical PID | Merged PIDs | Evidence |" in result.markdown
    assert "exact" in result.markdown
    assert "near (" in result.markdown
    assert "Lossless Source Appendix" in result.markdown


def test_markdown_contains_expected_headers_and_pid_references():
    result = build_auditable_markdown("第一段\n\n第二段")

    assert result.markdown.startswith("# Auditable Long Text Run\n")
    assert "## Rewritten Body (Evidence Linked)" in result.markdown
    assert "### Core Deduplicated Findings" in result.markdown
    assert "[[P000001]]" in result.markdown
    assert "> [[P000001]] 第一段" in result.markdown
    assert "## Coverage Report" in result.markdown


def test_build_auditable_markdown_honors_custom_model_language_and_threshold():
    result = build_auditable_markdown(
        "第一段\n\n第二段",
        model="gemini-custom-model",
        language="en",
        near_dedup_threshold=0.91,
    )

    assert result.model == "gemini-custom-model"
    assert result.language == "en"
    assert result.near_dedup_threshold == 0.91
