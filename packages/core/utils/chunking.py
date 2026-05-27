"""
Chunking utilities for Notebooklab.

Provides content-type detection and smart text chunking for embedding operations.
Supports HTML, Markdown, and plain text with appropriate splitters for each type.

Key functions:
- detect_content_type(): Detects content type from file extension or content heuristics
- chunk_text(): Splits text into chunks using appropriate splitter for content type

Environment Variables:
    OPEN_NOTEBOOK_CHUNK_SIZE: Maximum chunk size in characters (default: 1200)
    OPEN_NOTEBOOK_CHUNK_OVERLAP: Overlap between chunks in characters (default: 15% of CHUNK_SIZE)
"""

import re
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

from langchain_text_splitters import (
    HTMLHeaderTextSplitter,
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from packages.core.observability.logger import logger
from packages.core.settings import read_env


def _get_chunk_size() -> int:
    """Get chunk size from environment variable or use default."""
    chunk_size_str = read_env("OPEN_NOTEBOOK_CHUNK_SIZE")
    if chunk_size_str:
        try:
            chunk_size = int(chunk_size_str)
            if chunk_size < 100:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is too small. "
                    f"Using minimum value of 100."
                )
                return 100
            if chunk_size > 8192:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_SIZE ({chunk_size}) is very large. "
                    f"This may cause issues with some embedding models."
                )
            logger.info(f"Using custom chunk size: {chunk_size} characters")
            return chunk_size
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_SIZE value: '{chunk_size_str}'. "
                f"Using default: 1200"
            )
    return 1200


def _get_chunk_overlap(chunk_size: int) -> int:
    """Get chunk overlap from environment variable or calculate default (15% of chunk size)."""
    overlap_str = read_env("OPEN_NOTEBOOK_CHUNK_OVERLAP")
    if overlap_str:
        try:
            overlap = int(overlap_str)
            if overlap < 0:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be negative. "
                    f"Using 0."
                )
                return 0
            if overlap >= chunk_size:
                logger.warning(
                    f"OPEN_NOTEBOOK_CHUNK_OVERLAP ({overlap}) cannot be >= chunk size ({chunk_size}). "
                    f"Using 15% of chunk size: {int(chunk_size * 0.15)}"
                )
                return int(chunk_size * 0.15)
            logger.info(f"Using custom chunk overlap: {overlap} characters")
            return overlap
        except ValueError:
            logger.warning(
                f"Invalid OPEN_NOTEBOOK_CHUNK_OVERLAP value: '{overlap_str}'. "
                f"Using default: 15% of chunk size"
            )
    return int(chunk_size * 0.15)


# Constants (computed at import time from environment variables)
CHUNK_SIZE = _get_chunk_size()
CHUNK_OVERLAP = _get_chunk_overlap(CHUNK_SIZE)
HIGH_CONFIDENCE_THRESHOLD = 0.8  # Threshold for heuristics to override extension

logger.debug(
    f"Chunking configuration: CHUNK_SIZE={CHUNK_SIZE}, CHUNK_OVERLAP={CHUNK_OVERLAP}"
)


class ContentType(Enum):
    """Content type for chunking strategy selection."""

    HTML = "html"
    MARKDOWN = "markdown"
    PLAIN = "plain"


# File extension mappings
_EXTENSION_TO_CONTENT_TYPE = {
    # HTML
    ".html": ContentType.HTML,
    ".htm": ContentType.HTML,
    ".xhtml": ContentType.HTML,
    # Markdown
    ".md": ContentType.MARKDOWN,
    ".markdown": ContentType.MARKDOWN,
    ".mdown": ContentType.MARKDOWN,
    ".mkd": ContentType.MARKDOWN,
    # Plain text (explicit)
    ".txt": ContentType.PLAIN,
    ".text": ContentType.PLAIN,
    # Code files (treat as plain)
    ".py": ContentType.PLAIN,
    ".js": ContentType.PLAIN,
    ".ts": ContentType.PLAIN,
    ".java": ContentType.PLAIN,
    ".c": ContentType.PLAIN,
    ".cpp": ContentType.PLAIN,
    ".go": ContentType.PLAIN,
    ".rs": ContentType.PLAIN,
    ".rb": ContentType.PLAIN,
    ".php": ContentType.PLAIN,
    ".sh": ContentType.PLAIN,
    ".bash": ContentType.PLAIN,
    ".zsh": ContentType.PLAIN,
    ".sql": ContentType.PLAIN,
    ".json": ContentType.PLAIN,
    ".yaml": ContentType.PLAIN,
    ".yml": ContentType.PLAIN,
    ".xml": ContentType.PLAIN,
    ".csv": ContentType.PLAIN,
    ".tsv": ContentType.PLAIN,
}


def detect_content_type_from_extension(
    file_path: Optional[str],
) -> Optional[ContentType]:
    """
    Detect content type from file extension.

    Args:
        file_path: Path to the file (can be full path or just filename)

    Returns:
        ContentType if extension is recognized, None otherwise
    """
    if not file_path:
        return None

    try:
        extension = Path(file_path).suffix.lower()
        return _EXTENSION_TO_CONTENT_TYPE.get(extension)
    except Exception:
        return None


def detect_content_type_from_heuristics(text: str) -> Tuple[ContentType, float]:
    """
    Detect content type using content heuristics.

    Args:
        text: The text content to analyze

    Returns:
        Tuple of (ContentType, confidence_score) where confidence is 0.0-1.0
    """
    if not text or len(text) < 10:
        return ContentType.PLAIN, 0.5

    # Sample first 5000 chars for efficiency
    sample = text[:5000]

    # Check HTML first (most specific patterns)
    html_score = _calculate_html_score(sample)
    if html_score >= HIGH_CONFIDENCE_THRESHOLD:
        return ContentType.HTML, html_score

    # Check Markdown
    markdown_score = _calculate_markdown_score(sample)

    # Return the higher scoring type, or PLAIN if both are low
    if html_score > markdown_score and html_score > 0.3:
        return ContentType.HTML, html_score
    elif markdown_score > 0.3:
        return ContentType.MARKDOWN, markdown_score
    else:
        return ContentType.PLAIN, 0.6


def _calculate_html_score(text: str) -> float:
    """Calculate confidence score for HTML content."""
    normalized_text = text.lower()
    structural_tags = ("<head", "<body", "<div", "<span", "<p>", "<table", "<form")

    doctype_score = 0.4 if "<!doctype html" in normalized_text else 0.0
    html_tag_score = 0.3 if re.search(r"<html[\s>]", normalized_text) else 0.0
    strong_indicator_count = int(doctype_score > 0.0) + int(html_tag_score > 0.0)
    structural_hits = sum(tag in normalized_text for tag in structural_tags)
    structural_cap = 5 - strong_indicator_count
    structural_score = min(structural_hits, structural_cap) * 0.1
    header_score = 0.15 if re.search(r"<h[1-6][\s>]", normalized_text) else 0.0
    closing_tag_score = 0.1 if re.search(r"</\w+>", text) else 0.0

    score = (
        doctype_score
        + html_tag_score
        + structural_score
        + header_score
        + closing_tag_score
    )
    return min(score, 1.0)


def _calculate_markdown_score(text: str) -> float:
    """Calculate confidence score for Markdown content."""
    header_matches = len(re.findall(r"^#{1,6}\s+.+", text, re.MULTILINE))
    link_matches = len(re.findall(r"\[[^\]\n]{1,200}\]\([^\)\n]{1,2048}\)", text))
    list_matches = len(re.findall(r"^[\*\-\+]\s+", text, re.MULTILINE))
    list_matches += len(re.findall(r"^\d+\.\s+", text, re.MULTILINE))

    header_score = 0.35 if header_matches >= 3 else 0.2 if header_matches >= 1 else 0.0
    link_score = 0.25 if link_matches >= 2 else 0.15 if link_matches >= 1 else 0.0
    code_block_score = 0.2 if re.search(r"^```", text, re.MULTILINE) else 0.0
    inline_code_score = 0.1 if re.search(r"`[^`]+`", text) else 0.0
    list_score = 0.15 if list_matches >= 3 else 0.08 if list_matches >= 1 else 0.0
    emphasis_score = 0.1 if re.search(r"\*\*.+?\*\*|__.+?__", text) else 0.0
    blockquote_score = 0.1 if re.search(r"^>\s+", text, re.MULTILINE) else 0.0

    score = (
        header_score
        + link_score
        + code_block_score
        + inline_code_score
        + list_score
        + emphasis_score
        + blockquote_score
    )
    return min(score, 1.0)


def detect_content_type(text: str, file_path: Optional[str] = None) -> ContentType:
    """
    Detect content type using file extension (primary) and heuristics (fallback).

    Strategy:
    1. If file extension is available and recognized, use it as primary
    2. If no extension or generic extension (.txt), use heuristics
    3. Heuristics can override extension only with very high confidence

    Args:
        text: The text content
        file_path: Optional file path for extension-based detection

    Returns:
        Detected ContentType
    """
    # Try extension-based detection first
    extension_type = detect_content_type_from_extension(file_path)

    # Get heuristic-based detection
    heuristic_type, confidence = detect_content_type_from_heuristics(text)

    # If no extension or generic extension, use heuristics
    if extension_type is None:
        logger.debug(
            f"No file extension, using heuristics: {heuristic_type.value} "
            f"(confidence: {confidence:.2f})"
        )
        return heuristic_type

    # If extension suggests plain text but heuristics are very confident, override
    if extension_type == ContentType.PLAIN and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        logger.debug(
            f"Extension suggests plain, but heuristics override with "
            f"{heuristic_type.value} (confidence: {confidence:.2f})"
        )
        return heuristic_type

    # Otherwise trust the extension
    logger.debug(f"Using extension-based content type: {extension_type.value}")
    return extension_type


def _get_html_splitter() -> HTMLHeaderTextSplitter:
    """Get HTML header splitter configured for h1, h2, h3."""
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
    ]
    return HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


def _get_markdown_splitter() -> MarkdownHeaderTextSplitter:
    """Get Markdown header splitter configured for #, ##, ###."""
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    return MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )


def _get_plain_splitter() -> RecursiveCharacterTextSplitter:
    """Get plain text splitter using CHUNK_SIZE and CHUNK_OVERLAP constants."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
    )


def _apply_secondary_chunking(chunks: List[str]) -> List[str]:
    """
    Apply secondary chunking to ensure no chunk exceeds CHUNK_SIZE.

    Used when primary splitters (HTML/Markdown) produce oversized chunks.
    """
    result = []
    secondary_splitter = _get_plain_splitter()

    for chunk in chunks:
        if len(chunk) > CHUNK_SIZE:
            # Split oversized chunk
            sub_chunks = secondary_splitter.split_text(chunk)
            result.extend(sub_chunks)
        else:
            result.append(chunk)

    return result


def chunk_text(
    text: str,
    content_type: Optional[ContentType] = None,
    file_path: Optional[str] = None,
) -> List[str]:
    """
    Split text into chunks using appropriate splitter for content type.

    Args:
        text: The text to chunk
        content_type: Optional explicit content type (auto-detected if not provided)
        file_path: Optional file path for content type detection

    Returns:
        List of text chunks, each <= CHUNK_SIZE characters
    """
    if not text or not text.strip():
        return []

    # Short text doesn't need chunking
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(text, file_path)

    logger.debug(f"Chunking text with content type: {content_type.value}")

    # Select appropriate splitter
    if content_type == ContentType.HTML:
        html_splitter = _get_html_splitter()
        # HTML splitter returns Document objects
        docs = html_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    elif content_type == ContentType.MARKDOWN:
        markdown_splitter = _get_markdown_splitter()
        # Markdown splitter returns Document objects
        docs = markdown_splitter.split_text(text)
        chunks = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
    else:
        # Plain text - use recursive splitter directly
        plain_splitter = _get_plain_splitter()
        chunks = plain_splitter.split_text(text)

    # Apply secondary chunking if needed (for HTML/Markdown that may produce large chunks)
    if content_type in (ContentType.HTML, ContentType.MARKDOWN):
        chunks = _apply_secondary_chunking(chunks)

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c and c.strip()]

    logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks
