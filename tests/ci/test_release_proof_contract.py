from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _job_block(workflow_text: str, job_name: str) -> str:
    pattern = re.compile(
        rf"(?ms)^  {re.escape(job_name)}:\n(.*?)(?=^  [^\s][^:]*:\n|\Z)",
    )
    match = pattern.search(workflow_text)
    if match is None:
        raise AssertionError(f"job '{job_name}' not found")
    return match.group(1)


def test_setup_uv_python_action_pins_setup_python_to_full_sha() -> None:
    action_yaml = _read(".github/actions/setup-uv-python/action.yml")
    assert (
        "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405" in action_yaml
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


def test_release_proof_export_uses_explicit_ghcr_auth_inputs() -> None:
    workflow = _read(".github/workflows/build-and-release.yml")
    regular_block = _job_block(workflow, "build-regular")
    single_block = _job_block(workflow, "build-single")
    summary_block = _job_block(workflow, "summary")

    assert "packages: read" not in summary_block
    assert "GHCR_USERNAME: ${{ github.actor }}" not in summary_block
    assert "GHCR_TOKEN: ${{ secrets.GITHUB_TOKEN }}" not in summary_block
    assert (
        "GHCR_USERNAME: ${{ secrets.GHCR_USERNAME != '' && secrets.GHCR_USERNAME || github.actor }}"
        in regular_block
    )
    assert (
        "GHCR_TOKEN: ${{ secrets.GHCR_PUSH_TOKEN != '' && secrets.GHCR_PUSH_TOKEN || secrets.GITHUB_TOKEN }}"
        in regular_block
    )
    assert (
        "GHCR_USERNAME: ${{ secrets.GHCR_USERNAME != '' && secrets.GHCR_USERNAME || github.actor }}"
        in single_block
    )
    assert (
        "GHCR_TOKEN: ${{ secrets.GHCR_PUSH_TOKEN != '' && secrets.GHCR_PUSH_TOKEN || secrets.GITHUB_TOKEN }}"
        in single_block
    )
    assert "Download raw OCI release-proof evidence artifact (regular)" in summary_block
    assert "Download raw OCI release-proof evidence artifact (single)" in summary_block
