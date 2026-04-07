#!/usr/bin/env python3
"""Guard current-facing docs against incorrect local hook stage claims."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_README = REPO_ROOT / "tests" / "README.md"
PRE_COMMIT = REPO_ROOT / ".pre-commit-config.yaml"


def main() -> int:
    failures: list[str] = []
    tests_readme = TESTS_README.read_text(encoding="utf-8")
    pre_commit = PRE_COMMIT.read_text(encoding="utf-8")

    expected_truth_lines = (
        "- `pre-push` runs `tooling/scripts/ci/check_commit_authorship_range.sh` to keep new human-visible commit authorship on the configured maintainer identity while still allowing Dependabot as the only bot exception.",
        "- `pre-push` runs `tooling/scripts/ci/check_sensitive_surface_guard.py` to block tracked real local paths, personal identity literals, `.env` files, runtime cache residue, and log artifacts from entering public history.",
        "- `pre-push` runs `tooling/scripts/ci/check_github_security_alerts.py` to fail closed when the live repository still has open GitHub code-scanning or secret-scanning alerts.",
        "- `pre-push` runs `tooling/scripts/ci/check_live_test_static_audit.py` (static policy check only, does not execute live tests).",
        "- `pre-push` runs `tooling/scripts/ci/check_navigation_docs_pair.py` to enforce `AGENTS.md + CLAUDE.md` pair coverage in root and governed modules.",
        "- `pre-push` also runs `tooling/scripts/ci/check_workflow_policy.py` and CI contract tests (`tests/ci/test_required_gate_contract.py`, `tests/ci/test_prepush_policy_contract.py`, `tests/ci/test_artifact_evidence_contract.py`, `tests/ci/test_sensitive_surface_guard.py`) to block workflow-gate regressions before push.",
    )
    for line in expected_truth_lines:
        if line not in tests_readme:
            failures.append(
                f"tests/README.md missing current hook-stage truth line: {line}"
            )

    stale_lines = (
        "- `pre-commit` and `pre-push` both run `tooling/scripts/ci/check_live_test_static_audit.py` (static policy check only, does not execute live tests).",
        "- `pre-commit` and `pre-push` both run `tooling/scripts/ci/check_navigation_docs_pair.py` to enforce `AGENTS.md + CLAUDE.md` pair coverage in root and governed modules.",
        "- `pre-commit` now also runs `tooling/scripts/ci/check_workflow_policy.py` and CI contract tests (`tests/ci/test_required_gate_contract.py`, `tests/ci/test_prepush_policy_contract.py`, `tests/ci/test_artifact_evidence_contract.py`) to block workflow-gate regressions before push.",
    )
    for line in stale_lines:
        if line in tests_readme:
            failures.append(
                f"tests/README.md still contains stale hook-stage line: {line}"
            )

    required_stage_markers = (
        "name: workflow policy guard (pre-push)",
        "name: ci contract tests (pre-push)",
        "name: sensitive surface guard (pre-push)",
        "name: navigation docs guard (pre-push)",
        "name: live static audit (pre-push)",
        "name: local preflight guard (pre-push)",
        "name: commit authorship guard (pre-push range)",
    )
    for marker in required_stage_markers:
        if marker not in pre_commit:
            failures.append(
                f".pre-commit-config.yaml missing expected stage marker: {marker}"
            )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        "PASS: tests/README hook-stage descriptions match the current local hook stages."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
