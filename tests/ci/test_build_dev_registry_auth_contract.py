from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_DEV_WORKFLOW = REPO_ROOT / ".github/workflows/build-dev.yml"


def test_build_dev_probes_ghcr_registry_surface_before_dev_image_push() -> None:
    workflow = BUILD_DEV_WORKFLOW.read_text(encoding="utf-8")

    assert workflow.count("Probe GHCR registry push access") == 2
    assert "curl -fsSI https://ghcr.io/v2/" in workflow
    assert 'scope="repository:${GHCR_REPOSITORY}:pull,push"' in workflow
    assert "https://ghcr.io/v2/${GHCR_REPOSITORY}/blobs/${probe_digest}" in workflow
    assert "probe_digest=" in workflow
    assert "ghcr_push_allowed=false" in workflow
    assert "cannot access the GHCR registry push surface" in workflow


def test_build_single_push_is_gated_by_prepared_tags() -> None:
    workflow = BUILD_DEV_WORKFLOW.read_text(encoding="utf-8")

    assert "push: ${{ steps.tags.outputs.push }}" in workflow
