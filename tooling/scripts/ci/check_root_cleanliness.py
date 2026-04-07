#!/usr/bin/env python3
"""Enforce declared top-level allowlists for repo root and nested governed roots."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _tracked_top_level_items(repo_root: Path, scope_prefix: str = "") -> set[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")

    items: set[str] = set()
    scope_root = scope_prefix.rstrip("/")
    for line in result.stdout.splitlines():
        rel = line.strip()
        if not rel:
            continue
        if scope_root:
            scope_token = f"{scope_root}/"
            if not rel.startswith(scope_token):
                continue
            rel = rel[len(scope_token) :]
        if not rel or "/" in rel:
            continue
        target = repo_root / (f"{scope_root}/{rel}" if scope_root else rel)
        if not target.exists():
            continue
        items.add(rel)
    return items


def _forbidden_reference_hits(
    repo_root: Path,
    patterns: list[str],
    search_roots: list[str],
    *,
    scope_label: str,
) -> list[str]:
    if not patterns:
        return []

    existing_roots = [path for path in search_roots if (repo_root / path).exists()]
    hits: list[str] = []
    for pattern in patterns:
        result = subprocess.run(
            [
                "rg",
                "-n",
                pattern,
                "--hidden",
                "--glob",
                "!*.pyc",
                "--glob",
                "!.git/**",
                *existing_roots,
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode not in {0, 1}:
            raise RuntimeError(
                result.stderr.strip() or f"rg failed for pattern {pattern!r}"
            )
        if result.returncode == 0:
            hits.extend(
                f"{scope_label}: forbidden canonical reference matched /{pattern}/: {line}"
                for line in result.stdout.splitlines()
            )
    return hits


def _validate_scope(
    repo_root: Path,
    *,
    allowlist_rel_path: str,
    scope_root_rel: str = "",
    search_roots: list[str],
    scope_label: str,
) -> list[str]:
    scope_root = repo_root / scope_root_rel if scope_root_rel else repo_root
    if not scope_root.exists():
        return []

    allowlist = _load_json((repo_root / allowlist_rel_path).resolve())
    allowed_dirs = set(allowlist.get("allowed_directories", []))
    allowed_files = set(allowlist.get("allowed_files", []))
    local_patterns = [
        re.compile(pattern) for pattern in allowlist.get("local_allowed_patterns", [])
    ]
    forbidden_reference_patterns = list(
        allowlist.get("forbidden_reference_patterns", [])
    )

    current_items = {
        item.name for item in scope_root.iterdir() if item.name not in {".", ".."}
    }
    tracked_items = _tracked_top_level_items(repo_root, scope_root_rel)

    failures: list[str] = []
    for item in sorted(tracked_items):
        path = scope_root / item
        if path.is_dir():
            if item not in allowed_dirs:
                failures.append(
                    f"{scope_label}: tracked directory not declared in allowlist: {item}"
                )
        else:
            if item not in allowed_files:
                failures.append(
                    f"{scope_label}: tracked file not declared in allowlist: {item}"
                )

    for item in sorted(current_items):
        path = scope_root / item
        if item in tracked_items:
            continue
        if path.is_dir() and item in allowed_dirs:
            continue
        if path.is_file() and item in allowed_files:
            continue
        if any(pattern.fullmatch(item) for pattern in local_patterns):
            continue
        failures.append(f"{scope_label}: unexpected top-level item present: {item}")

    scoped_roots = [
        f"{scope_root_rel.rstrip('/')}/{root}" if scope_root_rel else root
        for root in search_roots
    ]
    failures.extend(
        _forbidden_reference_hits(
            repo_root,
            forbidden_reference_patterns,
            scoped_roots,
            scope_label=scope_label,
        )
    )
    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allowlist",
        default="config/root/top-level-allowlist.json",
        help="Path to primary top-level allowlist JSON",
    )
    parser.add_argument(
        "--mode",
        choices=("local", "authoritative"),
        default="local",
        help="local allows local-only patterns; authoritative additionally blocks declared forbidden root items",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    primary_allowlist = _load_json((repo_root / args.allowlist).resolve())

    failures = _validate_scope(
        repo_root,
        allowlist_rel_path=args.allowlist,
        search_roots=[
            "README.md",
            "docs",
            ".github",
            "Makefile",
            ".pre-commit-config.yaml",
            "ops",
            "AGENTS.md",
            "CLAUDE.md",
        ],
        scope_label="root",
    )
    if args.mode == "authoritative":
        for item in primary_allowlist.get("authoritative_disallowed_names", []):
            path = repo_root / item
            if path.exists():
                failures.append(
                    f"root: authoritative mode forbids top-level item: {item}"
                )
    failures.extend(
        _validate_scope(
            repo_root,
            allowlist_rel_path="config/root/mutants-top-level-allowlist.json",
            scope_root_rel="mutants",
            search_roots=[
                "AGENTS.md",
                "CLAUDE.md",
                "tests",
                "README.md",
                "pyproject.toml",
            ],
            scope_label="mutants",
        )
    )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        f"PASS: root cleanliness allowlists match tracked items and current workspace state (mode={args.mode})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
