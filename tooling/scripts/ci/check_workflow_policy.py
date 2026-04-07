#!/usr/bin/env python3
"""Enforce strict CI workflow policy contracts."""

from __future__ import annotations

import importlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

yaml: Any = importlib.import_module("yaml")

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

FORBIDDEN_BYPASS_VARS = (
    "SKIP_DOCS_CHANGE_GUARD",
    "COMMIT_GOVERNANCE_BASELINE_SHA",
    "COMMIT_GOVERNANCE_RANGE",
    "ATOMIC_COMMIT_MAX_FILES",
    "ATOMIC_COMMIT_MAX_TOP_LEVEL",
)

CRITICAL_WORKFLOWS_STRICT = (
    "test.yml",
    "pre-commit.yml",
    "build-and-release.yml",
    "build-dev.yml",
    "live-integration.yml",
    "uiux-gemini-gate.yml",
)

CONTINUE_ON_ERROR_ALLOWLIST: dict[str, set[str]] = {
    # Artifact download on failure is optional for issue enrichment,
    # and should not block the remediation issue creation itself.
    "uiux-auto-remediation.yml": {
        "Download UIUX gate inputs artifact from failed run",
    },
}

ARTIFACT_IGNORE_ALLOWLIST: dict[str, set[str]] = {
    # Retry logs are best-effort diagnostics and are allowed to be absent.
    "test.yml": {
        "Upload retry classification logs",
        "Upload bundle analysis",  # Bundle analysis is optional
    },
}

SHARED_POOL_RUNNER_EXPR = "runs-on: [self-hosted, shared-pool]"
HOSTED_UBUNTU_RUNNER_EXPR = "runs-on: ubuntu-latest"
TRUSTED_AUTHOR_ASSOCIATIONS_JSON = '["OWNER","MEMBER","COLLABORATOR"]'
CLAUDE_REQUIRED_IF_TOKENS = tuple(
    f"contains(fromJSON('{TRUSTED_AUTHOR_ASSOCIATIONS_JSON}'), github.event.{field}.author_association)"
    for field in ("comment", "review", "issue")
)
WORKFLOWS_REQUIRING_STRICT_ENV_STEP = (
    "test.yml",
    "auditable-quality-gate.yml",
    "uiux-gemini-gate.yml",
    "live-integration.yml",
)
SENSITIVE_ENVIRONMENT_JOBS: dict[str, tuple[str, ...]] = {
    "auditable-quality-gate.yml": ("required-ci-env", "promptfoo-eval", "ragas-eval"),
    "claude-code-review.yml": ("claude-review",),
    "claude.yml": ("claude",),
    "live-integration.yml": ("live-llm-gemini", "live-playwright-external"),
    "uiux-gemini-gate.yml": ("uiux-gemini-gate",),
}
SENSITIVE_ENVIRONMENT_NAME = "owner-approved-sensitive"
MAINLINE_CONTAINERIZED_WORKFLOWS = (
    "test.yml",
    "pre-commit.yml",
    "uiux-gemini-gate.yml",
    "live-integration.yml",
    "jscpd-duplication.yml",
)
FORBIDDEN_MAINLINE_SETUP_TOKENS = (
    "actions/setup-python@",
    "actions/setup-node@",
    "astral-sh/setup-uv@",
    "./.github/actions/setup-uv-python",
    "./.github/actions/setup-node-apps/web",
)
REQUIRED_MAINLINE_CONTAINER_TOKEN = "tooling/scripts/ci/run_in_consistent_container.sh"

WORKFLOW_RUN_SOURCE_POLICY: dict[str, tuple[str, ...]] = {
    "uiux-auto-remediation.yml": (
        "github.event.workflow_run.event == 'push'",
        "github.event.workflow_run.head_branch == 'main'",
    ),
    "build-dev.yml": (
        "github.event.workflow_run.event == 'push'",
        "github.event.workflow_run.head_branch == 'main'",
        "github.event.workflow_run.head_repository.full_name == github.repository",
    ),
}
WORKFLOW_RUN_UPSTREAM_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "build-dev.yml": ("Tests",),
    "uiux-auto-remediation.yml": ("UIUX Gemini Gate",),
}
BUILD_DEV_PACKAGE_WRITE_JOBS = ("build-regular", "build-single")
BUILD_RELEASE_PACKAGE_WRITE_JOBS = ("build-regular", "build-single")
BUILD_RELEASE_SCRIPT_POLICY_RE: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "workflow_dispatch main branch guard",
        re.compile(
            r"""(?m)^\s*if\s*\(\s*context\.eventName\s*===\s*['"]workflow_dispatch['"]\s*&&\s*context\.ref\s*!==\s*['"]refs/heads/main['"]\s*\)\s*\{"""
        ),
    ),
    (
        "release target_commitish guard",
        re.compile(
            r"""(?m)^\s*const\s+targetCommitish\s*=\s*String\(context\.payload\.release\?\.target_commitish\s*\|\|\s*['"]['"]\)\.trim\(\);"""
        ),
    ),
    (
        "trusted-branch ancestry check",
        re.compile(r"compareCommitsWithBasehead\("),
    ),
    (
        "required gate app slug guard",
        re.compile(
            r"""(?m)^\s*if\s*\(\s*run\.app\?\.slug\s*!==\s*['"]github-actions['"]\s*\)\s*\{"""
        ),
    ),
    (
        "required gate workflow identity lookup",
        re.compile(r"github\.rest\.actions\.getWorkflowRun\("),
    ),
    (
        "required gate workflow path guard",
        re.compile(
            r"""workflowPath\.startsWith\(\s*['"]\.github/workflows/test\.yml['"]\s*\)"""
        ),
    ),
    (
        "required gate head_sha guard",
        re.compile(r"workflowRun\.head_sha\s*===\s*sha"),
    ),
)
PULL_REQUEST_SECRET_GUARD_EXPR = (
    "github.event_name != 'pull_request' || "
    "(github.event.pull_request.head.repo.full_name == github.repository && github.actor != 'dependabot[bot]')"
)
EXTERNAL_PR_HOSTED_JOB_IF = (
    "github.event_name == 'pull_request' && "
    "(github.event.pull_request.head.repo.full_name != github.repository || github.actor == 'dependabot[bot]')"
)
PULL_REQUEST_SECRET_GUARD_RE = re.compile(
    r"github\.event_name\s*!=\s*['\"]pull_request['\"]"
    r"(?:\s*\|\|\s*"
    r"\(?\s*github\.event\.pull_request\.head\.repo\.full_name\s*==\s*github\.repository\s*"
    r"&&\s*github\.actor\s*!=\s*['\"]dependabot\[bot\]['\"]\s*\)?)?"
)
SECRETS_REFERENCE_RE = re.compile(
    r"\${{\s*secrets(?:\s*\.\s*[A-Za-z_][A-Za-z0-9_-]*|\s*\[\s*['\"][^'\"]+['\"]\s*\])"
)
HOSTED_FALLBACK_IF_POLICY_RE = re.compile(
    r"contains\(\s*fromJSON\(\s*.+?\s*\)\s*,\s*github\.event\.workflow_run\.conclusion\s*\)",
    flags=re.DOTALL,
)
HOSTED_FALLBACK_SCRIPT_POLICY_RE: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "blockedRunConclusions",
        re.compile(
            r"(?m)^\s*const\s+blockedRunConclusions\s*=\s*new\s+Set\(",
        ),
    ),
    (
        "isLatestMainHead",
        re.compile(r"(?m)^\s*const\s+isLatestMainHead\s*="),
    ),
    (
        "cancelled && !isLatestMainHead guard",
        re.compile(
            r"""(?m)^\s*if\s*\(\s*runConclusion\s*===\s*['"]cancelled['"]\s*&&\s*!isLatestMainHead\s*\)\s*\{"""
        ),
    ),
    (
        "cancelled branch guard",
        re.compile(
            r"""(?m)^\s*if\s*\(\s*runConclusion\s*===\s*['"]cancelled['"]\s*\)\s*\{"""
        ),
    ),
    (
        "cancelled rerun return",
        re.compile(
            r"(?m)^\s*return\s+hostedTargeted\s*&&\s*neverPickedRunner\s*&&\s*neverStarted\s*&&\s*blockedConclusion\s*;"
        ),
    ),
)

HOSTED_ONLY_WORKFLOW_JOBS = {
    "pre-commit.yml": ("pre-commit",),
    "pre-commit-outdated-check.yml": ("check-pre-commit-outdated",),
    "jscpd-duplication.yml": ("jscpd-duplication",),
    "uiux-gemini-gate.yml": ("uiux-gemini-gate",),
    "claude.yml": ("claude",),
    "claude-code-review.yml": ("claude-review",),
    "auditable-quality-gate.yml": ("required-ci-env", "promptfoo-eval", "ragas-eval"),
    "live-integration.yml": ("live-llm-gemini", "live-playwright-external"),
    "mutation-nightly.yml": ("mutation-python-nightly",),
    "uiux-auto-remediation.yml": ("open-remediation-issue",),
    "upstream-drift.yml": ("check-drift",),
}
WORKFLOW_RUNNER_POLICY: dict[str, dict[str, str]] = {
    name: {job: "hosted-any" for job in jobs}
    for name, jobs in HOSTED_ONLY_WORKFLOW_JOBS.items()
} | {
    "test.yml": {
        "required-ci-env": "hosted-any",
        "changes": "hosted-any",
        "security-scan": "hosted-any",
        "external-pr-security-scan": "external-hosted",
        "external-pr-fast-gate": "external-hosted",
        "governance-gates": "hosted-any",
        "runtime-policy-gates": "hosted-any",
        "test-smells": "hosted-any",
        "backend-lint": "hosted-any",
        "apps-web-lint": "hosted-any",
        "backend-shard-a": "hosted-any",
        "backend-shard-b": "hosted-any",
        "property-tests": "hosted-any",
        "mutation-python": "hosted-any",
        "apps-web": "hosted-any",
        "backend-coverage-merge": "hosted-any",
        "e2e": "hosted-any",
        "e2e-cross-browser-smoke": "hosted-any",
        "e2e-real-backend": "hosted-any",
        "post-test-housekeeping": "hosted-any",
        "coverage-thresholds": "hosted-any",
        "required-green-gate": "hosted-any",
    }
}


def _is_critical_workflow(path: Path) -> bool:
    return path.name in CRITICAL_WORKFLOWS_STRICT


def _line_failures_for_forbidden_vars(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for variable in FORBIDDEN_BYPASS_VARS:
            if variable in line:
                failures.append(f"{path}:{lineno}: forbidden bypass var '{variable}'")
    return failures


def _line_failures_for_unpinned_actions(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^\s*uses:\s*([^\s#]+)\s*(?:#.*)?$", line)
        if not match:
            continue
        uses_ref = match.group(1).strip()
        if uses_ref.startswith("./") or uses_ref.startswith("docker://"):
            continue
        if "@" not in uses_ref:
            failures.append(
                f"{path}:{lineno}: external action must pin to full commit SHA, got '{uses_ref}'"
            )
            continue
        ref = uses_ref.rsplit("@", 1)[1]
        if not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
            failures.append(
                f"{path}:{lineno}: external action must pin to full commit SHA, got '{uses_ref}'"
            )
    return failures


def _normalize_env_value(raw: str) -> str:
    return raw.strip().strip("'\"")


def _is_workspace_backed_path(value: str) -> bool:
    normalized = value.lower()
    return (
        "${{ github.workspace }}" in normalized
        or "${github_workspace}" in normalized
        or "$github_workspace" in normalized
    )


def _is_explicit_relative_path(value: str) -> bool:
    if not value:
        return False
    if value.startswith(("/", "~", "${{", "${", "$")):
        return False
    return True


def _line_failures_for_runner_workspace_pollution(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    sanitized_text = _strip_policy_comments(text)

    for lineno, line in enumerate(sanitized_text.splitlines(), start=1):
        env_match = re.match(r"^\s*PRE_COMMIT_HOME:\s*(.+?)\s*$", line)
        if env_match:
            value = _normalize_env_value(env_match.group(1))
            if value == "~/.cache/pre-commit":
                failures.append(
                    f"{path}:{lineno}: PRE_COMMIT_HOME must not use '~/.cache/pre-commit'; use /tmp or runner.temp outside the checkout workspace"
                )
                continue
            if value.startswith("~"):
                failures.append(
                    f"{path}:{lineno}: PRE_COMMIT_HOME must not use a '~' home-relative path; use /tmp or runner.temp outside the checkout workspace"
                )
                continue
            if _is_workspace_backed_path(value):
                failures.append(
                    f"{path}:{lineno}: PRE_COMMIT_HOME must not write under github.workspace/GITHUB_WORKSPACE; keep caches outside the checkout workspace"
                )
                continue
            if _is_explicit_relative_path(value):
                failures.append(
                    f"{path}:{lineno}: PRE_COMMIT_HOME must not use a relative path '{value}'; keep caches outside the checkout workspace"
                )

        runner_script_match = re.search(
            r"(?<![\w./-])(?:\./)?(?:config|run|remove)\.sh\b", line
        )
        if runner_script_match:
            failures.append(
                f"{path}:{lineno}: repo workflows must not invoke runner management script '{runner_script_match.group(0)}'; consume org-shared runners only"
            )

    return failures


def _extract_paths_ignore_patterns(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    results: list[tuple[int, str]] = []

    def _parse_inline_list(raw: str) -> list[str]:
        value = raw.strip()
        if not value:
            return []
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1]
        return [item.strip().strip("'\"") for item in value.split(",") if item.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]
        inline_match = re.match(r"^\s*paths-ignore:\s*(.+?)\s*$", line)
        if inline_match:
            for pattern in _parse_inline_list(inline_match.group(1)):
                results.append((i + 1, pattern))
            i += 1
            continue
        if re.match(r"^\s*paths-ignore:\s*$", line):
            base_indent = len(line) - len(line.lstrip(" "))
            j = i + 1
            while j < len(lines):
                candidate = lines[j]
                if not candidate.strip():
                    j += 1
                    continue
                indent = len(candidate) - len(candidate.lstrip(" "))
                if indent <= base_indent:
                    break
                m = re.match(r"^\s*-\s*(.+?)\s*$", candidate)
                if m:
                    pattern = m.group(1).strip().strip("'\"")
                    results.append((j + 1, pattern))
                j += 1
            i = j
            continue
        i += 1
    return results


def _is_docs_skip_pattern(pattern: str) -> bool:
    normalized = pattern.strip().lower()
    return any(
        token in normalized
        for token in ("docs/**", "**/*.md", "*.md", "readme", "changelog")
    )


def _iter_step_blocks(text: str) -> list[tuple[int, str, str]]:
    lines = text.splitlines()
    steps: list[tuple[int, str, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        name_match = re.match(r"^(\s*)-\s+name:\s+(.+?)\s*$", line)
        if not name_match:
            i += 1
            continue
        step_indent = len(name_match.group(1))
        step_name = name_match.group(2).strip().strip("'\"")
        start_line = i + 1

        j = i + 1
        while j < len(lines):
            candidate = lines[j]
            if not candidate.strip():
                j += 1
                continue
            candidate_indent = len(candidate) - len(candidate.lstrip(" "))
            if candidate_indent <= step_indent and re.match(
                r"^\s*-\s+name:\s+", candidate
            ):
                break
            j += 1

        block = "\n".join(lines[i:j])
        steps.append((start_line, step_name, block))
        i = j
    return steps


def _iter_job_blocks(text: str) -> list[tuple[int, str, str]]:
    lines = text.splitlines()
    jobs: list[tuple[int, str, str]] = []
    job_header_pattern = re.compile(r"^  ([A-Za-z0-9_./-]+):\s*$")
    i = 0
    while i < len(lines):
        line = lines[i]
        job_match = job_header_pattern.match(line)
        if not job_match:
            i += 1
            continue

        job_name = job_match.group(1)
        start_line = i + 1
        j = i + 1
        while j < len(lines):
            if job_header_pattern.match(lines[j]):
                break
            j += 1
        block = "\n".join(lines[i:j])
        jobs.append((start_line, job_name, block))
        i = j
    return jobs


def _validate_required_env_step(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    if path.name not in WORKFLOWS_REQUIRING_STRICT_ENV_STEP:
        return failures

    if "bash tooling/scripts/ci/check_required_ci_env.sh" not in text:
        failures.append(
            f"{path}: missing strict env gate step 'bash tooling/scripts/ci/check_required_ci_env.sh'"
        )
    if "GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}" not in text:
        failures.append(
            f"{path}: missing GEMINI_API_KEY secret wiring for strict env gate"
        )
    if (
        "OPEN_NOTEBOOK_ENCRYPTION_KEY: ${{ secrets.OPEN_NOTEBOOK_ENCRYPTION_KEY }}"
        not in text
    ):
        failures.append(
            f"{path}: missing OPEN_NOTEBOOK_ENCRYPTION_KEY secret wiring for strict env gate"
        )
    return failures


def _validate_runner_policy(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    expected_for_jobs = WORKFLOW_RUNNER_POLICY.get(path.name)
    if not expected_for_jobs:
        return failures

    found_job_blocks = {
        name: (lineno, block) for lineno, name, block in _iter_job_blocks(text)
    }
    for job_name, mode in expected_for_jobs.items():
        if job_name not in found_job_blocks:
            failures.append(
                f"{path}: missing job '{job_name}' required by runner routing policy"
            )
            continue
        line_no, block = found_job_blocks[job_name]
        uncommented_block = _strip_policy_comments(block)

        if mode == "self-hosted-any":
            if SHARED_POOL_RUNNER_EXPR not in uncommented_block:
                failures.append(
                    f"{path}:{line_no}: job '{job_name}' must use runner expression: {SHARED_POOL_RUNNER_EXPR}"
                )
            continue

        if mode == "hosted-any":
            if HOSTED_UBUNTU_RUNNER_EXPR not in uncommented_block:
                failures.append(
                    f"{path}:{line_no}: job '{job_name}' must use runner expression: {HOSTED_UBUNTU_RUNNER_EXPR}"
                )
            continue

        if mode == "external-hosted":
            if HOSTED_UBUNTU_RUNNER_EXPR not in uncommented_block:
                failures.append(
                    f"{path}:{line_no}: job '{job_name}' must use runner expression: {HOSTED_UBUNTU_RUNNER_EXPR}"
                )
            if EXTERNAL_PR_HOSTED_JOB_IF not in uncommented_block:
                failures.append(
                    f"{path}:{line_no}: job '{job_name}' must restrict hosted fallback execution to external pull_request events"
                )
            continue

        failures.append(
            f"{path}:{line_no}: unknown runner policy mode '{mode}' for job '{job_name}'"
        )
    return failures


def _validate_workflow_run_source_policy(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    required_tokens = WORKFLOW_RUN_SOURCE_POLICY.get(path.name)
    if not required_tokens:
        return failures

    uncommented_text = _strip_policy_comments(text)
    for token in required_tokens:
        if token not in uncommented_text:
            failures.append(
                f"{path}: missing workflow_run source constraint '{token}' for workflow '{path.name}'"
            )
    return failures


def _normalize_name_list(value: object) -> list[str]:
    if isinstance(value, str):
        cleaned = value.strip().strip("'\"")
        return [cleaned] if cleaned else []
    if isinstance(value, list):
        normalized: list[str] = []
        for item in value:
            cleaned = str(item).strip().strip("'\"")
            if cleaned:
                normalized.append(cleaned)
        return normalized
    return []


def _normalize_permission_scope(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _validate_workflow_run_upstream_allowlist(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    required_workflows = WORKFLOW_RUN_UPSTREAM_ALLOWLIST.get(path.name)
    if not required_workflows:
        return failures

    on_value = _extract_workflow_on_config(text)
    if not isinstance(on_value, dict):
        failures.append(
            f"{path}: missing workflow_run upstream workflow allowlist policy for workflow '{path.name}'"
        )
        return failures

    workflow_run_value = on_value.get("workflow_run")
    if not isinstance(workflow_run_value, dict):
        failures.append(
            f"{path}: missing workflow_run upstream workflow allowlist policy for workflow '{path.name}'"
        )
        return failures

    actual = sorted(set(_normalize_name_list(workflow_run_value.get("workflows"))))
    expected = sorted(set(required_workflows))
    if actual != expected:
        failures.append(
            f"{path}: workflow_run workflows allowlist must be exactly {expected} for workflow '{path.name}', got {actual or '<missing>'}"
        )
    return failures


def _validate_sensitive_environment_policy(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    required_jobs = SENSITIVE_ENVIRONMENT_JOBS.get(path.name)
    if not required_jobs:
        return failures

    jobs = _extract_jobs_from_workflow_yaml(text)
    for job_name in required_jobs:
        job = jobs.get(job_name)
        if not isinstance(job, dict):
            failures.append(
                f"{path}: missing job '{job_name}' required by sensitive environment policy"
            )
            continue

        environment = job.get("environment")
        environment_name = ""
        if isinstance(environment, str):
            environment_name = environment.strip()
        elif isinstance(environment, dict):
            environment_name = str(environment.get("name", "")).strip()

        if environment_name != SENSITIVE_ENVIRONMENT_NAME:
            failures.append(
                f"{path}: job '{job_name}' must declare environment '{SENSITIVE_ENVIRONMENT_NAME}'"
            )

    return failures


def _validate_build_dev_permission_minimization(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    if path.name != "build-dev.yml":
        return failures

    workflow = _load_workflow_yaml_object(text)
    top_permissions = workflow.get("permissions")
    if not isinstance(top_permissions, dict):
        failures.append(
            f"{path}: build-dev workflow must declare top-level permissions mapping"
        )
    else:
        if _normalize_permission_scope(top_permissions.get("contents")) != "read":
            failures.append(
                f"{path}: build-dev workflow top-level permissions must set contents: read"
            )
        top_packages = _normalize_permission_scope(top_permissions.get("packages"))
        if top_packages and top_packages != "none":
            failures.append(
                f"{path}: build-dev workflow top-level permissions must not request packages scope; set packages only on publishing jobs"
            )

    jobs = _extract_jobs_from_workflow_yaml(text)
    for job_name in BUILD_DEV_PACKAGE_WRITE_JOBS:
        job = jobs.get(job_name)
        if not isinstance(job, dict):
            failures.append(
                f"{path}: missing job '{job_name}' required by build-dev permission minimization policy"
            )
            continue
        job_permissions = job.get("permissions")
        if not isinstance(job_permissions, dict):
            failures.append(
                f"{path}: job '{job_name}' must declare explicit permissions mapping"
            )
            continue
        if _normalize_permission_scope(job_permissions.get("contents")) != "read":
            failures.append(
                f"{path}: job '{job_name}' must set permissions.contents to 'read'"
            )
        if _normalize_permission_scope(job_permissions.get("packages")) != "write":
            failures.append(
                f"{path}: job '{job_name}' must set permissions.packages to 'write'"
            )

    for job_name in ("extract-version", "summary"):
        job = jobs.get(job_name)
        if not isinstance(job, dict):
            continue
        job_permissions = job.get("permissions")
        if not isinstance(job_permissions, dict):
            continue
        pkg_scope = _normalize_permission_scope(job_permissions.get("packages"))
        if pkg_scope and pkg_scope != "none":
            failures.append(f"{path}: job '{job_name}' must not request packages scope")
    return failures


def _validate_build_release_policy(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    if path.name != "build-and-release.yml":
        return failures

    workflow = _load_workflow_yaml_object(text)
    top_permissions = workflow.get("permissions")
    if not isinstance(top_permissions, dict):
        failures.append(
            f"{path}: build-and-release workflow must declare top-level permissions mapping"
        )
    else:
        if _normalize_permission_scope(top_permissions.get("contents")) != "read":
            failures.append(
                f"{path}: build-and-release workflow top-level permissions must set contents: read"
            )
        top_packages = _normalize_permission_scope(top_permissions.get("packages"))
        if top_packages and top_packages != "none":
            failures.append(
                f"{path}: build-and-release workflow top-level permissions must not request packages scope; set packages only on publishing jobs"
            )

    jobs = _extract_jobs_from_workflow_yaml(text)
    verify_job = jobs.get("verify-required-green-gate")
    if not isinstance(verify_job, dict):
        failures.append(
            f"{path}: missing job 'verify-required-green-gate' required by build-and-release gate policy"
        )
    else:
        verify_permissions = verify_job.get("permissions")
        if not isinstance(verify_permissions, dict):
            failures.append(
                f"{path}: job 'verify-required-green-gate' must declare explicit permissions mapping"
            )
        elif _normalize_permission_scope(verify_permissions.get("checks")) != "read":
            failures.append(
                f"{path}: job 'verify-required-green-gate' must set permissions.checks to 'read'"
            )

        script_bodies: list[str] = []
        raw_steps = verify_job.get("steps", [])
        if isinstance(raw_steps, list):
            for step in raw_steps:
                if not isinstance(step, dict):
                    continue
                uses = str(step.get("uses", ""))
                if "actions/github-script@" not in uses:
                    continue
                with_section = step.get("with")
                if not isinstance(with_section, dict):
                    continue
                script = with_section.get("script")
                if isinstance(script, str):
                    script_bodies.append(script)

        if not script_bodies:
            failures.append(
                f"{path}: missing github-script required-green-gate validation step in job 'verify-required-green-gate'"
            )
        else:
            script_text = _strip_policy_comments("\n".join(script_bodies))
            for label, pattern in BUILD_RELEASE_SCRIPT_POLICY_RE:
                if pattern.search(script_text) is None:
                    failures.append(
                        f"{path}: missing build-and-release gate policy token '{label}' in workflow '{path.name}'"
                    )

    for job_name in BUILD_RELEASE_PACKAGE_WRITE_JOBS:
        job = jobs.get(job_name)
        if not isinstance(job, dict):
            failures.append(
                f"{path}: missing job '{job_name}' required by build-and-release permission minimization policy"
            )
            continue
        job_permissions = job.get("permissions")
        if not isinstance(job_permissions, dict):
            failures.append(
                f"{path}: job '{job_name}' must declare explicit permissions mapping"
            )
            continue
        if _normalize_permission_scope(job_permissions.get("contents")) != "read":
            failures.append(
                f"{path}: job '{job_name}' must set permissions.contents to 'read'"
            )
        if _normalize_permission_scope(job_permissions.get("packages")) != "write":
            failures.append(
                f"{path}: job '{job_name}' must set permissions.packages to 'write'"
            )

    for job_name in ("extract-version", "summary", "verify-required-green-gate"):
        job = jobs.get(job_name)
        if not isinstance(job, dict):
            continue
        job_permissions = job.get("permissions")
        if not isinstance(job_permissions, dict):
            continue
        pkg_scope = _normalize_permission_scope(job_permissions.get("packages"))
        if pkg_scope and pkg_scope != "none":
            failures.append(f"{path}: job '{job_name}' must not request packages scope")
    return failures


def _extract_event_tokens_from_inline_on_value(raw: str) -> set[str]:
    value = raw.strip()
    if not value:
        return set()

    if value.startswith("[") and value.endswith("]"):
        items = value[1:-1].split(",")
        return {item.strip().strip("'\"") for item in items if item.strip()}

    if value.startswith("{") and value.endswith("}"):
        return {
            match.group(1).strip()
            for match in re.finditer(r"""["']?([A-Za-z0-9_-]+)["']?\s*:""", value)
            if match.group(1).strip()
        }

    if "," in value:
        return {item.strip().strip("'\"") for item in value.split(",") if item.strip()}

    return {value.strip("'\"")}


def _extract_workflow_on_events_from_yaml(text: str) -> set[str]:
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError:
        return set()

    if not isinstance(parsed, dict):
        return set()

    on_value = parsed.get("on")
    if on_value is None:
        for key, value in parsed.items():
            if isinstance(key, str) and key.lower() == "on":
                on_value = value
                break
    if on_value is None and True in parsed:
        # PyYAML may parse the unquoted `on:` key as boolean True.
        on_value = parsed.get(True)
    if on_value is None:
        return set()

    if isinstance(on_value, str):
        return _extract_event_tokens_from_inline_on_value(on_value)
    if isinstance(on_value, list):
        return {
            str(item).strip().strip("'\"")
            for item in on_value
            if str(item).strip().strip("'\"")
        }
    if isinstance(on_value, dict):
        return {
            str(key).strip().strip("'\"")
            for key in on_value
            if str(key).strip().strip("'\"")
        }

    return set()


def _extract_workflow_on_events_from_text(text: str) -> set[str]:
    lines = text.splitlines()
    events: set[str] = set()
    i = 0

    while i < len(lines):
        line = lines[i]
        on_match = re.match(r"^(\s*)on:\s*(.*?)\s*$", line)
        if not on_match:
            i += 1
            continue

        on_indent = len(on_match.group(1))
        inline_raw = on_match.group(2).split("#", 1)[0].strip()
        if inline_raw:
            events.update(_extract_event_tokens_from_inline_on_value(inline_raw))
            i += 1
            continue

        j = i + 1
        while j < len(lines):
            candidate = lines[j]
            if not candidate.strip():
                j += 1
                continue

            candidate_indent = len(candidate) - len(candidate.lstrip(" "))
            if candidate_indent <= on_indent:
                break

            event_match = re.match(r"^\s*([A-Za-z0-9_-]+)\s*:", candidate)
            if event_match:
                events.add(event_match.group(1))
            j += 1

        i = j

    return events


def _extract_workflow_on_events(text: str) -> set[str]:
    return _extract_workflow_on_events_from_yaml(
        text
    ) | _extract_workflow_on_events_from_text(text)


def _extract_workflow_on_config(text: str) -> object:
    parsed = _load_workflow_yaml_object(text)
    on_value = parsed.get("on")
    if on_value is None:
        for key, value in parsed.items():
            if isinstance(key, str) and key.lower() == "on":
                on_value = value
                break
    if on_value is None and True in parsed:
        # PyYAML may parse the unquoted `on:` key as boolean True.
        on_value = parsed.get(True)
    return on_value


def _load_workflow_yaml_object(text: str) -> dict:
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError:
        return {}
    if isinstance(parsed, dict):
        return parsed
    return {}


def _extract_jobs_from_workflow_yaml(text: str) -> dict[str, dict]:
    parsed = _load_workflow_yaml_object(text)
    jobs = parsed.get("jobs")
    if not isinstance(jobs, dict):
        return {}
    normalized: dict[str, dict] = {}
    for name, job in jobs.items():
        if isinstance(job, dict):
            normalized[str(name)] = job
    return normalized


def _contains_secret_reference(value: object) -> bool:
    if isinstance(value, str):
        return SECRETS_REFERENCE_RE.search(value) is not None
    if isinstance(value, dict):
        return any(
            _contains_secret_reference(key) or _contains_secret_reference(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_secret_reference(item) for item in value)
    return False


def _normalize_expression(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def _contains_pull_request_secret_guard_in_if(value: object) -> bool:
    normalized = _normalize_expression(value)
    if not normalized:
        return False
    if normalized.startswith("${{") and normalized.endswith("}}"):
        normalized = _normalize_expression(normalized[3:-2].strip())
    return normalized in {
        PULL_REQUEST_SECRET_GUARD_EXPR,
        "github.event_name != 'pull_request'",
    }


def _validate_pull_request_secret_gate(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    events = _extract_workflow_on_events(text)

    if "pull_request_target" in events:
        failures.append(f"{path}: pull_request_target trigger is forbidden")

    has_pull_request_trigger = "pull_request" in events
    if not has_pull_request_trigger:
        return failures

    jobs = _extract_jobs_from_workflow_yaml(text)
    has_any_secret_reference = False
    for job_name, job in jobs.items():
        job_if = job.get("if")
        job_has_guard = _contains_pull_request_secret_guard_in_if(job_if)

        job_without_steps = {key: value for key, value in job.items() if key != "steps"}
        if _contains_secret_reference(job_without_steps):
            has_any_secret_reference = True
            if not job_has_guard:
                failures.append(
                    f"{path}: job '{job_name}' missing pull_request secret guard expression '{PULL_REQUEST_SECRET_GUARD_EXPR}' in job-level if while using secrets"
                )

        raw_steps = job.get("steps", [])
        if not isinstance(raw_steps, list):
            continue
        for idx, step in enumerate(raw_steps, start=1):
            if not isinstance(step, dict):
                continue
            if not _contains_secret_reference(step):
                continue
            has_any_secret_reference = True
            step_has_guard = _contains_pull_request_secret_guard_in_if(step.get("if"))
            if not job_has_guard and not step_has_guard:
                step_name = str(step.get("name") or f"<unnamed-step-{idx}>")
                failures.append(
                    f"{path}: step '{step_name}' in job '{job_name}' missing pull_request secret guard expression '{PULL_REQUEST_SECRET_GUARD_EXPR}' in job/step if while using secrets"
                )

    if not has_any_secret_reference:
        uncommented_text = _strip_policy_comments(text)
        if SECRETS_REFERENCE_RE.search(uncommented_text) is not None:
            failures.append(
                f"{path}: missing pull_request secret guard expression '{PULL_REQUEST_SECRET_GUARD_EXPR}'"
            )
    return failures


def _validate_claude_workflow_policy(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    if path.name != "claude.yml":
        return failures

    jobs = _extract_jobs_from_workflow_yaml(text)
    claude_job = jobs.get("claude")
    if not claude_job:
        failures.append(
            f"{path}: missing job 'claude' required by claude workflow policy"
        )
        return failures

    if_expr = _normalize_expression(
        _strip_policy_comments(str(claude_job.get("if", "")))
    )
    for token in CLAUDE_REQUIRED_IF_TOKENS:
        if _normalize_expression(token) not in if_expr:
            failures.append(
                f"{path}: claude job must enforce trusted author association token '{token}'"
            )

    permissions = claude_job.get("permissions")
    if not isinstance(permissions, dict):
        failures.append(f"{path}: claude job must declare explicit permissions mapping")
        return failures

    id_token_scope = permissions.get("id-token")
    if id_token_scope is not None and str(id_token_scope).strip().lower() != "none":
        failures.append(
            f"{path}: claude job must not request id-token permission (remove 'id-token' or set to 'none')"
        )

    return failures


def _validate_hosted_fallback_policy(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    if path.name != "hosted-fallback-autoswitch.yml":
        return failures
    jobs = _extract_jobs_from_workflow_yaml(text)
    detect_job = jobs.get("detect-and-switch")
    if not detect_job:
        failures.append(
            f"{path}: missing hosted fallback policy token 'detect-and-switch' in workflow '{path.name}'"
        )
        return failures

    if_expr = _normalize_expression(detect_job.get("if"))
    if HOSTED_FALLBACK_IF_POLICY_RE.search(if_expr) is None:
        failures.append(
            f"{path}: missing hosted fallback policy token 'github.event.workflow_run.conclusion guard' in workflow '{path.name}'"
        )

    raw_steps = detect_job.get("steps", [])
    script_bodies: list[str] = []
    if isinstance(raw_steps, list):
        for step in raw_steps:
            if not isinstance(step, dict):
                continue
            uses = str(step.get("uses", ""))
            if "actions/github-script@" not in uses:
                continue
            with_section = step.get("with")
            if isinstance(with_section, dict):
                script = with_section.get("script")
                if isinstance(script, str):
                    script_bodies.append(script)

    if not script_bodies:
        failures.append(
            f"{path}: missing hosted fallback policy token 'actions/github-script executable script' in workflow '{path.name}'"
        )
        return failures

    script_text = _strip_policy_comments("\n".join(script_bodies))
    for label, pattern in HOSTED_FALLBACK_SCRIPT_POLICY_RE:
        if pattern.search(script_text) is None:
            failures.append(
                f"{path}: missing hosted fallback policy token '{label}' in workflow '{path.name}'"
            )
    return failures


def _validate_mainline_containerization_policy(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    if path.name not in MAINLINE_CONTAINERIZED_WORKFLOWS:
        return failures

    uncommented_text = _strip_policy_comments(text)
    if REQUIRED_MAINLINE_CONTAINER_TOKEN not in uncommented_text:
        failures.append(
            f"{path}: mainline workflow '{path.name}' must invoke {REQUIRED_MAINLINE_CONTAINER_TOKEN}"
        )

    for token in FORBIDDEN_MAINLINE_SETUP_TOKENS:
        if token in uncommented_text:
            failures.append(
                f"{path}: mainline workflow '{path.name}' must not use host runtime bootstrap token '{token}'"
            )
    return failures


def _strip_policy_comments(text: str) -> str:
    """Remove YAML/JS comments so policy token checks cannot be bypassed by comments."""
    stripped_lines: list[str] = []
    in_block_comment = False

    for line in text.splitlines():
        current: list[str] = []
        in_single_quote = False
        in_double_quote = False
        i = 0
        while i < len(line):
            ch = line[i]
            nxt = line[i + 1] if i + 1 < len(line) else ""

            if in_block_comment:
                if ch == "*" and nxt == "/":
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue

            if not in_single_quote and not in_double_quote:
                if ch == "#":
                    break
                if ch == "/" and nxt == "/":
                    break
                if ch == "/" and nxt == "*":
                    in_block_comment = True
                    i += 2
                    continue
                if ch == "'":
                    in_single_quote = True
                elif ch == '"':
                    in_double_quote = True
                current.append(ch)
                i += 1
                continue

            current.append(ch)
            if ch == "'" and in_single_quote:
                in_single_quote = False
            elif ch == '"' and in_double_quote and line[i - 1] != "\\":
                in_double_quote = False
            i += 1

        stripped_lines.append("".join(current))

    return "\n".join(stripped_lines)


def _validate_single_workflow(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    failures.extend(_line_failures_for_forbidden_vars(path, text))
    failures.extend(_line_failures_for_unpinned_actions(path, text))
    failures.extend(_line_failures_for_runner_workspace_pollution(path, text))
    failures.extend(_validate_required_env_step(path, text))
    failures.extend(_validate_runner_policy(path, text))
    failures.extend(_validate_sensitive_environment_policy(path, text))
    failures.extend(_validate_workflow_run_source_policy(path, text))
    failures.extend(_validate_workflow_run_upstream_allowlist(path, text))
    failures.extend(_validate_build_dev_permission_minimization(path, text))
    failures.extend(_validate_build_release_policy(path, text))
    failures.extend(_validate_pull_request_secret_gate(path, text))
    failures.extend(_validate_claude_workflow_policy(path, text))
    failures.extend(_validate_hosted_fallback_policy(path, text))
    failures.extend(_validate_mainline_containerization_policy(path, text))

    for lineno, pattern in _extract_paths_ignore_patterns(text):
        if _is_critical_workflow(path):
            failures.append(
                f"{path}:{lineno}: paths-ignore is forbidden in critical workflow '{path.name}'"
            )
        if _is_docs_skip_pattern(pattern):
            failures.append(
                f"{path}:{lineno}: paths-ignore pattern '{pattern}' may skip docs-only governance"
            )

    for lineno, job_name, block in _iter_job_blocks(text):
        if _is_critical_workflow(path) and re.search(
            r"(?m)^\s*continue-on-error:\s*true\b", block
        ):
            failures.append(
                f"{path}:{lineno}: job-level continue-on-error: true is forbidden for job '{job_name}' in workflow '{path.name}'"
            )

    for lineno, step_name, block in _iter_step_blocks(text):
        if re.search(r"\bcontinue-on-error:\s*true\b", block):
            allowed = step_name in CONTINUE_ON_ERROR_ALLOWLIST.get(path.name, set())
            if not allowed:
                failures.append(
                    f"{path}:{lineno}: continue-on-error: true is forbidden for step '{step_name}' in workflow '{path.name}'"
                )

        if _is_critical_workflow(path) and re.search(
            r"^\s*uses:\s*.*upload-artifact@", block, re.MULTILINE
        ):
            if_no_files_found = re.search(
                r"^\s*if-no-files-found:\s*(.+?)\s*$", block, re.MULTILINE
            )
            if if_no_files_found is None:
                failures.append(
                    f"{path}:{lineno}: upload-artifact step '{step_name}' is missing explicit if-no-files-found policy in critical workflow '{path.name}'"
                )
                continue

            mode = if_no_files_found.group(1).strip().strip("'\"").lower()
            if mode != "error":
                allowed = step_name in ARTIFACT_IGNORE_ALLOWLIST.get(path.name, set())
                if not allowed:
                    failures.append(
                        f"{path}:{lineno}: upload-artifact step '{step_name}' must use if-no-files-found: error in critical workflow '{path.name}', got '{mode}'"
                    )

    return failures


def _extract_file_uri_targets(config_text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"""file://([^\s"'`<>]+)""", config_text)
    }


def _is_git_tracked(repo_root: Path, file_path: Path) -> bool:
    if not (repo_root / ".git").exists():
        return True
    try:
        relative_path = file_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return False
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "ls-files",
            "--error-unmatch",
            "--",
            relative_path,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def _validate_promptfoo_eval_file_contract(repo_root: Path = REPO_ROOT) -> list[str]:
    failures: list[str] = []
    promptfoo_dir = repo_root / "evals" / "promptfoo"
    config_path = promptfoo_dir / "promptfooconfig.yaml"
    required_files = (
        promptfoo_dir / "package.json",
        promptfoo_dir / "package-lock.json",
        config_path,
    )

    for path in required_files:
        if not path.is_file():
            failures.append(f"{path}: required promptfoo eval contract file is missing")

    if failures:
        return failures

    for path in required_files:
        if not _is_git_tracked(repo_root, path):
            failures.append(
                f"{path}: required promptfoo eval contract file is not tracked by git"
            )

    config_text = config_path.read_text(encoding="utf-8")
    missing_targets: list[str] = []
    for raw_target in sorted(_extract_file_uri_targets(config_text)):
        target_path = (promptfoo_dir / raw_target).resolve()
        try:
            target_path.relative_to(repo_root.resolve())
        except ValueError:
            failures.append(
                f"{config_path}: file:// target escapes repository root: {raw_target}"
            )
            continue
        if not target_path.exists():
            missing_targets.append(raw_target)
            continue
        if not _is_git_tracked(repo_root, target_path):
            failures.append(
                f"{config_path}: referenced file:// target is not tracked by git: {raw_target}"
            )

    for target in missing_targets:
        failures.append(
            f"{config_path}: referenced file:// target does not exist: {target}"
        )

    return failures


def main() -> int:
    failures: list[str] = []
    workflow_files = sorted(
        [*WORKFLOWS_DIR.glob("*.yml"), *WORKFLOWS_DIR.glob("*.yaml")]
    )

    for path in workflow_files:
        text = path.read_text(encoding="utf-8")
        failures.extend(_validate_single_workflow(path, text))
    failures.extend(_validate_promptfoo_eval_file_contract())

    if failures:
        print("FAIL [WORKFLOW-POLICY-001]: CI workflow policy violations found.")
        for item in failures:
            print(f"- {item}")
        return 1

    print(
        "PASS [WORKFLOW-POLICY-001]: workflow policy checks passed "
        "(no bypass vars, all external actions pinned to commit SHA, no pull_request_target and guarded pull_request secrets, "
        "PR jobs pinned to hosted-safe runner routing, claude workflow restricted to trusted associations without id-token, "
        "strict workflow_run upstream allowlists, build-dev/build-and-release least-privilege package permissions, "
        "build-and-release required-green-gate provenance + trusted-branch source-sha verification, "
        "no paths-ignore in critical workflows, no unsafe step/job continue-on-error, "
        "explicit strict artifact upload policy in critical workflows, strict env gates, runner routing contracts, "
        "and promptfoo eval file contract)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
