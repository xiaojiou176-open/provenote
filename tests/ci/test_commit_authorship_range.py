from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SCRIPT_RELATIVE_PATHS = (
    "tooling/scripts/ci/check_commit_authorship_range.sh",
    "tooling/scripts/ci/commit_governance_lib.sh",
)

MAINTAINER_NAME = "Repo Maintainer"
MAINTAINER_EMAIL = "maintainer@example.test"
DEPENDABOT_NAME = "dependabot[bot]"
DEPENDABOT_EMAIL = "49699333+dependabot[bot]@users.noreply.github.com"


def _run(
    repo: Path,
    *args: str,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        args,
        cwd=repo,
        text=True,
        capture_output=True,
        check=check,
        env=merged_env,
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _commit(
    repo: Path,
    *,
    subject: str,
    body: str = "",
    author_name: str,
    author_email: str,
    committer_name: str | None = None,
    committer_email: str | None = None,
) -> None:
    env = {
        "GIT_AUTHOR_NAME": author_name,
        "GIT_AUTHOR_EMAIL": author_email,
        "GIT_COMMITTER_NAME": committer_name or author_name,
        "GIT_COMMITTER_EMAIL": committer_email or author_email,
    }
    _run(repo, "git", "commit", "--allow-empty", "-m", subject, "-m", body, env=env)


def _setup_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "git", "init", "-b", "main")
    _run(repo, "git", "config", "user.name", MAINTAINER_NAME)
    _run(repo, "git", "config", "user.email", MAINTAINER_EMAIL)

    for rel_path in SCRIPT_RELATIVE_PATHS:
        target = repo / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            (REPO_ROOT / rel_path).read_text(encoding="utf-8"), encoding="utf-8"
        )

    _commit(
        repo,
        subject="feat(ci): seed authorship baseline",
        author_name=MAINTAINER_NAME,
        author_email=MAINTAINER_EMAIL,
    )

    baseline = _run(repo, "git", "rev-parse", "HEAD").stdout.strip()
    _write(repo / "tooling/scripts/ci/commit_governance_baseline.txt", baseline + "\n")
    _run(repo, "git", "checkout", "-b", "feature/authorship-guard")
    return repo


def _local_env() -> dict[str, str]:
    return {
        "CI": "",
        "GITHUB_ACTIONS": "",
        "GITHUB_EVENT_NAME": "",
        "GITHUB_BASE_REF": "",
        "GITHUB_HEAD_REF": "",
        "GITHUB_REF": "",
        "GITHUB_REF_NAME": "",
    }


def test_commit_authorship_guard_allows_configured_maintainer_identity(
    tmp_path: Path,
) -> None:
    repo = _setup_repo(tmp_path)
    _commit(
        repo,
        subject="fix(ci): keep maintainer authorship canonical",
        author_name=MAINTAINER_NAME,
        author_email=MAINTAINER_EMAIL,
    )

    completed = _run(
        repo,
        "bash",
        "tooling/scripts/ci/check_commit_authorship_range.sh",
        check=False,
        env=_local_env(),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS:" in completed.stdout


def test_commit_authorship_guard_allows_dependabot_exception(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _commit(
        repo,
        subject="chore(deps): allow dependabot bot exception",
        author_name=DEPENDABOT_NAME,
        author_email=DEPENDABOT_EMAIL,
    )

    completed = _run(
        repo,
        "bash",
        "tooling/scripts/ci/check_commit_authorship_range.sh",
        check=False,
        env=_local_env(),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS:" in completed.stdout


def test_commit_authorship_guard_rejects_codex_author(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    _commit(
        repo,
        subject="fix(ci): reject codex author",
        author_name="Codex",
        author_email="codex@example.com",
    )

    completed = _run(
        repo,
        "bash",
        "tooling/scripts/ci/check_commit_authorship_range.sh",
        check=False,
        env=_local_env(),
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert "disallowed author Codex <codex@example.com>" in completed.stdout


def test_commit_authorship_guard_rejects_non_maintainer_coauthor(
    tmp_path: Path,
) -> None:
    repo = _setup_repo(tmp_path)
    _commit(
        repo,
        subject="fix(ci): reject extra coauthor",
        body="Co-authored-by: Codex <codex@example.com>",
        author_name=MAINTAINER_NAME,
        author_email=MAINTAINER_EMAIL,
    )

    completed = _run(
        repo,
        "bash",
        "tooling/scripts/ci/check_commit_authorship_range.sh",
        check=False,
        env=_local_env(),
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert (
        "co-author trailer must stay on the configured maintainer identity"
        in completed.stdout
    )


def test_commit_authorship_guard_accepts_lowercase_coauthor_trailer(
    tmp_path: Path,
) -> None:
    repo = _setup_repo(tmp_path)
    _commit(
        repo,
        subject="fix(ci): accept lowercase maintainer coauthor trailer",
        body=f"co-authored-by: {MAINTAINER_NAME} <{MAINTAINER_EMAIL}>",
        author_name=MAINTAINER_NAME,
        author_email=MAINTAINER_EMAIL,
    )

    completed = _run(
        repo,
        "bash",
        "tooling/scripts/ci/check_commit_authorship_range.sh",
        check=False,
        env=_local_env(),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS:" in completed.stdout


def test_commit_authorship_guard_ignores_synthetic_pull_request_merge_commit(
    tmp_path: Path,
) -> None:
    repo = _setup_repo(tmp_path)
    baseline_file = repo / "tooling/scripts/ci/commit_governance_baseline.txt"
    main_sha = _run(repo, "git", "rev-parse", "main").stdout.strip()
    baseline_file.write_text(main_sha + "\n", encoding="utf-8")

    _commit(
        repo,
        subject="fix(ci): keep pr authorship scoped to feature head",
        author_name=MAINTAINER_NAME,
        author_email=MAINTAINER_EMAIL,
    )

    _run(repo, "git", "checkout", "-b", "pr-merge-view", "main")
    merge_env = {
        "GIT_AUTHOR_NAME": "GitHub",
        "GIT_AUTHOR_EMAIL": "noreply@github.com",
        "GIT_COMMITTER_NAME": "GitHub",
        "GIT_COMMITTER_EMAIL": "noreply@github.com",
    }
    merged = _run(
        repo,
        "git",
        "merge",
        "--no-ff",
        "feature/authorship-guard",
        "-m",
        "Merge pull request #1 from feature/authorship-guard",
        check=False,
        env=merge_env,
    )
    assert merged.returncode == 0, merged.stdout + merged.stderr

    completed = _run(
        repo,
        "bash",
        "tooling/scripts/ci/check_commit_authorship_range.sh",
        check=False,
        env={
            **_local_env(),
            "CI": "true",
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_BASE_REF": "main",
            "GITHUB_HEAD_REF": "feature/authorship-guard",
        },
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS:" in completed.stdout


def test_commit_authorship_guard_skips_when_ci_pull_request_only_sees_merge_ref(
    tmp_path: Path,
) -> None:
    repo = _setup_repo(tmp_path)
    _commit(
        repo,
        subject="chore(deps): allow dependabot bot exception",
        author_name=DEPENDABOT_NAME,
        author_email=DEPENDABOT_EMAIL,
    )

    _run(repo, "git", "checkout", "-b", "pr-merge-view", "main")
    merge_env = {
        "GIT_AUTHOR_NAME": "GitHub",
        "GIT_AUTHOR_EMAIL": "noreply@github.com",
        "GIT_COMMITTER_NAME": "GitHub",
        "GIT_COMMITTER_EMAIL": "noreply@github.com",
    }
    merged = _run(
        repo,
        "git",
        "merge",
        "--no-ff",
        "feature/authorship-guard",
        "-m",
        "Merge pull request #1 from dependabot/npm_and_yarn/example-1.2.3",
        check=False,
        env=merge_env,
    )
    assert merged.returncode == 0, merged.stdout + merged.stderr

    baseline_file = repo / "tooling/scripts/ci/commit_governance_baseline.txt"
    head_sha = _run(repo, "git", "rev-parse", "HEAD").stdout.strip()
    baseline_file.write_text(head_sha + "\n", encoding="utf-8")
    _run(repo, "git", "checkout", "--detach", head_sha)
    _run(repo, "git", "branch", "-D", "main")
    _run(repo, "git", "branch", "-D", "feature/authorship-guard")
    _run(repo, "git", "branch", "-D", "pr-merge-view")

    completed = _run(
        repo,
        "bash",
        "tooling/scripts/ci/check_commit_authorship_range.sh",
        check=False,
        env={
            **_local_env(),
            "CI": "true",
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_BASE_REF": "main",
            "GITHUB_HEAD_REF": "dependabot/npm_and_yarn/example-1.2.3",
            "OPEN_NOTEBOOK_EXTERNAL_PR_FAST_GATE": "1",
        },
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "FAIL:" not in completed.stdout
    assert "PASS:" in completed.stdout or "skip:" in completed.stdout


def test_commit_governance_lib_skips_empty_commit_set_only_for_external_fast_gate() -> (
    None
):
    completed = _run(
        REPO_ROOT,
        "bash",
        "-lc",
        "source tooling/scripts/ci/commit_governance_lib.sh && report_empty_enforceable_commit_set 'commit-authorship-range' HEAD deadbeef 1 1",
        check=False,
        env={
            **os.environ,
            "CI": "true",
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_BASE_REF": "main",
            "OPEN_NOTEBOOK_EXTERNAL_PR_FAST_GATE": "1",
        },
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (
        "skip: no enforceable commits visible in external pull_request fast gate."
        in completed.stdout
    )
