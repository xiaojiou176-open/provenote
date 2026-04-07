"""
Text utilities for Provenote.
Extracted from main utils to avoid circular imports.
"""

import re
from typing import Tuple

# Patterns for matching thinking content in AI responses
# Standard pattern: <think>...</think>
THINK_PATTERN = re.compile(r"<think>(.*?)</think>", re.DOTALL)
# Pattern for malformed output: content</think> (missing opening tag)
THINK_PATTERN_NO_OPEN = re.compile(r"^(.*?)</think>", re.DOTALL)
ALLOWED_VISIBLE_PUNCTUATION = {" ", "\n", "\t", ".", ",", "!", "?", "-"}

UNICODE_SPACE_REPLACEMENTS = {
    "\u2000": " ",
    "\u2001": " ",
    "\u2002": " ",
    "\u2003": " ",
    "\u2004": " ",
    "\u2005": " ",
    "\u2006": " ",
    "\u2007": " ",
    "\u2008": " ",
    "\u2009": " ",
    "\u200a": " ",
    "\u200b": " ",
    "\u202f": " ",
    "\u205f": " ",
    "\u3000": " ",
    "\N{NO-BREAK SPACE}": " ",
    "\u2028": "\n",
    "\u2029": "\n",
    "\r": "\n",
}


def _is_allowed_visible_character(char: str) -> bool:
    if char.isalnum() or char == "_":
        return True
    return char in ALLOWED_VISIBLE_PUNCTUATION


def remove_non_ascii(text: str) -> str:
    """Remove non-ASCII characters from text."""
    return "".join(char for char in text if ord(char) < 128)


def remove_non_printable(text: str) -> str:
    """Remove non-printable characters from text."""
    text = "".join(UNICODE_SPACE_REPLACEMENTS.get(char, char) for char in text)
    text = text.strip()

    # Keep letters (including accented ones), numbers, spaces, newlines, tabs, and basic punctuation
    return "".join(char for char in text if _is_allowed_visible_character(char))


def parse_thinking_content(content: object) -> Tuple[str, str]:
    """
    Parse message content to extract thinking content from <think> tags.

    Handles both well-formed tags and malformed output where the opening
    <think> tag is missing but </think> is present.

    Args:
        content (str): The original message content

    Returns:
        Tuple[str, str]: (thinking_content, cleaned_content)
            - thinking_content: Content from within <think> tags
            - cleaned_content: Original content with <think> blocks removed

    Example:
        >>> content = "<think>Let me analyze this</think>Here's my answer"
        >>> thinking, cleaned = parse_thinking_content(content)
        >>> print(thinking)
        "Let me analyze this"
        >>> print(cleaned)
        "Here's my answer"
    """
    # Input validation
    if not isinstance(content, str):
        return "", str(content) if content is not None else ""

    # Limit processing for very large content (100KB limit)
    if len(content) > 100000:
        return "", content

    # Find all well-formed thinking blocks
    thinking_matches = THINK_PATTERN.findall(content)

    if thinking_matches:
        # Join all thinking content with double newlines
        thinking_content = "\n\n".join(match.strip() for match in thinking_matches)

        # Remove all <think>...</think> blocks from the original content
        cleaned_content = THINK_PATTERN.sub("", content)

        # Clean up extra whitespace
        cleaned_content = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned_content).strip()

        return thinking_content, cleaned_content

    # Handle malformed output: content</think> (missing opening tag)
    # Some models like Nemotron output thinking without the opening <think> tag
    malformed_match = THINK_PATTERN_NO_OPEN.match(content)
    if malformed_match:
        thinking_content = malformed_match.group(1).strip()
        # Remove the thinking content and </think> tag
        cleaned_content = content[malformed_match.end() :].strip()
        return thinking_content, cleaned_content

    return "", content


def clean_thinking_content(content: str) -> str:
    """
    Remove thinking content from AI responses, returning only the cleaned content.

    This is a convenience function for cases where you only need the cleaned
    content and don't need access to the thinking process.

    Args:
        content (str): The original message content with potential <think> tags

    Returns:
        str: Content with <think> blocks removed and whitespace cleaned

    Example:
        >>> content = "<think>Let me think...</think>Here's the answer"
        >>> clean_thinking_content(content)
        "Here's the answer"
    """
    _, cleaned_content = parse_thinking_content(content)
    return cleaned_content


def extract_text_content(content) -> str:
    """Extract text from LLM response content.

    Handles both plain string responses and structured content formats
    (e.g. Gemini's envelope format):
    [{'type': 'text', 'text': '...', 'extras': {...}}]

    Args:
        content: The content from an AI message, either a string or a list of parts.

    Returns:
        The extracted text content as a string.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
        return "".join(text_parts)
    return str(content)
