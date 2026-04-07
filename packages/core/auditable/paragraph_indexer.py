from __future__ import annotations

import hashlib
import re

from packages.core.auditable.schemas import SourceParagraph


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_paragraphs(text: str) -> list[str]:
    return [chunk.strip() for chunk in re.split(r"\n\s*\n+", text) if chunk.strip()]


def index_source_paragraphs(text: str) -> list[SourceParagraph]:
    source_paragraphs: list[SourceParagraph] = []

    for order, raw_text in enumerate(split_paragraphs(text), start=1):
        canonical_text = normalize_whitespace(raw_text)
        canonical_hash = hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()

        source_paragraphs.append(
            SourceParagraph(
                pid=f"P{order:06d}",
                order=order,
                raw_text=raw_text,
                canonical_text=canonical_text,
                canonical_hash=canonical_hash,
            )
        )

    return source_paragraphs
