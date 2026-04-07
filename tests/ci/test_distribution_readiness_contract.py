from __future__ import annotations

import json
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_distribution_doc_exists_and_keeps_claim_ladder() -> None:
    text = _read("docs/distribution.md")
    assert "# Distribution Status" in text
    assert "`repo-owned prep exists`" in text
    assert "`public-ready package available`" in text
    assert "`publicly discoverable listing live`" in text
    assert "`official marketplace listing live`" in text
    assert "MCP Registry" in text
    assert "OpenClaw" in text


def test_distribution_doc_keeps_mcp_registry_boundary() -> None:
    text = _read("docs/distribution.md")
    assert "official MCP Registry already exists" in text
    assert "public-distribution/mcp-registry/server.json" in text
    assert "official registry requirements" in text
    assert (
        "registry-specific publication is still blocked by external publish/auth work"
        in text
    )
    assert "supported public package or public remote-server artifact" in text


def test_registry_prep_files_exist_for_mcp_registry_lane() -> None:
    assert (
        REPO_ROOT / "examples/public-distribution/mcp-registry/server.json"
    ).exists()
    example_payload = json.loads(
        _read("examples/public-distribution/mcp-registry/server.json")
    )
    assert example_payload["name"] == "io.github.xiaojiou176/provenote-mcp"
    assert example_payload["websiteUrl"].endswith("/docs/mcp.md")
    assert example_payload["version"] == "1.8.4"
    assert "packages" not in example_payload
    assert (
        REPO_ROOT
        / "examples/hosts/openclaw/clawhub/provenote-mcp-outcome-workflows/SKILL.md"
    ).exists()


def test_project_status_and_faq_link_distribution_boundary() -> None:
    project_status = _read("docs/project-status.md")
    faq = _read("docs/faq.md")
    assert "[distribution.md](distribution.md)" in project_status
    assert "[distribution.md](distribution.md)" in faq


def test_codex_integration_keeps_listing_truth_below_directory_live() -> None:
    codex = _read("docs/integrations/codex.md")
    assert "`public-ready package available`: yes" in codex
    assert (
        "`publicly discoverable listing live`: no official/public Codex directory listing is claimed here"
        in codex
    )


def test_registry_submission_pack_keeps_public_artifact_boundary() -> None:
    text = _read("examples/public-distribution/mcp-registry/README.md")
    assert "official quickstart still assumes a real published package" in text
    assert (
        "official registry requirements still enforce package-ownership verification"
        in text
    )
    assert "public package or public remote-server artifact" in text


def test_pyproject_exposes_public_package_metadata() -> None:
    payload = tomllib.loads(_read("pyproject.toml"))
    project = payload["project"]
    assert project["name"] == "provenote"
    assert "mcp" in project["keywords"]
    assert "long-context" in project["keywords"]
    assert project["urls"]["Homepage"].endswith("/docs/index.md")
    assert project["urls"]["Documentation"].endswith("/docs/index.md")
    assert project["urls"]["Source"] == "https://github.com/xiaojiou176/provenote"


def test_pyproject_tracks_public_distribution_artifact_ssot() -> None:
    payload = tomllib.loads(_read("pyproject.toml"))
    public_artifact = payload["tool"]["open_notebook"]["public_distribution_artifact"]
    assert public_artifact["package_name"] == "provenote"
    assert public_artifact["package_registry"] == "pypi"
    assert public_artifact["mcp_name"] == "io.github.xiaojiou176/provenote-mcp"
    assert "provenote-mcp" in public_artifact["entrypoints"]
    assert "server.json" in public_artifact["registry_manifests"]
    assert (
        "examples/public-distribution/mcp-registry/server.json"
        in public_artifact["registry_manifests"]
    )
