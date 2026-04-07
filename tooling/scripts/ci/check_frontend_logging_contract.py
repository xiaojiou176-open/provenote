#!/usr/bin/env python3
"""Block raw console logging in shared apps/web runtime surfaces."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

CONSOLE_TOKENS = (
    "console.debug(",
    "console.info(",
    "console.log(",
    "console.warn(",
    "console.error(",
)
DEFAULT_SCAN_ROOTS = ("apps/web/src",)
ALLOWED_FILE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
ALLOWED_CONSOLE_FILES = {"apps/web/src/lib/log.ts"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None, help="Repository root path")
    parser.add_argument(
        "--paths", nargs="*", default=None, help="Optional relative paths"
    )
    return parser


def _repo_root(raw: str | None) -> Path:
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parents[3]


def _is_frontend_source(path: Path) -> bool:
    return path.suffix in ALLOWED_FILE_SUFFIXES and path.is_file()


def _iter_default_files(repo_root: Path) -> Iterable[Path]:
    for root in DEFAULT_SCAN_ROOTS:
        root_path = repo_root / root
        if root_path.is_file() and _is_frontend_source(root_path):
            yield root_path
            continue
        if not root_path.is_dir():
            continue
        for candidate in sorted(root_path.rglob("*")):
            if _is_frontend_source(candidate):
                yield candidate


def _resolve_candidate_files(
    repo_root: Path, raw_paths: list[str] | None
) -> list[Path]:
    if not raw_paths:
        return sorted(dict.fromkeys(_iter_default_files(repo_root)))

    resolved: list[Path] = []
    default_roots = tuple((repo_root / item).resolve() for item in DEFAULT_SCAN_ROOTS)
    for raw in raw_paths:
        candidate = (repo_root / raw).resolve()
        if not candidate.exists():
            continue
        if candidate.is_dir():
            for nested in sorted(candidate.rglob("*")):
                if not _is_frontend_source(nested):
                    continue
                if any(nested.is_relative_to(root) for root in default_roots):
                    resolved.append(nested)
            continue
        if not _is_frontend_source(candidate):
            continue
        if any(candidate.is_relative_to(root) for root in default_roots):
            resolved.append(candidate)
    return sorted(dict.fromkeys(resolved))


def find_console_violations(repo_root: Path, files: list[Path]) -> list[str]:
    violations: list[str] = []
    for path in files:
        rel = path.relative_to(repo_root).as_posix()
        if rel in ALLOWED_CONSOLE_FILES:
            continue
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            if any(token in line for token in CONSOLE_TOKENS):
                violations.append(
                    f"{rel}:{lineno}: shared frontend runtime surfaces must use @/lib/log instead of raw console calls"
                )
    return violations


def main() -> int:
    args = build_parser().parse_args()
    repo_root = _repo_root(args.repo_root)
    scan_files = _resolve_candidate_files(repo_root, args.paths)

    if not scan_files:
        if args.paths:
            print(
                "PASS [FE-LOG-001]: no shared frontend logging files in provided scope."
            )
            return 0
        print(
            "FAIL [FE-LOG-BOOT-001]: no shared frontend logging files found in default scope; "
            "frontend logging gate must fail closed."
        )
        return 1

    violations = find_console_violations(repo_root, scan_files)
    if violations:
        print(
            "FAIL [FE-LOG-000]: shared apps/web runtime surfaces must use the unified frontend logger."
        )
        for item in violations:
            print(f"- {item}")
        return 1

    print(
        "PASS [FE-LOG-000]: apps/web runtime surfaces use the unified frontend logger."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
