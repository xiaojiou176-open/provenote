from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_WORKFLOW = REPO_ROOT / ".github/workflows/test.yml"
BUILD_RELEASE_WORKFLOW = REPO_ROOT / ".github/workflows/build-and-release.yml"
AUDITABLE_QUALITY_GATE_WORKFLOW = (
    REPO_ROOT / ".github/workflows/auditable-quality-gate.yml"
)

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


def test_runner_health_workflow_is_removed_from_current_hosted_first_contract() -> None:
    assert not (REPO_ROOT / ".github/workflows/runner-health.yml").exists(), (
        "Hosted-first CI should not keep a dedicated runner-health workflow"
    )


def test_tests_workflow_no_longer_contains_runner_bootstrap_job() -> None:
    workflow = _read(TEST_WORKFLOW)
    assert re.search(r"(?m)^  runner-bootstrap:\n", workflow) is None


def test_required_ci_env_job_keeps_pull_request_path_secretless() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, "required-ci-env")
    assert "github.event_name == 'pull_request'" in gate_block
    assert "github.event_name != 'pull_request'" in gate_block
    assert (
        "required CI secrets stay sealed and the PR continues on the hosted-safe path"
        in gate_block
    )


def test_auditable_quality_gate_sensitive_jobs_use_protected_environment() -> None:
    workflow = _read(AUDITABLE_QUALITY_GATE_WORKFLOW)
    for job_name in ("required-ci-env", "promptfoo-eval", "ragas-eval"):
        block = _job_block(workflow, job_name)
        assert "environment: owner-approved-sensitive" in block, (
            f"{job_name} must require the protected sensitive environment"
        )


def test_required_green_gate_excludes_cross_browser_smoke() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    assert "e2e-cross-browser-smoke" not in gate_block, (
        "required-green-gate must keep cross-browser smoke outside the deterministic required decision set"
    )


def test_required_green_gate_excludes_real_backend_smoke() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    assert "e2e-real-backend" not in gate_block, (
        "required-green-gate must keep real-backend smoke outside the deterministic required decision set"
    )


def test_required_green_gate_excludes_uiux_binding_job() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    assert "uiux-gemini-gate" not in gate_block, (
        "required-green-gate must not include uiux-gemini-gate in its deterministic required decision set"
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


def test_dependabot_prs_route_through_external_pr_gate_path() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    assert "github.actor == 'dependabot[bot]'" in gate_block, (
        "required-green-gate must classify Dependabot PRs as hosted-safe external-style PRs"
    )

    external_security = _job_block(workflow, "external-pr-security-scan")
    external_fast = _job_block(workflow, "external-pr-fast-gate")
    for block in (external_security, external_fast):
        assert "github.actor == 'dependabot[bot]'" in block, (
            "hosted external PR jobs must explicitly include Dependabot PR routing"
        )


def test_external_pr_fast_gate_keeps_networked_uv_resolution_enabled() -> None:
    workflow = _read(TEST_WORKFLOW)
    external_fast = _job_block(workflow, "external-pr-fast-gate")
    assert 'UV_OFFLINE: "0"' in external_fast, (
        "hosted external PR fast gate must disable UV offline mode so hosted-safe runners can resolve uncached packages"
    )


def test_external_pr_fast_gate_marks_external_commit_governance_context() -> None:
    workflow = _read(TEST_WORKFLOW)
    external_fast = _job_block(workflow, "external-pr-fast-gate")
    assert 'OPEN_NOTEBOOK_EXTERNAL_PR_FAST_GATE: "1"' in external_fast, (
        "hosted external PR fast gate must explicitly mark the external commit-governance context so empty maintenance ranges do not inherit trusted-lane failures"
    )


def test_secret_backed_pr_jobs_exclude_dependabot_actor() -> None:
    workflow = _read(TEST_WORKFLOW)
    required_ci_env_block = _job_block(workflow, "required-ci-env")
    assert "github.event_name != 'pull_request'" in required_ci_env_block, (
        "required-ci-env must keep all pull_request events on the hosted-safe secretless path"
    )

    for job_name in (
        "changes",
        "security-scan",
        "governance-gates",
        "runtime-policy-gates",
        "backend-lint",
        "apps-web-lint",
    ):
        block = _job_block(workflow, job_name)
        assert "github.actor != 'dependabot[bot]'" in block, (
            f"{job_name} must keep Dependabot PRs out of secret-backed trusted lanes"
        )


def test_required_green_gate_excludes_primary_e2e_suite() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    gate_needs_items = {
        line.strip().removeprefix("-").strip()
        for line in gate_block.splitlines()
        if line.strip().startswith("-")
    }
    assert "e2e" not in gate_needs_items, (
        "required-green-gate must keep the primary e2e suite outside the hard required signal set"
    )


def test_advisory_heavy_lanes_are_manual_only_and_not_required() -> None:
    workflow = _read(TEST_WORKFLOW)
    gate_block = _job_block(workflow, REQUIRED_GATE_JOB)
    for entry in ('"mutation-python": "mutation_python"',):
        assert entry not in gate_block, (
            f"required-green-gate must not treat advisory heavy lane {entry} as a required mapping"
        )

    for job_name in (
        "mutation-python",
        "e2e",
        "e2e-cross-browser-smoke",
        "e2e-real-backend",
    ):
        block = _job_block(workflow, job_name)
        assert "github.event_name == 'workflow_dispatch'" in block, (
            f"{job_name} must be manual-only instead of blocking the default push gate"
        )


def test_uiux_binding_and_perf_jobs_are_manual_only() -> None:
    workflow = _read(TEST_WORKFLOW)

    perf_block = _job_block(workflow, "performance-benchmarks")
    assert "github.event_name == 'workflow_dispatch'" in perf_block, (
        "performance-benchmarks must be manual-only because it depends on heavier runner/docker setup"
    )
    assert "github.ref == 'refs/heads/main'" in perf_block, (
        "performance-benchmarks must stay on the trusted main branch when manually dispatched"
    )

    uiux_workflow = _read(REPO_ROOT / ".github/workflows/uiux-gemini-gate.yml")
    assert "workflow_dispatch:" in uiux_workflow
    assert "pull_request:" not in uiux_workflow
    assert "push:" not in uiux_workflow
    assert "github.ref == 'refs/heads/main'" in uiux_workflow


def test_auditable_quality_gate_is_manual_only_on_main() -> None:
    workflow = _read(REPO_ROOT / ".github/workflows/auditable-quality-gate.yml")

    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
    assert "push:" not in workflow

    for job_name in ("required-ci-env", "promptfoo-eval", "ragas-eval"):
        block = _job_block(workflow, job_name)
        assert "github.event_name == 'workflow_dispatch'" in block, (
            f"{job_name} must stay manual-only in the auditable-quality-gate workflow"
        )
        assert "github.ref == 'refs/heads/main'" in block, (
            f"{job_name} must stay pinned to main when manually dispatched"
        )


def test_auditable_promptfoo_job_uses_repo_local_binary() -> None:
    workflow = _read(REPO_ROOT / ".github/workflows/auditable-quality-gate.yml")
    promptfoo_block = _job_block(workflow, "promptfoo-eval")
    assert "./node_modules/.bin/promptfoo --version" in promptfoo_block
    assert "./node_modules/.bin/promptfoo eval" in promptfoo_block
    assert "npx --no-install promptfoo" not in promptfoo_block


def test_frontend_tests_wait_for_frontend_lint_to_reduce_bootstrap_pressure() -> None:
    workflow = _read(TEST_WORKFLOW)
    apps_web_block = _job_block(workflow, "apps-web")
    assert "needs: [required-ci-env, apps-web-lint]" in apps_web_block


def test_frontend_non_e2e_jobs_use_static_frontend_bootstrap_profile() -> None:
    workflow = _read(TEST_WORKFLOW)
    lint_block = _job_block(workflow, "apps-web-lint")
    apps_web_block = _job_block(workflow, "apps-web")

    assert "--profile apps/web-static" in lint_block, (
        "apps-web-lint must use the static frontend bootstrap profile so lint-only checks do not bootstrap Playwright browser bundles on every run"
    )
    assert apps_web_block.count("--profile apps/web-static") == 3, (
        "apps-web must use the static frontend bootstrap profile for coverage, build, and bundle-size checks so non-E2E frontend lanes do not churn Playwright browser caches"
    )


def test_frontend_coverage_artifact_upload_includes_hidden_runtime_cache() -> None:
    workflow = _read(TEST_WORKFLOW)
    apps_web_block = _job_block(workflow, "apps-web")
    assert "name: apps-web-coverage-lcov" in apps_web_block
    assert "path: .runtime-cache/test/coverage/apps/web/lcov.info" in apps_web_block
    assert "include-hidden-files: true" in apps_web_block, (
        "apps-web coverage upload must include hidden runtime-cache files so lcov artifacts under .runtime-cache are not silently dropped by upload-artifact"
    )


def test_coverage_thresholds_download_backend_xml_into_runtime_cache_path() -> None:
    workflow = _read(TEST_WORKFLOW)
    block = _job_block(workflow, "coverage-thresholds")
    assert "name: backend-coverage-xml" in block
    assert "path: .runtime-cache/test/coverage/backend" in block, (
        "coverage-thresholds must download backend coverage.xml into the runtime-cache backend directory so check_coverage_thresholds.py can find .runtime-cache/test/coverage/backend/coverage.xml"
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
