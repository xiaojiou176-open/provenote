from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CJK_RE = tuple(chr(codepoint) for codepoint in range(0x4E00, 0xA000))


def test_navigation_docs_pair_declares_authority_output_strings() -> None:
    text = (REPO_ROOT / "tooling/scripts/ci/check_navigation_docs_pair.py").read_text(
        encoding="utf-8"
    )
    assert "[navigation-docs] Fix: add the missing docs pair" in text
    assert not any(char in text for char in CJK_RE)


def test_english_authority_boundary_declares_repo_wide_markdown_policy() -> None:
    text = (
        REPO_ROOT / "tooling/scripts/ci/check_english_authority_boundary.py"
    ).read_text(encoding="utf-8")
    assert "All tracked Markdown docs are English-only." in text
    assert '["git", "ls-files", "*.md"]' in text or 'git", "ls-files", "*.md' in text
    assert "OPERATOR_BOUNDARY_DOCS" in text


def test_english_authority_boundary_guard_passes_for_current_repo_state() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tooling/scripts/ci/check_english_authority_boundary.py"),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
