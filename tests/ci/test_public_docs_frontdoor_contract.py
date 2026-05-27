from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_HOST_BUNDLE_INDEX = (
    "https://github.com/xiaojiou176-open/notebooklab/blob/main/examples/hosts/README.md"
)


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_public_docs_frontdoor_html_exists_and_uses_main_landmark() -> None:
    text = _read("docs/index.html")
    assert '<html lang="en">' in text
    assert "<main" in text
    assert 'id="main-content"' in text
    assert "Turn messy long context into structured, inspectable outcomes." in text


def test_public_docs_frontdoor_keeps_outcome_first_and_second_ring_ordering() -> None:
    text = _read("docs/index.html")
    assert "Outcome-first workbench" in text
    assert "Long Context" in text
    assert "Quick Result Path" in text
    assert "Second ring after the product path is clear" in text
    assert "Official MCP Registry" in text
    assert "live OpenHands/extensions or ClawHub listing" in text


def test_public_docs_frontdoor_styles_inline_links_for_readability() -> None:
    text = _read("docs/index.html")
    assert "main p a," in text
    assert "main li a," in text
    assert "text-decoration: underline;" in text
    assert "text-underline-offset" in text


def test_public_docs_frontdoor_keeps_second_ring_links_pages_safe() -> None:
    text = _read("docs/index.html")
    assert f'href="{PUBLIC_HOST_BUNDLE_INDEX}"' in text
    assert 'href="../examples/' not in text
    assert 'href="./examples/' not in text
