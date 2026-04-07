from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_MD = REPO_ROOT / "AGENTS.md"
ALLOWED_TRACKED_AGENTS_PREFIXES = (
    ".agents/Tasks/TASK_BOARD-provenote-full-rollout.md",
    ".agents/Plans/2026-",
)


def _git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_agents_doc_records_tracked_agents_exceptions() -> None:
    text = AGENTS_MD.read_text(encoding="utf-8")
    assert "Current tracked exceptions under `.agents/` are intentional" in text
    assert ".agents/Tasks/TASK_BOARD-provenote-full-rollout.md" in text
    assert "tracked `.agents/Plans/2026-*.md`" in text


def test_tracked_agents_files_stay_within_documented_exception_set() -> None:
    tracked = _git_lines("ls-files", ".agents")
    assert tracked, "expected the current tracked .agents exception set to exist"
    unexpected = [
        path
        for path in tracked
        if not any(
            path.startswith(prefix) for prefix in ALLOWED_TRACKED_AGENTS_PREFIXES
        )
    ]
    assert not unexpected, (
        "tracked .agents files must stay inside the documented exception set; "
        f"unexpected paths: {unexpected}"
    )


def test_untracked_agents_files_remain_ignored_by_default() -> None:
    probe = REPO_ROOT / ".agents" / "tmp-ignore-probe.md"
    try:
        probe.write_text("ignore probe\n", encoding="utf-8")
        result = subprocess.run(
            [
                "git",
                "check-ignore",
                "--verbose",
                "--",
                str(probe.relative_to(REPO_ROOT)),
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        probe.unlink(missing_ok=True)

    assert ".gitignore:" in result.stdout
    assert ":.agents/" in result.stdout
