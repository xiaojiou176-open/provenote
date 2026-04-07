#!/usr/bin/env python3
"""Fail closed on non-canonical repo-owned runtime output paths."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SKIP_DIRS = {
    ".git",
    ".runtime-cache",
    "node_modules",
    ".next",
    ".next-playwright",
    ".next-playwright-manual",
    "__pycache__",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy",
        default="config/runtime/output-path-policy.json",
        help="Path to the output path policy JSON file",
    )
    return parser


def _iter_scan_files(repo_root: Path, scan_roots: list[str]) -> list[Path]:
    files: list[Path] = []
    for rel_path in scan_roots:
        target = repo_root / rel_path
        if not target.exists():
            continue
        if target.is_file():
            files.append(target)
            continue
        files.extend(
            path
            for path in target.rglob("*")
            if path.is_file() and not any(part in SKIP_DIRS for part in path.parts)
        )
    return sorted({path.resolve() for path in files})


def _is_under(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    policy = _load_json((repo_root / args.policy).resolve())

    forbidden_paths = policy.get("forbidden_paths", [])
    allowed_paths = policy.get("tool_constrained_allowed_paths", [])
    scan_roots = policy.get("scan_roots", [])
    reference_patterns = policy.get("forbidden_reference_patterns", [])

    failures: list[str] = []

    if not isinstance(forbidden_paths, list) or not forbidden_paths:
        failures.append("forbidden_paths must be a non-empty list")
        forbidden_paths = []
    if not isinstance(allowed_paths, list):
        failures.append("tool_constrained_allowed_paths must be a list")
        allowed_paths = []
    if not isinstance(scan_roots, list) or not scan_roots:
        failures.append("scan_roots must be a non-empty list")
        scan_roots = []
    if not isinstance(reference_patterns, list) or not reference_patterns:
        failures.append("forbidden_reference_patterns must be a non-empty list")
        reference_patterns = []

    allowed_roots = [(repo_root / item).resolve() for item in allowed_paths]

    for rel_path in forbidden_paths:
        target = (repo_root / rel_path).resolve()
        if target.exists() and not any(
            _is_under(target, root) for root in allowed_roots
        ):
            failures.append(f"forbidden runtime output path present: {rel_path}")

    for file_path in _iter_scan_files(repo_root, scan_roots):
        rel = file_path.relative_to(repo_root).as_posix()
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in reference_patterns:
            regex = re.compile(pattern)
            for match in regex.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                snippet = text.splitlines()[line_no - 1].strip()
                failures.append(
                    f"{rel}:{line_no}: forbidden non-canonical output reference -> {snippet}"
                )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        "PASS: non-canonical repo-owned runtime output paths are absent and authoritative references stay on canonical paths."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
