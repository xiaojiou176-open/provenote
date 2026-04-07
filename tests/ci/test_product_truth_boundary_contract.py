from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_readme_declares_chat_vs_auditable_boundary() -> None:
    readme = _read("README.md")
    assert "Product Truth Boundary" in readme
    assert "Ordinary chat and ask flows" in readme
    assert "auditable markdown and auditable-runs" in readme


def test_architecture_keeps_traceability_lane_explicit() -> None:
    text = _read("docs/architecture.md")
    assert "Traceability boundary" in text
    assert "Ordinary chat is a fast assistant surface." in text
    assert "auditable-runs" in text
