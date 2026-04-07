from __future__ import annotations

import os

import pytest

# mutmut sets this per mutant at runtime; default only for pytest collection/bootstrap.
os.environ.setdefault("MUTANT_UNDER_TEST", "__collect__")
from packages.core.utils.chunking import (
    ContentType,
    _calculate_html_score,
    detect_content_type_from_heuristics,
)
from packages.core.utils.text_utils import (
    parse_thinking_content,
    remove_non_printable,
)


def test_detect_content_type_heuristics_samples_exactly_5000_chars(monkeypatch):
    seen_lengths: list[int] = []

    def fake_html_score(sample: str) -> float:
        seen_lengths.append(len(sample))
        return 0.0

    monkeypatch.setattr(
        "packages.core.utils.chunking._calculate_html_score", fake_html_score
    )
    monkeypatch.setattr(
        "packages.core.utils.chunking._calculate_markdown_score", lambda _sample: 0.0
    )

    content_type, confidence = detect_content_type_from_heuristics("x" * 7000)
    assert seen_lengths == [5000]
    assert content_type == ContentType.PLAIN
    assert confidence == pytest.approx(0.6)


def test_detect_content_type_heuristics_markdown_threshold_is_inclusive(monkeypatch):
    monkeypatch.setattr(
        "packages.core.utils.chunking._calculate_html_score", lambda _sample: 0.1
    )
    monkeypatch.setattr(
        "packages.core.utils.chunking._calculate_markdown_score", lambda _sample: 0.8
    )

    content_type, confidence = detect_content_type_from_heuristics("x" * 50)
    assert content_type == ContentType.MARKDOWN
    assert confidence == pytest.approx(0.8)


def test_calculate_html_score_doctype_structural_indicator_cap_shape():
    text = "<!DOCTYPE html><head><body><div><span><p><table><form"
    assert _calculate_html_score(text) == pytest.approx(0.8)


def test_calculate_html_score_html_structural_indicator_cap_shape():
    text = "<html><head><body><div><span><p><table><form"
    assert _calculate_html_score(text) == pytest.approx(0.7)


def test_parse_thinking_content_100000_boundary_is_processed():
    payload = "<think>secret</think>" + ("a" * (100000 - len("<think>secret</think>")))
    thinking, cleaned = parse_thinking_content(payload)
    assert thinking == "secret"
    assert cleaned == "a" * (100000 - len("<think>secret</think>"))


def test_parse_thinking_content_100001_boundary_is_short_circuited():
    payload = "<think>secret</think>" + ("a" * (100001 - len("<think>secret</think>")))
    thinking, cleaned = parse_thinking_content(payload)
    assert thinking == ""
    assert cleaned == payload


def test_remove_non_printable_normalizes_internal_unicode_whitespace_to_space():
    assert remove_non_printable("A\u2000B") == "A B"
