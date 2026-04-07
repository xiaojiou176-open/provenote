#!/usr/bin/env python3
"""Validate the legacy provider removal-readiness ledger."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

ALLOWED_READINESS = {"keep", "candidate", "unknown", "removed"}


def main() -> int:
    failures: list[str] = []
    ledger_path = REPO_ROOT / "config/runtime/legacy-provider-removal-ledger.json"

    if not ledger_path.exists():
        print("FAIL: missing config/runtime/legacy-provider-removal-ledger.json")
        return 1

    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        failures.append(
            "legacy-provider-removal-ledger must contain a non-empty entries list"
        )
    else:
        for entry in entries:
            if not isinstance(entry, dict):
                failures.append(
                    "legacy-provider-removal-ledger entries must be objects"
                )
                continue
            for field in (
                "surface",
                "layer",
                "current_usage_signal",
                "removal_readiness",
                "reason",
            ):
                if not entry.get(field):
                    failures.append(
                        f"legacy-provider-removal-ledger entry missing field: {field}"
                    )
            readiness = entry.get("removal_readiness")
            if readiness not in ALLOWED_READINESS:
                failures.append(
                    f"legacy-provider-removal-ledger entry has invalid removal_readiness: {readiness!r}"
                )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: legacy provider removal readiness ledger is well-formed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
