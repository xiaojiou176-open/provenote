#!/usr/bin/env python3
"""Enforce google-genai imports to stay inside the dedicated adapter layer."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

IMPORT_PATTERN = re.compile(
    r"^\s*(from\s+google\s+import\s+genai|from\s+google\.genai\s+import|import\s+google\.genai)\b"
)
DYNAMIC_IMPORT_PATTERN = re.compile(
    r"(?:"
    r"importlib\.(?:import_module|__import__)\(\s*['\"]google(?:\.genai(?:\.[\w.]+)?)?['\"]\s*\)"
    r"|__import__\(\s*['\"]google(?:\.genai(?:\.[\w.]+)?)?['\"]\s*\)"
    r"|importlib\.util\.find_spec\(\s*['\"]google\.genai(?:\.[\w.]+)?['\"]\s*\)"
    r")"
)
ALLOWED_FILES = {
    "packages/core/ai/google_genai_adapter.py",
}
SKIP_DIRS = {".git", ".venv", ".runtime-cache", "node_modules", "__pycache__"}


def _iter_python_files(repo_root: Path) -> list[Path]:
    """Prefer git-tracked Python files for stable CI performance."""
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo_root), "ls-files", "--", "*.py"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        tracked = []
        for rel in output.splitlines():
            rel_path = Path(rel)
            if any(part in SKIP_DIRS for part in rel_path.parts):
                continue
            tracked.append(repo_root / rel_path)
        if tracked:
            return sorted(tracked)
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    discovered: list[Path] = []
    for root, dirs, files in os.walk(repo_root, topdown=True, followlinks=False):
        dirs[:] = [directory for directory in dirs if directory not in SKIP_DIRS]
        for filename in files:
            if filename.endswith(".py"):
                discovered.append(Path(root) / filename)
    return sorted(discovered)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    violations: list[str] = []

    for file_path in _iter_python_files(repo_root):
        rel = file_path.relative_to(repo_root).as_posix()
        if rel in ALLOWED_FILES:
            continue

        try:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError as exc:
            violations.append(f"{rel}:0: [read-failed] {exc}")
            continue

        for lineno, line in enumerate(
            lines,
            start=1,
        ):
            if IMPORT_PATTERN.search(line) or DYNAMIC_IMPORT_PATTERN.search(line):
                violations.append(f"{rel}:{lineno}: {line.strip()}")

    if violations:
        print(
            "FAIL [GOOGLE-GENAI-001]: direct google-genai imports are only allowed in adapter layer."
        )
        print("Allowed files:")
        for path in sorted(ALLOWED_FILES):
            print(f"- {path}")
        print("Violations:")
        for item in violations:
            print(f"- {item}")
        return 1

    print(
        "PASS [GOOGLE-GENAI-001]: google-genai imports are isolated to adapter layer."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
