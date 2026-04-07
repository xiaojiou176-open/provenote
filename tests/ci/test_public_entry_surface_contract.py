from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_PRIVATE_SURFACE_PATTERNS = (
    re.compile(r"https://github\.com/[^/\s]+/[^/\s]+-private\b"),
    re.compile(r"\b[^/\s]+/[^/\s]+-private\b"),
)

CURRENT_FACING_ENTRY_FILES = (
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/installation_issue.yml",
    "SUPPORT.md",
    "SECURITY.md",
)


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_issue_contact_links_stay_repo_local() -> None:
    issue_config = _read(".github/ISSUE_TEMPLATE/config.yml")

    assert "url: ../../../security/policy" in issue_config
    assert "url: ../../../blob/main/SUPPORT.md" in issue_config


def test_current_facing_entry_surfaces_do_not_route_back_to_old_private_repo() -> None:
    for rel_path in CURRENT_FACING_ENTRY_FILES:
        text = _read(rel_path)
        for pattern in FORBIDDEN_PRIVATE_SURFACE_PATTERNS:
            assert not pattern.search(text), (
                f"{rel_path} routes back to retired private surface pattern: {pattern.pattern}"
            )
