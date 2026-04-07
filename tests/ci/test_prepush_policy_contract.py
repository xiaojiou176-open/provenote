from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TRUSTED_PR_GUARD = (
    "github.event_name != 'pull_request' || "
    "(github.event.pull_request.head.repo.full_name == github.repository && github.actor != 'dependabot[bot]')"
)


def _load_pre_commit_config() -> dict:
    config_text = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(config_text)
    assert isinstance(data, dict)
    return data


def _find_local_hook(hook_id: str) -> dict:
    config = _load_pre_commit_config()
    repos = config.get("repos", [])
    assert isinstance(repos, list)
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        if repo.get("repo") != "local":
            continue
        hooks = repo.get("hooks", [])
        if not isinstance(hooks, list):
            continue
        for hook in hooks:
            if isinstance(hook, dict) and hook.get("id") == hook_id:
                return hook
    raise AssertionError(f"hook '{hook_id}' not found in local pre-commit repo")


def test_pre_push_hook_uses_fast_local_preflight_mode() -> None:
    hook = _find_local_hook("local-preflight-pre-push")
    assert (
        hook.get("entry")
        == "env OPEN_NOTEBOOK_PREPUSH_HOOK_CONTEXT=1 bash tooling/scripts/ci/local_preflight_before_push.sh --mode fast"
    )
    assert hook.get("pass_filenames") is False
    stages = hook.get("stages", [])
    assert isinstance(stages, list)
    assert stages == ["pre-push"]


def test_commit_authorship_hook_is_scoped_to_pre_push() -> None:
    hook = _find_local_hook("commit-authorship-range-pre-push")
    assert (
        hook.get("entry") == "bash tooling/scripts/ci/check_commit_authorship_range.sh"
    )
    assert hook.get("pass_filenames") is False
    stages = hook.get("stages", [])
    assert isinstance(stages, list)
    assert stages == ["pre-push"]


def test_sensitive_surface_hook_is_scoped_to_pre_push() -> None:
    hook = _find_local_hook("sensitive-surface-pre-push")
    assert (
        hook.get("entry")
        == "bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_sensitive_surface_guard.py"
    )
    assert hook.get("pass_filenames") is False
    stages = hook.get("stages", [])
    assert isinstance(stages, list)
    assert stages == ["pre-push"]


def test_github_security_alerts_hook_is_scoped_to_pre_push() -> None:
    hook = _find_local_hook("github-security-alerts-pre-push")
    assert (
        hook.get("entry")
        == "bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_github_security_alerts.py"
    )
    assert hook.get("pass_filenames") is False
    stages = hook.get("stages", [])
    assert isinstance(stages, list)
    assert stages == ["pre-push"]


def test_no_commit_to_branch_is_scoped_to_pre_commit_only() -> None:
    config = _load_pre_commit_config()
    repos = config.get("repos", [])
    assert isinstance(repos, list)

    no_commit_hook = None
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        if repo.get("repo") != "https://github.com/pre-commit/pre-commit-hooks":
            continue
        hooks = repo.get("hooks", [])
        if not isinstance(hooks, list):
            continue
        for hook in hooks:
            if isinstance(hook, dict) and hook.get("id") == "no-commit-to-branch":
                no_commit_hook = hook
                break

    assert isinstance(no_commit_hook, dict), (
        "no-commit-to-branch hook must remain configured"
    )
    assert no_commit_hook.get("stages") == ["pre-commit"]


def test_local_preflight_defaults_to_fast_mode() -> None:
    script_text = (
        REPO_ROOT / "tooling/scripts/ci/local_preflight_before_push.sh"
    ).read_text(encoding="utf-8")
    assert re.search(r'^\s*MODE="fast"\s*$', script_text, flags=re.MULTILINE)


def test_local_preflight_fast_mode_uses_repo_fast_container_profile() -> None:
    script_text = (
        REPO_ROOT / "tooling/scripts/ci/local_preflight_before_push.sh"
    ).read_text(encoding="utf-8")
    assert 'CONTAINER_PROFILE="repo-fast"' in script_text
    assert '--profile "${CONTAINER_PROFILE}"' in script_text


def test_make_ci_local_preflight_defaults_to_fast_mode() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert (
        "bash tooling/scripts/ci/local_preflight_before_push.sh --mode $${LOCAL_PREFLIGHT_MODE:-fast}"
        in makefile
    )


def test_unified_test_gate_fast_mode_uses_repo_fast_container_profile() -> None:
    script_text = (
        REPO_ROOT / "tooling/scripts/ci/run_unified_test_gate.sh"
    ).read_text(encoding="utf-8")
    assert 'CONTAINER_PROFILE="repo-fast"' in script_text
    assert 'if [[ "${MODE}" == "fast" ]]; then' in script_text


def test_unified_test_gate_can_skip_duplicate_prepush_guards_for_hook_context() -> None:
    script_text = (
        REPO_ROOT / "tooling/scripts/ci/run_unified_test_gate.sh"
    ).read_text(encoding="utf-8")
    assert 'OPEN_NOTEBOOK_PREPUSH_HOOK_CONTEXT="${OPEN_NOTEBOOK_PREPUSH_HOOK_CONTEXT:-0}"' in script_text
    assert "skip duplicated dedicated pre-push guards before fast smoke" in script_text


def test_unified_test_gate_runs_navigation_docs_guard_as_single_step() -> None:
    script_text = (
        REPO_ROOT / "tooling/scripts/ci/run_unified_test_gate.sh"
    ).read_text(encoding="utf-8")
    assert (
        'run_step "navigation-docs-pair-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py'
        in script_text
    )


def test_workflow_policy_guard_passes_for_current_repo() -> None:
    required_contract_files = (
        REPO_ROOT / "evals" / "promptfoo" / "package.json",
        REPO_ROOT / "evals" / "promptfoo" / "package-lock.json",
        REPO_ROOT / "evals" / "promptfoo" / "promptfooconfig.yaml",
    )
    untracked_contract_files: list[Path] = []
    for path in required_contract_files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", rel],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if tracked.returncode != 0:
            untracked_contract_files.append(path)

    completed = subprocess.run(
        [sys.executable, "tooling/scripts/ci/check_workflow_policy.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    violations = []
    if not untracked_contract_files:
        if completed.returncode != 0:
            violations.append(completed.stdout + "\n" + completed.stderr)
    else:
        if completed.returncode != 1:
            violations.append(completed.stdout + "\n" + completed.stderr)
        for path in untracked_contract_files:
            if (
                f"{path}: required promptfoo eval contract file is not tracked by git"
                not in completed.stdout
            ):
                violations.append(f"Missing expected path in stdout: {path}")
    assert not violations, violations


def test_pre_commit_and_jscpd_workflows_skip_secret_gate_for_dependabot() -> None:
    for workflow_name in ("pre-commit.yml", "jscpd-duplication.yml"):
        workflow = (REPO_ROOT / ".github" / "workflows" / workflow_name).read_text(
            encoding="utf-8"
        )
        assert "GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}" not in workflow
        assert (
            "OPEN_NOTEBOOK_ENCRYPTION_KEY: ${{ secrets.OPEN_NOTEBOOK_ENCRYPTION_KEY }}"
            not in workflow
        )
        assert "check_required_ci_env.sh" not in workflow, (
            f"{workflow_name} must stay secretless so all pull_request traffic remains on the hosted-safe path"
        )


def _load_workflow_policy_module():
    module_path = REPO_ROOT / "tooling/scripts/ci/check_workflow_policy.py"
    spec = importlib.util.spec_from_file_location("check_workflow_policy", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_workflow_policy_iter_job_blocks_accepts_slash_job_ids() -> None:
    policy = _load_workflow_policy_module()
    jobs = policy._iter_job_blocks(
        """
name: Slash jobs
jobs:
  apps/web-lint:
    runs-on: ubuntu-latest
  apps/web:
    runs-on: ubuntu-latest
"""
    )

    assert [job_name for _, job_name, _ in jobs] == ["apps/web-lint", "apps/web"]


def test_workflow_policy_rejects_job_level_continue_on_error_true_in_critical_workflow() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Poisoned
jobs:
  poisoned:
    continue-on-error: true
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any(
        "job-level continue-on-error: true is forbidden" in item for item in failures
    )


def test_workflow_policy_rejects_upload_artifact_without_explicit_if_no_files_found() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Poisoned
jobs:
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: Upload report without strictness
        uses: actions/upload-artifact@v4
        with:
          name: report
          path: artifacts/report
""",
    )
    assert any("missing explicit if-no-files-found policy" in item for item in failures)


def test_workflow_policy_rejects_upload_artifact_warn_mode_in_critical_workflow() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Poisoned
jobs:
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: Upload report with warn mode
        uses: actions/upload-artifact@v4
        with:
          name: report
          path: artifacts/report
          if-no-files-found: warn
""",
    )
    assert any("must use if-no-files-found: error" in item for item in failures)


def test_workflow_policy_rejects_host_runtime_bootstrap_in_mainline_workflow() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/pre-commit.yml"),
        """
name: Pre-commit
jobs:
  pre-commit:
    runs-on: [self-hosted, shared-pool]
    steps:
      - uses: actions/checkout@1111111111111111111111111111111111111111
      - uses: actions/setup-node@2222222222222222222222222222222222222222
      - run: echo poisoned
""",
    )
    assert any(
        "must not use host runtime bootstrap token 'actions/setup-node@'" in item
        for item in failures
    )


def test_workflow_policy_requires_container_runner_in_mainline_workflow() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/live-integration.yml"),
        """
name: Live Integration
jobs:
  live-llm-gemini:
    runs-on: [self-hosted, shared-pool]
    steps:
      - uses: actions/checkout@1111111111111111111111111111111111111111
      - run: echo poisoned
""",
    )
    assert any(
        "must invoke tooling/scripts/ci/run_in_consistent_container.sh" in item
        for item in failures
    )


def test_workflow_policy_requires_uiux_auto_remediation_source_constraints() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/uiux-auto-remediation.yml"),
        """
name: UIUX Auto Remediation
on:
  workflow_run:
    workflows: ["UIUX Gemini Gate"]
    types: [completed]
jobs:
  open-remediation-issue:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any(
        "missing workflow_run source constraint 'github.event.workflow_run.event == 'push''"
        in item
        for item in failures
    )
    assert any(
        "missing workflow_run source constraint 'github.event.workflow_run.head_branch == 'main''"
        in item
        for item in failures
    )


def test_workflow_policy_rejects_commented_workflow_run_source_constraints() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/uiux-auto-remediation.yml"),
        """
name: UIUX Auto Remediation
on:
  workflow_run:
    workflows: ["UIUX Gemini Gate"]
    types: [completed]
jobs:
  open-remediation-issue:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    # github.event.workflow_run.event == 'push'
    # github.event.workflow_run.head_branch == 'main'
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any(
        "missing workflow_run source constraint 'github.event.workflow_run.event == 'push''"
        in item
        for item in failures
    )
    assert any(
        "missing workflow_run source constraint 'github.event.workflow_run.head_branch == 'main''"
        in item
        for item in failures
    )


def test_workflow_policy_requires_build_dev_workflow_run_source_constraints() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/build-dev.yml"),
        """
name: Development Build
on:
  workflow_run:
    workflows: [Tests]
    types: [completed]
jobs:
  extract-version:
    if: ${{ github.event_name != 'workflow_run' || (github.event.workflow_run.conclusion == 'success' && github.event.workflow_run.head_branch == 'main') }}
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any(
        "missing workflow_run source constraint 'github.event.workflow_run.event == 'push''"
        in item
        for item in failures
    )
    assert any(
        "missing workflow_run source constraint 'github.event.workflow_run.head_repository.full_name == github.repository'"
        in item
        for item in failures
    )


def test_workflow_policy_rejects_commented_build_dev_workflow_run_source_constraints() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/build-dev.yml"),
        """
name: Development Build
on:
  workflow_run:
    workflows: [Tests]
    types: [completed]
jobs:
  extract-version:
    if: ${{ github.event_name != 'workflow_run' || (github.event.workflow_run.conclusion == 'success' && github.event.workflow_run.head_branch == 'main') }}
    # github.event.workflow_run.event == 'push'
    # github.event.workflow_run.head_repository.full_name == github.repository
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any(
        "missing workflow_run source constraint 'github.event.workflow_run.event == 'push''"
        in item
        for item in failures
    )
    assert any(
        "missing workflow_run source constraint 'github.event.workflow_run.head_repository.full_name == github.repository'"
        in item
        for item in failures
    )


def test_workflow_policy_rejects_build_dev_unexpected_workflow_run_upstream_sources() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/build-dev.yml"),
        """
name: Development Build
on:
  workflow_run:
    workflows: [Tests, Poisoned]
    types: [completed]
permissions:
  contents: read
jobs:
  extract-version:
    if: ${{ github.event.workflow_run.event == 'push' && github.event.workflow_run.head_branch == 'main' && github.event.workflow_run.head_repository.full_name == github.repository }}
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-regular:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-single:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  summary:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
""",
    )
    assert any(
        "workflow_run workflows allowlist must be exactly" in item for item in failures
    )


def test_workflow_policy_rejects_build_dev_top_level_packages_scope() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/build-dev.yml"),
        """
name: Development Build
on:
  workflow_run:
    workflows: [Tests]
    types: [completed]
permissions:
  contents: read
  packages: write
jobs:
  extract-version:
    if: ${{ github.event.workflow_run.event == 'push' && github.event.workflow_run.head_branch == 'main' && github.event.workflow_run.head_repository.full_name == github.repository }}
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-regular:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-single:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  summary:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
""",
    )
    assert any(
        "top-level permissions must not request packages scope" in item
        for item in failures
    )


def test_workflow_policy_rejects_build_dev_publish_job_without_packages_write() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/build-dev.yml"),
        """
name: Development Build
on:
  workflow_run:
    workflows: [Tests]
    types: [completed]
permissions:
  contents: read
jobs:
  extract-version:
    if: ${{ github.event.workflow_run.event == 'push' && github.event.workflow_run.head_branch == 'main' && github.event.workflow_run.head_repository.full_name == github.repository }}
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-regular:
    permissions:
      contents: read
      packages: read
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-single:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  summary:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
""",
    )
    assert any(
        "job 'build-regular' must set permissions.packages to 'write'" in item
        for item in failures
    )


def test_workflow_policy_rejects_build_release_top_level_packages_scope() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/build-and-release.yml"),
        """
name: Build and Release
permissions:
  contents: read
  packages: write
jobs:
  verify-required-green-gate:
    permissions:
      checks: read
    runs-on: ubuntu-latest
    steps:
      - name: Validate required-green-gate on same SHA
        uses: actions/github-script@f28e40c7f34bde8b3046d885e986cb6290c5673b
        with:
          script: |
            const sha = context.sha;
            const trustedBranches = new Set(["main"]);
            if (context.eventName === "workflow_dispatch" && context.ref !== "refs/heads/main") {
              return;
            }
            if (context.eventName === "release") {
              const targetCommitish = String(context.payload.release?.target_commitish || "").trim();
              if (!trustedBranches.has(targetCommitish)) {
                return;
              }
            }
            await github.rest.repos.compareCommitsWithBasehead({
              owner: context.repo.owner,
              repo: context.repo.repo,
              basehead: `${sha}...main`,
            });
            for (const run of []) {
              if (run.app?.slug !== "github-actions") {
                continue;
              }
              const { data: workflowRun } = await github.rest.actions.getWorkflowRun({
                owner: context.repo.owner,
                repo: context.repo.repo,
                run_id: 1,
              });
              const workflowPath = String(workflowRun.path || "");
              if (workflowPath.startsWith(".github/workflows/test.yml") && workflowRun.head_sha === sha) {
                break;
              }
            }
  extract-version:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-regular:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-single:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  summary:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
""",
    )
    assert any(
        "build-and-release workflow top-level permissions must not request packages scope"
        in item
        for item in failures
    )


def test_workflow_policy_rejects_build_release_publish_job_without_packages_write() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/build-and-release.yml"),
        """
name: Build and Release
permissions:
  contents: read
jobs:
  verify-required-green-gate:
    permissions:
      checks: read
    runs-on: ubuntu-latest
    steps:
      - name: Validate required-green-gate on same SHA
        uses: actions/github-script@f28e40c7f34bde8b3046d885e986cb6290c5673b
        with:
          script: |
            const sha = context.sha;
            const trustedBranches = new Set(["main"]);
            if (context.eventName === "workflow_dispatch" && context.ref !== "refs/heads/main") {
              return;
            }
            if (context.eventName === "release") {
              const targetCommitish = String(context.payload.release?.target_commitish || "").trim();
              if (!trustedBranches.has(targetCommitish)) {
                return;
              }
            }
            await github.rest.repos.compareCommitsWithBasehead({
              owner: context.repo.owner,
              repo: context.repo.repo,
              basehead: `${sha}...main`,
            });
            for (const run of []) {
              if (run.app?.slug !== "github-actions") {
                continue;
              }
              const { data: workflowRun } = await github.rest.actions.getWorkflowRun({
                owner: context.repo.owner,
                repo: context.repo.repo,
                run_id: 1,
              });
              const workflowPath = String(workflowRun.path || "");
              if (workflowPath.startsWith(".github/workflows/test.yml") && workflowRun.head_sha === sha) {
                break;
              }
            }
  extract-version:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-regular:
    permissions:
      contents: read
      packages: read
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-single:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  summary:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
""",
    )
    assert any(
        "job 'build-regular' must set permissions.packages to 'write'" in item
        for item in failures
    )


def test_workflow_policy_requires_build_release_gate_source_and_identity_tokens() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/build-and-release.yml"),
        """
name: Build and Release
permissions:
  contents: read
jobs:
  verify-required-green-gate:
    permissions:
      checks: read
    runs-on: ubuntu-latest
    steps:
      - name: Validate required-green-gate on same SHA
        uses: actions/github-script@f28e40c7f34bde8b3046d885e986cb6290c5673b
        with:
          script: |
            const requiredName = "required-green-gate";
            const sha = context.sha;
            const { data } = await github.rest.checks.listForRef({
              owner: context.repo.owner,
              repo: context.repo.repo,
              ref: sha,
              per_page: 100,
            });
            const matches = data.check_runs.filter((run) => run.name === requiredName);
            core.info(String(matches.length));
  extract-version:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-regular:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-single:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  summary:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
""",
    )
    assert any(
        "missing build-and-release gate policy token 'required gate app slug guard'"
        in item
        for item in failures
    )
    assert any(
        "missing build-and-release gate policy token 'release target_commitish guard'"
        in item
        for item in failures
    )


def test_workflow_policy_rejects_commented_build_release_gate_tokens() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/build-and-release.yml"),
        """
name: Build and Release
permissions:
  contents: read
jobs:
  verify-required-green-gate:
    permissions:
      checks: read
    runs-on: ubuntu-latest
    steps:
      - name: Validate required-green-gate on same SHA
        uses: actions/github-script@f28e40c7f34bde8b3046d885e986cb6290c5673b
        with:
          script: |
            // if (context.eventName === "workflow_dispatch" && context.ref !== "refs/heads/main") {
            // const targetCommitish = String(context.payload.release?.target_commitish || "").trim();
            // await github.rest.repos.compareCommitsWithBasehead({});
            // if (run.app?.slug !== "github-actions") {
            // const { data: workflowRun } = await github.rest.actions.getWorkflowRun({});
            // const workflowPath = String(workflowRun.path || "");
            // if (workflowPath.startsWith(".github/workflows/test.yml") && workflowRun.head_sha === sha) {}
            return;
  extract-version:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-regular:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  build-single:
    permissions:
      contents: read
      packages: write
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
  summary:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo ok
""",
    )
    assert any(
        "missing build-and-release gate policy token 'workflow_dispatch main branch guard'"
        in item
        for item in failures
    )


def test_workflow_policy_requires_hosted_fallback_cancelled_convergence_tokens() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/hosted-fallback-autoswitch.yml"),
        """
name: Hosted Runner Fallback Autoswitch
jobs:
  detect-and-switch:
    if: >-
      github.event_name == 'workflow_dispatch' ||
      (github.event_name == 'workflow_run' &&
       contains(fromJSON('["failure","startup_failure","timed_out","cancelled"]'), github.event.workflow_run.conclusion) &&
       github.event.workflow_run.event == 'push' &&
       github.event.workflow_run.head_branch == 'main')
    steps:
      - name: Decide and apply fallback switch
        uses: actions/github-script@f28e40c7f34bde8b3046d885e986cb6290c5673b
        with:
          script: |
            const blockedRunConclusions = new Set(["failure", "startup_failure", "timed_out", "cancelled"]);
            const billingOrQuotaBlocked = jobs.some((job) => {
              const blockedConclusion = ["failure", "startup_failure", "timed_out", "cancelled"].includes(
                String(job.conclusion || "").toLowerCase(),
              );
              return hostedTargeted && neverPickedRunner && blockedConclusion;
            });
""",
    )
    assert any(
        "missing hosted fallback policy token" in item and "isLatestMainHead" in item
        for item in failures
    )


def test_workflow_policy_rejects_commented_hosted_fallback_tokens() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/hosted-fallback-autoswitch.yml"),
        """
name: Hosted Runner Fallback Autoswitch
jobs:
  detect-and-switch:
    if: >-
      github.event_name == 'workflow_dispatch' ||
      (github.event_name == 'workflow_run' &&
       contains(fromJSON('["failure","startup_failure","timed_out","cancelled"]'), github.event.workflow_run.conclusion) &&
       github.event.workflow_run.event == 'push' &&
       github.event.workflow_run.head_branch == 'main')
    steps:
      - name: Decide and apply fallback switch
        uses: actions/github-script@f28e40c7f34bde8b3046d885e986cb6290c5673b
        with:
          script: |
            // contains(fromJSON('["failure","startup_failure","timed_out","cancelled"]'), github.event.workflow_run.conclusion)
            // const blockedRunConclusions = new Set(["failure", "startup_failure", "timed_out", "cancelled"]);
            // const isLatestMainHead = String(run?.head_sha || "") === String(defaultBranchHeadSha || "");
            // if (runConclusion === "cancelled" && !isLatestMainHead) {
            // if (runConclusion === "cancelled") {
            // return hostedTargeted && neverPickedRunner && neverStarted && blockedConclusion;
            return true;
""",
    )
    assert any(
        "missing hosted fallback policy token" in item
        and "blockedRunConclusions" in item
        for item in failures
    )


def test_workflow_policy_rejects_hosted_fallback_token_stuffing_in_non_executable_regions() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/hosted-fallback-autoswitch.yml"),
        """
name: Hosted Runner Fallback Autoswitch
jobs:
  detect-and-switch:
    if: github.event_name == 'workflow_dispatch'
    steps:
      - name: Decide and apply fallback switch
        uses: actions/github-script@f28e40c7f34bde8b3046d885e986cb6290c5673b
        with:
          script: |
            const bait0 = "contains(fromJSON('[\\"failure\\",\\"startup_failure\\",\\"timed_out\\",\\"cancelled\\"]'), github.event.workflow_run.conclusion)";
            const bait1 = "const blockedRunConclusions = new Set([\\"failure\\", \\"startup_failure\\", \\"timed_out\\", \\"cancelled\\"]);";
            const bait2 = "const isLatestMainHead = String(run?.head_sha || \\"\\") === String(defaultBranchHeadSha || \\"\\");";
            const bait3 = "if (runConclusion === \\"cancelled\\" && !isLatestMainHead) {";
            const bait4 = "if (runConclusion === \\"cancelled\\") {";
            const bait5 = "return hostedTargeted && neverPickedRunner && neverStarted && blockedConclusion;";
            return true;
""",
    )
    assert any(
        "missing hosted fallback policy token" in item
        and "github.event.workflow_run.conclusion guard" in item
        for item in failures
    )


def test_workflow_policy_rejects_missing_promptfoo_contract_files(
    tmp_path: Path,
) -> None:
    policy = _load_workflow_policy_module()
    repo_root = tmp_path / "repo"
    promptfoo_dir = repo_root / "evals" / "promptfoo"
    promptfoo_dir.mkdir(parents=True, exist_ok=True)

    (promptfoo_dir / "package.json").write_text("{}", encoding="utf-8")
    (promptfoo_dir / "promptfooconfig.yaml").write_text(
        "tests: file://../datasets/longtext_cases.jsonl\n", encoding="utf-8"
    )

    failures = policy._validate_promptfoo_eval_file_contract(repo_root)
    assert any("package-lock.json" in item for item in failures)


def test_workflow_policy_rejects_missing_promptfoo_file_uri_target(
    tmp_path: Path,
) -> None:
    policy = _load_workflow_policy_module()
    repo_root = tmp_path / "repo"
    promptfoo_dir = repo_root / "evals" / "promptfoo"
    promptfoo_dir.mkdir(parents=True, exist_ok=True)

    (promptfoo_dir / "package.json").write_text("{}", encoding="utf-8")
    (promptfoo_dir / "package-lock.json").write_text("{}", encoding="utf-8")
    (promptfoo_dir / "promptfooconfig.yaml").write_text(
        "defaultTest:\n"
        "  assert:\n"
        "    - type: javascript\n"
        "      value: file://assertions/no_uncited_claims.js\n",
        encoding="utf-8",
    )

    failures = policy._validate_promptfoo_eval_file_contract(repo_root)
    assert any("referenced file:// target does not exist" in item for item in failures)


def test_workflow_policy_rejects_untracked_promptfoo_contract_file(
    tmp_path: Path, monkeypatch
) -> None:
    policy = _load_workflow_policy_module()
    repo_root = tmp_path / "repo"
    promptfoo_dir = repo_root / "evals" / "promptfoo"
    promptfoo_dir.mkdir(parents=True, exist_ok=True)
    (repo_root / ".git").mkdir()

    (promptfoo_dir / "package.json").write_text("{}", encoding="utf-8")
    (promptfoo_dir / "package-lock.json").write_text("{}", encoding="utf-8")
    (promptfoo_dir / "assertions").mkdir(parents=True, exist_ok=True)
    (repo_root / "evals" / "datasets").mkdir(parents=True, exist_ok=True)
    (promptfoo_dir / "assertions" / "no_uncited_claims.js").write_text(
        "module.exports = () => true;\n", encoding="utf-8"
    )
    (repo_root / "evals" / "datasets" / "longtext_cases.jsonl").write_text(
        "{}\n", encoding="utf-8"
    )
    (promptfoo_dir / "promptfooconfig.yaml").write_text(
        "tests: file://../datasets/longtext_cases.jsonl\n"
        "defaultTest:\n"
        "  assert:\n"
        "    - type: javascript\n"
        "      value: file://assertions/no_uncited_claims.js\n",
        encoding="utf-8",
    )

    def _fake_run(cmd: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        path_arg = cmd[-1]
        returncode = 1 if path_arg == "evals/promptfoo/package-lock.json" else 0
        return subprocess.CompletedProcess(cmd, returncode, "", "")

    monkeypatch.setattr(policy.subprocess, "run", _fake_run)

    failures = policy._validate_promptfoo_eval_file_contract(repo_root)
    assert any(
        "package-lock.json" in item and "not tracked by git" in item
        for item in failures
    )


def test_workflow_policy_extract_file_uri_targets_strips_quotes() -> None:
    policy = _load_workflow_policy_module()
    targets = policy._extract_file_uri_targets(
        'defaultTest:\n  assert:\n    - value: "file://assertions/no_uncited_claims.js"\n'
    )
    assert targets == {"assertions/no_uncited_claims.js"}


def test_workflow_policy_rejects_unpinned_external_action_ref() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Poisoned
jobs:
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: Unpinned checkout
        uses: actions/checkout@v4
""",
    )
    assert any("must pin to full commit SHA" in item for item in failures)


def test_workflow_policy_rejects_pull_request_target_trigger() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Poisoned
on:
  pull_request_target:
    branches: [main]
jobs:
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any("pull_request_target trigger is forbidden" in item for item in failures)


def test_workflow_policy_rejects_inline_pull_request_target_trigger() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/non-critical.yml"),
        """
name: Poisoned
on:
  pull_request_target: {}
jobs:
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any("pull_request_target trigger is forbidden" in item for item in failures)


def test_workflow_policy_rejects_pull_request_target_scalar_on_trigger() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/non-critical.yml"),
        """
name: Poisoned
on: pull_request_target
jobs:
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any("pull_request_target trigger is forbidden" in item for item in failures)


def test_workflow_policy_rejects_pull_request_target_in_event_array() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/non-critical.yml"),
        """
name: Poisoned
on: [push, pull_request_target]
jobs:
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any("pull_request_target trigger is forbidden" in item for item in failures)


def test_workflow_policy_rejects_pre_commit_home_tilde_cache_path() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/pre-commit.yml"),
        """
name: Poisoned
jobs:
  poisoned:
    runs-on: [self-hosted, shared-pool]
    env:
      PRE_COMMIT_HOME: ~/.cache/pre-commit
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any(
        "PRE_COMMIT_HOME must not use '~/.cache/pre-commit'" in item
        for item in failures
    )


def test_workflow_policy_rejects_pre_commit_home_relative_path() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/pre-commit.yml"),
        """
name: Poisoned
jobs:
  poisoned:
    runs-on: [self-hosted, shared-pool]
    env:
      PRE_COMMIT_HOME: .runtime-cache/pre-commit-home
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any(
        "PRE_COMMIT_HOME must not use a relative path" in item for item in failures
    )


def test_workflow_policy_rejects_pre_commit_home_github_workspace_path() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/pre-commit.yml"),
        """
name: Poisoned
jobs:
  poisoned:
    runs-on: [self-hosted, shared-pool]
    env:
      PRE_COMMIT_HOME: ${{ github.workspace }}/.cache/pre-commit
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any(
        "must not write under github.workspace/GITHUB_WORKSPACE" in item
        for item in failures
    )


def test_workflow_policy_rejects_pre_commit_home_github_workspace_env_path() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/pre-commit.yml"),
        """
name: Poisoned
jobs:
  poisoned:
    runs-on: [self-hosted, shared-pool]
    env:
      PRE_COMMIT_HOME: ${GITHUB_WORKSPACE}/.cache/pre-commit
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any(
        "must not write under github.workspace/GITHUB_WORKSPACE" in item
        for item in failures
    )


def test_workflow_policy_rejects_runner_management_scripts() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Poisoned
jobs:
  poisoned:
    runs-on: [self-hosted, shared-pool]
    steps:
      - name: mutate-runner
        run: |
          ./run.sh
          config.sh --check
          remove.sh
""",
    )
    assert any(
        "repo workflows must not invoke runner management script './run.sh'" in item
        for item in failures
    )
    assert any(
        "repo workflows must not invoke runner management script 'config.sh'" in item
        for item in failures
    )
    assert any(
        "repo workflows must not invoke runner management script 'remove.sh'" in item
        for item in failures
    )


def test_workflow_policy_rejects_pull_request_secrets_without_guard() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Poisoned
on:
  pull_request:
    branches: [main]
jobs:
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: secret use without guard
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: echo poisoned
""",
    )
    assert any(
        "missing pull_request secret guard expression" in item for item in failures
    )


def test_workflow_policy_rejects_inline_pull_request_secrets_without_guard() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/non-critical.yml"),
        """
name: Poisoned
on:
  pull_request: {}
jobs:
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: secret use without guard
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: echo poisoned
""",
    )
    assert any(
        "missing pull_request secret guard expression" in item for item in failures
    )


def test_workflow_policy_rejects_pull_request_secrets_without_guard_when_on_array() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/non-critical.yml"),
        """
name: Poisoned
on: [pull_request, workflow_dispatch]
jobs:
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: secret use without guard
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: echo poisoned
""",
    )
    assert any(
        "missing pull_request secret guard expression" in item for item in failures
    )


def test_workflow_policy_accepts_equivalent_pull_request_same_repo_guard() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        f"""
name: Safe
on:
  pull_request:
    branches: [main]
jobs:
  safe:
    if: {TRUSTED_PR_GUARD}
    runs-on: ubuntu-latest
    steps:
      - name: guarded secret use
        env:
          GEMINI_API_KEY: ${{{{ secrets.GEMINI_API_KEY }}}}
        run: echo guarded
""",
    )
    assert not any(
        "missing pull_request secret guard expression" in item for item in failures
    )


def test_workflow_policy_accepts_guard_with_scalar_pull_request_trigger() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/non-critical.yml"),
        f"""
name: Safe
on: pull_request
jobs:
  safe:
    if: {TRUSTED_PR_GUARD}
    runs-on: ubuntu-latest
    steps:
      - name: guarded secret use
        env:
          GEMINI_API_KEY: ${{{{ secrets.GEMINI_API_KEY }}}}
        run: echo guarded
""",
    )
    assert not any(
        "missing pull_request secret guard expression" in item for item in failures
    )


def test_workflow_policy_accepts_stricter_non_pull_request_secret_guard() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Safe
on:
  pull_request:
    branches: [main]
jobs:
  safe:
    runs-on: ubuntu-latest
    steps:
      - name: guarded secret use
        if: ${{ github.event_name != 'pull_request' }}
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: echo guarded
""",
    )
    assert not any(
        "missing pull_request secret guard expression" in item for item in failures
    )


def test_workflow_policy_rejects_pull_request_secret_guard_superset_expression() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Poisoned
on:
  pull_request:
    branches: [main]
jobs:
  poisoned:
    if: ${{ github.event_name != 'pull_request' || github.actor == 'trusted-user' }}
    runs-on: ubuntu-latest
    steps:
      - name: unsafe broadened guard
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: echo poisoned
""",
    )
    assert any(
        "missing pull_request secret guard expression" in item for item in failures
    )


def test_workflow_policy_rejects_pull_request_secret_guard_bait_in_unrelated_job() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Poisoned
on:
  pull_request:
    branches: [main]
jobs:
  bait:
    if: github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-latest
    steps:
      - name: no secret here
        run: echo bait
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: secret use without local guard
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: echo poisoned
""",
    )
    assert any(
        "missing pull_request secret guard expression" in item for item in failures
    )


def test_workflow_policy_rejects_pull_request_secret_guard_bait_in_non_secret_step() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        f"""
name: Poisoned
on:
  pull_request:
    branches: [main]
jobs:
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: bait guard only
        if: {TRUSTED_PR_GUARD}
        run: echo bait
      - name: secret use without guard
        env:
          GEMINI_API_KEY: ${{{{ secrets.GEMINI_API_KEY }}}}
        run: echo poisoned
""",
    )
    assert any(
        "missing pull_request secret guard expression" in item
        and "secret use without guard" in item
        for item in failures
    )


def test_workflow_policy_accepts_pull_request_secret_step_level_guard() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        f"""
name: Safe
on:
  pull_request:
    branches: [main]
jobs:
  safe:
    runs-on: ubuntu-latest
    steps:
      - name: guarded secret use
        if: {TRUSTED_PR_GUARD}
        env:
          GEMINI_API_KEY: ${{{{ secrets.GEMINI_API_KEY }}}}
        run: echo guarded
""",
    )
    assert not any(
        "missing pull_request secret guard expression" in item for item in failures
    )


def test_workflow_policy_rejects_pull_request_bracket_secret_without_guard() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Poisoned
on:
  pull_request:
    branches: [main]
jobs:
  poisoned:
    runs-on: ubuntu-latest
    steps:
      - name: bracket secret use without guard
        env:
          GEMINI_API_KEY: ${{ secrets['GEMINI_API_KEY'] }}
        run: echo poisoned
""",
    )
    assert any(
        "missing pull_request secret guard expression" in item for item in failures
    )


def test_workflow_policy_accepts_pull_request_bracket_secret_with_guard() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        f"""
name: Safe
on:
  pull_request:
    branches: [main]
jobs:
  safe:
    if: {TRUSTED_PR_GUARD}
    runs-on: ubuntu-latest
    steps:
      - name: guarded bracket secret use
        env:
          GEMINI_API_KEY: ${{{{ secrets["GEMINI_API_KEY"] }}}}
        run: echo guarded
""",
    )
    assert not any(
        "missing pull_request secret guard expression" in item for item in failures
    )


def test_workflow_policy_rejects_pull_request_guard_only_in_comments() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Poisoned
on:
  pull_request:
    branches: [main]
jobs:
  poisoned:
    # github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-latest
    steps:
      - name: secret use without guard
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: echo poisoned
""",
    )
    assert any(
        "missing pull_request secret guard expression" in item for item in failures
    )


def test_workflow_policy_rejects_pre_commit_runner_without_hosted_contract() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/pre-commit.yml"),
        """
name: Pre-commit
jobs:
  pre-commit:
    runs-on: [self-hosted, shared-pool]
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any(
        "job 'pre-commit' must use runner expression" in item for item in failures
    )


def test_workflow_policy_rejects_hosted_core_job_without_hosted_runner_contract() -> (
    None
):
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Tests
jobs:
  backend-lint:
    runs-on: [self-hosted, shared-pool]
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any(
        "job 'backend-lint' must use runner expression: runs-on: ubuntu-latest" in item
        for item in failures
    )


def test_workflow_policy_rejects_external_hosted_job_without_external_pr_gate() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/test.yml"),
        """
name: Tests
jobs:
  external-pr-fast-gate:
    runs-on: ubuntu-latest
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any(
        "must restrict hosted fallback execution to external pull_request events"
        in item
        for item in failures
    )


def test_workflow_policy_rejects_claude_without_trusted_author_association() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/claude.yml"),
        """
name: Claude Code
jobs:
  claude:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude'))
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
      actions: read
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any("trusted author association token" in item for item in failures)


def test_workflow_policy_rejects_claude_id_token_permission() -> None:
    policy = _load_workflow_policy_module()
    failures = policy._validate_single_workflow(
        Path(".github/workflows/claude.yml"),
        """
name: Claude Code
jobs:
  claude:
    if: |
      contains(fromJSON('["OWNER","MEMBER","COLLABORATOR"]'), github.event.comment.author_association) &&
      contains(fromJSON('["OWNER","MEMBER","COLLABORATOR"]'), github.event.review.author_association) &&
      contains(fromJSON('["OWNER","MEMBER","COLLABORATOR"]'), github.event.issue.author_association)
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
      actions: read
      id-token: write
    steps:
      - name: noop
        run: echo poisoned
""",
    )
    assert any("must not request id-token permission" in item for item in failures)
