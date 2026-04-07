from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_english_runtime_boundary_guard_passes_for_current_repo_state() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tooling/scripts/ci/check_english_runtime_boundary.py"),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
