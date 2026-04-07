from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_GUARD = REPO_ROOT / "tooling/scripts/ci/check_docs_change_guard.sh"
COMMIT_RANGE_GUARD = REPO_ROOT / "tooling/scripts/ci/check_commit_message_range.sh"
UIUX_GATE = REPO_ROOT / "tooling/scripts/ci/run_uiux_gemini_gate.py"


def _run(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=merged_env,
        text=True,
        capture_output=True,
        check=False,
    )


def _init_temp_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()

    assert _run(["git", "init", "-b", "main"], cwd=repo).returncode == 0
    assert (
        _run(["git", "config", "user.name", "CI Guard Test"], cwd=repo).returncode == 0
    )
    assert (
        _run(
            ["git", "config", "user.email", "ci-guard-test@example.com"], cwd=repo
        ).returncode
        == 0
    )

    scripts_ci = repo / "tooling" / "scripts" / "ci"
    scripts_ci.mkdir(parents=True)
    (scripts_ci / "check_commit_message_range.sh").write_text(
        COMMIT_RANGE_GUARD.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (scripts_ci / "commit_governance_lib.sh").write_text(
        (REPO_ROOT / "tooling/scripts/ci/commit_governance_lib.sh").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )

    tracked_file = repo / "README.md"
    tracked_file.write_text("seed\n", encoding="utf-8")
    assert (
        _run(
            [
                "git",
                "add",
                "README.md",
                "tooling/scripts/ci/check_commit_message_range.sh",
                "tooling/scripts/ci/commit_governance_lib.sh",
            ],
            cwd=repo,
        ).returncode
        == 0
    )
    assert (
        _run(["git", "commit", "-m", "feat(ci): seed temp repo"], cwd=repo).returncode
        == 0
    )
    assert (
        _run(["git", "checkout", "-b", "feature/ci-gate-test"], cwd=repo).returncode
        == 0
    )
    (repo / "feature.txt").write_text("feature-commit\n", encoding="utf-8")
    assert _run(["git", "add", "feature.txt"], cwd=repo).returncode == 0
    assert (
        _run(
            ["git", "commit", "-m", "ci: feature commit for range"], cwd=repo
        ).returncode
        == 0
    )

    baseline_file = scripts_ci / "commit_governance_baseline.txt"
    head = _run(["git", "rev-parse", "HEAD"], cwd=repo)
    assert head.returncode == 0
    baseline_file.write_text(head.stdout.strip() + "\n", encoding="utf-8")
    return repo


def test_docs_change_guard_forbids_skip_var_in_ci_and_allows_local_skip() -> None:
    ci_fail = _run(
        ["bash", str(DOCS_GUARD), "--mode", "pre-push"],
        cwd=REPO_ROOT,
        env={"CI": "true", "SKIP_DOCS_CHANGE_GUARD": "1"},
    )
    assert ci_fail.returncode == 1
    assert "SKIP_DOCS_CHANGE_GUARD is forbidden in CI" in ci_fail.stdout

    local_skip = _run(
        ["bash", str(DOCS_GUARD), "--mode", "pre-push"],
        cwd=REPO_ROOT,
        env={"CI": "", "GITHUB_ACTIONS": "", "SKIP_DOCS_CHANGE_GUARD": "1"},
    )
    assert local_skip.returncode == 0
    assert "skipped via SKIP_DOCS_CHANGE_GUARD=1" in local_skip.stdout


def test_commit_range_guard_fails_in_ci_when_checked_is_zero(tmp_path: Path) -> None:
    repo = _init_temp_git_repo(tmp_path)
    script = repo / "tooling" / "scripts" / "ci" / "check_commit_message_range.sh"

    ci_run = _run(
        ["bash", str(script)],
        cwd=repo,
        env={
            "CI": "true",
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_EVENT_BEFORE": "0000000000000000000000000000000000000000",
        },
    )
    assert ci_run.returncode == 1
    assert "FAIL: no enforceable commits after baseline in CI" in ci_run.stdout

    local_run = _run(
        ["bash", str(script)],
        cwd=repo,
        env={"CI": "", "GITHUB_ACTIONS": ""},
    )
    assert local_run.returncode == 0
    assert "skip: no commits after baseline" in local_run.stdout


def test_commit_range_guard_ignores_synthetic_pull_request_merge_commit(
    tmp_path: Path,
) -> None:
    repo = _init_temp_git_repo(tmp_path)
    script = repo / "tooling" / "scripts" / "ci" / "check_commit_message_range.sh"
    baseline_file = (
        repo / "tooling" / "scripts" / "ci" / "commit_governance_baseline.txt"
    )

    main_sha = _run(["git", "rev-parse", "main"], cwd=repo)
    assert main_sha.returncode == 0
    baseline_file.write_text(main_sha.stdout.strip() + "\n", encoding="utf-8")

    assert (
        _run(["git", "checkout", "-b", "pr-merge-view", "main"], cwd=repo).returncode
        == 0
    )
    merge_commit = _run(
        [
            "git",
            "merge",
            "--no-ff",
            "feature/ci-gate-test",
            "-m",
            "Merge pull request #1 from feature/ci-gate-test",
        ],
        cwd=repo,
    )
    assert merge_commit.returncode == 0, merge_commit.stdout + merge_commit.stderr

    ci_run = _run(
        ["bash", str(script)],
        cwd=repo,
        env={
            "CI": "true",
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_BASE_REF": "main",
            "GITHUB_HEAD_REF": "feature/ci-gate-test",
        },
    )
    assert ci_run.returncode == 0, ci_run.stdout + ci_run.stderr
    assert "PASS:" in ci_run.stdout


def test_uiux_gate_blocks_legacy_auto_generate_by_default(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    evaluator = tmp_path / "evaluator.json"

    blocked = _run(
        [
            sys.executable,
            str(UIUX_GATE),
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--auto-generate",
        ],
        cwd=REPO_ROOT,
    )
    assert blocked.returncode == 2
    assert "FAIL [UIUX-GATE-TRUST-000]" in blocked.stdout

    report_dir = tmp_path / "playwright-report"
    results_dir = tmp_path / "test-results"
    report_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    (report_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    (results_dir / "trace.zip").write_text("zip", encoding="utf-8")
    (results_dir / "screenshot.png").write_text("png", encoding="utf-8")
    (results_dir / "results.json").write_text("{}", encoding="utf-8")

    allowed = _run(
        [
            sys.executable,
            str(UIUX_GATE),
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--auto-generate",
            "--allow-legacy-auto-generate",
            "--allow-deterministic-fallback",
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
        ],
        cwd=REPO_ROOT,
    )
    assert allowed.returncode == 1
    assert "DEGRADED [UIUX-GATE-002]" in allowed.stdout
