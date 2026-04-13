from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_examples_hosts_index_links_submission_packs() -> None:
    text = _read("examples/hosts/README.md")
    assert "claude-code/DIRECTORY_SUBMISSION.md" in text
    assert "codex/PLUGIN_DIRECTORY_SUBMISSION.md" in text
    assert "openclaw/CLAWHUB_SUBMISSION.md" in text
    assert "../public-distribution/mcp-registry/README.md" in text


def test_claude_directory_submission_pack_tracks_claim_ladder() -> None:
    text = _read("examples/hosts/claude-code/DIRECTORY_SUBMISSION.md")
    assert "public-ready package available" in text
    assert "Anthropic's Software Directory terms" in text
    assert "Anthropic marketplace listing live" in text
    assert "https://code.claude.com/docs/en/mcp" in text
    assert "https://code.claude.com/docs/en/discover-plugins" in text
    assert (
        "https://code.claude.com/docs/en/plugins#submit-your-plugin-to-the-official-marketplace"
        in text
    )
    assert "official docs now expose discovery and submission docs" in text


def test_codex_directory_submission_pack_tracks_official_surface_limits() -> None:
    text = _read("examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md")
    assert (
        "did **not** verify a live official Codex plugin or directory submission flow"
        in text
    )
    assert "self-serve public listing path" in text
    assert "public-ready package available" in text
    assert "https://developers.openai.com/codex/mcp/" in text
    assert "https://developers.openai.com/codex/plugins" in text


def test_openclaw_submission_pack_points_to_canonical_publish_skill() -> None:
    text = _read("examples/hosts/openclaw/CLAWHUB_SUBMISSION.md")
    assert "clawhub/provenote-mcp-outcome-workflows/SKILL.md" in text
    assert "authenticated publish and sync flows" in text
    assert "https://docs.openclaw.ai/tools/clawhub" in text
    assert "clawhub skill publish <path>" in text
    assert "clawhub package publish <source> --dry-run" in text
    skill = _read(
        "examples/hosts/openclaw/clawhub/provenote-mcp-outcome-workflows/SKILL.md"
    )
    assert "public-ready ClawHub skill package" in skill
    assert (
        "not a claim that Provenote already ships official OpenClaw listing live"
        in skill
    )


def test_mcp_registry_submission_pack_exists_and_points_to_docs() -> None:
    payload = json.loads(_read("examples/public-distribution/mcp-registry/server.json"))
    assert payload["name"] == "io.github.xiaojiou176-open/provenote-mcp"
    assert payload["websiteUrl"].endswith("/docs/mcp.md")
    assert payload["version"] == "1.8.5"
    readme = _read("examples/public-distribution/mcp-registry/README.md")
    assert "## Official Raw URLs" in readme
    assert "- MCP Registry homepage:" in readme
    assert "PUBLISHABLE_ARTIFACT.md" in readme
    assert "mcp-publisher login github" in readme
    assert "mcp-publisher publish" in readme
    assert (
        "does **not** claim that a supported public package or public remote-server artifact is already published"
        in readme
    )


def test_distribution_docs_point_to_submission_packs() -> None:
    assert "DIRECTORY_SUBMISSION.md" in _read("docs/integrations/claude-code.md")
    assert "PLUGIN_DIRECTORY_SUBMISSION.md" in _read("docs/integrations/codex.md")
    assert "CLAWHUB_SUBMISSION.md" in _read("docs/integrations/openclaw.md")
    assert "examples/public-distribution/mcp-registry/README.md" in _read("docs/mcp.md")
