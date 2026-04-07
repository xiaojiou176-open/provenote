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
        "config/runtime/space-surfaces.json",
        "config/runtime/sensitive-surface-policy.json",
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
        "tooling/scripts/ci/check_space_surfaces.py",
        "tooling/scripts/ci/check_layer_boundaries.py",
        "tooling/scripts/ci/check_frontend_layer_boundaries.mjs",
        "tooling/scripts/ci/check_cache_wipe_rebuild.sh",
        "tooling/scripts/ci/check_external_surfaces.py",
        "tooling/scripts/ci/check_open_source_surface.py",
        "tooling/scripts/ci/check_sensitive_surface_guard.py",
        "tooling/scripts/ci/check_github_security_alerts.py",
        "tooling/scripts/ci/check_path_truth_drift.py",
        "tooling/scripts/ci/check_provider_surface_truth.py",
        "tooling/scripts/ci/check_commit_authorship_range.sh",
        "tooling/scripts/ci/check_selective_port_ledger.py",
        "tooling/scripts/ci/check_legacy_provider_removal_ledger.py",
        "tooling/scripts/ci/check_legacy_provider_runtime_imports.py",
        "tooling/scripts/ci/check_podcasts_topology_mapping.py",
        "tooling/scripts/ci/export_oci_evidence.py",
        "tooling/scripts/ci/check_no_floating_external_inputs.py",
        "tooling/scripts/ci/check_upstream_compatibility_matrix_sync.py",
        "tooling/scripts/git/temporary_upstream_ref.sh",
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
        "tooling/scripts/ops/audit_space_surfaces.py",
        "tooling/scripts/ops/audit_space_surfaces.sh",
        "tooling/scripts/ops/cleanup_machine_cache.py",
        "tooling/scripts/ops/cleanup_machine_cache.sh",
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
        outputs["apps-web-coverage-lcov"]
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
        "live-teardown-evidence-llm": (
            ".github/workflows/live-integration.yml",
            "test_live_integration_workflow_exports_live_teardown_witness_artifacts",
        ),
        "live-teardown-evidence-external-web": (
            ".github/workflows/live-integration.yml",
            "test_live_integration_workflow_exports_live_teardown_witness_artifacts",
        ),
        "benchmark-results": (
            ".github/workflows/test.yml",
            "test_performance_benchmark_workflow_exports_benchmark_results_evidence",
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


def test_root_allowlist_tracks_root_registry_metadata() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/root/top-level-allowlist.json").read_text(encoding="utf-8")
    )
    assert "server.json" in payload["allowed_files"]


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


def test_final_closure_atomic_exception_is_narrow_and_audited() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/ci/atomic-commit-exceptions.json").read_text(
            encoding="utf-8"
        )
    )
    exception = next(
        item
        for item in payload["exceptions"]
        if item["id"] == "final-closure-gate-runtime-2026-03-26"
    )
    assert exception["pre_commit_branches"] == ["codex/final-closure-exec"]
    assert exception["pre_push_branches"] == ["codex/final-closure-exec", "main"]
    assert exception["subject_regex"] == "^fix\\(ci\\): unblock final closure gates$"
    assert exception["audit_doc"] == "docs/development.md"
    assert exception["expires_on"] == "2026-03-31"
    assert set(exception["required_paths"]) == {
        ".github/workflows/uiux-gemini-gate.yml",
        "docs/development.md",
        "tests/ci/test_atomic_commit_migration_exception.py",
        "tests/ci/test_consistent_container_contract.py",
        "tooling/scripts/ci/check_mutation_guard.py",
        "tooling/scripts/ci/run_in_consistent_container.sh",
    }


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
    precommit_lint = (REPO_ROOT / "tooling/scripts/ci/pre_commit_lint.sh").read_text(
        encoding="utf-8"
    )
    workflow = (REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")

    for token in (
        "check_root_cleanliness.py",
        "check_entrypoint_contract.py",
        "check_output_path_policy.py",
        "check_runtime_surfaces.py",
        "check_space_surfaces.py",
        "check_layer_boundaries.py",
        "check_frontend_layer_boundaries.mjs",
        "check_frontend_api_contract_drift.py",
        "check_external_surfaces.py",
        "check_sensitive_surface_guard.py",
        "check_github_security_alerts.py",
        "check_path_truth_drift.py",
        "check_provider_surface_truth.py",
        "check_commit_authorship_range.sh",
        "check_no_floating_external_inputs.py",
    ):
        assert token in unified
    for token in (
        "check_root_cleanliness.py",
        "check_entrypoint_contract.py",
        "check_output_path_policy.py",
        "check_runtime_surfaces.py",
        "check_space_surfaces.py",
        "check_layer_boundaries.py",
        "check_frontend_layer_boundaries.mjs",
        "check_frontend_api_contract_drift.py",
        "check_external_surfaces.py",
        "check_sensitive_surface_guard.py",
        "check_github_security_alerts.py",
        "check_path_truth_drift.py",
        "check_provider_surface_truth.py",
        "check_commit_authorship_range.sh",
        "check_no_floating_external_inputs.py",
    ):
        assert token in workflow
    for token in (
        "check_commit_authorship_range.sh",
        "check_sensitive_surface_guard.py",
        "check_github_security_alerts.py",
        "check_path_truth_drift.py",
        "check_provider_surface_truth.py",
        "check_navigation_docs_pair.py",
        "check_public_identity_surface.py",
        "check_public_distribution_surface.py",
        "check_public_ci_boundary.py",
    ):
        assert token in precommit
    assert "pre_commit_lint.sh" in precommit
    for token in (
        "check_entrypoint_contract.py",
        "check_space_surfaces.py",
        "check_host_process_safety.py",
        "check_sensitive_surface_guard.py",
        "check_frontend_api_contract_drift.py",
    ):
        assert token in precommit_lint
    assert "mutants-top-level-allowlist.json" in (
        REPO_ROOT / "tooling/scripts/ci/check_root_cleanliness.py"
    ).read_text(encoding="utf-8")


def test_unified_gate_forwards_external_fast_gate_marker_into_container_reexec() -> (
    None
):
    unified = (REPO_ROOT / "tooling/scripts/ci/run_unified_test_gate.sh").read_text(
        encoding="utf-8"
    )

    assert (
        'OPEN_NOTEBOOK_EXTERNAL_PR_FAST_GATE="${OPEN_NOTEBOOK_EXTERNAL_PR_FAST_GATE:-}"'
        in unified
    ), (
        "unified fast gate must forward the external fast-gate marker into the container re-exec so commit governance stays lane-aware"
    )


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


def test_host_process_safety_gate_is_wired_into_runtime_surfaces() -> None:
    precommit_lint = (REPO_ROOT / "tooling/scripts/ci/pre_commit_lint.sh").read_text(
        encoding="utf-8"
    )
    workflow = (REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "check_host_process_safety.py" in precommit_lint
    assert "check_host_process_safety.py" in workflow


def test_sensitive_surface_guard_is_wired_into_runtime_surfaces() -> None:
    precommit = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    precommit_lint = (REPO_ROOT / "tooling/scripts/ci/pre_commit_lint.sh").read_text(
        encoding="utf-8"
    )
    workflow = (REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")
    unified = (REPO_ROOT / "tooling/scripts/ci/run_unified_test_gate.sh").read_text(
        encoding="utf-8"
    )

    token = "check_sensitive_surface_guard.py"
    assert token in precommit
    assert token in precommit_lint
    assert token in workflow
    assert token in unified


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
        "resolve_open_notebook_repo_ci_cache_root",
        "resolve_open_notebook_machine_ci_npm_cache_dir",
        "resolve_open_notebook_machine_playwright_cache_dir",
        "resolve_open_notebook_machine_uv_cache_dir",
        "resolve_open_notebook_repo_managed_uv_environment",
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

    completed = subprocess.run(
        ["bash", "-lc", shell_script],
        check=False,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_directory_content_wipe_preserves_root_mountpoint(tmp_path: Path) -> None:
    target_dir = tmp_path / "uv-project-environment"
    nested_dir = target_dir / "lib" / "python3.12" / "site-packages"
    nested_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "pyvenv.cfg").write_text(
        "home = /usr/bin/python3.12\n", encoding="utf-8"
    )
    (nested_dir / "sample.py").write_text("print('hello')\n", encoding="utf-8")

    shell_script = f"""
set -euo pipefail
source "{REPO_ROOT}/tooling/scripts/runtime/cache_env.sh"
target_dir="{target_dir}"
wipe_open_notebook_directory_contents "$target_dir"
test -d "$target_dir"
test -z "$(find "$target_dir" -mindepth 1 -print -quit)"
"""

    completed = subprocess.run(
        ["bash", "-lc", shell_script],
        check=False,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_managed_uv_wrapper_uses_machine_level_uv_cache_contract() -> None:
    cache_env = (REPO_ROOT / "tooling/scripts/runtime/cache_env.sh").read_text(
        encoding="utf-8"
    )
    wrapper = (REPO_ROOT / "tooling/scripts/runtime/run_uv_managed.sh").read_text(
        encoding="utf-8"
    )

    for token in (
        "resolve_open_notebook_repo_runtime_cache_dir()",
        "resolve_open_notebook_repo_managed_uv_environment()",
        "resolve_open_notebook_machine_uv_cache_dir()",
        "printf '%s/python/uv-cache",
        'RUNTIME_CACHE_DIR="$(resolve_open_notebook_repo_runtime_cache_dir "${ROOT_DIR}")"',
        'UV_PROJECT_ENVIRONMENT="$(resolve_open_notebook_repo_managed_uv_environment "${ROOT_DIR}")"',
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


def test_managed_uv_wrapper_shims_python_to_python3_when_python_is_missing() -> None:
    wrapper = (REPO_ROOT / "tooling/scripts/runtime/run_uv_managed.sh").read_text(
        encoding="utf-8"
    )

    for token in (
        "ensure_python_command_shim()",
        "if command -v python >/dev/null 2>&1; then",
        "if ! command -v python3 >/dev/null 2>&1; then",
        'local shim_dir="${RUNTIME_CACHE_DIR}/shim-bin"',
        'local python_shim="${shim_dir}/python"',
        'if [[ ! -e "${python_shim}" ]]; then',
        'ln -s "$(command -v python3)" "${python_shim}" 2>/dev/null || true',
        'export PATH="${shim_dir}:${PATH}"',
    ):
        assert token in wrapper, (
            "managed uv wrapper must preserve canonical `run python ...` commands by shimming python to python3 when the host only exposes python3"
        )


def test_managed_uv_rebuild_uses_content_wipe_instead_of_mountpoint_delete() -> None:
    cache_env = (REPO_ROOT / "tooling/scripts/runtime/cache_env.sh").read_text(
        encoding="utf-8"
    )
    wrapper = (REPO_ROOT / "tooling/scripts/runtime/run_uv_managed.sh").read_text(
        encoding="utf-8"
    )
    pre_commit_lint = (REPO_ROOT / "tooling/scripts/ci/pre_commit_lint.sh").read_text(
        encoding="utf-8"
    )
    container_bootstrap = (
        REPO_ROOT / "tooling/scripts/ci/run_in_consistent_container.sh"
    ).read_text(encoding="utf-8")

    assert "wipe_open_notebook_directory_contents()" in cache_env
    assert (
        'wipe_open_notebook_directory_contents "${UV_PROJECT_ENVIRONMENT}"' in wrapper
    )
    assert (
        'wipe_open_notebook_directory_contents "${UV_PROJECT_ENVIRONMENT}"'
        in pre_commit_lint
    )
    assert (
        'wipe_open_notebook_directory_contents "$UV_PROJECT_ENVIRONMENT"'
        in container_bootstrap
    )

    for text in (wrapper, pre_commit_lint, container_bootstrap):
        assert 'rm -rf "${UV_PROJECT_ENVIRONMENT}"' not in text
        assert 'rm -rf "$UV_PROJECT_ENVIRONMENT"' not in text


def test_runtime_pre_commit_frontend_lint_matches_ci_workflow_entrypoint() -> None:
    pre_commit_lint = (REPO_ROOT / "tooling/scripts/ci/pre_commit_lint.sh").read_text(
        encoding="utf-8"
    )
    workflow = (REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "npm --prefix apps/web run lint" not in pre_commit_lint
    assert "cd apps/web && npm run lint && cd ../.." in workflow
    assert "cd apps/web\n      npm run lint" in pre_commit_lint


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
