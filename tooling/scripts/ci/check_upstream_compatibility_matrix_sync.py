#!/usr/bin/env python3
"""Validate the structured upstream compatibility matrix against declared external surfaces."""

from __future__ import annotations

import argparse
import json
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
        "--surfaces",
        default="config/upstream/external-surfaces.json",
        help="Path to external surfaces registry",
    )
    parser.add_argument(
        "--matrix",
        default="config/upstream/compatibility-matrix.json",
        help="Path to structured compatibility matrix",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    surfaces = _load_json((repo_root / args.surfaces).resolve()).get("surfaces", [])
    matrix = _load_json((repo_root / args.matrix).resolve()).get("surfaces", [])
    failures: list[str] = []

    indexed_surfaces = {
        item["name"]: item
        for item in surfaces
        if isinstance(item, dict) and item.get("name")
    }
    indexed_matrix = {
        item["name"]: item
        for item in matrix
        if isinstance(item, dict) and item.get("name")
    }

    for name, item in indexed_surfaces.items():
        if name not in indexed_matrix:
            failures.append(f"compatibility matrix missing external surface: {name}")
            continue
        matrix_item = indexed_matrix[name]
        for field in (
            "supported_pin",
            "verification_lane",
            "blocking_lane",
            "rollback_action",
            "owner",
            "incompatibility_semantics",
        ):
            if not str(matrix_item.get(field, "")).strip():
                failures.append(
                    f"compatibility matrix surface {name} missing field {field}"
                )
        if (
            str(item.get("verification_lane", "")).strip()
            != str(matrix_item.get("verification_lane", "")).strip()
        ):
            failures.append(
                f"compatibility matrix verification lane drift for {name}: registry={item.get('verification_lane')} matrix={matrix_item.get('verification_lane')}"
            )
        if (
            str(item.get("owner", "")).strip()
            != str(matrix_item.get("owner", "")).strip()
        ):
            failures.append(
                f"compatibility matrix owner drift for {name}: registry={item.get('owner')} matrix={matrix_item.get('owner')}"
            )

    for name in indexed_matrix:
        if name not in indexed_surfaces:
            failures.append(
                f"compatibility matrix references unknown external surface: {name}"
            )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        "PASS: structured upstream compatibility matrix matches declared external surfaces."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
