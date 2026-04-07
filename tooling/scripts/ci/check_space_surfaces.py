#!/usr/bin/env python3
"""Validate the disk space governance registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_FIELDS = (
    "name",
    "path",
    "scope",
    "ownership",
    "kind",
    "rebuildability",
    "retention_class",
    "default_action",
    "inventory_class",
    "owner_evidence",
    "rebuild_command",
    "notes",
)

ENUMS = {
    "scope": {"repo_internal", "repo_external"},
    "ownership": {
        "exclusive",
        "shared_primary",
        "shared",
        "unknown",
        "historical_candidate",
    },
    "kind": {
        "dependency",
        "runtime_cache",
        "evidence",
        "backup",
        "state",
        "browser_state",
        "tooling",
        "git_metadata",
    },
    "rebuildability": {
        "immediate",
        "costly",
        "network_required",
        "unknown",
        "not_rebuildable",
    },
    "retention_class": {
        "ephemeral",
        "rebuildable",
        "evidence",
        "protected",
        "shared_layer",
    },
    "default_action": {
        "safe_clear",
        "cautious_clear",
        "verify_before_clear",
        "do_not_clear",
    },
    "inventory_class": {
        "repo_managed_candidate",
        "advisory_only",
    },
}

REQUIRED_SURFACES = {
    "apps-web-node-modules": {
        "path": "apps/web/node_modules",
        "default_action": "cautious_clear",
    },
    "apps-web-nextjs-cache": {
        "path": "apps/web/.runtime-cache/build/next/cache",
        "default_action": "cautious_clear",
    },
    "repo-runtime-ruff-cache": {
        "path": ".runtime-cache/local/ruff-cache",
        "default_action": "cautious_clear",
    },
    "repo-runtime-mypy-cache": {
        "path": ".runtime-cache/local/mypy-cache",
        "default_action": "cautious_clear",
    },
    "repo-runtime-apps-web-coverage-dir": {
        "path": ".runtime-cache/test/coverage/apps/web",
        "default_action": "verify_before_clear",
    },
    "repo-runtime-apps-web-coverage-batches": {
        "path": ".runtime-cache/test/coverage-batches/apps-web",
        "default_action": "verify_before_clear",
    },
    "repo-runtime-apps-web-direct-coverage-dir": {
        "path": ".runtime-cache/test/coverage/apps/web-direct",
        "default_action": "verify_before_clear",
    },
    "repo-runtime-manual-front-a": {
        "path": ".runtime-cache/manual-front-a",
        "default_action": "verify_before_clear",
    },
    "repo-runtime-manual-front-b": {
        "path": ".runtime-cache/manual-front-b",
        "default_action": "verify_before_clear",
    },
    "repo-runtime-coverage-artifact-staging": {
        "path": ".runtime-cache/tmp/coverage-artifact",
        "default_action": "safe_clear",
    },
    "repo-runtime-history-rebuild": {
        "path": ".runtime-cache/history-rebuild",
        "default_action": "verify_before_clear",
    },
    "repo-runtime-final-release-proof-snapshots": {
        "path": ".runtime-cache/runs/final-release-proof-*",
        "default_action": "verify_before_clear",
    },
    "repo-git-cursor-dir": {
        "path": ".git/cursor",
        "default_action": "verify_before_clear",
    },
    "repo-git-dir": {"path": ".git", "default_action": "do_not_clear"},
    "repo-git-objects": {"path": ".git/objects", "default_action": "do_not_clear"},
    "mutants-worktree": {
        "path": "mutants",
        "default_action": "verify_before_clear",
    },
    "repo-managed-uv-project-environment": {
        "path": ".runtime-cache/venv/default",
        "default_action": "verify_before_clear",
    },
    "repo-ci-host-bootstrap-frontend-cache-root": {
        "path": ".runtime-cache/ci-host/bootstrap/apps-web-node-modules",
        "default_action": "verify_before_clear",
    },
    "repo-ci-host-python-uv-cache": {
        "path": ".runtime-cache/ci-host/home-cache/provenote/python/uv-cache",
        "default_action": "cautious_clear",
    },
    "repo-ci-host-python-uv-project-environment": {
        "path": ".runtime-cache/ci-host/home-cache/provenote/python/uv-project-environment",
        "default_action": "verify_before_clear",
    },
    "repo-ci-host-pre-commit-home": {
        "path": ".runtime-cache/ci-host/home-cache/pre-commit",
        "default_action": "cautious_clear",
    },
    "repo-ci-host-go-build-cache": {
        "path": ".runtime-cache/ci-host/home-cache/go-build",
        "default_action": "cautious_clear",
    },
    "repo-ci-host-tmp": {
        "path": ".runtime-cache/ci-host/tmp",
        "default_action": "safe_clear",
    },
    "shared-npm-cache": {
        "path": "${HOME}/.npm",
        "retention_class": "shared_layer",
    },
    "shared-uv-cache": {
        "path": "${HOME}/.cache/uv",
        "retention_class": "shared_layer",
    },
    "shared-system-playwright-cache": {
        "path": "${HOME}/Library/Caches/ms-playwright",
        "retention_class": "shared_layer",
    },
    "shared-docker-desktop": {
        "path": "${HOME}/Library/Containers/com.docker.docker",
        "retention_class": "shared_layer",
    },
    "machine-ci-host-npm-cache": {
        "path": "${HOME}/.cache/provenote/ci-host/npm-cache",
        "default_action": "cautious_clear",
    },
    "machine-tooling-bin": {
        "path": "${HOME}/.cache/provenote/tooling/bin",
        "default_action": "verify_before_clear",
    },
    "machine-browser-chrome-user-data": {
        "path": "${HOME}/.cache/provenote/browser/chrome-user-data",
        "default_action": "do_not_clear",
    },
}

ALLOWED_REPO_EXTERNAL_EXCLUSIVE_SURFACES = {
    "machine-uv-cache",
    "machine-playwright-cache",
    "machine-ci-host-npm-cache",
    "machine-tooling-bin",
    "machine-browser-chrome-user-data",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        default="config/runtime/space-surfaces.json",
        help="Path to space surfaces registry JSON",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    registry_path = (REPO_ROOT / args.registry).resolve()
    payload = _load_json(registry_path)
    surfaces = payload.get("surfaces", [])
    failures: list[str] = []

    if not isinstance(surfaces, list) or not surfaces:
        print("FAIL: space surfaces registry must declare a non-empty surfaces list")
        return 1

    seen_names: set[str] = set()
    indexed: dict[str, dict[str, Any]] = {}
    for item in surfaces:
        if not isinstance(item, dict):
            failures.append("space surface entries must be objects")
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            failures.append(f"space surface missing name: {item}")
            continue
        if name in seen_names:
            failures.append(f"duplicate space surface name: {name}")
        seen_names.add(name)
        indexed[name] = item

        for field in REQUIRED_FIELDS:
            if field == "rebuild_command":
                if field not in item:
                    failures.append(
                        f"space surface {name} missing required field {field}"
                    )
                continue
            if not str(item.get(field, "")).strip():
                failures.append(f"space surface {name} missing required field {field}")

        for field, allowed in ENUMS.items():
            value = str(item.get(field, "")).strip()
            if value and value not in allowed:
                failures.append(
                    f"space surface {name} has invalid {field}={value!r}; expected one of {sorted(allowed)}"
                )

        path_kind = str(item.get("path_kind", "path")).strip() or "path"
        if path_kind not in {"path", "glob"}:
            failures.append(
                f"space surface {name} has invalid path_kind={path_kind!r}; expected 'path' or 'glob'"
            )

        owner_evidence = str(item.get("owner_evidence", "")).strip()
        if owner_evidence and owner_evidence.startswith("${HOME}") is False:
            if not (REPO_ROOT / owner_evidence).exists():
                failures.append(
                    f"space surface {name} owner_evidence missing in repo: {owner_evidence}"
                )

        if (
            str(item.get("retention_class", "")).strip() == "shared_layer"
            and str(item.get("default_action", "")).strip() != "do_not_clear"
        ):
            failures.append(
                f"space surface {name} is shared_layer and must use default_action=do_not_clear"
            )

        cleanup_owner = str(item.get("cleanup_owner", "")).strip()
        scope = str(item.get("scope", "")).strip()
        ownership = str(item.get("ownership", "")).strip()
        retention_class = str(item.get("retention_class", "")).strip()
        default_action = str(item.get("default_action", "")).strip()
        inventory_class = str(item.get("inventory_class", "")).strip()

        if cleanup_owner and retention_class == "shared_layer":
            failures.append(
                f"space surface {name} must not declare cleanup_owner for shared_layer surfaces"
            )

        if cleanup_owner and scope == "repo_external" and ownership != "exclusive":
            failures.append(
                f"space surface {name} must not declare cleanup_owner unless repo_external ownership is exclusive"
            )

        expected_inventory_class = "advisory_only"
        if scope == "repo_internal" and default_action in {
            "safe_clear",
            "cautious_clear",
        }:
            expected_inventory_class = "repo_managed_candidate"
        elif (
            scope == "repo_external"
            and ownership == "exclusive"
            and default_action in {"safe_clear", "cautious_clear"}
            and retention_class != "shared_layer"
        ):
            expected_inventory_class = "repo_managed_candidate"

        if inventory_class != expected_inventory_class:
            failures.append(
                f"space surface {name} must use inventory_class={expected_inventory_class!r}, got {inventory_class!r}"
            )

        if scope == "repo_external" and ownership == "exclusive":
            if name not in ALLOWED_REPO_EXTERNAL_EXCLUSIVE_SURFACES:
                failures.append(
                    f"space surface {name} must not remain machine-wide; only download-cache surfaces may stay under repo_external/exclusive"
                )

    for name, expected in REQUIRED_SURFACES.items():
        item = indexed.get(name)
        if item is None:
            failures.append(f"required space surface missing: {name}")
            continue
        for field, expected_value in expected.items():
            if item.get(field) != expected_value:
                failures.append(
                    f"space surface {name} must set {field}={expected_value!r}, got {item.get(field)!r}"
                )

    machine_cache_policy = payload.get("machine_cache_policy")
    if not isinstance(machine_cache_policy, dict):
        failures.append("machine_cache_policy must be declared as an object")
    else:
        required_policy_keys = {
            "clearable_root_cap_bytes",
            "historical_max_age_days",
            "bootstrap_stale_max_age_days",
            "bootstrap_keep_generations",
        }
        missing_policy_keys = sorted(
            required_policy_keys.difference(machine_cache_policy)
        )
        if missing_policy_keys:
            failures.append(
                "machine_cache_policy missing required keys: "
                + ", ".join(missing_policy_keys)
            )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        f"PASS: space surfaces registry is well-formed and covers guarded cleanup/shared-layer classifications ({len(surfaces)} surfaces)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
