from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_DEV = REPO_ROOT / ".github" / "workflows" / "build-dev.yml"
BUILD_RELEASE = REPO_ROOT / ".github" / "workflows" / "build-and-release.yml"


def test_build_dev_ghcr_login_allows_secret_override() -> None:
    source = BUILD_DEV.read_text(encoding="utf-8")

    assert "Login to GitHub Container Registry" in source
    assert (
        "secrets.GHCR_PUSH_TOKEN != '' && secrets.GHCR_PUSH_TOKEN || secrets.GITHUB_TOKEN"
        in source
    )
    assert (
        "secrets.GHCR_USERNAME != '' && secrets.GHCR_USERNAME || github.actor" in source
    )


def test_build_and_release_ghcr_login_and_export_allow_secret_override() -> None:
    source = BUILD_RELEASE.read_text(encoding="utf-8")

    assert "Login to GitHub Container Registry" in source
    assert (
        "secrets.GHCR_PUSH_TOKEN != '' && secrets.GHCR_PUSH_TOKEN || secrets.GITHUB_TOKEN"
        in source
    )
    assert (
        "secrets.GHCR_USERNAME != '' && secrets.GHCR_USERNAME || github.actor" in source
    )
