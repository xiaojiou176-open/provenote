#!/usr/bin/env python3
"""Fail closed on floating external inputs in active entrypoints."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy",
        default="config/upstream/floating-input-policy.json",
        help="Path to the floating input policy JSON file",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    policy = _load_json((repo_root / args.policy).resolve())

    scan_roots = policy.get("scan_roots", [])
    patterns = policy.get("forbidden_patterns", [])
    failures: list[str] = []

    if not isinstance(scan_roots, list) or not scan_roots:
        failures.append("scan_roots must be a non-empty list")
        scan_roots = []
    if not isinstance(patterns, list) or not patterns:
        failures.append("forbidden_patterns must be a non-empty list")
        patterns = []

    for rel_path in scan_roots:
        target = repo_root / rel_path
        if not target.is_file():
            failures.append(f"floating-input policy target missing: {rel_path}")
            continue
        text = target.read_text(encoding="utf-8")
        for pattern in patterns:
            regex = re.compile(pattern)
            for match in regex.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                snippet = text.splitlines()[line_no - 1].strip()
                failures.append(
                    f"{rel_path}:{line_no}: floating external input forbidden -> {snippet}"
                )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: active entrypoints are free of floating external inputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
