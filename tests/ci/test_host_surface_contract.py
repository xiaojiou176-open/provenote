from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_claude_code_page_keeps_repo_backed_proof_loop() -> None:
    text = _read("docs/integrations/claude-code.md")
    assert "## Repo-Backed Proof Loop" in text
    assert "public-ready Claude Code starter bundle" in text
    assert "[../../tests/test_mcp_server.py]" in text
    assert "../../examples/hosts/README.md" in text


def test_codex_page_keeps_repo_backed_proof_loop() -> None:
    text = _read("docs/integrations/codex.md")
    assert "## Repo-Backed Proof Loop" in text
    assert "public-ready Codex starter bundle" in text
    assert "[../../tests/test_mcp_server.py]" in text
    assert "../../examples/hosts/README.md" in text


def test_cursor_page_keeps_repo_backed_proof_loop() -> None:
    text = _read("docs/integrations/cursor.md")
    assert "## Repo-Backed Proof Loop" in text
    assert "[../../tests/test_mcp_server.py]" in text
    assert "../../examples/hosts/README.md" in text
    assert "../../examples/hosts/cursor/provenote-outcome-bundle/README.md" in text


def test_openclaw_page_keeps_local_proof_prep_boundary() -> None:
    text = _read("docs/integrations/openclaw.md")
    assert "## Current Claim Ladder" in text
    assert "../../examples/hosts/openclaw/README.md" in text
    assert "../../examples/hosts/openclaw/CLAWHUB_SUBMISSION.md" in text
    assert "does **not** claim" in text
    assert "every other OpenClaw marketplace, directory, or registry surface" in text


def test_mcp_overview_points_to_tracked_host_examples() -> None:
    text = _read("docs/mcp.md")
    assert "../examples/hosts/README.md" in text
    assert "integrations/openclaw.md" in text
    assert "distribution.md" in text


def test_readme_points_to_tracked_host_examples() -> None:
    text = _read("README.md")
    assert "./examples/hosts/README.md" in text
    assert "./docs/distribution.md" in text


def test_opencode_page_points_to_direct_starter_bundle() -> None:
    text = _read("docs/integrations/opencode.md")
    assert "../../examples/hosts/opencode/provenote-outcome-bundle/README.md" in text


def test_host_examples_index_lists_bundle_family() -> None:
    text = _read("examples/hosts/README.md")
    assert "provenote-claude-bundle" in text
    assert "provenote-cursor-bundle" in text
    assert "provenote-codex-bundle" in text
    assert "[openclaw/README.md]" in text


def test_project_status_keeps_claim_ladder_and_distribution_matrix() -> None:
    text = _read("docs/project-status.md")
    assert "## Claim Ladder" in text
    assert "## Distribution Surface Matrix" in text
    assert "`public-ready package available`" in text
    assert "Official MCP Registry" in text
