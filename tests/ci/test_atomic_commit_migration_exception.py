from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SCRIPT_RELATIVE_PATHS = (
    "tooling/scripts/ci/check_atomic_commit_scope.sh",
    "tooling/scripts/ci/check_atomic_commit_scope_range.sh",
    "tooling/scripts/ci/commit_governance_lib.sh",
    "config/ci/atomic-commit-exceptions.json",
    "docs/development.md",
)

FINAL_CLOSURE_EXCEPTION_PATHS = (
    ".github/workflows/uiux-gemini-gate.yml",
    "docs/development.md",
    "tests/ci/test_atomic_commit_migration_exception.py",
    "tests/ci/test_consistent_container_contract.py",
    "tooling/scripts/ci/check_mutation_guard.py",
    "tooling/scripts/ci/run_in_consistent_container.sh",
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(
    repo: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=repo,
        text=True,
        capture_output=True,
        check=check,
    )


def _local_git_env(**overrides: str) -> dict[str, str]:
    env = {
        **os.environ,
        "CI": "",
        "GITHUB_ACTIONS": "",
        "GITHUB_BASE_REF": "",
        "GITHUB_EVENT_NAME": "",
        "GITHUB_HEAD_REF": "",
        "GITHUB_REF": "",
        "GITHUB_REF_NAME": "",
    }
    env.update(overrides)
    return env


def _setup_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "git", "init", "-b", "main")
    _run(repo, "git", "config", "user.name", "Codex Test")
    _run(repo, "git", "config", "user.email", "codex@example.com")
    _run(repo, "git", "commit", "--allow-empty", "-m", "chore: bootstrap")

    for rel_path in SCRIPT_RELATIVE_PATHS:
        target = repo / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            (REPO_ROOT / rel_path).read_text(encoding="utf-8"), encoding="utf-8"
        )

    _run(repo, "git", "checkout", "-b", "codex/hard-cut-governance-final")
    return repo


def _setup_final_closure_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "git", "init", "-b", "main")
    _run(repo, "git", "config", "user.name", "Codex Test")
    _run(repo, "git", "config", "user.email", "codex@example.com")
    _run(repo, "git", "commit", "--allow-empty", "-m", "chore: bootstrap")

    for rel_path in (*SCRIPT_RELATIVE_PATHS, *FINAL_CLOSURE_EXCEPTION_PATHS):
        target = repo / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            (REPO_ROOT / rel_path).read_text(encoding="utf-8"), encoding="utf-8"
        )

    _run(repo, "git", "add", ".")
    _run(repo, "git", "commit", "-m", "chore: seed governance baseline")
    _run(repo, "git", "checkout", "-b", "codex/final-closure-exec")
    return repo


def _stage_large_migration(repo: Path) -> None:
    payload_paths = (
        "apps/web/a.txt",
        "apps/web/b.txt",
        "apps/web/c.txt",
        "apps/web/d.txt",
        "apps/web/e.txt",
        "apps/web/f.txt",
        "packages/core/a.py",
        "packages/core/b.py",
        "packages/core/c.py",
        "packages/core/d.py",
        "packages/core/e.py",
        "packages/core/f.py",
        "services/api/a.py",
        "services/api/b.py",
        "services/api/c.py",
        "services/api/d.py",
        "services/api/e.py",
        "services/api/f.py",
        "tests/ci/a.txt",
        "tests/ci/b.txt",
        "tests/ci/c.txt",
    )
    for rel_path in payload_paths:
        _write(repo / rel_path, f"{rel_path}\n")

    _run(repo, "git", "add", ".")


def _stage_final_closure_exception(repo: Path) -> None:
    for rel_path in FINAL_CLOSURE_EXCEPTION_PATHS:
        target = repo / rel_path
        target.write_text(
            target.read_text(encoding="utf-8") + "\n# final closure touch\n",
            encoding="utf-8",
        )
    _run(repo, "git", "add", ".")


def test_staged_atomic_guard_allows_audited_migration_exception(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _stage_large_migration(repo)

    completed = subprocess.run(
        ["bash", "tooling/scripts/ci/check_atomic_commit_scope.sh"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env=_local_git_env(ATOMIC_COMMIT_ENFORCE="1"),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "ALLOW: audited migration exception" in completed.stdout


def test_staged_atomic_guard_rejects_large_batch_outside_migration_branch(
    tmp_path: Path,
) -> None:
    repo = _setup_repo(tmp_path)
    _run(repo, "git", "checkout", "main")
    _stage_large_migration(repo)

    completed = subprocess.run(
        ["bash", "tooling/scripts/ci/check_atomic_commit_scope.sh"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env=_local_git_env(ATOMIC_COMMIT_ENFORCE="1"),
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert "ENFORCED: blocking commit" in completed.stdout


def test_atomic_commit_range_allows_registered_migration_commit(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _stage_large_migration(repo)
    _run(
        repo,
        "git",
        "commit",
        "-m",
        "refactor(batch-01/repo-hard-cut): migrate to governed apps services packages topology",
    )

    completed = subprocess.run(
        ["bash", "tooling/scripts/ci/check_atomic_commit_scope_range.sh"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env=_local_git_env(COMMIT_GOVERNANCE_BASELINE_SHA="HEAD~1"),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "ALLOW:" in completed.stdout


def test_atomic_commit_range_uses_github_head_ref_for_audited_exception_in_detached_ci(
    tmp_path: Path,
) -> None:
    repo = _setup_final_closure_repo(tmp_path)
    _stage_final_closure_exception(repo)
    _run(repo, "git", "commit", "-m", "fix(ci): unblock final closure gates")
    _run(repo, "git", "checkout", "--detach", "HEAD")

    completed = subprocess.run(
        ["bash", "tooling/scripts/ci/check_atomic_commit_scope_range.sh"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "CI": "true",
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_BASE_REF": "main",
            "GITHUB_HEAD_REF": "codex/final-closure-exec",
        },
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "ALLOW:" in completed.stdout


def test_atomic_commit_range_skips_empty_set_only_for_external_fast_gate(
    tmp_path: Path,
) -> None:
    repo = _setup_repo(tmp_path)
    baseline_file = repo / "tooling/scripts/ci/commit_governance_baseline.txt"
    head_sha = _run(repo, "git", "rev-parse", "HEAD").stdout.strip()
    baseline_file.write_text(head_sha + "\n", encoding="utf-8")

    completed = subprocess.run(
        ["bash", "tooling/scripts/ci/check_atomic_commit_scope_range.sh"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "CI": "true",
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_BASE_REF": "main",
            "GITHUB_HEAD_REF": "dependabot/npm_and_yarn/example-1.2.3",
            "OPEN_NOTEBOOK_EXTERNAL_PR_FAST_GATE": "1",
        },
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (
        "skip: no enforceable commits visible in external pull_request fast gate."
        in completed.stdout
    )
