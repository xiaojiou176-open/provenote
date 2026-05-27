from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tooling/scripts/ops/cleanup_machine_cache.py"
WRAPPER = REPO_ROOT / "tooling/scripts/ops/cleanup_machine_cache.sh"


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


def _registry_payload() -> dict[str, object]:
    return {
        "version": 1,
        "policy_note": "tmp",
        "status_columns_note": "tmp",
        "surfaces": [
            {
                "name": "machine-playwright-cache",
                "path": "${HOME}/.cache/notebooklab/playwright/ms-playwright",
                "scope": "repo_external",
                "ownership": "exclusive",
                "kind": "dependency",
                "rebuildability": "network_required",
                "retention_class": "rebuildable",
                "default_action": "cautious_clear",
                "inventory_class": "repo_managed_candidate",
                "owner_evidence": "AGENTS.md",
                "rebuild_command": "",
                "notes": "tmp",
                "ttl_days": 30,
                "max_bytes": 2147483648,
            },
            {
                "name": "machine-uv-cache",
                "path": "${HOME}/.cache/notebooklab/python/uv-cache",
                "scope": "repo_external",
                "ownership": "exclusive",
                "kind": "dependency",
                "rebuildability": "network_required",
                "retention_class": "rebuildable",
                "default_action": "cautious_clear",
                "inventory_class": "repo_managed_candidate",
                "owner_evidence": "AGENTS.md",
                "rebuild_command": "",
                "notes": "tmp",
                "ttl_days": 14,
                "max_bytes": 3221225472,
            },
            {
                "name": "machine-browser-chrome-user-data",
                "path": "${HOME}/.cache/notebooklab/browser/chrome-user-data",
                "scope": "repo_external",
                "ownership": "exclusive",
                "kind": "state",
                "rebuildability": "not_rebuildable",
                "retention_class": "protected",
                "default_action": "do_not_clear",
                "inventory_class": "advisory_only",
                "owner_evidence": "AGENTS.md",
                "rebuild_command": "",
                "notes": "tmp",
            },
            {
                "name": "machine-ci-host",
                "path": "${HOME}/.cache/notebooklab/ci-host",
                "scope": "repo_external",
                "ownership": "exclusive",
                "kind": "tooling",
                "rebuildability": "unknown",
                "retention_class": "protected",
                "default_action": "verify_before_clear",
                "inventory_class": "advisory_only",
                "owner_evidence": "AGENTS.md",
                "rebuild_command": "",
                "notes": "tmp",
            },
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
            {
                "name": "shared-npm-cache",
                "path": "${HOME}/.npm",
                "scope": "repo_external",
                "ownership": "shared",
                "kind": "runtime_cache",
                "rebuildability": "network_required",
                "retention_class": "shared_layer",
                "default_action": "do_not_clear",
                "inventory_class": "advisory_only",
                "owner_evidence": "AGENTS.md",
                "rebuild_command": "",
                "notes": "tmp",
            },
            {
                "name": "shared-uv-cache",
                "path": "${HOME}/.cache/uv",
                "scope": "repo_external",
                "ownership": "shared",
                "kind": "runtime_cache",
                "rebuildability": "network_required",
                "retention_class": "shared_layer",
                "default_action": "do_not_clear",
                "inventory_class": "advisory_only",
                "owner_evidence": "AGENTS.md",
                "rebuild_command": "",
                "notes": "tmp",
            },
        ],
        "machine_cache_policy": {
            "clearable_root_cap_bytes": 1024,
            "historical_max_age_days": 0,
            "bootstrap_stale_max_age_days": 0,
            "bootstrap_keep_generations": 0,
        },
    }


def _write_registry(path: Path) -> None:
    path.write_text(json.dumps(_registry_payload()), encoding="utf-8")


def _touch_old(path: Path) -> None:
    old_epoch = 946684800
    os.utime(path, (old_epoch, old_epoch))


def _build_temp_machine_cache(home: Path) -> tuple[Path, Path, Path]:
    playwright_cache = home / ".cache" / "notebooklab" / "playwright" / "ms-playwright"
    playwright_cache.mkdir(parents=True)
    (playwright_cache / "browser.bin").write_text("browser", encoding="utf-8")
    uv_cache = home / ".cache" / "notebooklab" / "python" / "uv-cache"
    uv_cache.mkdir(parents=True)
    (uv_cache / "wheel.bin").write_text("uv", encoding="utf-8")
    browser_root = home / ".cache" / "notebooklab" / "browser" / "chrome-user-data"
    browser_root.mkdir(parents=True)
    (browser_root / "Local State").write_text("{}", encoding="utf-8")
    (browser_root / "Profile 1").mkdir()

    historical_candidate = home / ".cache" / "notebooklab-rewrite-snapshot"
    historical_candidate.mkdir(parents=True)
    (historical_candidate / "payload.txt").write_text("snapshot", encoding="utf-8")
    _touch_old(historical_candidate)

    bootstrap_root = (
        home
        / ".cache"
        / "notebooklab"
        / "ci-host"
        / "bootstrap"
        / "apps-web-node-modules"
    )
    active_dir = bootstrap_root / _frontend_lock_hash()
    stale_dir = bootstrap_root / ("deadbeef" * 8)
    active_dir.mkdir(parents=True)
    stale_dir.mkdir(parents=True)
    (active_dir / "payload.txt").write_text("active", encoding="utf-8")
    (stale_dir / "payload.txt").write_text("stale", encoding="utf-8")
    _touch_old(stale_dir)

    shared_npm_cache = home / ".npm"
    shared_npm_cache.mkdir(parents=True)
    (shared_npm_cache / "shared.txt").write_text("shared", encoding="utf-8")

    return historical_candidate, active_dir, stale_dir


def test_machine_cache_cleanup_scripts_exist_and_expose_modes() -> None:
    assert SCRIPT.exists()
    assert WRAPPER.exists()
    text = SCRIPT.read_text(encoding="utf-8")
    assert '"audit-only", "dry-run", "apply"' in text
    assert "--include-historical-candidates" in text
    assert "--include-stale-bootstrap-snapshots" in text


def test_machine_cache_cleanup_audit_only_reports_candidates_without_selecting_actions(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    registry_path = tmp_path / "space-surfaces.json"
    _write_registry(registry_path)
    _build_temp_machine_cache(home)

    result = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--registry",
            str(registry_path),
            "--mode",
            "audit-only",
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
    assert payload["summary"]["selected_action_count"] == 0
    registered = {item["name"] for item in payload["registered_clearable_surfaces"]}
    assert "machine-playwright-cache" in registered
    assert "machine-uv-cache" in registered
    assert "machine-browser-chrome-user-data" not in registered
    assert "shared-npm-cache" not in registered
    assert "shared-uv-cache" not in registered


def test_machine_cache_cleanup_dry_run_selects_only_opted_in_historical_and_stale_items(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    registry_path = tmp_path / "space-surfaces.json"
    _write_registry(registry_path)
    historical_candidate, active_dir, stale_dir = _build_temp_machine_cache(home)

    result = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--registry",
            str(registry_path),
            "--mode",
            "dry-run",
            "--format",
            "json",
            "--include-historical-candidates",
            "--include-stale-bootstrap-snapshots",
            "--historical-max-age-days",
            "0",
            "--bootstrap-stale-max-age-days",
            "0",
            "--bootstrap-keep-generations",
            "0",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "HOME": str(home)},
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    selected = {item["path"] for item in payload["planned_actions"] if item["selected"]}
    assert str(historical_candidate) in selected
    assert str(stale_dir) in selected
    assert str(active_dir) not in selected


def test_machine_cache_cleanup_apply_preserves_active_bootstrap_snapshot(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    registry_path = tmp_path / "space-surfaces.json"
    _write_registry(registry_path)
    historical_candidate, active_dir, stale_dir = _build_temp_machine_cache(home)

    result = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--registry",
            str(registry_path),
            "--mode",
            "apply",
            "--format",
            "json",
            "--include-historical-candidates",
            "--include-stale-bootstrap-snapshots",
            "--historical-max-age-days",
            "0",
            "--bootstrap-stale-max-age-days",
            "0",
            "--bootstrap-keep-generations",
            "0",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "HOME": str(home)},
    )

    assert result.returncode == 0, result.stderr
    assert historical_candidate.exists() is False
    assert stale_dir.exists() is False
    assert active_dir.exists() is True


def test_machine_cache_cleanup_apply_preserves_browser_user_data_root(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    registry_path = tmp_path / "space-surfaces.json"
    _write_registry(registry_path)
    _build_temp_machine_cache(home)

    browser_root = home / ".cache" / "notebooklab" / "browser" / "chrome-user-data"

    result = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--registry",
            str(registry_path),
            "--mode",
            "apply",
            "--format",
            "json",
            "--include-historical-candidates",
            "--historical-max-age-days",
            "0",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "HOME": str(home)},
    )

    assert result.returncode == 0, result.stderr
    assert browser_root.exists()
    assert (browser_root / "Local State").exists()
    assert (browser_root / "Profile 1").is_dir()


def test_machine_cache_cleanup_apply_prunes_only_oldest_entries_when_surface_cap_is_hit(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    registry_path = tmp_path / "space-surfaces.json"
    payload = _registry_payload()
    payload["machine_cache_policy"]["clearable_root_cap_bytes"] = 4096
    payload["surfaces"][0]["ttl_days"] = 999
    payload["surfaces"][0]["max_bytes"] = 5000
    registry_path.write_text(json.dumps(payload), encoding="utf-8")

    playwright_cache = home / ".cache" / "notebooklab" / "playwright" / "ms-playwright"
    playwright_cache.mkdir(parents=True)
    old_entry = playwright_cache / "old-browser.bin"
    new_entry = playwright_cache / "new-browser.bin"
    old_entry.write_text("123456", encoding="utf-8")
    new_entry.write_text("12", encoding="utf-8")
    _touch_old(old_entry)

    result = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--registry",
            str(registry_path),
            "--mode",
            "apply",
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
    assert old_entry.exists() is False
    assert new_entry.exists() is True
