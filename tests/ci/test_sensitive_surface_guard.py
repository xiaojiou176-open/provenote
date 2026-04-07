from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "tooling/scripts/ci/check_sensitive_surface_guard.py"
SPEC = importlib.util.spec_from_file_location(
    "check_sensitive_surface_guard", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_sensitive_surface_guard_script_exists() -> None:
    assert SCRIPT_PATH.exists()


def test_sensitive_surface_guard_passes_against_current_repo_state() -> None:
    assert GUARD.collect_failures(REPO_ROOT) == []


def test_sensitive_surface_guard_flags_real_local_path_in_tracked_doc(
    tmp_path: Path,
) -> None:
    rel_path = ".agents/Tasks/example.md"
    leaked_path = "/" + "Users/" + "alice/secrets/project"
    _write(tmp_path / rel_path, f"path: {leaked_path}\n")

    failures = GUARD.collect_failures(tmp_path, tracked_files=[rel_path])

    assert any("real macOS home path" in item for item in failures)


def test_sensitive_surface_guard_flags_hardcoded_personal_identity(
    tmp_path: Path,
) -> None:
    rel_path = "docs/incident.md"
    maintainer_name = "Yifeng (" + "Terry) Yu"
    maintainer_email = "125581657+" + "xiaojiou176@users.noreply.github.com"
    personal_mailbox = "xiao176jiou" + "@gmail.com"
    _write(
        tmp_path / rel_path,
        f"Owner: {maintainer_name} <{maintainer_email}> {personal_mailbox}\n",
    )

    failures = GUARD.collect_failures(tmp_path, tracked_files=[rel_path])

    assert any("hardcoded maintainer name" in item for item in failures)
    assert any("hardcoded maintainer GitHub noreply email" in item for item in failures)
    assert any("hardcoded maintainer Gmail address" in item for item in failures)


def test_sensitive_surface_guard_flags_tracked_log_artifact(tmp_path: Path) -> None:
    rel_path = "logs/operator.log"
    _write(tmp_path / rel_path, "clean\n")

    failures = GUARD.collect_failures(tmp_path, tracked_files=[rel_path])

    assert any("tracked log directory" in item for item in failures)


def test_sensitive_surface_guard_flags_tracked_env_file(tmp_path: Path) -> None:
    rel_path = ".env"
    _write(tmp_path / rel_path, "SAFE=1\n")

    failures = GUARD.collect_failures(tmp_path, tracked_files=[rel_path])

    assert any("tracked .env file" in item for item in failures)


def test_sensitive_surface_guard_cli_passes_for_current_repo() -> None:
    completed = subprocess.run(
        [sys.executable, "tooling/scripts/ci/check_sensitive_surface_guard.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PASS:" in completed.stdout
