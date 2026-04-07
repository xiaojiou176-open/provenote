from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DOC = REPO_ROOT / ".github/repo-settings/required-checks.snapshot.md"
TEST_WORKFLOW = REPO_ROOT / ".github/workflows/test.yml"
SCRIPT_PATH = REPO_ROOT / "tooling/scripts/ci/check_public_ci_boundary.py"

SPEC = importlib.util.spec_from_file_location("check_public_ci_boundary", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
BOUNDARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOUNDARY)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_required_checks_snapshot_declares_boundary_sections() -> None:
    snapshot = _read(SNAPSHOT_DOC)

    for needle in (
        "# Required Checks Snapshot",
        "## Maintainer-Only Trusted Lanes",
        "## Public Contributor Lanes",
        "## Verification Boundary",
        "This file is a repo snapshot/expectation only.",
    ):
        assert needle in snapshot


def test_required_checks_snapshot_lists_expected_checks() -> None:
    snapshot = _read(SNAPSHOT_DOC)

    for needle in (
        "Required Green Gate",
        "UIUX Gemini Gate",
        "external-pr-security-scan",
        "external-pr-fast-gate",
    ):
        assert needle in snapshot


def test_public_ci_boundary_check_is_wired_into_tests_workflow() -> None:
    workflow = _read(TEST_WORKFLOW)

    assert "check_public_ci_boundary.py" in workflow


def test_public_ci_boundary_script_passes_against_repo_contract() -> None:
    assert BOUNDARY.main() == 0
