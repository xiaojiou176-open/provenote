from __future__ import annotations

import json
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_pyproject_keeps_publishable_public_metadata() -> None:
    data = tomllib.loads(_read("pyproject.toml"))
    project = data["project"]
    assert project["name"] == "provenote"
    assert "mcp" in project["keywords"]
    assert project["urls"]["Documentation"] == "https://xiaojiou176-open.github.io/provenote/"
    assert project["urls"]["Source"] == "https://github.com/xiaojiou176-open/provenote"


def test_claude_and_cursor_bundle_manifests_keep_richer_metadata() -> None:
    claude_payload = json.loads(
        _read(
            "examples/hosts/claude-code/provenote-outcome-bundle/.claude-plugin/plugin.json"
        )
    )
    openclaw_claude_payload = json.loads(
        _read(
            "examples/hosts/openclaw/provenote-claude-bundle/.claude-plugin/plugin.json"
        )
    )
    openclaw_cursor_payload = json.loads(
        _read(
            "examples/hosts/openclaw/provenote-cursor-bundle/.cursor-plugin/plugin.json"
        )
    )
    for payload in (
        claude_payload,
        openclaw_claude_payload,
        openclaw_cursor_payload,
    ):
        assert payload["version"] == "1.8.5"
        assert payload["repository"] == "https://github.com/xiaojiou176-open/provenote"
        assert "keywords" in payload


def test_promotion_kit_exists_and_maps_core_assets() -> None:
    text = _read("docs/promotion-kit.md")
    assert "Asset Inventory" in text
    assert "Short Pitch Set" in text
    assert "Suggested Demo Flow" in text
    assert "docs/assets/social/provenote-social-preview.png" in text


def test_registry_public_artifact_prep_runbook_exists() -> None:
    text = _read("examples/public-distribution/mcp-registry/PUBLISHABLE_ARTIFACT.md")
    assert "uv build" in text
    assert "public-artifact prep" in text
    assert "mcp-publisher login github" in text
