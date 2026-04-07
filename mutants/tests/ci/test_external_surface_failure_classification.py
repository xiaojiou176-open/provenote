from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_external_surfaces_declare_blocking_lanes() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/upstream/external-surfaces.json").read_text(
            encoding="utf-8"
        )
    )
    for item in payload["surfaces"]:
        assert item["blocking_lane"], f"missing blocking lane for {item['name']}"


def test_no_implicit_external_surface_guard_exists() -> None:
    guard = REPO_ROOT / "tooling/scripts/ci/check_no_implicit_external_surface.py"
    assert guard.exists()


def test_gemini_api_surface_declares_live_witness_binding() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/upstream/external-surfaces.json").read_text(
            encoding="utf-8"
        )
    )
    gemini_surface = next(
        item for item in payload["surfaces"] if item["name"] == "gemini-api"
    )

    assert gemini_surface["witness_artifact_surface"] == "live-teardown-evidence-llm"
    assert (
        gemini_surface["witness_test_name"]
        == "test_google_live_connection_and_generation"
    )


def test_ghcr_release_images_surface_declares_release_proof_witness_binding() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/upstream/external-surfaces.json").read_text(
            encoding="utf-8"
        )
    )
    ghcr_surface = next(
        item for item in payload["surfaces"] if item["name"] == "ghcr-release-images"
    )

    assert ghcr_surface["witness_artifact_surface"] == "release-proof"
    assert (
        ghcr_surface["witness_test_name"]
        == "test_release_proof_workflow_exports_raw_registry_backed_evidence"
    )
