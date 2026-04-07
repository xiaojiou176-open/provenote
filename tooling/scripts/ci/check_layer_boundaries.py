#!/usr/bin/env python3
"""Enforce first-party Python layer dependency boundaries."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

IMPORT_RE = re.compile(
    r"^\s*(?:from\s+(?P<from>[A-Za-z_][\w.]*)\s+import\b|import\s+(?P<import>[A-Za-z_][\w.]*))"
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rules",
        default="config/architecture/layer-boundaries.json",
        help="Path to layer boundary rules JSON",
    )
    return parser


def _resolve_layer(rel_path: str, path_layers: list[dict[str, str]]) -> str | None:
    for item in path_layers:
        prefix = str(item.get("prefix", "")).strip()
        if prefix and rel_path.startswith(prefix):
            return str(item.get("layer", "")).strip() or None
    return None


def _module_prefix_for_path_prefix(path_prefix: str) -> str:
    normalized = path_prefix.strip().rstrip("/")
    return normalized.replace("/", ".")


def _first_party_target(
    module_path: str, path_layers: list[dict[str, str]]
) -> str | None:
    for item in path_layers:
        prefix = str(item.get("prefix", "")).strip()
        layer = str(item.get("layer", "")).strip()
        module_prefix = _module_prefix_for_path_prefix(prefix)
        if (
            module_prefix
            and layer
            and (
                module_path == module_prefix
                or module_path.startswith(f"{module_prefix}.")
            )
        ):
            return layer
    return None


def _exception_match(
    rel_path: str,
    import_path: str,
    exception_imports: list[dict[str, str]],
) -> bool:
    for item in exception_imports:
        source = str(item.get("source", "")).strip()
        target_prefix = str(item.get("target_prefix", "")).strip()
        if rel_path == source and import_path.startswith(target_prefix):
            return True
    return False


def _iter_python_files(
    repo_root: Path, path_layers: list[dict[str, str]]
) -> list[Path]:
    files: list[Path] = []
    for item in path_layers:
        prefix = str(item.get("prefix", "")).strip().rstrip("/")
        if not prefix:
            continue
        root = repo_root / prefix
        if not root.exists():
            continue
        files.extend(sorted(root.rglob("*.py")))
    return sorted(dict.fromkeys(files))


def find_boundary_violations(
    repo_root: Path,
    *,
    path_layers: list[dict[str, str]],
    layer_import_rules: dict[str, list[str]],
    exception_imports: list[dict[str, str]],
) -> list[str]:
    violations: list[str] = []
    for file_path in _iter_python_files(repo_root, path_layers):
        rel_path = file_path.relative_to(repo_root).as_posix()
        source_layer = _resolve_layer(rel_path, path_layers)
        if source_layer is None:
            continue
        allowed_targets = set(layer_import_rules.get(source_layer, []))
        for lineno, line in enumerate(
            file_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            match = IMPORT_RE.match(line)
            if match is None:
                continue
            import_path = match.group("from") or match.group("import") or ""
            target_layer = _first_party_target(import_path, path_layers)
            if target_layer is None:
                continue
            if _exception_match(rel_path, import_path, exception_imports):
                continue
            if target_layer not in allowed_targets:
                violations.append(
                    f"{rel_path}:{lineno}: layer '{source_layer}' must not import '{import_path}' (target layer '{target_layer}')"
                )
    return violations


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    payload = _load_json((repo_root / args.rules).resolve())

    path_layers = payload.get("path_layers", [])
    layer_import_rules = payload.get("layer_import_rules", {})
    exception_imports = payload.get("exception_imports", [])
    failures: list[str] = []

    if not isinstance(path_layers, list) or not path_layers:
        failures.append("path_layers must be a non-empty array")
    if not isinstance(layer_import_rules, dict) or not layer_import_rules:
        failures.append("layer_import_rules must be a non-empty object")
    if not isinstance(exception_imports, list):
        failures.append("exception_imports must be a list")

    violations = find_boundary_violations(
        repo_root,
        path_layers=path_layers if isinstance(path_layers, list) else [],
        layer_import_rules=layer_import_rules
        if isinstance(layer_import_rules, dict)
        else {},
        exception_imports=exception_imports
        if isinstance(exception_imports, list)
        else [],
    )
    failures.extend(violations)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: Python layer boundary rules hold for first-party imports.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
