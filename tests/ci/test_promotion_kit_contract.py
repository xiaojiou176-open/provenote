from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_promotion_kit_links_core_visual_assets() -> None:
    text = _read("docs/promotion-kit.md")
    assert "docs/assets/hero/provenote-hero.png" in text
    assert "docs/assets/demo/provenote-quick-result-overview.png" in text
    assert "docs/assets/proof/provenote-proof-stack.png" in text
    assert "docs/assets/architecture/provenote-architecture.png" in text
    assert "docs/assets/social/provenote-social-preview.png" in text


def test_promotion_kit_keeps_safe_distribution_pitch() -> None:
    text = _read("docs/promotion-kit.md")
    assert "Public-ready install packages are available today." in text
    assert (
        "Official marketplace or registry listings are only claimed once they are actually live."
        in text
    )
