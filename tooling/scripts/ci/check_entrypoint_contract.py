#!/usr/bin/env python3
"""Enforce official Python entrypoint usage against the managed uv wrapper contract."""

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
        "--contract",
        default="config/runtime/entrypoint-contract.json",
        help="Path to the entrypoint contract JSON file",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    contract_path = (repo_root / args.contract).resolve()
    contract = _load_json(contract_path)

    wrapper = str(contract.get("managed_wrapper", "")).strip()
    scan_roots = contract.get("authoritative_scan_roots", [])
    forbidden_patterns = contract.get("forbidden_patterns", [])
    failures: list[str] = []

    if not wrapper:
        failures.append("entrypoint contract missing managed_wrapper")
    if not isinstance(scan_roots, list) or not scan_roots:
        failures.append(
            "entrypoint contract authoritative_scan_roots must be a non-empty list"
        )
        scan_roots = []
    if not isinstance(forbidden_patterns, list) or not forbidden_patterns:
        failures.append(
            "entrypoint contract forbidden_patterns must be a non-empty list"
        )
        forbidden_patterns = []

    for rel_path in scan_roots:
        if not isinstance(rel_path, str) or not rel_path.strip():
            failures.append(f"invalid authoritative scan path: {rel_path!r}")
            continue
        file_path = (repo_root / rel_path).resolve()
        if not file_path.is_file():
            failures.append(f"authoritative entrypoint file missing: {rel_path}")
            continue
        text = file_path.read_text(encoding="utf-8")
        if rel_path == str(Path(wrapper)):
            continue
        for pattern in forbidden_patterns:
            regex = re.compile(pattern)
            for match in regex.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                snippet = text.splitlines()[line_no - 1].strip()
                failures.append(
                    f"{rel_path}:{line_no}: forbidden bare uv entrypoint usage -> {snippet}"
                )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        f"PASS: official entrypoints route Python commands through the managed wrapper ({wrapper})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
