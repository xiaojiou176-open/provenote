#!/usr/bin/env python3
"""Validate source processing completion semantics fail closed on lookup issues."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.api.sources_service import SourcesService


def _assert(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


class _StubSourcesService(SourcesService):
    def __init__(self, resolver: Callable[[str], dict[str, Any]]) -> None:
        self._resolver = resolver

    def get_source_status(self, source_id: str) -> dict[str, Any]:
        return self._resolver(source_id)


def _build_status_resolver(status: str | None) -> Callable[[str], dict[str, Any]]:
    def _resolver(_source_id: str) -> dict[str, Any]:
        return {"status": status}

    return _resolver


def main() -> int:
    failures: list[str] = []

    terminal_expectations = {
        "completed": True,
        "failed": True,
        None: True,
        "processing": False,
        "queued": False,
        "unknown": False,
        "error": False,
    }

    for status, expected in terminal_expectations.items():
        service = _StubSourcesService(_build_status_resolver(status))
        observed = service.is_source_processing_complete("source:1")
        _assert(
            observed is expected,
            f"is_source_processing_complete should return {expected} for status={status!r}, got {observed}",
            failures,
        )

    def _raise_lookup_error(_source_id: str) -> dict[str, Any]:
        raise RuntimeError("boom")

    service = _StubSourcesService(_raise_lookup_error)
    _assert(
        service.is_source_processing_complete("source:1") is False,
        "status lookup exceptions must fail closed instead of returning completed",
        failures,
    )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        "PASS: source processing completion semantics fail closed for unknown/error lookup paths."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
