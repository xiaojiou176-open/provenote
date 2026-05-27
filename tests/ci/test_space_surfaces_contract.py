from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_space_surfaces_registry_declares_expected_guardrails() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/runtime/space-surfaces.json").read_text(encoding="utf-8")
    )
    indexed = {item["name"]: item for item in payload["surfaces"]}

    assert indexed["apps-web-node-modules"]["default_action"] == "cautious_clear", (
        "apps/web/node_modules must never be downgraded to safe_clear"
    )
    assert indexed["repo-runtime-ruff-cache"]["default_action"] == "cautious_clear"
    assert indexed["repo-runtime-mypy-cache"]["default_action"] == "cautious_clear"
    assert (
        indexed["apps-web-nextjs-cache"]["path"]
        == "apps/web/.runtime-cache/build/next/cache"
    )
    assert (
        indexed["repo-runtime-apps-web-coverage-dir"]["default_action"]
        == "verify_before_clear"
    )
    assert (
        indexed["repo-runtime-apps-web-coverage-batches"]["default_action"]
        == "verify_before_clear"
    )
    assert (
        indexed["repo-runtime-apps-web-direct-coverage-dir"]["default_action"]
        == "verify_before_clear"
    )
    assert indexed["repo-runtime-manual-front-a"]["default_action"] == (
        "verify_before_clear"
    )
    assert indexed["repo-runtime-manual-front-b"]["default_action"] == (
        "verify_before_clear"
    )
    assert indexed["repo-runtime-coverage-artifact-staging"]["default_action"] == (
        "safe_clear"
    )
    assert indexed["repo-runtime-history-rebuild"]["default_action"] == (
        "verify_before_clear"
    )
    assert (
        indexed["repo-runtime-final-release-proof-snapshots"]["default_action"]
        == "verify_before_clear"
    )
    assert indexed["repo-git-cursor-dir"]["default_action"] == "verify_before_clear"
    assert indexed["repo-git-dir"]["default_action"] == "do_not_clear"
    assert indexed["repo-git-objects"]["default_action"] == "do_not_clear"
    assert indexed["mutants-worktree"]["default_action"] == "verify_before_clear"
    assert indexed["repo-managed-uv-project-environment"]["default_action"] == (
        "verify_before_clear"
    )
    assert indexed["repo-ci-host-bootstrap-frontend-cache-root"]["default_action"] == (
        "verify_before_clear"
    )
    assert indexed["repo-ci-host-python-uv-cache"]["default_action"] == (
        "cautious_clear"
    )
    assert indexed["repo-ci-host-python-uv-project-environment"]["default_action"] == (
        "verify_before_clear"
    )
    assert indexed["repo-ci-host-pre-commit-home"]["default_action"] == (
        "cautious_clear"
    )
    assert indexed["repo-ci-host-go-build-cache"]["default_action"] == (
        "cautious_clear"
    )
    assert indexed["repo-ci-host-tmp"]["default_action"] == "safe_clear"

    for surface_name in (
        "shared-npm-cache",
        "shared-uv-cache",
        "shared-system-playwright-cache",
        "shared-docker-desktop",
    ):
        surface = indexed[surface_name]
        assert surface["retention_class"] == "shared_layer"
        assert surface["default_action"] == "do_not_clear"
        assert surface["inventory_class"] == "advisory_only"

    for surface_name in (
        "machine-playwright-cache",
        "machine-uv-cache",
        "machine-ci-host-npm-cache",
        "machine-browser-chrome-user-data",
        "machine-tooling-bin",
    ):
        surface = indexed[surface_name]
        assert surface["scope"] == "repo_external"
        assert surface["ownership"] == "exclusive"
    assert indexed["machine-browser-chrome-user-data"]["retention_class"] == "protected"
    assert (
        indexed["machine-browser-chrome-user-data"]["default_action"] == "do_not_clear"
    )
    assert (
        indexed["machine-browser-chrome-user-data"]["inventory_class"]
        == "advisory_only"
    )
    assert indexed["machine-tooling-bin"]["default_action"] == "verify_before_clear"
    assert indexed["machine-tooling-bin"]["inventory_class"] == "advisory_only"
    for surface_name in (
        "machine-playwright-cache",
        "machine-uv-cache",
        "machine-ci-host-npm-cache",
    ):
        assert indexed[surface_name]["inventory_class"] == "repo_managed_candidate"

    for removed_surface in (
        "machine-uv-project-environment",
        "machine-ci-host",
        "machine-ci-host-bootstrap-frontend-cache-root",
        "machine-ci-host-python-uv-cache",
        "machine-ci-host-python-uv-project-environment",
        "machine-ci-host-pre-commit-home",
        "machine-ci-host-go-build-cache",
        "machine-ci-host-tmp",
    ):
        assert removed_surface not in indexed

    machine_wide_exclusive = {
        name
        for name, surface in indexed.items()
        if surface["scope"] == "repo_external" and surface["ownership"] == "exclusive"
    }
    assert machine_wide_exclusive == {
        "machine-browser-chrome-user-data",
        "machine-playwright-cache",
        "machine-uv-cache",
        "machine-ci-host-npm-cache",
        "machine-tooling-bin",
    }
    assert payload["machine_cache_policy"]["clearable_root_cap_bytes"] == 6442450944
    assert payload["machine_cache_policy"]["historical_max_age_days"] == 0


def test_local_playwright_commands_use_managed_cache_wrapper() -> None:
    package_json = (REPO_ROOT / "apps/web/package.json").read_text(encoding="utf-8")
    wrapper = (REPO_ROOT / "apps/web/scripts/run-playwright-managed.sh").read_text(
        encoding="utf-8"
    )

    assert "run-playwright-managed.sh install chromium" in package_json
    assert "run-playwright-managed.sh test" in package_json
    assert 'source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"' in wrapper
    assert 'if [[ -z "${PLAYWRIGHT_BROWSERS_PATH:-}" ]]; then' in wrapper
    assert (
        'PLAYWRIGHT_BROWSERS_PATH="$(resolve_open_notebook_machine_playwright_cache_dir "${MACHINE_CACHE_ROOT}")"'
        in wrapper
    )


def test_runtime_entrypoint_machine_cache_auto_clean_keeps_bootstrap_cleanup_manual() -> (
    None
):
    run_uv_managed = (
        REPO_ROOT / "tooling/scripts/runtime/run_uv_managed.sh"
    ).read_text(encoding="utf-8")
    playwright_wrapper = (
        REPO_ROOT / "apps/web/scripts/run-playwright-managed.sh"
    ).read_text(encoding="utf-8")

    for text in (run_uv_managed, playwright_wrapper):
        assert "--include-historical-candidates" in text
        assert "--historical-max-age-days 0" in text
        assert "--include-stale-bootstrap-snapshots" not in text


def test_post_test_housekeeping_dry_run_prints_cleanup_inventory() -> None:
    housekeeping = (
        REPO_ROOT / "tooling/scripts/ci/post_test_housekeeping.sh"
    ).read_text(encoding="utf-8")

    assert "audit_space_surfaces.sh" in housekeeping
    assert "--cleanup-owner cleanup_runtime_cache.sh" in housekeeping
    assert "--action-filter safe_clear,cautious_clear" in housekeeping


def test_space_governance_runbook_mentions_machine_cache_lane() -> None:
    runbook = (REPO_ROOT / "docs/runbooks/space-governance.md").read_text(
        encoding="utf-8"
    )

    assert "cleanup_machine_cache.sh --mode audit-only" in runbook
    assert "--include-stale-bootstrap-snapshots" in runbook
    assert "active-bootstrap-cache" in runbook
    assert "stale-bootstrap-candidate" in runbook
    assert "~/.cache/uv" in runbook


def test_space_surfaces_checker_allows_repo_external_exclusive_candidates() -> None:
    result = subprocess.run(
        [
            "python3",
            "tooling/scripts/ci/check_space_surfaces.py",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_audit_space_surfaces_cli_emits_json_for_custom_registry(
    tmp_path: Path,
) -> None:
    sample_dir = tmp_path / "sample-cache"
    sample_dir.mkdir()
    (sample_dir / "payload.txt").write_text("cache", encoding="utf-8")

    registry_path = tmp_path / "space-surfaces.json"
    registry_path.write_text(
        json.dumps(
            {
                "version": 1,
                "policy_note": "tmp",
                "status_columns_note": "tmp",
                "surfaces": [
                    {
                        "name": "tmp-surface",
                        "path": str(sample_dir),
                        "scope": "repo_external",
                        "ownership": "exclusive",
                        "kind": "runtime_cache",
                        "rebuildability": "immediate",
                        "retention_class": "ephemeral",
                        "default_action": "safe_clear",
                        "owner_evidence": "AGENTS.md",
                        "rebuild_command": "",
                        "notes": "tmp",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "python3",
            "tooling/scripts/ops/audit_space_surfaces.py",
            "--registry",
            str(registry_path),
            "--format",
            "json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    surface = payload["surfaces"][0]
    assert surface["name"] == "tmp-surface"
    assert surface["exists"] is True
    assert surface["ownership_confirmed"] is True
    assert surface["rebuildability_confirmed"] is True
    assert surface["clear_allowed"] is True
    assert surface["size_bytes"] > 0


def test_audit_space_surfaces_distinct_summary_avoids_parent_child_double_count(
    tmp_path: Path,
) -> None:
    root = tmp_path / "cache-root"
    child = root / "child"
    child.mkdir(parents=True)
    (root / "root.bin").write_text("abcd", encoding="utf-8")
    (child / "child.bin").write_text("efgh", encoding="utf-8")

    registry_path = tmp_path / "space-surfaces.json"
    registry_path.write_text(
        json.dumps(
            {
                "version": 1,
                "policy_note": "tmp",
                "status_columns_note": "tmp",
                "surfaces": [
                    {
                        "name": "root-surface",
                        "path": str(root),
                        "scope": "repo_internal",
                        "ownership": "exclusive",
                        "kind": "runtime_cache",
                        "rebuildability": "costly",
                        "retention_class": "rebuildable",
                        "default_action": "cautious_clear",
                        "inventory_class": "repo_managed_candidate",
                        "owner_evidence": "AGENTS.md",
                        "rebuild_command": "",
                        "notes": "tmp",
                    },
                    {
                        "name": "child-surface",
                        "path": str(child),
                        "scope": "repo_internal",
                        "ownership": "exclusive",
                        "kind": "runtime_cache",
                        "rebuildability": "immediate",
                        "retention_class": "ephemeral",
                        "default_action": "safe_clear",
                        "inventory_class": "repo_managed_candidate",
                        "owner_evidence": "AGENTS.md",
                        "rebuild_command": "",
                        "notes": "tmp",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "python3",
            "tooling/scripts/ops/audit_space_surfaces.py",
            "--registry",
            str(registry_path),
            "--format",
            "json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    summary = payload["summary"]
    root_surface = next(
        item for item in payload["surfaces"] if item["name"] == "root-surface"
    )
    child_surface = next(
        item for item in payload["surfaces"] if item["name"] == "child-surface"
    )

    assert summary["repo_internal_bytes_distinct"] == root_surface["size_bytes"]
    assert summary["repo_internal_bytes_distinct"] < (
        root_surface["size_bytes"] + child_surface["size_bytes"]
    )


def test_docker_attribution_requires_more_than_daemon_reachability() -> None:
    import importlib.util

    script_path = REPO_ROOT / "tooling/scripts/ops/audit_space_surfaces.py"
    spec = importlib.util.spec_from_file_location("audit_space_surfaces", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)

    surface = {"requires_daemon_attribution": True}
    assert (
        module._docker_attribution_status(surface, docker_available=False)
        == "unresolved"
    )
    assert (
        module._docker_attribution_status(surface, docker_available=True)
        == "reachable_but_unattributed"
    )


def test_audit_space_surfaces_human_output_uses_distinct_summary_and_no_fake_docker_resolution(
    tmp_path: Path,
) -> None:
    docker_surface = tmp_path / "docker-surface"
    docker_surface.mkdir()
    (docker_surface / "payload.txt").write_text("cache", encoding="utf-8")

    registry_path = tmp_path / "space-surfaces.json"
    registry_path.write_text(
        json.dumps(
            {
                "version": 1,
                "policy_note": "tmp",
                "status_columns_note": "tmp",
                "surfaces": [
                    {
                        "name": "tmp-docker-surface",
                        "path": str(docker_surface),
                        "scope": "repo_external",
                        "ownership": "shared",
                        "kind": "tooling",
                        "rebuildability": "unknown",
                        "retention_class": "shared_layer",
                        "default_action": "do_not_clear",
                        "inventory_class": "advisory_only",
                        "owner_evidence": "AGENTS.md",
                        "rebuild_command": "",
                        "requires_daemon_attribution": True,
                        "notes": "tmp",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "python3",
            "tooling/scripts/ops/audit_space_surfaces.py",
            "--registry",
            str(registry_path),
            "--format",
            "human",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Distinct Summary" in result.stdout
    assert "Docker attribution:" in result.stdout
    assert "Docker attribution: resolved" not in result.stdout


def _frontend_lock_hash() -> str:
    digest = hashlib.sha256()
    for rel_path in (
        "apps/web/package-lock.json",
        "apps/web/package.json",
        "tooling/scripts/ci/run_in_consistent_container.sh",
    ):
        path = REPO_ROOT / rel_path
        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        digest.update(f"{file_hash}  {rel_path}\n".encode("utf-8"))
    return digest.hexdigest()


def test_audit_space_surfaces_reports_named_candidates_and_bootstrap_snapshots(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    candidate_dir = home / ".cache" / "notebooklab-rewrite-snapshot"
    candidate_dir.mkdir(parents=True)
    (candidate_dir / "snapshot.txt").write_text("snapshot", encoding="utf-8")

    bootstrap_root = (
        home
        / ".cache"
        / "notebooklab"
        / "ci-host"
        / "bootstrap"
        / "apps-web-node-modules"
    )
    active_hash = _frontend_lock_hash()
    stale_hash = "deadbeef" * 8
    active_dir = bootstrap_root / active_hash
    stale_dir = bootstrap_root / stale_hash
    active_dir.mkdir(parents=True)
    stale_dir.mkdir(parents=True)
    (active_dir / "payload.txt").write_text("active", encoding="utf-8")
    (stale_dir / "payload.txt").write_text("stale", encoding="utf-8")

    registry_path = tmp_path / "space-surfaces.json"
    registry_path.write_text(
        json.dumps(
            {
                "version": 1,
                "policy_note": "tmp",
                "status_columns_note": "tmp",
                "surfaces": [
                    {
                        "name": "machine-ci-host-bootstrap-frontend-cache-root",
                        "path": "${HOME}/.cache/notebooklab/ci-host/bootstrap/apps-web-node-modules",
                        "scope": "repo_external",
                        "ownership": "exclusive",
                        "kind": "dependency",
                        "rebuildability": "costly",
                        "retention_class": "protected",
                        "default_action": "verify_before_clear",
                        "inventory_class": "advisory_only",
                        "owner_evidence": "AGENTS.md",
                        "rebuild_command": "",
                        "notes": "tmp",
                    },
                    {
                        "name": "historical-notebooklab-cache-candidates",
                        "path": "${HOME}/.cache/notebooklab-*",
                        "path_kind": "glob",
                        "scope": "repo_external",
                        "ownership": "historical_candidate",
                        "kind": "backup",
                        "rebuildability": "unknown",
                        "retention_class": "protected",
                        "default_action": "verify_before_clear",
                        "inventory_class": "advisory_only",
                        "owner_evidence": "AGENTS.md",
                        "rebuild_command": "",
                        "notes": "tmp",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "python3",
            "tooling/scripts/ops/audit_space_surfaces.py",
            "--registry",
            str(registry_path),
            "--format",
            "json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "HOME": str(home)},
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    derived = {item["name"]: item for item in payload["derived_candidates"]}

    assert (
        derived[f"named-candidate:{candidate_dir.name}"]["candidate_status"]
        == "historical-candidate"
    )
    assert (
        derived[f"bootstrap-snapshot:{active_hash}"]["candidate_status"]
        == "active-bootstrap-cache"
    )
    stale_snapshot = derived[f"bootstrap-snapshot:{stale_hash}"]
    assert stale_snapshot["candidate_status"] == "stale-bootstrap-candidate"
    assert stale_snapshot["cleanup_eligible"] is False
