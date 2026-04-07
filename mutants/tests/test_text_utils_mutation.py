from __future__ import annotations

from packages.core.utils.text_utils import (
    ALLOWED_VISIBLE_PUNCTUATION,
    UNICODE_SPACE_REPLACEMENTS,
    _is_allowed_visible_character,
    clean_thinking_content,
    extract_text_content,
    parse_thinking_content,
    remove_non_ascii,
    remove_non_printable,
)


def test_remove_non_ascii_strips_non_ascii_chars() -> None:
    assert remove_non_ascii("Hello 世界 café") == "Hello  caf"


def test_remove_non_ascii_strips_delete_control_boundary() -> None:
    assert remove_non_ascii(f"A{chr(128)}B") == "AB"


def test_remove_non_printable_preserves_tabs_and_newlines() -> None:
    text = "Line1\nLine2\tTabbed\u2000"
    assert remove_non_printable(text) == "Line1\nLine2\tTabbed"


def test_remove_non_printable_normalizes_line_separators_and_nbsp() -> None:
    text = "A\u2028B\u2029C\rD\xa0E"
    assert remove_non_printable(text) == "A\nB\nC\nD E"


def test_remove_non_printable_drops_control_chars_and_symbols() -> None:
    text = "ok\u0000\u0001@\u2603!"
    assert remove_non_printable(text) == "ok!"


def test_remove_non_printable_drops_vertical_tab_and_form_feed() -> None:
    text = "A\x0bB\x0cC\tD\nE"
    assert remove_non_printable(text) == "ABC\tD\nE"


def test_remove_non_printable_strips_outer_unicode_spaces_and_preserves_inner_ascii_spacing() -> (
    None
):
    text = "\u2002 Hello\xa0World \u3000"
    assert remove_non_printable(text) == "Hello World"


def test_remove_non_printable_normalizes_all_supported_unicode_spaces() -> None:
    for source, replacement in UNICODE_SPACE_REPLACEMENTS.items():
        assert remove_non_printable(f"A{source}B") == f"A{replacement}B".strip()


def test_is_allowed_visible_character_accepts_expected_boundaries() -> None:
    assert _is_allowed_visible_character("_") is True
    assert _is_allowed_visible_character("9") is True
    assert _is_allowed_visible_character(".") is True
    assert _is_allowed_visible_character("@") is False
    for char in ALLOWED_VISIBLE_PUNCTUATION:
        assert _is_allowed_visible_character(char) is True


def test_parse_thinking_content_handles_well_formed_tags() -> None:
    thinking, cleaned = parse_thinking_content("<think>inner</think>answer")
    assert thinking == "inner"
    assert cleaned == "answer"


def test_parse_thinking_content_handles_malformed_missing_open_tag() -> None:
    thinking, cleaned = parse_thinking_content("hidden</think>visible")
    assert thinking == "hidden"
    assert cleaned == "visible"


def test_parse_thinking_content_for_large_content_returns_original() -> None:
    huge = "x" * 100001
    thinking, cleaned = parse_thinking_content(huge)
    assert thinking == ""
    assert cleaned == huge


def test_parse_thinking_content_with_multiple_blocks_joins_and_cleans() -> None:
    payload = "before\n<think> first </think>\n\n<think>second</think>\n\nafter"
    thinking, cleaned = parse_thinking_content(payload)
    assert thinking == "first\n\nsecond"
    assert cleaned == "before\n\nafter"


def test_parse_thinking_content_without_tags_returns_original() -> None:
    thinking, cleaned = parse_thinking_content("plain answer only")
    assert thinking == ""
    assert cleaned == "plain answer only"


def test_parse_thinking_content_handles_non_string_input() -> None:
    thinking_none, cleaned_none = parse_thinking_content(None)
    thinking_int, cleaned_int = parse_thinking_content(123)
    assert thinking_none == ""
    assert cleaned_none == ""
    assert thinking_int == ""
    assert cleaned_int == "123"


def test_parse_thinking_content_exact_100000_boundary_is_processed() -> None:
    payload = "<think>secret</think>" + ("a" * (100000 - len("<think>secret</think>")))
    thinking, cleaned = parse_thinking_content(payload)
    assert thinking == "secret"
    assert cleaned == "a" * (100000 - len("<think>secret</think>"))


def test_clean_thinking_content_removes_hidden_block() -> None:
    assert clean_thinking_content("<think>secret</think>public") == "public"


def test_clean_thinking_content_without_thinking_block_is_stable() -> None:
    assert clean_thinking_content("already clean") == "already clean"


def test_extract_text_content_from_structured_list() -> None:
    payload = [{"type": "text", "text": "A"}, {"type": "text", "text": "B"}, "!"]
    assert extract_text_content(payload) == "AB!"


def test_extract_text_content_ignores_non_text_items() -> None:
    payload = [{"type": "meta"}, {"type": "text", "text": "A"}, 1, "B"]
    assert extract_text_content(payload) == "AB"


def test_extract_text_content_fallback_to_str() -> None:
    assert extract_text_content(123) == "123"
