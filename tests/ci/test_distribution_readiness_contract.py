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
    assert "live Official MCP Registry entry for `provenote-mcp`" in text
    assert "public-distribution/mcp-registry/server.json" in text
    assert "Fresh registry read-back now returns" in text
    assert "status `active`" in text
    assert "version `1.8.5`" in text
    assert "package-backed public artifact is still a later packaging upgrade" in text
    assert (
        "live registry entry points back to the repo-owned MCP docs/install surface"
        in text
    )


def test_registry_prep_files_exist_for_mcp_registry_lane() -> None:
    assert (
        REPO_ROOT / "examples/public-distribution/mcp-registry/server.json"
    ).exists()
    example_payload = json.loads(
        _read("examples/public-distribution/mcp-registry/server.json")
    )
    assert example_payload["name"] == "io.github.xiaojiou176-open/provenote-mcp"
    assert example_payload["websiteUrl"].endswith("/docs/mcp.md")
    assert example_payload["version"] == "1.8.5"
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


def test_readme_project_status_distribution_and_mcp_keep_registry_truth_in_sync() -> None:
    readme = _read("README.md")
    project_status = _read("docs/project-status.md")
    distribution = _read("docs/distribution.md")
    mcp = _read("docs/mcp.md")

    assert "live websiteUrl-backed `provenote-mcp` entry" in readme
    assert "live Official MCP Registry entry for `provenote-mcp`" in project_status
    assert "live Official MCP Registry entry for `provenote-mcp`" in distribution
    assert "live websiteUrl-backed entry for `provenote-mcp`" in mcp
    assert (
        "therefore the honest boundary is `live registry entry: yes`, `package-backed public artifact: no`, and `other host marketplace listing: no`"
        in mcp
    )


def test_codex_integration_keeps_listing_truth_below_directory_live() -> None:
    codex = _read("docs/integrations/codex.md")
    assert "`public-ready package available`: yes" in codex
    assert (
        "`publicly discoverable listing live`: no official/public Codex directory listing is claimed here"
        in codex
    )


def test_registry_submission_pack_keeps_public_artifact_boundary() -> None:
    text = _read("examples/public-distribution/mcp-registry/README.md")
    assert "Official MCP Registry now returns a live active entry" in text
    assert "status is `active`" in text
    assert "published version is `1.8.5`" in text
    assert (
        "package-backed public install artifact is still a separate packaging improvement"
        in text
    )
    assert (
        "does **not** claim that a supported public package or public remote-server artifact is already published"
        in text
    )


def test_pyproject_exposes_public_package_metadata() -> None:
    payload = tomllib.loads(_read("pyproject.toml"))
    project = payload["project"]
    assert project["name"] == "provenote"
    assert "mcp" in project["keywords"]
    assert "long-context" in project["keywords"]
    assert (
        project["urls"]["Homepage"] == "https://xiaojiou176-open.github.io/provenote/"
    )
    assert (
        project["urls"]["Documentation"]
        == "https://xiaojiou176-open.github.io/provenote/"
    )
    assert project["urls"]["Source"] == "https://github.com/xiaojiou176-open/provenote"


def test_pyproject_tracks_public_distribution_artifact_ssot() -> None:
    payload = tomllib.loads(_read("pyproject.toml"))
    public_artifact = payload["tool"]["open_notebook"]["public_distribution_artifact"]
    assert public_artifact["package_name"] == "provenote"
    assert public_artifact["package_registry"] == "pypi"
    assert public_artifact["mcp_name"] == "io.github.xiaojiou176-open/provenote-mcp"
    assert "provenote-mcp" in public_artifact["entrypoints"]
    assert "server.json" in public_artifact["registry_manifests"]
    assert (
        "examples/public-distribution/mcp-registry/server.json"
        in public_artifact["registry_manifests"]
    )
