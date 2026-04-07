#!/usr/bin/env python3
"""Guard English-only active runtime source and prompt surfaces."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CJK_RE = re.compile(r"[\u4e00-\u9fff]")

# These paths participate in the default runtime/product surface and must keep
# English-only defaults so public collaboration and diagnostics remain searchable.
INCLUDED_PREFIXES = (
    "services/",
    "packages/core/",
    "packages/prompts/",
    "apps/web/src/",
)

EXCLUDED_PREFIXES = (
    "apps/web/src/lib/locales/",
    "apps/web/src/lib/api/generated/",
)

ALLOWED_FILES: set[str] = set()

EXCLUDED_SUFFIXES = (
    ".test.ts",
    ".test.tsx",
    ".test.js",
    ".test.jsx",
    ".spec.ts",
    ".spec.tsx",
    ".spec.js",
    ".spec.jsx",
)


def tracked_runtime_files() -> list[str]:
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()

    result: list[str] = []
    for rel_path in tracked:
        if not rel_path:
            continue
        if rel_path in ALLOWED_FILES:
            continue
        if not rel_path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".jinja")):
            continue
        if rel_path.endswith(EXCLUDED_SUFFIXES):
            continue
        if not rel_path.startswith(INCLUDED_PREFIXES):
            continue
        if rel_path.startswith(EXCLUDED_PREFIXES):
            continue
        result.append(rel_path)
    return result


def main() -> int:
    failures: list[str] = []

    for rel_path in tracked_runtime_files():
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if CJK_RE.search(text):
            failures.append(
                f"{rel_path} must keep active runtime defaults and prompts English-only."
            )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: active runtime source and prompt surfaces keep English-only defaults.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
