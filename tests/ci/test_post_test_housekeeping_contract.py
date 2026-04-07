from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_post_test_housekeeping_defaults_upstream_drift_to_advisory() -> None:
    script = (REPO_ROOT / "tooling/scripts/ci/post_test_housekeeping.sh").read_text(
        encoding="utf-8"
    )

    assert (
        'STRICT_UPSTREAM_CHECK="${HOUSEKEEPING_STRICT_UPSTREAM_CHECK:-false}"' in script
    )
    assert "--strict-upstream-check" in script
    assert "--no-strict-divergence" in script
    assert "strict upstream housekeeping is disabled" in script
    assert "git remote add upstream" not in script
    assert "configure missing upstream remote" not in script
