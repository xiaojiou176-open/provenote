#!/usr/bin/env python3
"""Fail if repo runtime paths directly import legacy provider SDK surfaces."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SEARCH_ROOTS = (
    REPO_ROOT / "packages",
    REPO_ROOT / "services",
    REPO_ROOT / "apps" / "web" / "src",
)

PATTERNS = (
    re.compile(r"\bfrom\s+langchain_anthropic\b"),
    re.compile(r"\bimport\s+langchain_anthropic\b"),
    re.compile(r"\bfrom\s+langchain_ollama\b"),
    re.compile(r"\bimport\s+langchain_ollama\b"),
    re.compile(r"\bfrom\s+langchain_groq\b"),
    re.compile(r"\bimport\s+langchain_groq\b"),
    re.compile(r"\bfrom\s+langchain_mistralai\b"),
    re.compile(r"\bimport\s+langchain_mistralai\b"),
    re.compile(r"\bChatAnthropic\b"),
    re.compile(r"\bChatOllama\b"),
    re.compile(r"\bChatGroq\b"),
    re.compile(r"\bMistralAI\b"),
)


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "node_modules" in path.parts:
                continue
            if path.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            files.append(path)
    return files


def main() -> int:
    failures: list[str] = []

    for path in iter_source_files():
        text = path.read_text(encoding="utf-8")
        for idx, line in enumerate(text.splitlines(), start=1):
            for pattern in PATTERNS:
                if pattern.search(line):
                    rel_path = path.relative_to(REPO_ROOT)
                    failures.append(
                        f"{rel_path}:{idx}: direct legacy provider runtime import/symbol found: {line.strip()}"
                    )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: repo runtime paths contain no direct legacy provider SDK imports.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
