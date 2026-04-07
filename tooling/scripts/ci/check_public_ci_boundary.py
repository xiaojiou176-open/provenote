#!/usr/bin/env python3
"""Validate the repo-owned trusted/public CI boundary contract."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
UIUX_WORKFLOW = REPO_ROOT / ".github/workflows/uiux-gemini-gate.yml"
TEST_WORKFLOW = REPO_ROOT / ".github/workflows/test.yml"
BUILD_RELEASE_WORKFLOW = REPO_ROOT / ".github/workflows/build-and-release.yml"
SNAPSHOT_DOC = REPO_ROOT / ".github/repo-settings/required-checks.snapshot.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require_contains(
    failures: list[str], *, text: str, needle: str, label: str
) -> None:
    if needle not in text:
        failures.append(f"{label} missing expected text: {needle}")


def main() -> int:
    failures: list[str] = []

    uiux_workflow = _read(UIUX_WORKFLOW)
    test_workflow = _read(TEST_WORKFLOW)
    build_release_workflow = _read(BUILD_RELEASE_WORKFLOW)
    snapshot_doc = _read(SNAPSHOT_DOC)
    _require_contains(
        failures,
        text=uiux_workflow,
        needle="workflow_dispatch:",
        label=UIUX_WORKFLOW.as_posix(),
    )
    _require_contains(
        failures,
        text=uiux_workflow,
        needle="manual maintainer-only witness lane",
        label=UIUX_WORKFLOW.as_posix(),
    )
    _require_contains(
        failures,
        text=uiux_workflow,
        needle="github.ref == 'refs/heads/main'",
        label=UIUX_WORKFLOW.as_posix(),
    )
    if "pull_request:" in uiux_workflow or "push:" in uiux_workflow:
        failures.append(
            f"{UIUX_WORKFLOW.as_posix()} must remain manual-only; push/pull_request triggers are intentionally disabled"
        )
    if "--allow-deterministic-fallback" in uiux_workflow:
        failures.append(
            f"{UIUX_WORKFLOW.as_posix()} must not opt into --allow-deterministic-fallback"
        )
    if "--allow-legacy-auto-generate" in uiux_workflow:
        failures.append(
            f"{UIUX_WORKFLOW.as_posix()} must not opt into --allow-legacy-auto-generate"
        )

    _require_contains(
        failures,
        text=test_workflow,
        needle="external-pr-security-scan",
        label=TEST_WORKFLOW.as_posix(),
    )
    _require_contains(
        failures,
        text=test_workflow,
        needle="external-pr-fast-gate",
        label=TEST_WORKFLOW.as_posix(),
    )
    _require_contains(
        failures,
        text=test_workflow,
        needle="check_public_ci_boundary.py",
        label=TEST_WORKFLOW.as_posix(),
    )

    _require_contains(
        failures,
        text=build_release_workflow,
        needle='const trustedBranches = new Set(["main"]);',
        label=BUILD_RELEASE_WORKFLOW.as_posix(),
    )
    _require_contains(
        failures,
        text=build_release_workflow,
        needle='const requiredCheckName = "Required Green Gate";',
        label=BUILD_RELEASE_WORKFLOW.as_posix(),
    )
    _require_contains(
        failures,
        text=build_release_workflow,
        needle="const requiredNames = new Set([requiredCheckName]);",
        label=BUILD_RELEASE_WORKFLOW.as_posix(),
    )
    _require_contains(
        failures,
        text=build_release_workflow,
        needle='workflowPath.startsWith(".github/workflows/test.yml")',
        label=BUILD_RELEASE_WORKFLOW.as_posix(),
    )

    for needle in (
        "# Required Checks Snapshot",
        "## Maintainer-Only Trusted Lanes",
        "## Public Contributor Lanes",
        "## Verification Boundary",
        "Required Green Gate",
        "UIUX Gemini Gate",
        "Performance Benchmarks",
        "external-pr-security-scan",
        "external-pr-fast-gate",
        "manual-only trusted witness lane",
        "This file is a repo snapshot/expectation only.",
    ):
        _require_contains(
            failures,
            text=snapshot_doc,
            needle=needle,
            label=SNAPSHOT_DOC.as_posix(),
        )

    if failures:
        print(
            "FAIL [CI-BOUNDARY-001]: trusted/public CI boundary contract drift detected."
        )
        for item in failures:
            print(f"- {item}")
        return 1

    print(
        "PASS [CI-BOUNDARY-001]: trusted/public CI boundary contract is explicit and in sync."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
