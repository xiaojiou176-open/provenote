from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_public_workspace_proof_pack_tracks_sources_to_auditable_markdown() -> None:
    text = _read("examples/public-proof/README.md")
    assert "`/sources -> source detail -> Auditable Markdown`" in text
    assert "../../apps/web/src/app/(dashboard)/sources/page.tsx" in text
    assert "../../apps/web/src/app/(dashboard)/sources/[id]/page.tsx" in text
    assert "./auditable-markdown/README.md" in text
    assert "not a hosted demo" in text


def test_readme_quickstart_and_proof_link_the_workspace_proof_pack() -> None:
    readme = _read("README.md")
    quickstart = _read("docs/quickstart.md")
    proof = _read("docs/proof.md")
    distribution = _read("docs/distribution.md")

    assert "./examples/public-proof/README.md" in readme
    assert "../examples/public-proof/README.md" in quickstart
    assert "../examples/public-proof/README.md" in proof
    assert "../examples/public-proof/README.md" in distribution
    assert "/sources -> source detail -> Auditable Markdown" in distribution
    assert "registry-first story" in distribution


def test_project_status_separates_latest_release_tag_from_current_main() -> None:
    text = _read("docs/project-status.md")
    assert "`Provenote v1.8.5` is the latest published release tag" in text
    assert "current `main` is the working branch" in text
