from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_DEV = REPO_ROOT / ".github" / "workflows" / "build-dev.yml"
BUILD_RELEASE = REPO_ROOT / ".github" / "workflows" / "build-and-release.yml"
SOURCE_LABEL = (
    "org.opencontainers.image.source=${{ github.server_url }}/${{ github.repository }}"
)


def test_build_dev_workflow_sets_ghcr_source_label_on_both_image_jobs() -> None:
    source = BUILD_DEV.read_text(encoding="utf-8")

    assert source.count(SOURCE_LABEL) >= 2
    assert "Build and push regular image" in source
    assert "Build and push single-container image" in source


def test_build_release_workflow_sets_ghcr_source_label_on_both_image_jobs() -> None:
    source = BUILD_RELEASE.read_text(encoding="utf-8")

    assert source.count(SOURCE_LABEL) >= 2
    assert "Build and push regular image" in source
    assert "Build and push single-container image" in source
