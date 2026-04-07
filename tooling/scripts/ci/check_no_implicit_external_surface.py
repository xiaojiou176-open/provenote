#!/usr/bin/env python3
"""Fail closed on undeclared external integration black boxes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FORBIDDEN_PATHS = (
    ".gitmodules",
    "vendor",
    "patches",
)

IGNORED_PACKAGE_JSON_PREFIXES = (
    ".runtime-cache/ci-host/bootstrap/apps-web-node-modules/",
)

FORBIDDEN_PATTERNS = (
    "patchedDependencies",
    '"overrides"',
    '"resolutions"',
    "latest",
)


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
        help="Path to external surfaces registry",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    registry = _load_json((repo_root / args.registry).resolve())
    failures: list[str] = []
    allowed_package_override_surfaces_raw = registry.get(
        "package_override_surfaces", []
    )
    allowed_package_override_surfaces: dict[str, set[str]] = {}

    if not isinstance(allowed_package_override_surfaces_raw, list):
        failures.append(
            "external surfaces registry package_override_surfaces must be a list"
        )
    else:
        for entry in allowed_package_override_surfaces_raw:
            if not isinstance(entry, dict):
                failures.append(
                    "external surfaces registry package_override_surfaces entries must be objects"
                )
                continue

            rel_path = entry.get("path")
            allowed_keys = entry.get("allowed_keys")
            if not isinstance(rel_path, str) or not rel_path:
                failures.append(
                    "external surfaces registry package_override_surfaces entries must declare a non-empty path"
                )
                continue
            if not isinstance(allowed_keys, list) or not all(
                isinstance(item, str) and item for item in allowed_keys
            ):
                failures.append(
                    f"external surfaces registry package_override_surfaces[{rel_path}] must declare non-empty string allowed_keys"
                )
                continue
            allowed_package_override_surfaces[rel_path] = set(allowed_keys)

    for rel_path in FORBIDDEN_PATHS:
        path = repo_root / rel_path
        if path.exists():
            failures.append(
                f"forbidden implicit external surface path present: {rel_path}"
            )

    for package_json in repo_root.rglob("package.json"):
        rel_path = package_json.relative_to(repo_root).as_posix()
        if "node_modules" in package_json.parts or any(
            rel_path.startswith(prefix) for prefix in IGNORED_PACKAGE_JSON_PREFIXES
        ):
            continue
        text = package_json.read_text(encoding="utf-8")
        allowed_keys = allowed_package_override_surfaces.get(rel_path, set())
        for key, pattern in (
            ("patchedDependencies", '"patchedDependencies"'),
            ("overrides", '"overrides"'),
            ("resolutions", '"resolutions"'),
        ):
            if pattern in text and key not in allowed_keys:
                failures.append(
                    f"{rel_path}: forbidden implicit external package override surface {pattern}"
                )

    surfaces = registry.get("surfaces", [])
    if not isinstance(surfaces, list) or not surfaces:
        failures.append("external surfaces registry must be non-empty")

    image_pins = [
        item.get("pin", "")
        for item in surfaces
        if isinstance(item, dict) and item.get("kind") == "image"
    ]
    for pin in image_pins:
        if isinstance(pin, str) and pin.strip().lower() == "latest":
            failures.append(
                "external surfaces registry must not allow latest image pins"
            )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: no implicit external integration black boxes detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
