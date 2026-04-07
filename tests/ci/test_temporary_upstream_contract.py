from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SCRIPT_RELATIVE_PATHS = (
    "tooling/scripts/ci/check_upstream_drift.sh",
    "tooling/scripts/ci/check_selective_port_ledger.py",
    "tooling/scripts/git/temporary_upstream_ref.sh",
)

MAINTAINER_NAME = "Repo Maintainer"
MAINTAINER_EMAIL = "maintainer@example.test"


def _run(
    cwd: Path,
    *args: str,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = None if env is None else {**os.environ, **env}
    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=check,
        env=merged_env,
    )


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run(cwd, "git", *args, check=check)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _commit(repo: Path, message: str, filename: str, content: str) -> str:
    _write(repo / filename, content)
    _git(repo, "add", filename)
    env = {
        "GIT_AUTHOR_NAME": MAINTAINER_NAME,
        "GIT_AUTHOR_EMAIL": MAINTAINER_EMAIL,
        "GIT_COMMITTER_NAME": MAINTAINER_NAME,
        "GIT_COMMITTER_EMAIL": MAINTAINER_EMAIL,
    }
    _run(repo, "git", "commit", "-m", message, env=env)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _copy_scripts(repo: Path) -> None:
    for rel_path in SCRIPT_RELATIVE_PATHS:
        target = repo / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            (REPO_ROOT / rel_path).read_text(encoding="utf-8"), encoding="utf-8"
        )


def _assert_no_temp_upstream_refs(repo: Path) -> None:
    refs = _git(
        repo,
        "for-each-ref",
        "--format=%(refname)",
        "refs/open-notebook/upstream-cache",
    ).stdout.strip()
    assert refs == ""


def _setup_origin_and_upstream(tmp_path: Path) -> tuple[Path, Path, str]:
    upstream_repo = tmp_path / "upstream"
    origin_bare = tmp_path / "origin.git"
    work_repo = tmp_path / "work"

    upstream_repo.mkdir()
    _git(upstream_repo, "init", "-b", "main")
    _git(upstream_repo, "config", "user.name", MAINTAINER_NAME)
    _git(upstream_repo, "config", "user.email", MAINTAINER_EMAIL)
    base_sha = _commit(
        upstream_repo,
        "feat(upstream): seed upstream base",
        "README.md",
        "base\n",
    )

    _git(tmp_path, "clone", "--bare", str(upstream_repo), str(origin_bare))
    _git(tmp_path, "clone", str(origin_bare), str(work_repo))
    _copy_scripts(work_repo)

    _commit(
        upstream_repo,
        "feat(upstream): move upstream ahead",
        "UPSTREAM_ONLY.md",
        "ahead\n",
    )

    return work_repo, upstream_repo, base_sha[:7]


def test_check_upstream_drift_uses_temporary_upstream_ref_when_remote_is_absent(
    tmp_path: Path,
) -> None:
    work_repo, upstream_repo, _ = _setup_origin_and_upstream(tmp_path)

    completed = _run(
        work_repo,
        "bash",
        "tooling/scripts/ci/check_upstream_drift.sh",
        "--branch",
        "main",
        check=False,
        env={"OPEN_NOTEBOOK_UPSTREAM_URL": str(upstream_repo)},
    )

    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert (
        "DRIFT: origin/main is behind upstream/main by 1 commit(s)." in completed.stdout
    )
    assert _git(work_repo, "remote", "get-url", "upstream", check=False).returncode != 0
    assert (
        _git(
            work_repo,
            "show-ref",
            "--verify",
            "--quiet",
            "refs/remotes/upstream/main",
            check=False,
        ).returncode
        != 0
    )
    _assert_no_temp_upstream_refs(work_repo)


def test_selective_port_ledger_can_validate_with_on_demand_upstream_ref(
    tmp_path: Path,
) -> None:
    work_repo, upstream_repo, base_short = _setup_origin_and_upstream(tmp_path)

    observed_at = "2026-03-28T00:00:00Z"
    refresh_after = "2026-03-30T00:00:00Z"

    ledger = {
        "policy_mode": "selective-port-first",
        "merge_rebase_default": False,
        "allowed_sync_strategies": ["selective-port"],
        "freshness_policy": {
            "max_snapshot_age_hours": 48,
            "required_entry_fields": [
                "observed_at_utc",
                "refresh_required_after_utc",
                "snapshot_scope",
                "current_truth_boundary",
            ],
            "refresh_cadence": "manual",
            "stale_snapshot_rule": "refresh before citing counts",
            "missing_metadata_rule": "missing freshness metadata is invalid",
        },
        "live_git_truth": {
            "observed_at_utc": observed_at,
            "refresh_required_after_utc": refresh_after,
            "snapshot_scope": ["origin_upstream_ref_comparison"],
            "current_truth_boundary": "Current truth is origin/main versus upstream/main.",
            "origin_ref": "origin/main",
            "upstream_ref": "upstream/main",
            "origin_only_commits": 0,
            "upstream_only_commits": 1,
            "has_merge_base": True,
            "root_commits": [base_short, base_short],
        },
        "entries": [
            {
                "id": "sample-entry",
                "observed_at_utc": observed_at,
                "refresh_required_after_utc": refresh_after,
                "snapshot_scope": ["historical-batch"],
                "current_truth_boundary": "Historical planning context only.",
                "recommended_strategy": "selective-port",
                "clusters": [
                    {
                        "topic": "sample",
                        "commits": ["abcdef1"],
                        "surface": "docs",
                        "recommended_strategy": "selective-port",
                        "reason": "exercise the validator contract",
                    }
                ],
            }
        ],
    }
    mapping = {
        "freshness": {
            "max_snapshot_age_hours": 48,
            "observed_at_utc": observed_at,
            "refresh_required_after_utc": refresh_after,
            "snapshot_scope": ["podcasts-topology"],
            "current_truth_boundary": "Mapping freshness is current through the declared window.",
        }
    }

    _write(
        work_repo / "config/upstream/selective-port-ledger.json",
        json.dumps(ledger, indent=2) + "\n",
    )
    _write(
        work_repo / "config/upstream/podcasts-topology-mapping.json",
        json.dumps(mapping, indent=2) + "\n",
    )
    _write(
        work_repo / "docs/development.md",
        "\n".join(
            [
                "# Development",
                "This repo uses selective-port-first upstream maintenance.",
                "Freshness matters for current topology truth.",
                "The selective port SOP cites observed_at_utc explicitly.",
            ]
        )
        + "\n",
    )

    completed = _run(
        work_repo,
        "python3",
        "tooling/scripts/ci/check_selective_port_ledger.py",
        "--now-utc",
        "2026-03-28T12:00:00Z",
        check=False,
        env={"OPEN_NOTEBOOK_UPSTREAM_URL": str(upstream_repo)},
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS:" in completed.stdout
    assert _git(work_repo, "remote", "get-url", "upstream", check=False).returncode != 0
    _assert_no_temp_upstream_refs(work_repo)
