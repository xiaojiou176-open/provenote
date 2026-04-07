from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_open_source_surface_gate_script_exists() -> None:
    assert (REPO_ROOT / "tooling/scripts/ci/check_open_source_surface.py").exists()


def test_required_public_collaboration_files_exist() -> None:
    for rel_path in (
        "LICENSE",
        "README.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "CODEOWNERS",
        "SUPPORT.md",
    ):
        assert (REPO_ROOT / rel_path).exists(), rel_path


def test_readme_routes_to_public_boundary_files() -> None:
    readme = _read("README.md")
    for token in ("SECURITY.md", "SUPPORT.md", "CODE_OF_CONDUCT.md", "CODEOWNERS"):
        assert token in readme


def test_contributing_routes_to_boundary_files() -> None:
    contributing = _read("CONTRIBUTING.md")
    for token in ("SUPPORT.md", "SECURITY.md", "CODE_OF_CONDUCT.md"):
        assert token in contributing


def test_issue_template_config_exposes_security_and_support_links() -> None:
    issue_config = _read(".github/ISSUE_TEMPLATE/config.yml")
    assert "security/policy" in issue_config
    assert "SUPPORT.md" in issue_config


def test_open_source_surface_gate_passes_on_current_repo_state() -> None:
    result = subprocess.run(
        ["python3", "tooling/scripts/ci/check_open_source_surface.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS:" in result.stdout
