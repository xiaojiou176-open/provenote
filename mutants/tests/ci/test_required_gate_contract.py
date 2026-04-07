from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_WORKFLOW = REPO_ROOT / ".github/workflows/test.yml"
BUILD_RELEASE_WORKFLOW = REPO_ROOT / ".github/workflows/build-and-release.yml"

REQUIRED_GATE_JOB = "required-green-gate"
VERIFY_GATE_JOB = "verify-required-green-gate"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _job_block(workflow_text: str, job_name: str) -> str:
    pattern = re.compile(
        rf"(?ms)^  {re.escape(job_name)}:\n(.*?)(?=^  [^\s][^:]*:\n|\Z)",
    )
    match = pattern.search(workflow_text)
    if match is None:
        raise AssertionError(f"job '{job_name}' not found")
    return match.group(1)


def test_tests_workflow_has_required_green_gate_job() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    assert gate_block.strip() != ""


def test_required_green_gate_includes_cross_browser_smoke() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    assert "e2e-cross-browser-smoke" in gate_block, (
        "required-green-gate must include cross-browser smoke in its required decision set"
    )


def test_required_green_gate_includes_real_backend_smoke() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    assert "e2e-real-backend" in gate_block, (
        "required-green-gate must include real-backend smoke in its required decision set"
    )


def test_required_green_gate_includes_uiux_binding_job() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    assert "uiux-gemini-gate" in gate_block, (
        "required-green-gate must include uiux-gemini-gate in its required decision set"
    )


def test_required_green_gate_includes_external_pr_hosted_jobs() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    assert "external-pr-security-scan" in gate_block, (
        "required-green-gate must include the hosted external PR security scan path"
    )
    assert "external-pr-fast-gate" in gate_block, (
        "required-green-gate must include the hosted external PR fast gate path"
    )


def test_required_green_gate_includes_primary_e2e_suite() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    gate_needs_items = {
        line.strip().removeprefix("-").strip()
        for line in gate_block.splitlines()
        if line.strip().startswith("-")
    }
    assert "e2e" in gate_needs_items, (
        "required-green-gate must include the primary e2e suite as a hard required signal"
    )


def test_e2e_lanes_are_conditionally_required_via_changes_contract() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    for entry in (
        '"e2e": "e2e_chromium"',
        '"e2e-cross-browser-smoke": "e2e_cross_browser"',
        '"e2e-real-backend": "e2e_real_backend"',
    ):
        assert entry in gate_block, (
            f"required-green-gate optional_jobs must include mapping {entry}"
        )

    assert "needs.changes.outputs.e2e_chromium == 'true'" in workflow, (
        "e2e job must be gated by changes.e2e_chromium"
    )
    assert "needs.changes.outputs.e2e_cross_browser == 'true'" in workflow, (
        "e2e-cross-browser-smoke job must be gated by changes.e2e_cross_browser"
    )
    assert "needs.changes.outputs.e2e_real_backend == 'true'" in workflow, (
        "e2e-real-backend job must be gated by changes.e2e_real_backend"
    )


def test_key_e2e_and_gate_jobs_do_not_use_continue_on_error_true() -> None:
    workflow = _read(TEST_WORKFLOW)
    for job_name in (
        "e2e",
        "e2e-cross-browser-smoke",
        "e2e-real-backend",
        REQUIRED_GATE_JOB,
    ):
        block = _job_block(workflow, job_name)
        assert re.search(r"(?m)^\s*continue-on-error:\s*true\b", block) is None, (
            f"{job_name} must not set continue-on-error: true; gate-critical jobs must fail hard"
        )


def test_release_verify_job_references_same_required_gate_name() -> None:
    workflow = _read(BUILD_RELEASE_WORKFLOW)
    verify_block = _job_block(workflow, VERIFY_GATE_JOB)

    required_name_decl = re.search(
        r"const\s+requiredCheckName\s*=\s*[\"']([^\"']+)[\"']\s*;",
        verify_block,
    )
    if required_name_decl is None:
        raise AssertionError("requiredCheckName constant not found in verify job")
    assert required_name_decl.group(1) == "Required Green Gate"


def test_build_jobs_need_verify_required_green_gate() -> None:
    workflow = _read(BUILD_RELEASE_WORKFLOW)

    for build_job in ("build-regular", "build-single"):
        block = _job_block(workflow, build_job)
        has_verify_in_needs = (
            re.search(
                rf"(?m)^\s*needs:\s*\[[^\]]*\b{re.escape(VERIFY_GATE_JOB)}\b", block
            )
            is not None
            or re.search(
                rf"(?ms)^\s*needs:\s*\n(?:\s*-\s*[^\n]+\n)*\s*-\s*{re.escape(VERIFY_GATE_JOB)}\s*$",
                block,
            )
            is not None
        )
        assert has_verify_in_needs, (
            f"build job '{build_job}' must declare '{VERIFY_GATE_JOB}' in needs to keep release gating hard"
        )


def test_consistent_container_runner_script_exists() -> None:
    assert (REPO_ROOT / "tooling/scripts/ci/run_in_consistent_container.sh").exists(), (
        "apps/web CI containerization contract requires tooling/scripts/ci/run_in_consistent_container.sh"
    )


def test_frontend_related_jobs_use_consistent_container_runner() -> None:
    workflow = _read(TEST_WORKFLOW)

    for job_name in (
        "apps-web",
        "e2e",
        "e2e-cross-browser-smoke",
        "e2e-real-backend",
    ):
        block = _job_block(workflow, job_name)
        assert "tooling/scripts/ci/run_in_consistent_container.sh" in block, (
            f"{job_name} must invoke the consistent container runner for apps/web execution"
        )


def test_backend_related_jobs_use_consistent_container_runner() -> None:
    workflow = _read(TEST_WORKFLOW)

    for job_name in (
        "governance-gates",
        "runtime-policy-gates",
        "backend-lint",
        "backend-shard-a",
        "backend-shard-b",
        "property-tests",
        "mutation-python",
        "backend-coverage-merge",
        "coverage-thresholds",
    ):
        block = _job_block(workflow, job_name)
        assert "tooling/scripts/ci/run_in_consistent_container.sh" in block, (
            f"{job_name} must invoke the consistent container runner for repo-owned CI execution"
        )


def test_uiux_workflow_uses_consistent_container_runner() -> None:
    workflow = _read(REPO_ROOT / ".github/workflows/uiux-gemini-gate.yml")
    assert "tooling/scripts/ci/run_in_consistent_container.sh" in workflow, (
        "uiux-gemini-gate must invoke the consistent container runner for apps/web execution"
    )


def test_pre_commit_and_live_workflows_use_consistent_container_runner() -> None:
    for rel_path in (
        ".github/workflows/pre-commit.yml",
        ".github/workflows/live-integration.yml",
        ".github/workflows/jscpd-duplication.yml",
    ):
        workflow = _read(REPO_ROOT / rel_path)
        assert "tooling/scripts/ci/run_in_consistent_container.sh" in workflow, (
            f"{rel_path} must invoke the consistent container runner for repo-owned CI execution"
        )
