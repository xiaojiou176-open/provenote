from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "tooling/scripts/ci/check_first_party_file_length.py"
)


def _write_lines(path: Path, line_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join([f"line_{index}" for index in range(line_count)])
    path.write_text(content + "\n", encoding="utf-8")


def _run_guard(
    repo_root: Path, config: dict[str, object]
) -> subprocess.CompletedProcess[str]:
    config_path = repo_root / "length_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            "--config",
            str(config_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_file_length_guard_fails_on_global_limit_breach(tmp_path: Path) -> None:
    _write_lines(tmp_path / "services/api/oversized.py", 801)
    config = {
        "global_max_lines": 800,
        "warning_threshold": 700,
        "roots": ["services"],
        "extensions": [".py"],
        "exclude_globs": [],
        "frozen_file_max_lines": {},
    }

    result = _run_guard(tmp_path, config)

    assert result.returncode == 1
    assert "FAIL [FILE-LEN-001]" in result.stdout
    assert "services/api/oversized.py: 801" in result.stdout


def test_file_length_guard_fails_when_frozen_file_grows(tmp_path: Path) -> None:
    _write_lines(tmp_path / "packages/core/application/models.py", 11)
    config = {
        "global_max_lines": 800,
        "warning_threshold": 700,
        "roots": ["services", "packages"],
        "extensions": [".py"],
        "exclude_globs": [],
        "frozen_file_max_lines": {"packages/core/application/models.py": 10},
    }

    result = _run_guard(tmp_path, config)

    assert result.returncode == 1
    assert "FAIL [FILE-LEN-002]" in result.stdout
    assert "packages/core/application/models.py: 11 > 10" in result.stdout


def test_file_length_guard_ignores_excluded_generated_file(tmp_path: Path) -> None:
    _write_lines(tmp_path / "services/api/generated_pb2.py", 1200)
    _write_lines(tmp_path / "services/api/normal.py", 12)
    config = {
        "global_max_lines": 800,
        "warning_threshold": 700,
        "roots": ["services"],
        "extensions": [".py"],
        "exclude_globs": ["**/*_pb2.py"],
        "frozen_file_max_lines": {},
    }

    result = _run_guard(tmp_path, config)

    assert result.returncode == 0
    assert "PASS: first-party file length guard passed." in result.stdout
    assert "generated_pb2.py" not in result.stdout


def test_file_length_guard_allows_frozen_file_at_cap_above_global_limit(
    tmp_path: Path,
) -> None:
    _write_lines(tmp_path / "packages/core/application/models.py", 11)
    config = {
        "global_max_lines": 10,
        "warning_threshold": 7,
        "roots": ["packages"],
        "extensions": [".py"],
        "exclude_globs": [],
        "frozen_file_max_lines": {"packages/core/application/models.py": 11},
    }

    result = _run_guard(tmp_path, config)

    assert result.returncode == 0
    assert "PASS: first-party file length guard passed." in result.stdout
