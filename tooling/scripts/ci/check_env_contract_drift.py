#!/usr/bin/env python3
"""Ensure the canonical env contract stays aligned with runtime code and defaults."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

ENV_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]+$")
SETTINGS_READERS = {"read_env", "read_env_str", "read_bool", "read_int", "read_float"}
ENV_DEFAULT_ANNOTATION_PATTERN = re.compile(
    r"^\s*#\s*DEFAULT\s+([A-Z][A-Z0-9_]+)\s*=\s*(.*?)\s*$"
)


def normalize_default_value(value: Any) -> str:
    if value is None:
        return "_unset_"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def normalize_annotated_default(value: str) -> str:
    normalized = value.strip().strip('"').strip("'")
    if normalized.lower() in {"_unset_", "unset", "<unset>", "none", "null"}:
        return "_unset_"
    if normalized.lower() in {"true", "false"}:
        return normalized.lower()
    return normalized


def load_contract(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"contract must be an object: {path}")
    return payload


def extract_settings_env_keys(settings_path: Path) -> set[str]:
    tree = ast.parse(
        settings_path.read_text(encoding="utf-8"), filename=str(settings_path)
    )
    keys: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id not in SETTINGS_READERS:
            continue
        if not node.args:
            continue

        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            value = first_arg.value.strip()
            if ENV_KEY_PATTERN.match(value):
                keys.add(value)
    return keys


def extract_google_runtime_keys(repo_root: Path) -> set[str]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from packages.core.settings import GOOGLE_PROVIDER_ENV_VARS

    return {key for key in GOOGLE_PROVIDER_ENV_VARS if ENV_KEY_PATTERN.match(key)}


def extract_legacy_blocklist_keys(repo_root: Path) -> set[str]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from packages.core.settings import LEGACY_PROVIDER_ENV_BLOCKLIST

    return {key for key in LEGACY_PROVIDER_ENV_BLOCKLIST if ENV_KEY_PATTERN.match(key)}


def _extract_get_settings_default_bindings(tree: ast.Module) -> dict[str, Any]:
    local_defaults: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "get_settings":
            for statement in node.body:
                if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                    continue
                target = statement.targets[0]
                if not isinstance(target, ast.Name):
                    continue
                if isinstance(statement.value, ast.Constant):
                    local_defaults[target.id] = statement.value.value
            break
    return local_defaults


def _resolve_simple_default(expr: ast.AST, local_defaults: dict[str, Any]) -> Any:
    if isinstance(expr, ast.Constant):
        return expr.value
    if isinstance(expr, ast.Name):
        return local_defaults.get(expr.id)
    return None


def extract_settings_env_defaults(settings_path: Path) -> dict[str, str]:
    tree = ast.parse(
        settings_path.read_text(encoding="utf-8"), filename=str(settings_path)
    )
    local_defaults = _extract_get_settings_default_bindings(tree)
    defaults: dict[str, str] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id not in SETTINGS_READERS:
            continue
        if len(node.args) < 2:
            continue

        key_arg = node.args[0]
        if not isinstance(key_arg, ast.Constant) or not isinstance(key_arg.value, str):
            continue
        key = key_arg.value.strip()
        if not ENV_KEY_PATTERN.match(key):
            continue

        resolved = _resolve_simple_default(node.args[1], local_defaults)
        defaults[key] = normalize_default_value(resolved)

    return defaults


def extract_env_example_default_annotations(
    env_example_path: Path,
) -> dict[str, tuple[str, int]]:
    annotations: dict[str, tuple[str, int]] = {}
    for line_no, raw_line in enumerate(
        env_example_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        match = ENV_DEFAULT_ANNOTATION_PATTERN.match(raw_line)
        if not match:
            continue
        annotations[match.group(1)] = (
            normalize_annotated_default(match.group(2)),
            line_no,
        )
    return annotations


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", default="config/env-contract.json")
    parser.add_argument("--settings", default="packages/core/settings.py")
    parser.add_argument("--env-example", default=".env.example")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    contract_path = (repo_root / args.contract).resolve()
    settings_path = (repo_root / args.settings).resolve()
    env_example_path = (repo_root / args.env_example).resolve()

    contract = load_contract(contract_path)
    settings_keys = extract_settings_env_keys(settings_path)
    settings_defaults = extract_settings_env_defaults(settings_path)
    google_runtime_keys = extract_google_runtime_keys(repo_root)
    blocked_legacy_keys = extract_legacy_blocklist_keys(repo_root)
    env_defaults = extract_env_example_default_annotations(env_example_path)

    contract_required = contract.get("required", [])
    contract_optional = contract.get("optional", [])
    contract_forbidden = contract.get("forbidden", [])
    blocked_legacy_contract = set(contract.get("blocked_legacy_provider_env_vars", []))
    default_sync_keys = set(contract.get("default_sync_keys", []))

    settings_contract_keys = {
        item["name"]
        for item in [*contract_required, *contract_optional]
        if isinstance(item, dict) and item.get("source") == "settings"
    }
    google_contract_keys = {
        item["name"]
        for item in [*contract_required, *contract_optional]
        if isinstance(item, dict) and item.get("google_runtime") is True
    }
    forbidden_contract_keys = {
        item["name"] for item in contract_forbidden if isinstance(item, dict)
    }

    missing_in_settings = sorted(settings_contract_keys - settings_keys)
    extra_in_settings = sorted(settings_keys - settings_contract_keys)
    forbidden_in_settings = sorted(settings_keys & forbidden_contract_keys)
    missing_in_google_contract = sorted(google_runtime_keys - google_contract_keys)
    extra_in_google_contract = sorted(google_contract_keys - google_runtime_keys)
    blocked_legacy_missing = sorted(blocked_legacy_keys - blocked_legacy_contract)
    blocked_legacy_extra = sorted(blocked_legacy_contract - blocked_legacy_keys)

    default_mismatches: list[tuple[str, str, str, int]] = []
    for item in [*contract_required, *contract_optional]:
        if not isinstance(item, dict):
            continue
        if item.get("source") != "settings":
            continue
        key = item["name"]
        if key not in settings_defaults:
            continue
        contract_default = normalize_default_value(item.get("default"))
        if settings_defaults[key] != contract_default:
            default_mismatches.append(
                (key, contract_default, settings_defaults[key], 0)
            )

    env_example_missing = sorted(
        key for key in default_sync_keys if key not in env_defaults
    )
    env_example_mismatches: list[tuple[str, str, str, int]] = []
    for key in sorted(default_sync_keys):
        if key not in env_defaults or key not in settings_defaults:
            continue
        doc_value, line_no = env_defaults[key]
        code_value = settings_defaults[key]
        if doc_value != code_value:
            env_example_mismatches.append((key, doc_value, code_value, line_no))

    failures: list[str] = []
    if missing_in_settings:
        failures.append(
            "settings.py missing canonical env reads: " + ", ".join(missing_in_settings)
        )
    if extra_in_settings:
        failures.append(
            "settings.py contains non-canonical env reads: "
            + ", ".join(extra_in_settings)
        )
    if forbidden_in_settings:
        failures.append(
            "settings.py still reads forbidden env names: "
            + ", ".join(forbidden_in_settings)
        )
    if missing_in_google_contract:
        failures.append(
            "config/env-contract.json missing Google runtime vars: "
            + ", ".join(missing_in_google_contract)
        )
    if extra_in_google_contract:
        failures.append(
            "config/env-contract.json declares unexpected Google runtime vars: "
            + ", ".join(extra_in_google_contract)
        )
    if blocked_legacy_missing:
        failures.append(
            "config/env-contract.json missing blocked legacy vars: "
            + ", ".join(blocked_legacy_missing)
        )
    if blocked_legacy_extra:
        failures.append(
            "config/env-contract.json has blocked legacy vars not present in settings.py: "
            + ", ".join(blocked_legacy_extra)
        )
    for key, contract_default, settings_default, _ in default_mismatches:
        failures.append(
            f"default mismatch for {key}: contract={contract_default!r}, settings.py={settings_default!r}"
        )
    if env_example_missing:
        failures.append(
            ".env.example missing default annotations for: "
            + ", ".join(env_example_missing)
        )
    for key, doc_value, code_value, line_no in env_example_mismatches:
        failures.append(
            f".env.example default mismatch for {key} (line {line_no}): doc={doc_value!r}, settings.py={code_value!r}"
        )

    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        return 1

    print(
        "PASS: canonical env contract, runtime settings, Google runtime blocklist, and .env.example defaults are aligned "
        f"({len(settings_contract_keys)} settings vars, {len(blocked_legacy_contract)} blocked legacy vars)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
