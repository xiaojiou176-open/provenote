from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_supervisor_log_path_guard_is_nested_under_log_contract() -> None:
    log_contract = (REPO_ROOT / "tooling/scripts/ci/check_log_contract.py").read_text(
        encoding="utf-8"
    )
    assert "check_supervisor_log_path.py" in log_contract


def test_supervisor_log_path_guard_passes_for_current_repo_state() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tooling/scripts/ci/check_supervisor_log_path.py"),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout or result.stderr
