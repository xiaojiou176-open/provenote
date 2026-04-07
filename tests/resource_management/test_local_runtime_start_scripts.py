from __future__ import annotations

import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
START_SCRIPTS = (
    ROOT_DIR / "tooling/scripts/dev/start_api_local.sh",
    ROOT_DIR / "tooling/scripts/dev/start_frontend_local.sh",
    ROOT_DIR / "tooling/scripts/dev/start_surreal_local.sh",
    ROOT_DIR / "tooling/scripts/dev/start_worker_local.sh",
)


def test_start_scripts_fail_closed_on_unsafe_pid_record() -> None:
    for script_path in START_SCRIPTS:
        content = script_path.read_text(encoding="utf-8")
        assert 'if safe_process_prepare_pid_file "${PID_FILE}"; then' in content
        assert "existing_state=0" in content
        assert "else" in content
        assert "existing_state=$?" in content
        assert 'if [[ "${existing_state}" -eq 2 ]]; then' in content


def test_shell_if_compound_would_hide_unsafe_exit_code() -> None:
    result = subprocess.run(
        [
            "bash",
            "-lc",
            'if (exit 2); then :; fi; echo "$?"',
        ],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "0"
