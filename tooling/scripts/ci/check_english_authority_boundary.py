#!/usr/bin/env python3
"""Guard English-only tracked Markdown surfaces."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
OPERATOR_BOUNDARY_DOCS = ("AGENTS.md", "CLAUDE.md")
AUTHORITY_SCOPE_NOTE = (
    "All tracked Markdown docs are English-only. This includes root docs, public docs, "
    "module navigation docs, and snapshot Markdown tracked under .github/."
)
BOUNDARY_NOTE = "Internal operator guidance for this fork. Not canonical public collaboration policy"


def main() -> int:
    failures: list[str] = []

    tracked_markdown = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()

    for rel_path in tracked_markdown:
        if not rel_path:
            continue
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if CJK_RE.search(text):
            failures.append(f"{rel_path} must stay English-only.")

    for rel_path in OPERATOR_BOUNDARY_DOCS:
        text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        if BOUNDARY_NOTE not in text:
            failures.append(
                f"{rel_path} must declare its internal operator boundary note."
            )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        f"PASS: {AUTHORITY_SCOPE_NOTE} Operator docs declare their internal boundary."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
