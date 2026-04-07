from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_codeowners_routes_to_named_repo_local_steward() -> None:
    codeowners = _read("CODEOWNERS")
    assert "@xiaojiou176" in codeowners


def test_maintainers_declares_named_repo_local_steward() -> None:
    maintainers = _read("MAINTAINERS.md")
    assert "Named Repo-Local Steward" in maintainers
    assert "@xiaojiou176" in maintainers


def test_issue_template_config_routes_to_maintainers_boundary() -> None:
    config = _read(".github/ISSUE_TEMPLATE/config.yml")
    assert "Repository Stewardship Boundary" in config
    assert "MAINTAINERS.md" in config
