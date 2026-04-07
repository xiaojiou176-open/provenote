from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_public_distribution_surface_guard_passes_for_current_repo_state() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tooling/scripts/ci/check_public_distribution_surface.py"),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_public_surface_snapshot_keeps_social_preview_exact_pack() -> None:
    text = (REPO_ROOT / ".github/repo-settings/public-surface.snapshot.md").read_text(
        encoding="utf-8"
    )
    assert "docs/assets/social/provenote-social-preview.png" in text
    assert "https://github.com/xiaojiou176-open/provenote/settings" in text
    assert "General -> Social preview -> Edit / Upload image" in text
