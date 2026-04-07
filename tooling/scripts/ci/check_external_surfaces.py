#!/usr/bin/env python3
"""Validate semantic upstream/external surfaces inventory for CI/runtime integrations."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "name",
    "kind",
    "source",
    "pin_type",
    "pin",
    "owner",
    "reason",
    "consumer_paths",
    "verification_lane",
    "compatibility_lane",
    "upgrade_playbook",
    "rollback_path",
    "license",
    "security_update_expectation",
    "lifecycle_class",
)

REQUIRED_MARKERS = {
    "upstream-open-notebook-repo": "https://github.com/lfnovo/open-notebook.git",
    "gemini-api": "GEMINI_API_KEY",
    "surrealdb-container-image": "surrealdb/surrealdb:v2.3.10",
    "surrealdb-binary": "CI_SURREAL_",
    "nodejs-binary": "CI_NODE_SHA256",
    "uv-binary-image": "ghcr.io/astral-sh/uv:0.10.9",
    "node-runtime-image": "node:22.22.1-bookworm-slim",
    "ci-base-image": "CI_BASE_IMAGE=",
    "playwright-browser-binaries": "CI_PLAYWRIGHT_VERSION=",
    "ghcr-release-images": "ghcr.io",
    "fastmcp-library": "from fastmcp import FastMCP",
    "content-core-library": "from content_core import extract_content",
    "ai-prompter-library": "from ai_prompter import Prompter",
    "esperanto-library": "from esperanto import (",
    "podcast-creator-library": "from podcast_creator import configure, create_podcast",
}


def _index_by_key(entries: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        raw_key = str(item.get(key, "")).strip()
        if raw_key:
            indexed[raw_key] = item
    return indexed


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        default="config/upstream/external-surfaces.json",
        help="Path to external surfaces registry JSON",
    )
    return parser


def _repo_grep(repo_root: Path, needle: str) -> bool:
    result = subprocess.run(
        ["rg", "-n", "--fixed-strings", needle, "."],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _consumer_path_exists(repo_root: Path, consumer_path: str) -> bool:
    candidate = (repo_root / consumer_path).resolve()
    repo_root_resolved = repo_root.resolve()
    try:
        candidate.relative_to(repo_root_resolved)
    except ValueError:
        return False
    return candidate.exists()


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    registry = _load_json((repo_root / args.registry).resolve())
    runtime_surfaces_registry = _load_json(
        (repo_root / "config/runtime/runtime-surfaces.json").resolve()
    )
    ownership_registry = _load_json(
        (repo_root / "config/upstream/ownership-map.json").resolve()
    )
    pin_registry = _load_json(
        (repo_root / "config/upstream/source-pin-registry.json").resolve()
    )
    patch_registry = _load_json(
        (repo_root / "config/upstream/patch-registry.json").resolve()
    )
    surfaces = registry.get("surfaces", [])
    ownership_entries = ownership_registry.get("owners", [])
    pin_entries = pin_registry.get("pins", [])
    patch_entries = patch_registry.get("entries", [])
    runtime_surfaces = runtime_surfaces_registry.get("surfaces", [])

    failures: list[str] = []
    if not isinstance(surfaces, list) or not surfaces:
        print("FAIL: external surfaces registry must declare a non-empty surfaces list")
        return 1
    if not isinstance(ownership_entries, list):
        failures.append("ownership-map owners must be a list")
        ownership_entries = []
    if not isinstance(pin_entries, list):
        failures.append("source-pin-registry pins must be a list")
        pin_entries = []
    if not isinstance(patch_entries, list):
        failures.append("patch-registry entries must be a list")
        patch_entries = []
    if not isinstance(runtime_surfaces, list):
        failures.append("runtime surfaces registry must declare surfaces as a list")
        runtime_surfaces = []

    indexed: dict[str, dict[str, Any]] = {}
    for item in surfaces:
        if not isinstance(item, dict):
            failures.append("surface entries must be objects")
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            failures.append(f"surface missing name: {item}")
            continue
        indexed[name] = item
        for field in REQUIRED_FIELDS:
            value = item.get(field)
            if field == "consumer_paths":
                if not isinstance(value, list) or not value:
                    failures.append(f"surface {name} missing non-empty consumer_paths")
                continue
            if not str(value or "").strip():
                failures.append(f"surface {name} missing required field {field}")
        if str(item.get("pin", "")).strip().lower() == "latest":
            failures.append(f"surface {name} must not pin to latest")

    for surface_name, marker in REQUIRED_MARKERS.items():
        if surface_name not in indexed:
            failures.append(
                f"required external surface missing from registry: {surface_name}"
            )
            continue
        if not _repo_grep(repo_root, marker):
            failures.append(
                f"registry marker for {surface_name} not found in repo scan: {marker}"
            )

    owners_by_surface = _index_by_key(ownership_entries, "surface")
    pins_by_surface = _index_by_key(pin_entries, "surface")
    patches_by_surface = _index_by_key(patch_entries, "surface")
    runtime_surfaces_by_name = _index_by_key(runtime_surfaces, "name")

    for name, item in indexed.items():
        owner_entry = owners_by_surface.get(name)
        if owner_entry is None:
            failures.append(f"ownership-map missing surface: {name}")
        elif (
            str(owner_entry.get("owner", "")).strip()
            != str(item.get("owner", "")).strip()
        ):
            failures.append(
                f"ownership-map owner mismatch for {name}: {owner_entry.get('owner')} != {item.get('owner')}"
            )

        pin_entry = pins_by_surface.get(name)
        if pin_entry is None:
            failures.append(f"source-pin-registry missing surface: {name}")
        else:
            expected_pin_kind = str(item.get("pin_type", "")).strip()
            if str(pin_entry.get("pin_kind", "")).strip() != expected_pin_kind:
                failures.append(
                    f"source-pin-registry pin_kind mismatch for {name}: {pin_entry.get('pin_kind')} != {expected_pin_kind}"
                )
            if (
                str(pin_entry.get("verification_lane", "")).strip()
                != str(item.get("verification_lane", "")).strip()
            ):
                failures.append(
                    f"source-pin-registry verification_lane mismatch for {name}"
                )

        lifecycle_class = str(item.get("lifecycle_class", "")).strip()
        if (
            "fork" in lifecycle_class
            or "patch" in lifecycle_class
            or "vendor" in lifecycle_class
        ):
            if name not in patches_by_surface:
                failures.append(
                    f"patch-registry missing governed fork/patch surface: {name}"
                )

    for name, item in indexed.items():
        for consumer_path in item.get("consumer_paths", []):
            if not isinstance(consumer_path, str) or not consumer_path.strip():
                failures.append(
                    f"surface {name} has invalid consumer path: {consumer_path!r}"
                )
                continue
            if not _consumer_path_exists(repo_root, consumer_path):
                failures.append(
                    f"surface {name} consumer path does not exist in repo: {consumer_path}"
                )

        if str(item.get("blocking_lane", "")).startswith("tests/live/"):
            witness_surface = str(item.get("witness_artifact_surface", "")).strip()
            witness_test_name = str(item.get("witness_test_name", "")).strip()
            if not witness_surface:
                failures.append(
                    f"live-governed surface {name} must declare witness_artifact_surface"
                )
            elif witness_surface not in runtime_surfaces_by_name:
                failures.append(
                    f"live-governed surface {name} references unknown runtime surface witness {witness_surface}"
                )
            if not witness_test_name:
                failures.append(
                    f"live-governed surface {name} must declare witness_test_name"
                )

            blocking_lane = str(item.get("blocking_lane", "")).strip()
            if blocking_lane:
                blocking_lane_path = repo_root / blocking_lane
                if not blocking_lane_path.exists():
                    failures.append(
                        f"blocking lane path missing for {name}: {blocking_lane}"
                    )
                else:
                    text = blocking_lane_path.read_text(encoding="utf-8")
                    if "LIVE_TEARDOWN_EVIDENCE_FILE" not in text:
                        failures.append(
                            f"blocking lane for {name} must reference LIVE_TEARDOWN_EVIDENCE_FILE"
                        )
                    if witness_test_name and witness_test_name not in text:
                        failures.append(
                            f"blocking lane for {name} missing witness test name {witness_test_name}"
                        )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        f"PASS: external surfaces registry is well-formed and covers required semantic integration markers ({len(indexed)} surfaces)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
