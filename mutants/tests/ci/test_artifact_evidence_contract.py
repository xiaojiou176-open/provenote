from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
RUNTIME_SURFACES = REPO_ROOT / "config" / "runtime" / "runtime-surfaces.json"


@dataclass(frozen=True)
class UploadArtifactStep:
    name: str
    path: str
    if_no_files_found: str | None


def _parse_upload_artifact_steps(yaml_text: str) -> list[UploadArtifactStep]:
    step_re = re.compile(r"(?m)^\s*-\s+name:\s+(.+?)\s*$")
    path_re = re.compile(r"(?m)^\s*path:\s*(.+?)\s*$")
    if_no_files_re = re.compile(r"(?m)^\s*if-no-files-found:\s*(.+?)\s*$")
    uses_upload_re = re.compile(r"(?m)^\s*uses:\s*.*upload-artifact@")

    matches = list(step_re.finditer(yaml_text))
    steps: list[UploadArtifactStep] = []

    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(yaml_text)
        block = yaml_text[start:end]
        if not uses_upload_re.search(block):
            continue

        path_match = path_re.search(block)
        path_value = path_match.group(1).strip().strip("\"'") if path_match else ""
        if_no_files_match = if_no_files_re.search(block)
        if_no_files_value = (
            if_no_files_match.group(1).strip().strip("\"'")
            if if_no_files_match
            else None
        )
        steps.append(
            UploadArtifactStep(
                name=match.group(1).strip(),
                path=path_value,
                if_no_files_found=if_no_files_value,
            )
        )

    return steps


def _collect_steps_for_path(
    yaml_text: str, expected_path: str
) -> list[UploadArtifactStep]:
    return [
        s for s in _parse_upload_artifact_steps(yaml_text) if s.path == expected_path
    ]


def _find_non_error_steps(
    yaml_text: str, expected_path: str
) -> tuple[list[UploadArtifactStep], list[UploadArtifactStep]]:
    matched_steps = _collect_steps_for_path(yaml_text, expected_path)
    non_error_steps = [s for s in matched_steps if s.if_no_files_found != "error"]
    return matched_steps, non_error_steps


def _load_registry() -> dict[str, object]:
    return json.loads(RUNTIME_SURFACES.read_text(encoding="utf-8"))


def test_test_workflow_e2e_report_artifact_is_strict() -> None:
    workflow = (WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")
    matched_steps, non_error_steps = _find_non_error_steps(
        workflow, ".runtime-cache/runs/current/evidence/playwright/report"
    )

    assert matched_steps, (
        "Expected at least one upload-artifact step for E2E Playwright report."
    )
    assert not non_error_steps, (
        "E2E Playwright report artifact must use if-no-files-found: error. "
        f"Offending steps: {[s.name for s in non_error_steps]}"
    )


def test_uiux_gate_inputs_artifact_is_strict() -> None:
    workflow = (WORKFLOWS_DIR / "uiux-gemini-gate.yml").read_text(encoding="utf-8")
    matched_steps, non_error_steps = _find_non_error_steps(
        workflow, ".runtime-cache/runs/current/evidence/uiux-gemini"
    )

    assert matched_steps, "Expected UIUX gate inputs artifact upload step to exist."
    assert not non_error_steps, (
        "UIUX gate inputs artifact must use if-no-files-found: error. "
        f"Offending steps: {[s.name for s in non_error_steps]}"
    )


def test_runtime_surfaces_tracks_uiux_gate_bundle() -> None:
    registry = _load_registry()
    critical = registry["surfaces"]
    assert any(
        item["name"] == "uiux-gemini-bundle"
        and item["workflow"] == ".github/workflows/uiux-gemini-gate.yml"
        and item["truth_basis"] == "witness-backed"
        and item["verification_lane"] == ".github/workflows/uiux-gemini-gate.yml"
        and item["witness_test_name"]
        == "test_uiux_gate_workflow_generates_fresh_evidence_bundle"
        for item in critical
    ), "runtime surfaces registry must track the canonical UIUX gate bundle"


def test_runtime_surfaces_tracks_live_teardown_names() -> None:
    registry = _load_registry()
    critical = registry["surfaces"]
    for artifact_name in (
        "live-teardown-evidence-llm",
        "live-teardown-evidence-external-web",
    ):
        assert any(item["name"] == artifact_name for item in critical), (
            f"runtime surfaces registry must include {artifact_name}"
        )


def test_runtime_surfaces_entries_include_evidence_contract_fields() -> None:
    registry = _load_registry()
    entries = registry["surfaces"]
    for item in entries:
        for field in (
            "canonical_path",
            "producer",
            "consumer",
            "retention_class",
            "run_correlation_required",
        ):
            assert field in item, (
                f"runtime surface entry missing {field}: {item['name']}"
            )


def test_runtime_surfaces_uiux_bundle_points_to_canonical_path() -> None:
    registry = _load_registry()
    critical = registry["surfaces"]
    uiux_entry = next(item for item in critical if item["name"] == "uiux-gemini-bundle")
    assert (
        uiux_entry["canonical_path"]
        == ".runtime-cache/runs/current/evidence/uiux-gemini"
    )
    assert uiux_entry["run_correlation_required"] is True


def test_runtime_surfaces_release_proof_and_action_evidence_bind_witness_tests() -> (
    None
):
    registry = _load_registry()
    indexed = {item["name"]: item for item in registry["surfaces"]}

    release_proof = indexed["release-proof"]
    assert release_proof["truth_basis"] == "witness-backed"
    assert release_proof["verification_lane"] == ".github/workflows/build-and-release.yml"
    assert (
        release_proof["witness_test_name"]
        == "test_release_proof_workflow_exports_raw_registry_backed_evidence"
    )

    action_runtime = indexed["apps/web-action-runtime-evidence"]
    assert action_runtime["truth_basis"] == "witness-backed"
    assert (
        action_runtime["verification_lane"]
        == "tooling/scripts/ci/check_frontend_action_matrix.py"
    )
    assert (
        action_runtime["witness_test_name"]
        == "test_check_frontend_action_matrix_runtime_contract_passes_when_complete"
    )


def test_uiux_gate_workflow_generates_fresh_evidence_bundle() -> None:
    workflow = (WORKFLOWS_DIR / "uiux-gemini-gate.yml").read_text(encoding="utf-8")
    assert "Generate UIUX gate evidence bundle" in workflow, (
        "UIUX workflow must generate manifest/evaluator from the current run before gating."
    )
    assert ".runtime-cache/runs/current/evidence/uiux-gemini/manifest.json" in workflow
    assert ".runtime-cache/runs/current/evidence/uiux-gemini/evaluator.json" in workflow


def test_uiux_gate_workflow_passes_run_binding_arguments() -> None:
    workflow = (WORKFLOWS_DIR / "uiux-gemini-gate.yml").read_text(encoding="utf-8")
    assert '--expected-git-sha "${GITHUB_SHA}"' in workflow, (
        "UIUX gate invocation must bind manifest/evaluator to current git SHA."
    )
    assert '--expected-run-id "${GITHUB_RUN_ID}"' in workflow, (
        "UIUX gate invocation must bind manifest/evaluator to current workflow run id."
    )


def test_uiux_gate_workflow_keeps_blocking_mode_without_fallback_opt_in() -> None:
    workflow = (WORKFLOWS_DIR / "uiux-gemini-gate.yml").read_text(encoding="utf-8")
    assert "--allow-deterministic-fallback" not in workflow, (
        "Blocking UIUX workflow must not opt in deterministic fallback."
    )
    assert "--allow-legacy-auto-generate" not in workflow, (
        "Blocking UIUX workflow must not opt in legacy auto-generate mode."
    )


def test_live_integration_teardown_evidence_artifacts_are_strict() -> None:
    workflow = (WORKFLOWS_DIR / "live-integration.yml").read_text(encoding="utf-8")
    required_paths = [
        ".runtime-cache/runs/current/evidence/live-teardown/live-llm.jsonl",
        ".runtime-cache/runs/current/evidence/live-teardown/live-external-web.jsonl",
    ]

    for required_path in required_paths:
        matched_steps, non_error_steps = _find_non_error_steps(workflow, required_path)
        assert matched_steps, f"Expected live teardown upload step for {required_path}."
        assert not non_error_steps, (
            f"Live teardown artifact {required_path} must use if-no-files-found: error. "
            f"Offending steps: {[s.name for s in non_error_steps]}"
        )


def test_counterfactual_fails_when_artifact_policy_is_not_error() -> None:
    poisoned_yaml = """
name: Poisoned Contract
jobs:
  sample:
    runs-on: ubuntu-latest
    steps:
      - name: Upload UIUX gate inputs
        uses: actions/upload-artifact@v4
        with:
          name: uiux-gemini-gate-inputs
          path: .runtime-cache/runs/current/evidence/uiux-gemini
          if-no-files-found: ignore
"""
    matched_steps, non_error_steps = _find_non_error_steps(
        poisoned_yaml, ".runtime-cache/runs/current/evidence/uiux-gemini"
    )

    assert matched_steps, (
        "Counterfactual fixture should include one target artifact upload step."
    )
    assert len(non_error_steps) == 1
    assert non_error_steps[0].if_no_files_found == "ignore"


def test_test_workflow_coverage_artifacts_use_runtime_cache_locations() -> None:
    workflow = (WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")
    assert ".runtime-cache/test/coverage/backend/coverage.xml" in workflow
    assert ".runtime-cache/test/coverage/apps/web/lcov.info" in workflow


def test_build_release_workflow_exports_raw_release_proof_evidence() -> None:
    workflow = (WORKFLOWS_DIR / "build-and-release.yml").read_text(encoding="utf-8")
    assert "Export raw OCI release-proof evidence from GHCR" in workflow
    assert "tooling/scripts/ci/export_oci_evidence.py" in workflow
    assert ".runtime-cache/runs/current/evidence/release-proof/oci" in workflow
    assert '"source_role": "auxiliary_summary"' not in workflow


def test_release_proof_generator_surfaces_raw_registry_exports() -> None:
    generator = (REPO_ROOT / "tooling/scripts/ci/generate_release_proof.py").read_text(
        encoding="utf-8"
    )
    assert "source_role" in generator
    assert "direct_artifact" in generator
    assert "Evidence Kind" in generator
