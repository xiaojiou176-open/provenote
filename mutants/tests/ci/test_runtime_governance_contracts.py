from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_runtime_governance_contract_files_exist() -> None:
    required_paths = (
        "config/root/top-level-allowlist.json",
        "config/root/mutants-top-level-allowlist.json",
        "config/ci/atomic-commit-exceptions.json",
        "config/architecture/layer-boundaries.json",
        "config/architecture/frontend-layer-boundaries.json",
        "config/runtime/runtime-surfaces.json",
        "config/runtime/entrypoint-contract.json",
        "config/upstream/floating-input-policy.json",
        "config/upstream/external-surfaces.json",
        "config/upstream/compatibility-matrix.json",
        "config/upstream/ownership-map.json",
        "config/upstream/source-pin-registry.json",
        "config/upstream/patch-registry.json",
        "contracts/observability/log-event.schema.json",
        "contracts/api/openapi.yaml",
        "contracts/evidence/artifact-bundle.schema.json",
        "contracts/runtime/output-paths.schema.json",
        "tooling/scripts/ci/check_root_cleanliness.py",
        "tooling/scripts/ci/check_entrypoint_contract.py",
        "tooling/scripts/ci/check_output_path_policy.py",
        "tooling/scripts/ci/check_runtime_surfaces.py",
        "tooling/scripts/ci/check_layer_boundaries.py",
        "tooling/scripts/ci/check_frontend_layer_boundaries.mjs",
        "tooling/scripts/ci/check_cache_wipe_rebuild.sh",
        "tooling/scripts/ci/check_external_surfaces.py",
        "tooling/scripts/ci/check_open_source_surface.py",
        "tooling/scripts/ci/check_path_truth_drift.py",
        "tooling/scripts/ci/check_provider_surface_truth.py",
        "tooling/scripts/ci/check_selective_port_ledger.py",
        "tooling/scripts/ci/check_legacy_provider_removal_ledger.py",
        "tooling/scripts/ci/check_legacy_provider_runtime_imports.py",
        "tooling/scripts/ci/check_podcasts_topology_mapping.py",
        "tooling/scripts/ci/export_oci_evidence.py",
        "tooling/scripts/ci/check_no_floating_external_inputs.py",
        "tooling/scripts/ci/check_upstream_compatibility_matrix_sync.py",
        "tooling/scripts/ci/check_log_contract.py",
        "tooling/scripts/ci/check_log_sink_integrity.py",
        "tooling/scripts/ci/check_frontend_logging_contract.py",
        "tooling/scripts/ci/check_frontend_log_schema_sync.mjs",
        "tooling/scripts/ci/check_openapi_contract_drift.py",
        "tooling/scripts/ci/check_frontend_api_contract_drift.py",
        "tooling/scripts/api/export_openapi_contract.py",
        "tooling/scripts/api/generate_frontend_api_contract.py",
        "tooling/scripts/runtime/cache_env.sh",
        "tooling/scripts/runtime/run_uv_managed.sh",
        "apps/web/src/lib/api/generated/openapi-contract.ts",
    )
    for rel_path in required_paths:
        assert (REPO_ROOT / rel_path).exists(), (
            f"missing runtime governance contract file: {rel_path}"
        )


def test_runtime_surfaces_registry_promotes_runtime_cache_coverage_paths() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/runtime/runtime-surfaces.json").read_text(encoding="utf-8")
    )
    outputs = {item["name"]: item["canonical_path"] for item in payload["surfaces"]}
    assert (
        outputs["backend-coverage-xml"]
        == ".runtime-cache/test/coverage/backend/coverage.xml"
    )
    assert (
        outputs["apps/web-coverage-lcov"]
        == ".runtime-cache/test/coverage/apps/web/lcov.info"
    )


def test_log_runtime_surfaces_explicitly_mark_witness_backed_truth() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/runtime/runtime-surfaces.json").read_text(encoding="utf-8")
    )
    assert "witness-backed" in payload["truth_classification_note"]
    assert "static-only" in payload["truth_classification_note"]

    surfaces = {item["name"]: item for item in payload["surfaces"]}
    expected = {
        "local-logs": "test_process_logger_emits_runtime_witness_with_bound_context",
        "ci-logs": "test_process_logger_emits_runtime_witness_with_bound_context",
        "single-container-logs": "test_supervisor_log_path_guard_passes_for_current_repo_state",
    }
    for surface_name, witness_test_name in expected.items():
        surface = surfaces[surface_name]
        assert surface["truth_basis"] == "witness-backed"
        assert (
            surface["verification_lane"] == "tooling/scripts/ci/check_log_contract.py"
        )
        assert surface["witness_test_name"] == witness_test_name


def test_high_value_runtime_surfaces_are_upgraded_to_witness_backed_truth() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/runtime/runtime-surfaces.json").read_text(encoding="utf-8")
    )
    surfaces = {item["name"]: item for item in payload["surfaces"]}
    expected = {
        "uiux-gemini-bundle": (
            ".github/workflows/uiux-gemini-gate.yml",
            "test_uiux_gate_workflow_generates_fresh_evidence_bundle",
        ),
        "release-proof": (
            ".github/workflows/build-and-release.yml",
            "test_release_proof_workflow_exports_raw_registry_backed_evidence",
        ),
        "apps/web-action-runtime-evidence": (
            "tooling/scripts/ci/check_frontend_action_matrix.py",
            "test_check_frontend_action_matrix_runtime_contract_passes_when_complete",
        ),
    }
    for surface_name, (verification_lane, witness_test_name) in expected.items():
        surface = surfaces[surface_name]
        assert surface["truth_basis"] == "witness-backed"
        assert surface["verification_lane"] == verification_lane
        assert surface["witness_test_name"] == witness_test_name


def test_upstream_registries_cover_same_surface_set() -> None:
    external = json.loads(
        (REPO_ROOT / "config/upstream/external-surfaces.json").read_text(
            encoding="utf-8"
        )
    )
    owners = json.loads(
        (REPO_ROOT / "config/upstream/ownership-map.json").read_text(encoding="utf-8")
    )
    pins = json.loads(
        (REPO_ROOT / "config/upstream/source-pin-registry.json").read_text(
            encoding="utf-8"
        )
    )
    patches = json.loads(
        (REPO_ROOT / "config/upstream/patch-registry.json").read_text(encoding="utf-8")
    )

    surface_names = {item["name"] for item in external["surfaces"]}
    owner_names = {item["surface"] for item in owners["owners"]}
    pin_names = {item["surface"] for item in pins["pins"]}
    patch_names = {item["surface"] for item in patches["entries"]}

    assert owner_names == surface_names
    assert pin_names == surface_names
    assert "upstream-open-notebook-repo" in patch_names


def test_external_surfaces_cover_key_application_runtime_dependencies() -> None:
    external = json.loads(
        (REPO_ROOT / "config/upstream/external-surfaces.json").read_text(
            encoding="utf-8"
        )
    )
    surface_names = {item["name"] for item in external["surfaces"]}
    assert {
        "fastmcp-library",
        "content-core-library",
        "ai-prompter-library",
        "esperanto-library",
        "podcast-creator-library",
    }.issubset(surface_names)


def test_mutants_root_allowlist_tracks_new_topology() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/root/mutants-top-level-allowlist.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["allowed_directories"] == [
        ".runtime-cache",
        "packages",
        "services",
        "tests",
    ]
    forbidden = payload["forbidden_reference_patterns"]
    assert "(^|[\\s\"'`])mutants/api/" in forbidden
    assert "(^|[\\s\"'`])mutants/open_notebook/" in forbidden


def test_atomic_commit_exception_register_is_scoped_and_backed_by_audit_doc() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/ci/atomic-commit-exceptions.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["version"] == 1
    exception = payload["exceptions"][0]
    assert exception["id"] == "hard-cut-governance-topology-2026-03-15"
    assert exception["pre_commit_branches"] == ["codex/hard-cut-governance-final"]
    assert exception["pre_push_branches"] == [
        "codex/hard-cut-governance-final",
        "main",
    ]
    assert exception["subject_regex"].startswith(
        "^refactor\\(batch-01/repo-hard-cut\\)"
    )
    assert (REPO_ROOT / exception["audit_doc"]).exists()
    required_paths = set(exception["required_paths"])
    assert "config/ci/atomic-commit-exceptions.json" in required_paths
    assert "docs/development.md" in required_paths


def test_pre_commit_ruff_version_matches_runtime_ruff_floor() -> None:
    pre_commit = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "https://github.com/astral-sh/ruff-pre-commit" in pre_commit
    assert "rev: v0.14.13" in pre_commit
    assert "ruff>=0.14.13" in pyproject


def test_legacy_mypy_ini_uses_runtime_cache_dir() -> None:
    legacy_mypy = (REPO_ROOT / "mypy.ini").read_text(encoding="utf-8")
    assert "cache_dir = .runtime-cache/local/mypy-cache" in legacy_mypy


def test_unified_gate_and_prepush_reference_new_runtime_governance_guards() -> None:
    unified = (REPO_ROOT / "tooling/scripts/ci/run_unified_test_gate.sh").read_text(
        encoding="utf-8"
    )
    precommit = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    workflow = (REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")

    for token in (
        "check_root_cleanliness.py",
        "check_entrypoint_contract.py",
        "check_output_path_policy.py",
        "check_runtime_surfaces.py",
        "check_layer_boundaries.py",
        "check_frontend_layer_boundaries.mjs",
        "check_frontend_api_contract_drift.py",
        "check_external_surfaces.py",
        "check_open_source_surface.py",
        "check_path_truth_drift.py",
        "check_provider_surface_truth.py",
        "check_selective_port_ledger.py",
        "check_legacy_provider_removal_ledger.py",
        "check_legacy_provider_runtime_imports.py",
        "check_podcasts_topology_mapping.py",
        "check_no_floating_external_inputs.py",
        "check_upstream_compatibility_matrix_sync.py",
        "check_log_contract.py",
        "check_log_sink_integrity.py",
        "check_frontend_log_schema_sync.mjs",
    ):
        assert token in unified
        assert token in workflow
    for token in (
        "check_entrypoint_contract.py",
        "check_output_path_policy.py",
        "check_frontend_layer_boundaries.mjs",
        "check_frontend_api_contract_drift.py",
        "check_open_source_surface.py",
        "check_path_truth_drift.py",
        "check_provider_surface_truth.py",
        "check_selective_port_ledger.py",
        "check_legacy_provider_removal_ledger.py",
        "check_legacy_provider_runtime_imports.py",
        "check_podcasts_topology_mapping.py",
        "check_no_floating_external_inputs.py",
        "check_upstream_compatibility_matrix_sync.py",
        "check_frontend_log_schema_sync.mjs",
    ):
        assert token in precommit
    assert "mutants-top-level-allowlist.json" in (
        REPO_ROOT / "tooling/scripts/ci/check_root_cleanliness.py"
    ).read_text(encoding="utf-8")


def test_frontend_logging_contract_is_wired_into_runtime_entrypoints() -> None:
    unified = (REPO_ROOT / "tooling/scripts/ci/run_unified_test_gate.sh").read_text(
        encoding="utf-8"
    )
    precommit_lint = (REPO_ROOT / "tooling/scripts/ci/pre_commit_lint.sh").read_text(
        encoding="utf-8"
    )
    workflow = (REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")

    token = "check_frontend_logging_contract.py"
    assert token in unified
    assert token in precommit_lint
    assert token in workflow
    assert "check_frontend_log_schema_sync.mjs" in unified
    assert "check_frontend_log_schema_sync.mjs" in precommit_lint
    assert "check_frontend_log_schema_sync.mjs" in workflow


def test_cache_wipe_rebuild_gate_is_wired_into_full_runtime_policy() -> None:
    unified = (REPO_ROOT / "tooling/scripts/ci/run_unified_test_gate.sh").read_text(
        encoding="utf-8"
    )
    workflow = (REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")
    cache_wipe = (
        REPO_ROOT / "tooling/scripts/ci/check_cache_wipe_rebuild.sh"
    ).read_text(encoding="utf-8")

    assert "check_cache_wipe_rebuild.sh fast" in unified
    assert "check_cache_wipe_rebuild.sh fast" in workflow
    for token in (
        "restore_runtime_cache_layout()",
        'source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"',
        'RUNTIME_CACHE_DIR="$(resolve_open_notebook_repo_runtime_cache_dir "${ROOT_DIR}")"',
        'wipe_open_notebook_runtime_cache_contents "${RUNTIME_CACHE_DIR}"',
        "resolve_open_notebook_machine_cache_root",
        "resolve_open_notebook_machine_ci_cache_root",
        "resolve_open_notebook_machine_playwright_cache_dir",
        "resolve_open_notebook_machine_uv_cache_dir",
        "resolve_open_notebook_managed_uv_environment",
        'export OPEN_NOTEBOOK_MACHINE_CACHE_ROOT="${MACHINE_CACHE_ROOT}"',
        'export UV_CACHE_DIR="${UV_CACHE_DIR:-${MACHINE_UV_CACHE_DIR}}"',
        ".runtime-cache/build/egg-info",
    ):
        assert token in cache_wipe, (
            "cache wipe rebuild contract must recreate repo runtime skeleton while keeping machine-level toolchain caches outside the checkout"
        )


def test_runtime_cache_wipe_helper_tolerates_transient_recreation(
    tmp_path: Path,
) -> None:
    cache_dir = tmp_path / ".runtime-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    shell_script = f"""
set -euo pipefail
source "{REPO_ROOT}/tooling/scripts/runtime/cache_env.sh"
cache_dir="{cache_dir}"
mkdir -p "$cache_dir/test/coverage-batches/apps-web"
(
  for _ in $(seq 1 20); do
    mkdir -p "$cache_dir/test/coverage-batches/apps-web"
    : > "$cache_dir/test/coverage-batches/apps-web/race.tmp"
    sleep 0.01
  done
) &
writer_pid=$!
wipe_open_notebook_runtime_cache_contents "$cache_dir"
wait "$writer_pid"
wipe_open_notebook_runtime_cache_contents "$cache_dir"
test -z "$(find "$cache_dir" -mindepth 1 -print -quit)"
"""

    subprocess.run(["bash", "-lc", shell_script], check=True, cwd=REPO_ROOT)


def test_managed_uv_wrapper_uses_machine_level_uv_cache_contract() -> None:
    cache_env = (REPO_ROOT / "tooling/scripts/runtime/cache_env.sh").read_text(
        encoding="utf-8"
    )
    wrapper = (REPO_ROOT / "tooling/scripts/runtime/run_uv_managed.sh").read_text(
        encoding="utf-8"
    )

    for token in (
        "resolve_open_notebook_repo_runtime_cache_dir()",
        "resolve_open_notebook_machine_uv_cache_dir()",
        "printf '%s/python/uv-cache",
        'RUNTIME_CACHE_DIR="$(resolve_open_notebook_repo_runtime_cache_dir "${ROOT_DIR}")"',
        'MACHINE_UV_CACHE_DIR="$(resolve_open_notebook_machine_uv_cache_dir "${MACHINE_CACHE_ROOT}")"',
        'export OPEN_NOTEBOOK_MACHINE_CACHE_ROOT="${MACHINE_CACHE_ROOT}"',
        'export UV_CACHE_DIR="${UV_CACHE_DIR:-${MACHINE_UV_CACHE_DIR}}"',
        'mkdir -p "${UV_CACHE_DIR}"',
    ):
        assert token in cache_env or token in wrapper, (
            "managed uv wrapper must bind wheel cache to the machine-level cache contract so offline rebuilds can reuse pre-warmed artifacts"
        )


def test_managed_uv_wrapper_rebuilds_missing_python_environments() -> None:
    wrapper = (REPO_ROOT / "tooling/scripts/runtime/run_uv_managed.sh").read_text(
        encoding="utf-8"
    )

    assert 'if [[ ! -x "${UV_PROJECT_ENVIRONMENT}/bin/python" ]]; then' in wrapper
    assert "return 0" in wrapper, (
        "managed uv wrapper must treat a missing bin/python inside the managed environment as a broken env that should be rebuilt"
    )


def test_log_event_schema_requires_runtime_correlation_fields() -> None:
    payload = json.loads(
        (REPO_ROOT / "contracts/observability/log-event.schema.json").read_text(
            encoding="utf-8"
        )
    )
    required = set(payload["required"])
    for field in (
        "run_id",
        "request_id",
        "trace_id",
        "user_id",
        "test_id",
        "artifact_group",
        "redaction_version",
    ):
        assert field in required


def test_openapi_contract_exists_and_declares_paths() -> None:
    import yaml

    payload = yaml.safe_load(
        (REPO_ROOT / "contracts/api/openapi.yaml").read_text(encoding="utf-8")
    )
    assert "openapi" in payload
    assert "paths" in payload
    assert payload["paths"], "tracked OpenAPI contract must not be empty"
