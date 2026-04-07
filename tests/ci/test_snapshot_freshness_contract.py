from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_snapshot_freshness_guard_exists() -> None:
    assert (REPO_ROOT / "tooling/scripts/ci/check_snapshot_freshness.py").exists()


def test_snapshot_freshness_guard_passes_on_current_repo_state() -> None:
    result = subprocess.run(
        ["python3", "tooling/scripts/ci/check_snapshot_freshness.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS:" in result.stdout
