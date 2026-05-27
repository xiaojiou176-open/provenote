from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
HOSTS_ROOT = REPO_ROOT / "examples" / "hosts"
PACKET_INDEX = HOSTS_ROOT / "packet-index.json"


def _read_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), f"{path} must contain a YAML object"
    return payload


def test_host_packet_index_tracks_all_public_ready_bundles() -> None:
    payload = json.loads(PACKET_INDEX.read_text(encoding="utf-8"))

    assert payload["schemaVersion"] == "1.0.0"
    assert payload["kind"] == "host_packet_index"
    assert payload["version"] == "1.8.5"
    assert payload["schema"] == "./packet-manifest.schema.json"
    assert len(payload["bundles"]) == 7
    assert len(payload["submissionPacks"]) == 4


def test_each_bundle_manifest_is_present_and_self_describing() -> None:
    payload = json.loads(PACKET_INDEX.read_text(encoding="utf-8"))

    for bundle in payload["bundles"]:
        manifest_path = (HOSTS_ROOT / bundle["manifest"].removeprefix("./")).resolve()
        assert manifest_path.exists(), f"missing bundle manifest: {manifest_path}"
        manifest = _read_yaml(manifest_path)
        assert manifest["schemaVersion"] == "1.0.0"
        assert manifest["kind"] == "host_packet"
        assert manifest["id"] == bundle["id"]
        assert manifest["host"] == bundle["host"]
        assert manifest["supportTier"] == bundle["claimLevel"]
        assert manifest["publicationStatus"] == "repo_owned_packet_not_listed"
        assert manifest["repository"]["type"] == "git"
        assert manifest["repository"]["url"].endswith("notebooklab.git")
        assert manifest["repository"]["directory"] in str(manifest_path.parent)
        assert manifest["placement"]["relativePath"].endswith("README.md")
        assert manifest["placement"]["discoveryRoots"]
        assert manifest["packetArtifacts"]
        assert manifest["capabilities"]
        assert manifest["smoke"]["path"] == "README.md"
        assert manifest["smoke"]["minimalFlow"]
        assert manifest["smoke"]["preferredFlow"]
        assert "does not claim a live official" in manifest["claimBoundary"]


def test_packet_index_is_referenced_by_public_distribution_docs() -> None:
    hosts_readme = (HOSTS_ROOT / "README.md").read_text(encoding="utf-8")
    distribution_doc = (REPO_ROOT / "docs" / "distribution.md").read_text(
        encoding="utf-8"
    )
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "packet-index.json" in hosts_readme
    assert "manifest.yaml" in hosts_readme
    assert "packet-index.json" in distribution_doc
    assert "packet-index.json" in readme
