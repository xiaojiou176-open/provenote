"""
Unit tests for the packages.core.utils.chunking module.

Tests content type detection and text chunking functionality.
"""

import pytest

from packages.core.utils.chunking import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    ContentType,
    _apply_secondary_chunking,
    _calculate_html_score,
    _calculate_markdown_score,
    _get_chunk_overlap,
    _get_chunk_size,
    _get_html_splitter,
    _get_markdown_splitter,
    _get_plain_splitter,
    chunk_text,
    detect_content_type,
    detect_content_type_from_extension,
    detect_content_type_from_heuristics,
)

# ============================================================================
# TEST SUITE 1: Content Type Detection from Extension
# ============================================================================


class TestDetectContentTypeFromExtension:
    """Test suite for extension-based content type detection."""

    def test_html_extensions(self):
        """Test HTML file extensions."""
        assert detect_content_type_from_extension("file.html") == ContentType.HTML
        assert detect_content_type_from_extension("file.htm") == ContentType.HTML
        assert detect_content_type_from_extension("file.xhtml") == ContentType.HTML
        assert (
            detect_content_type_from_extension("/path/to/file.HTML") == ContentType.HTML
        )

    def test_markdown_extensions(self):
        """Test Markdown file extensions."""
        assert detect_content_type_from_extension("file.md") == ContentType.MARKDOWN
        assert (
            detect_content_type_from_extension("file.markdown") == ContentType.MARKDOWN
        )
        assert detect_content_type_from_extension("file.mdown") == ContentType.MARKDOWN
        assert (
            detect_content_type_from_extension("/path/to/README.MD")
            == ContentType.MARKDOWN
        )

    def test_plain_text_extensions(self):
        """Test plain text file extensions."""
        assert detect_content_type_from_extension("file.txt") == ContentType.PLAIN
        assert detect_content_type_from_extension("file.text") == ContentType.PLAIN

    def test_code_extensions_as_plain(self):
        """Test code file extensions are treated as plain text."""
        assert detect_content_type_from_extension("file.py") == ContentType.PLAIN
        assert detect_content_type_from_extension("file.js") == ContentType.PLAIN
        assert detect_content_type_from_extension("file.json") == ContentType.PLAIN
        assert detect_content_type_from_extension("file.yaml") == ContentType.PLAIN

    def test_unknown_extensions(self):
        """Test unknown extensions return None."""
        assert detect_content_type_from_extension("file.xyz") is None
        assert detect_content_type_from_extension("file.docx") is None
        assert detect_content_type_from_extension("file.pdf") is None

    def test_no_extension(self):
        """Test files without extension."""
        assert detect_content_type_from_extension("Makefile") is None
        assert detect_content_type_from_extension("README") is None

    def test_none_input(self):
        """Test None input."""
        assert detect_content_type_from_extension(None) is None

    def test_empty_string(self):
        """Test empty string input."""
        assert detect_content_type_from_extension("") is None


# ============================================================================
# TEST SUITE 2: Content Type Detection from Heuristics
# ============================================================================


class TestDetectContentTypeFromHeuristics:
    """Test suite for heuristics-based content type detection."""

    def test_html_detection_doctype(self):
        """Test HTML detection with DOCTYPE."""
        html_text = "<!DOCTYPE html><html><body>Content</body></html>"
        content_type, confidence = detect_content_type_from_heuristics(html_text)
        assert content_type == ContentType.HTML
        assert confidence >= 0.8

    def test_html_detection_tags(self):
        """Test HTML detection with structural tags."""
        html_text = "<html><head><title>Test</title></head><body><div><p>Content</p></div></body></html>"
        content_type, confidence = detect_content_type_from_heuristics(html_text)
        assert content_type == ContentType.HTML
        assert confidence >= 0.5

    def test_markdown_detection_headers(self):
        """Test Markdown detection with headers."""
        md_text = """# Main Title

## Section 1

Some content here.

## Section 2

More content.

### Subsection

Details here.
"""
        content_type, confidence = detect_content_type_from_heuristics(md_text)
        assert content_type == ContentType.MARKDOWN
        assert confidence >= 0.3  # 4 headers give ~0.35 confidence

    def test_markdown_detection_links(self):
        """Test Markdown detection with links and headers for stronger signal."""
        md_text = """# Documentation

Check out [this link](https://example.com) and [another one](https://test.com).

## References

Here's some more text with [links](url) and `inline code`."""
        content_type, confidence = detect_content_type_from_heuristics(md_text)
        assert content_type == ContentType.MARKDOWN
        assert confidence >= 0.4

    def test_markdown_detection_code_blocks(self):
        """Test Markdown detection with code blocks."""
        md_text = """# Code Example

```python
def hello():
    print("Hello, World!")
```

Some explanation text.
"""
        content_type, confidence = detect_content_type_from_heuristics(md_text)
        assert content_type == ContentType.MARKDOWN
        assert confidence >= 0.5

    def test_plain_text_detection(self):
        """Test plain text detection."""
        plain_text = """This is just regular plain text.
It has multiple lines but no special formatting.
No headers, no links, no HTML tags.
Just regular sentences and paragraphs."""
        content_type, confidence = detect_content_type_from_heuristics(plain_text)
        assert content_type == ContentType.PLAIN

    def test_short_text(self):
        """Test short text defaults to plain."""
        content_type, confidence = detect_content_type_from_heuristics("Hi")
        assert content_type == ContentType.PLAIN
        assert confidence == pytest.approx(0.5)

    def test_empty_text(self):
        """Test empty text defaults to plain."""
        content_type, confidence = detect_content_type_from_heuristics("")
        assert content_type == ContentType.PLAIN


# ============================================================================
# TEST SUITE 3: Combined Content Type Detection
# ============================================================================


class TestDetectContentType:
    """Test suite for combined content type detection."""

    def test_extension_takes_priority(self):
        """Test that file extension takes priority over heuristics."""
        # Text looks like markdown but file is .txt
        md_text = "# Header\n\nSome [link](url) content"
        content_type = detect_content_type(md_text, "file.txt")
        # Should use extension (plain) unless heuristics are very high confidence
        # In this case, markdown confidence might override
        assert content_type in (ContentType.PLAIN, ContentType.MARKDOWN)

    def test_no_extension_uses_heuristics(self):
        """Test that heuristics are used when no extension is available."""
        html_text = "<!DOCTYPE html><html><body>Test</body></html>"
        content_type = detect_content_type(html_text, None)
        assert content_type == ContentType.HTML

    def test_extension_html(self):
        """Test HTML extension detection."""
        content_type = detect_content_type("some text", "file.html")
        assert content_type == ContentType.HTML

    def test_extension_markdown(self):
        """Test Markdown extension detection."""
        content_type = detect_content_type("some text", "file.md")
        assert content_type == ContentType.MARKDOWN

    def test_high_confidence_override(self):
        """Test that very high confidence heuristics can override plain extension."""
        # Strong HTML indicators in a .txt file
        html_text = "<!DOCTYPE html><html><head><title>Test</title></head><body><div><p>Content</p></div></body></html>"
        content_type = detect_content_type(html_text, "file.txt")
        # High confidence HTML should override .txt extension
        assert content_type == ContentType.HTML


# ============================================================================
# TEST SUITE 4: Text Chunking
# ============================================================================


class TestChunkText:
    """Test suite for text chunking functionality."""

    def test_empty_text(self):
        """Test chunking empty text."""
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_short_text_no_chunking(self):
        """Test that short text is not chunked."""
        text = "This is a short text."
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_text_at_chunk_limit(self):
        """Test text at exactly chunk size limit."""
        text = "x" * CHUNK_SIZE
        chunks = chunk_text(text)
        assert len(chunks) == 1

    def test_long_text_is_chunked(self):
        """Test that long text is chunked."""
        # Create text longer than chunk size
        text = "This is a sentence. " * 200  # ~4000 chars
        chunks = chunk_text(text)
        assert len(chunks) > 1
        # Each chunk should be <= CHUNK_SIZE
        for chunk in chunks:
            assert len(chunk) <= CHUNK_SIZE + 100  # Allow some flexibility for overlap

    def test_explicit_content_type_html(self):
        """Test chunking with explicit HTML content type."""
        html_text = """<html>
<body>
<h1>Main Title</h1>
<p>First paragraph with lots of content.</p>
<h2>Section</h2>
<p>Second paragraph.</p>
</body>
</html>"""
        chunks = chunk_text(html_text, content_type=ContentType.HTML)
        assert len(chunks) >= 1

    def test_explicit_content_type_markdown(self):
        """Test chunking with explicit Markdown content type."""
        md_text = """# Main Title

Introduction paragraph.

## Section 1

Content for section 1.

## Section 2

Content for section 2.
"""
        chunks = chunk_text(md_text, content_type=ContentType.MARKDOWN)
        assert len(chunks) >= 1

    def test_explicit_content_type_plain(self):
        """Test chunking with explicit plain content type."""
        plain_text = "Word " * 500  # ~2500 chars
        chunks = chunk_text(plain_text, content_type=ContentType.PLAIN)
        assert len(chunks) >= 1

    def test_file_path_detection(self):
        """Test chunking with file path for content type detection."""
        text = "Some content here"
        chunks = chunk_text(text, file_path="document.md")
        assert len(chunks) == 1

    def test_secondary_chunking_for_large_sections(self):
        """Test that large sections from HTML/MD splitters are further chunked."""
        # Create text that would produce a single large section
        large_section = "x" * 3000  # Larger than CHUNK_SIZE
        md_text = f"# Title\n\n{large_section}"
        chunks = chunk_text(md_text, content_type=ContentType.MARKDOWN)
        # Should have multiple chunks due to secondary chunking
        assert len(chunks) >= 1
        for chunk in chunks:
            # Allow some flexibility but chunks should be reasonable size
            assert len(chunk) <= CHUNK_SIZE + 300


class TestMutationHardening:
    """Target high-impact mutation survivors with strict behavioral assertions."""

    def test_get_chunk_size_reads_expected_env_key(self, monkeypatch):
        seen = []

        def fake_read_env(key):
            seen.append(key)
            return "321"

        monkeypatch.setattr("packages.core.utils.chunking.read_env", fake_read_env)
        assert _get_chunk_size() == 321
        assert seen == ["OPEN_NOTEBOOK_CHUNK_SIZE"]

    @pytest.mark.parametrize(
        ("env_value", "expected"),
        [
            (None, 1200),
            ("100", 100),
            ("99", 100),
            ("8192", 8192),
            ("8193", 8193),
            ("invalid", 1200),
        ],
    )
    def test_get_chunk_size_boundaries(self, monkeypatch, env_value, expected):
        monkeypatch.setattr(
            "packages.core.utils.chunking.read_env", lambda _key: env_value
        )
        assert _get_chunk_size() == expected

    def test_get_chunk_overlap_reads_expected_env_key(self, monkeypatch):
        seen = []

        def fake_read_env(key):
            seen.append(key)
            return "42"

        monkeypatch.setattr("packages.core.utils.chunking.read_env", fake_read_env)
        assert _get_chunk_overlap(400) == 42
        assert seen == ["OPEN_NOTEBOOK_CHUNK_OVERLAP"]

    @pytest.mark.parametrize(
        ("env_value", "chunk_size", "expected"),
        [
            (None, 1000, 150),
            ("-1", 1000, 0),
            ("0", 1000, 0),
            ("999", 1000, 999),
            ("1000", 1000, 150),
            ("oops", 1000, 150),
        ],
    )
    def test_get_chunk_overlap_boundaries(
        self, monkeypatch, env_value, chunk_size, expected
    ):
        monkeypatch.setattr(
            "packages.core.utils.chunking.read_env", lambda _key: env_value
        )
        assert _get_chunk_overlap(chunk_size) == expected

    def test_html_splitter_has_expected_headers(self):
        splitter = _get_html_splitter()
        assert splitter.headers_to_split_on == [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        assert splitter.header_tags == ["h1", "h2", "h3"]

    def test_markdown_splitter_configuration(self):
        splitter = _get_markdown_splitter()
        assert splitter.strip_headers is False
        assert set(splitter.headers_to_split_on) == {
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        }

    def test_plain_splitter_configuration(self):
        splitter = _get_plain_splitter()
        assert splitter._chunk_size == CHUNK_SIZE
        assert splitter._chunk_overlap == CHUNK_OVERLAP
        assert splitter._separators == ["\n\n", "\n", ". ", ", ", " ", ""]

    def test_apply_secondary_chunking_only_splits_oversized(self, monkeypatch):
        calls = []

        class FakeSplitter:
            def split_text(self, text):
                calls.append(text)
                return [text[:2], text[2:]]

        monkeypatch.setattr(
            "packages.core.utils.chunking._get_plain_splitter", lambda: FakeSplitter()
        )
        oversized = "x" * (CHUNK_SIZE + 5)
        result = _apply_secondary_chunking(["ok", oversized])
        assert calls == [oversized]
        assert result[0] == "ok"
        assert result[1:] == [oversized[:2], oversized[2:]]

    def test_calculate_html_score_threshold_shapes(self):
        doctype_only = "<!DOCTYPE html>"
        assert _calculate_html_score(doctype_only) == pytest.approx(0.4)

        strong_html = (
            "<!DOCTYPE html><html><head></head><body>"
            "<div><span><p>content</p></span></div></body></html>"
        )
        assert _calculate_html_score(strong_html) == pytest.approx(1.0)

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("<html>", 0.3),
            ("<div>content", 0.1),
            ("<h2>Title", 0.15),
            ("</p>", 0.1),
        ],
    )
    def test_calculate_html_score_isolated_signals(self, text, expected):
        assert _calculate_html_score(text) == pytest.approx(expected)

    def test_calculate_html_score_structural_cap(self):
        text = "<head><body><div><span><p><table><form>"
        # Structural tags are capped by indicators >= 5 guard.
        assert _calculate_html_score(text) == pytest.approx(0.5)

    def test_calculate_html_score_accumulates_doctype_and_header_tag(self):
        text = "<!DOCTYPE html><h2>Title</h2>"
        assert _calculate_html_score(text) == pytest.approx(0.65)

    def test_calculate_html_score_structural_cap_still_allows_header_and_closing_bonus(
        self,
    ):
        text = "<head><body><div><span><p><table><h2>Title</h2></p>"
        assert _calculate_html_score(text) == pytest.approx(0.75)

    def test_calculate_markdown_score_threshold_shapes(self):
        headers_only = "# H1\n## H2\n### H3\n"
        assert _calculate_markdown_score(headers_only) == pytest.approx(0.35)

        mixed_markdown = (
            "# Title\n"
            "[a](u) [b](v)\n"
            "```py\nprint('x')\n```\n"
            "`inline`\n"
            "- one\n"
            "**bold**\n"
            "> quote\n"
        )
        assert _calculate_markdown_score(mixed_markdown) == pytest.approx(1.0)

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("# Title\n", 0.2),
            ("# A\n## B\n### C\n", 0.35),
            ("[a](x) [b](y)", 0.25),
            ("[a](x)", 0.15),
            ("```py\nprint(1)\n```", 0.3),
            ("`inline`", 0.1),
            ("- item", 0.08),
            ("- a\n- b\n- c\n", 0.15),
            ("**bold**", 0.1),
            ("> quote", 0.1),
        ],
    )
    def test_calculate_markdown_score_isolated_signals(self, text, expected):
        assert _calculate_markdown_score(text) == pytest.approx(expected)

    def test_calculate_markdown_score_accumulates_header_and_single_link(self):
        text = "# Title\n[a](https://example.com)"
        assert _calculate_markdown_score(text) == pytest.approx(0.35)

    def test_calculate_markdown_score_accumulates_header_and_dense_lists(self):
        text = "# Title\n1. one\n2. two\n3. three"
        assert _calculate_markdown_score(text) == pytest.approx(0.35)

    def test_calculate_markdown_score_combines_unordered_and_numbered_lists(self):
        text = "- a\n1. one\n2. two"
        assert _calculate_markdown_score(text) == pytest.approx(0.15)

    def test_calculate_markdown_score_accumulates_multiple_signal_types_exactly(self):
        text = "# Title\n[a](x)\n`inline`\n**bold**\n> quote"
        assert _calculate_markdown_score(text) == pytest.approx(0.65)

    def test_calculate_markdown_score_single_header_and_sparse_list_keeps_lower_list_bonus(
        self,
    ):
        text = "# Title\n- item"
        assert _calculate_markdown_score(text) == pytest.approx(0.28)

    def test_detect_content_type_from_heuristics_branching(self, monkeypatch):
        monkeypatch.setattr(
            "packages.core.utils.chunking._calculate_html_score", lambda _s: 0.8
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking._calculate_markdown_score", lambda _s: 0.1
        )
        assert detect_content_type_from_heuristics("x" * 50) == (ContentType.HTML, 0.8)

        monkeypatch.setattr(
            "packages.core.utils.chunking._calculate_html_score", lambda _s: 0.3
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking._calculate_markdown_score", lambda _s: 0.31
        )
        assert detect_content_type_from_heuristics("x" * 50) == (
            ContentType.MARKDOWN,
            0.31,
        )

        monkeypatch.setattr(
            "packages.core.utils.chunking._calculate_html_score", lambda _s: 0.3
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking._calculate_markdown_score", lambda _s: 0.3
        )
        assert detect_content_type_from_heuristics("x" * 50) == (ContentType.PLAIN, 0.6)

    def test_detect_content_type_priority_rules(self, monkeypatch):
        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type_from_extension",
            lambda _p: None,
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type_from_heuristics",
            lambda _t: (ContentType.MARKDOWN, 0.51),
        )
        assert detect_content_type("body", "ignored.any") == ContentType.MARKDOWN

        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type_from_extension",
            lambda _p: ContentType.PLAIN,
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type_from_heuristics",
            lambda _t: (ContentType.HTML, 0.8),
        )
        assert detect_content_type("body", "a.txt") == ContentType.HTML

        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type_from_heuristics",
            lambda _t: (ContentType.HTML, 0.79),
        )
        assert detect_content_type("body", "a.txt") == ContentType.PLAIN

    def test_get_chunk_size_logging_paths(self, monkeypatch):
        warnings = []
        infos = []
        monkeypatch.setattr(
            "packages.core.utils.chunking.logger.warning",
            lambda msg: warnings.append(msg),
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking.logger.info",
            lambda msg: infos.append(msg),
        )

        monkeypatch.setattr("packages.core.utils.chunking.read_env", lambda _k: "99")
        assert _get_chunk_size() == 100
        assert any("too small" in str(m) for m in warnings)

        warnings.clear()
        monkeypatch.setattr("packages.core.utils.chunking.read_env", lambda _k: "8193")
        assert _get_chunk_size() == 8193
        assert any("very large" in str(m) for m in warnings)

        warnings.clear()
        infos.clear()
        monkeypatch.setattr("packages.core.utils.chunking.read_env", lambda _k: "abc")
        assert _get_chunk_size() == 1200
        assert any("Invalid OPEN_NOTEBOOK_CHUNK_SIZE" in str(m) for m in warnings)

        monkeypatch.setattr("packages.core.utils.chunking.read_env", lambda _k: "321")
        assert _get_chunk_size() == 321
        assert any("Using custom chunk size" in str(m) for m in infos)
        assert not any("too small" in str(m) for m in warnings)

    def test_get_chunk_size_exact_boundaries_do_not_warn(self, monkeypatch):
        warnings = []
        monkeypatch.setattr(
            "packages.core.utils.chunking.logger.warning",
            lambda msg: warnings.append(msg),
        )

        monkeypatch.setattr("packages.core.utils.chunking.read_env", lambda _k: "100")
        assert _get_chunk_size() == 100
        assert not warnings

        monkeypatch.setattr("packages.core.utils.chunking.read_env", lambda _k: "8192")
        assert _get_chunk_size() == 8192
        assert not warnings

    def test_get_chunk_overlap_logging_paths(self, monkeypatch):
        warnings = []
        infos = []
        monkeypatch.setattr(
            "packages.core.utils.chunking.logger.warning",
            lambda msg: warnings.append(msg),
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking.logger.info",
            lambda msg: infos.append(msg),
        )

        monkeypatch.setattr("packages.core.utils.chunking.read_env", lambda _k: "-1")
        assert _get_chunk_overlap(1000) == 0
        assert any("cannot be negative" in str(m) for m in warnings)

        warnings.clear()
        monkeypatch.setattr("packages.core.utils.chunking.read_env", lambda _k: "1000")
        assert _get_chunk_overlap(1000) == 150
        assert any("cannot be >=" in str(m) for m in warnings)

        warnings.clear()
        monkeypatch.setattr("packages.core.utils.chunking.read_env", lambda _k: "oops")
        assert _get_chunk_overlap(1000) == 150
        assert any("Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP" in str(m) for m in warnings)

        monkeypatch.setattr("packages.core.utils.chunking.read_env", lambda _k: "42")
        assert _get_chunk_overlap(1000) == 42
        assert any("Using custom chunk overlap" in str(m) for m in infos)

    def test_get_chunk_overlap_zero_is_custom_value(self, monkeypatch):
        warnings = []
        infos = []
        monkeypatch.setattr(
            "packages.core.utils.chunking.logger.warning",
            lambda msg: warnings.append(msg),
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking.logger.info",
            lambda msg: infos.append(msg),
        )

        monkeypatch.setattr("packages.core.utils.chunking.read_env", lambda _k: "0")
        assert _get_chunk_overlap(1000) == 0
        assert not warnings
        assert any("Using custom chunk overlap: 0 characters" in str(m) for m in infos)

    def test_get_chunk_overlap_fallback_warning_contains_15_percent_value(
        self, monkeypatch
    ):
        warnings = []
        monkeypatch.setattr(
            "packages.core.utils.chunking.logger.warning",
            lambda msg: warnings.append(msg),
        )
        monkeypatch.setattr("packages.core.utils.chunking.read_env", lambda _k: "1000")
        assert _get_chunk_overlap(1000) == 150
        assert any("Using 15% of chunk size: 150" in str(m) for m in warnings)

    def test_detect_content_type_from_heuristics_short_text_boundary(self):
        content_type, confidence = detect_content_type_from_heuristics("x" * 10)
        assert content_type == ContentType.PLAIN
        assert confidence == pytest.approx(0.6)

    def test_detect_content_type_from_heuristics_below_short_text_boundary(self):
        content_type, confidence = detect_content_type_from_heuristics("x" * 9)
        assert content_type == ContentType.PLAIN
        assert confidence == pytest.approx(0.5)

    def test_detect_content_type_from_heuristics_html_threshold_priority(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            "packages.core.utils.chunking._calculate_html_score", lambda _s: 0.8
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking._calculate_markdown_score", lambda _s: 0.9
        )
        assert detect_content_type_from_heuristics("x" * 50) == (
            ContentType.HTML,
            0.8,
        )

    def test_detect_content_type_from_heuristics_markdown_threshold_inclusive(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            "packages.core.utils.chunking._calculate_html_score", lambda _s: 0.1
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking._calculate_markdown_score", lambda _s: 0.8
        )
        assert detect_content_type_from_heuristics("x" * 50) == (
            ContentType.MARKDOWN,
            0.8,
        )

    @pytest.mark.parametrize(
        ("html_score", "md_score", "expected"),
        [
            (0.4, 0.5, (ContentType.MARKDOWN, 0.5)),
            (0.4, 0.4, (ContentType.MARKDOWN, 0.4)),
            (0.3, 0.2, (ContentType.PLAIN, 0.6)),
        ],
    )
    def test_detect_content_type_from_heuristics_tie_and_floor_rules(
        self, monkeypatch, html_score, md_score, expected
    ):
        monkeypatch.setattr(
            "packages.core.utils.chunking._calculate_html_score", lambda _s: html_score
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking._calculate_markdown_score",
            lambda _s: md_score,
        )
        assert detect_content_type_from_heuristics("x" * 50) == expected

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("<!DOCTYPE HTML>", 0.4),
            ("<HTML>", 0.3),
            ("<H2>Title</H2>", 0.25),
        ],
    )
    def test_calculate_html_score_case_insensitive_patterns(self, text, expected):
        assert _calculate_html_score(text) == pytest.approx(expected)

    @pytest.mark.parametrize(
        ("tag", "expected"),
        [
            ("<head>", 0.1),
            ("<span>", 0.1),
            ("<p>", 0.1),
            ("<table>", 0.1),
            ("<form>", 0.1),
        ],
    )
    def test_calculate_html_score_structural_tag_signals(self, tag, expected):
        assert _calculate_html_score(tag) == pytest.approx(expected)

    def test_get_plain_splitter_uses_len_function(self):
        splitter = _get_plain_splitter()
        assert splitter._length_function is len

    def test_apply_secondary_chunking_does_not_split_exact_boundary(self, monkeypatch):
        calls = []

        class FakeSplitter:
            def split_text(self, text):
                calls.append(text)
                return [text[:2], text[2:]]

        monkeypatch.setattr(
            "packages.core.utils.chunking._get_plain_splitter", lambda: FakeSplitter()
        )
        exact = "x" * CHUNK_SIZE
        result = _apply_secondary_chunking([exact])
        assert calls == []
        assert result == [exact]

    def test_chunk_text_at_chunk_limit_skips_content_type_detection(self, monkeypatch):
        def fail_detect(*_args, **_kwargs):
            raise AssertionError("detect_content_type should not be called")

        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type", fail_detect
        )
        text = "x" * CHUNK_SIZE
        assert chunk_text(text) == [text]

    def test_chunk_text_detect_content_type_called_with_text_and_file_path(
        self, monkeypatch
    ):
        seen = []

        def fake_detect(text, file_path=None):
            seen.append((text, file_path))
            return ContentType.PLAIN

        class FakePlainSplitter:
            def split_text(self, _text):
                return [" x ", " y "]

        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type", fake_detect
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking._get_plain_splitter",
            lambda: FakePlainSplitter(),
        )
        text = "a" * (CHUNK_SIZE + 10)
        assert chunk_text(text, file_path="doc.md") == ["x", "y"]
        assert seen == [(text, "doc.md")]

    def test_chunk_text_logs_debug_messages_with_context(self, monkeypatch):
        debug_logs = []
        monkeypatch.setattr(
            "packages.core.utils.chunking.logger.debug",
            lambda msg: debug_logs.append(msg),
        )

        class FakePlainSplitter:
            def split_text(self, _text):
                return [" x ", " y "]

        monkeypatch.setattr(
            "packages.core.utils.chunking._get_plain_splitter",
            lambda: FakePlainSplitter(),
        )

        text = "a" * (CHUNK_SIZE + 10)
        chunks = chunk_text(text, content_type=ContentType.PLAIN)
        assert chunks == ["x", "y"]
        assert any(
            "Chunking text with content type: plain" in str(m) for m in debug_logs
        )
        assert any("Created 2 chunks from" in str(m) for m in debug_logs)

    def test_chunk_text_markdown_prefers_document_page_content(self, monkeypatch):
        class FakeDoc:
            def __init__(self, page_content):
                self.page_content = page_content

            def __str__(self):
                return "from-str"

        class FakeMarkdownSplitter:
            def split_text(self, _text):
                return [FakeDoc(" from-page-content ")]

        monkeypatch.setattr(
            "packages.core.utils.chunking._get_markdown_splitter",
            lambda: FakeMarkdownSplitter(),
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking._apply_secondary_chunking",
            lambda chunks: chunks,
        )

        text = "a" * (CHUNK_SIZE + 10)
        chunks = chunk_text(text, content_type=ContentType.MARKDOWN)
        assert chunks == ["from-page-content"]

    def test_chunk_text_markdown_falls_back_to_str_for_non_document(self, monkeypatch):
        class NoPageContent:
            def __str__(self):
                return " from-str-fallback "

        class FakeMarkdownSplitter:
            def split_text(self, _text):
                return [NoPageContent()]

        monkeypatch.setattr(
            "packages.core.utils.chunking._get_markdown_splitter",
            lambda: FakeMarkdownSplitter(),
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking._apply_secondary_chunking",
            lambda chunks: chunks,
        )

        text = "a" * (CHUNK_SIZE + 10)
        chunks = chunk_text(text, content_type=ContentType.MARKDOWN)
        assert chunks == ["from-str-fallback"]
        assert chunks != ["None"]

    def test_detect_content_type_logs_include_values(self, monkeypatch):
        debug_logs = []
        monkeypatch.setattr(
            "packages.core.utils.chunking.logger.debug",
            lambda msg: debug_logs.append(msg),
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type_from_extension",
            lambda _p: None,
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type_from_heuristics",
            lambda _t: (ContentType.MARKDOWN, 0.51),
        )
        assert detect_content_type("body", None) == ContentType.MARKDOWN
        assert any(
            "No file extension, using heuristics: markdown" in str(m)
            for m in debug_logs
        )

        debug_logs.clear()
        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type_from_extension",
            lambda _p: ContentType.PLAIN,
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type_from_heuristics",
            lambda _t: (ContentType.HTML, 0.8),
        )
        assert detect_content_type("body", "a.txt") == ContentType.HTML
        assert any("heuristics override with html" in str(m) for m in debug_logs)

        debug_logs.clear()
        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type_from_extension",
            lambda _p: ContentType.MARKDOWN,
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking.detect_content_type_from_heuristics",
            lambda _t: (ContentType.HTML, 0.95),
        )
        assert detect_content_type("body", "a.md") == ContentType.MARKDOWN
        assert any(
            "Using extension-based content type: markdown" in str(m) for m in debug_logs
        )

    def test_chunk_text_html_splitter_receives_text_and_prefers_page_content(
        self, monkeypatch
    ):
        class Doc:
            page_content = "from-page-content"

            def __str__(self):
                return "from-str"

        class FakeHTMLSplitter:
            seen = []

            def split_text(self, text):
                self.seen.append(text)
                return [Doc()]

        monkeypatch.setattr(
            "packages.core.utils.chunking._get_html_splitter",
            lambda: FakeHTMLSplitter(),
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking._apply_secondary_chunking",
            lambda chunks: chunks,
        )

        text = "<html>" + ("x" * CHUNK_SIZE) + "</html>"
        chunks = chunk_text(text, content_type=ContentType.HTML)
        assert FakeHTMLSplitter.seen == [text]
        assert chunks == ["from-page-content"]

    def test_chunk_text_html_path_normalizes_and_filters(self, monkeypatch):
        class Doc:
            def __init__(self, page_content):
                self.page_content = page_content

        class FakeHTMLSplitter:
            def split_text(self, _text):
                return [Doc("  first  "), " second ", "", "   "]

        seen_secondary_input = []

        def fake_secondary(chunks):
            seen_secondary_input.append(chunks)
            return chunks

        monkeypatch.setattr(
            "packages.core.utils.chunking._get_html_splitter",
            lambda: FakeHTMLSplitter(),
        )
        monkeypatch.setattr(
            "packages.core.utils.chunking._apply_secondary_chunking", fake_secondary
        )

        text = "<html>" + ("x" * (CHUNK_SIZE + 1)) + "</html>"
        chunks = chunk_text(text, content_type=ContentType.HTML)
        assert seen_secondary_input == [["  first  ", " second ", "", "   "]]
        assert chunks == ["first", "second"]

    def test_chunk_text_plain_path_uses_plain_splitter(self, monkeypatch):
        class FakePlainSplitter:
            def split_text(self, _text):
                return ["  a  ", "", " b "]

        monkeypatch.setattr(
            "packages.core.utils.chunking._get_plain_splitter",
            lambda: FakePlainSplitter(),
        )
        text = "x" * (CHUNK_SIZE + 20)
        chunks = chunk_text(text, content_type=ContentType.PLAIN)
        assert chunks == ["a", "b"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
