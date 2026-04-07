#!/usr/bin/env python3
"""Validate the podcasts topology mapping prerequisite for the upstream batch."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    mapping_path = REPO_ROOT / "config/upstream/podcasts-topology-mapping.json"
    if not mapping_path.exists():
        print("FAIL: missing config/upstream/podcasts-topology-mapping.json")
        return 1

    payload = json.loads(mapping_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    if payload.get("upstream_batch") != "podcasts-feature-batch":
        failures.append("podcasts topology mapping must target podcasts-feature-batch")

    mappings = payload.get("mappings")
    if not isinstance(mappings, list) or not mappings:
        failures.append(
            "podcasts topology mapping must contain a non-empty mappings list"
        )
    else:
        for item in mappings:
            if not isinstance(item, dict):
                failures.append("podcasts topology mapping entries must be objects")
                continue
            if not item.get("upstream_path"):
                failures.append("mapping entry missing upstream_path")
            if item.get("status") not in {"mapped", "missing-equivalent"}:
                failures.append(
                    f"mapping entry has invalid status: {item.get('status')!r}"
                )
            current_mapping = item.get("current_mapping")
            if item.get("status") == "mapped":
                if not isinstance(current_mapping, str) or not current_mapping:
                    failures.append(
                        f"mapped entry must provide current_mapping: {item.get('upstream_path')!r}"
                    )
                elif not (REPO_ROOT / current_mapping).exists():
                    failures.append(
                        f"mapped current file does not exist: {current_mapping!r}"
                    )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        "PASS: podcasts topology mapping is present and points to current repo surfaces."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
