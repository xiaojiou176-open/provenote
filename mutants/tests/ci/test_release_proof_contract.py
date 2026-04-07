from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_setup_uv_python_action_pins_setup_python_to_full_sha() -> None:
    action_yaml = _read(".github/actions/setup-uv-python/action.yml")
    assert (
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in action_yaml
    )


def test_build_and_release_exposes_build_metadata_job_outputs() -> None:
    workflow = _read(".github/workflows/build-and-release.yml")
    assert (
        "image_metadata: ${{ steps.build-regular-image.outputs.metadata }}" in workflow
    )
    assert (
        "image_metadata: ${{ steps.build-single-image.outputs.metadata }}" in workflow
    )
    assert 'const requiredCheckName = "Required Green Gate";' in workflow
    assert '--required-gate "Required Green Gate|success|' in workflow


def test_release_proof_workflow_exports_raw_registry_backed_evidence() -> None:
    workflow = _read(".github/workflows/build-and-release.yml")
    assert "Export raw OCI release-proof evidence from GHCR" in workflow
    assert "tooling/scripts/ci/export_oci_evidence.py" in workflow
    assert ".runtime-cache/runs/current/evidence/release-proof/oci" in workflow
