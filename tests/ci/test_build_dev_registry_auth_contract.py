from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_DEV_WORKFLOW = REPO_ROOT / ".github/workflows/build-dev.yml"


def test_build_dev_probes_ghcr_access_before_dev_image_push() -> None:
    workflow = BUILD_DEV_WORKFLOW.read_text(encoding="utf-8")

    assert workflow.count("Probe GHCR package access") == 2
    assert (
        "https://api.github.com/orgs/${owner}/packages/container/${package_name}"
        in workflow
    )
    assert (
        "https://api.github.com/users/${owner}/packages/container/${package_name}"
        in workflow
    )
    assert "ghcr_push_allowed=false" in workflow
    assert (
        "Publish skipped because package access is not available to the workflow token"
        in workflow
    )
