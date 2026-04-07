#!/usr/bin/env python3
"""Validate apps/web Playwright action matrix contract."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ALLOWED_SELECTOR_TYPES = {"data-testid", "id", "role"}
ALLOWED_RUNTIME_LAYERS = {"ui-ready", "network-contract", "payload-shape"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--matrix",
        default="apps/web/e2e/action-matrix.json",
        help="Path to action matrix JSON file (relative to repo root by default).",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Override repository root. Defaults to script parents[3].",
    )
    parser.add_argument(
        "--runtime-evidence",
        default=None,
        help="Optional runtime evidence JSON path. Relative paths resolve from repo root.",
    )
    parser.add_argument(
        "--require-runtime-evidence",
        action="store_true",
        help="Fail when --runtime-evidence is missing and runtime contracts exist.",
    )
    return parser


def _resolve_repo_root(value: str | None) -> Path:
    if value:
        return Path(value).resolve()
    return Path(__file__).resolve().parents[3]


def _resolve_matrix_path(repo_root: Path, matrix_arg: str) -> Path:
    matrix_path = Path(matrix_arg)
    if matrix_path.is_absolute():
        return matrix_path
    return (repo_root / matrix_path).resolve()


def _resolve_optional_path(repo_root: Path, raw_path: str | None) -> Path | None:
    if raw_path is None:
        return None
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{label} root must be a JSON object")
    return payload


def _validate_expected_counts(expected_counts: Any) -> tuple[dict[str, int], list[str]]:
    errors: list[str] = []
    if not isinstance(expected_counts, dict):
        return {}, [
            "FAIL [ACTION-MATRIX-SCHEMA-001]: meta.expected_counts must be an object."
        ]
    required = ("total", "data-testid", "id", "role")
    out: dict[str, int] = {}
    for key in required:
        value = expected_counts.get(key)
        if not isinstance(value, int) or value < 0:
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-002]: meta.expected_counts.{key} must be a non-negative integer."
            )
            continue
        out[key] = value
    return out, errors


def _selector_present(selector_type: str, selector: str, content: str) -> bool:
    probes: tuple[str, ...]
    if selector_type == "data-testid":
        probes = (
            f'data-testid="{selector}"',
            f"data-testid='{selector}'",
            selector,
        )
    elif selector_type == "role":
        _, _, label = selector.partition(":")
        role_label = label.strip().lower()
        role_tokens = tuple(
            token for token in role_label.replace("/", " ").split() if token
        )
        lowered_content = content.lower()
        return (
            "getByRole" in content
            and all(token in lowered_content for token in role_tokens)
        ) or (role_label != "" and role_label in lowered_content)
    else:
        probes = (
            f'id="{selector}"',
            f"id='{selector}'",
            f"#{selector}",
            selector,
        )
    return any(probe in content for probe in probes)


def _validate_playwright(selector_type: str, selector: str, playwright: str) -> bool:
    if selector_type == "data-testid":
        return "getByTestId" in playwright or "data-testid" in playwright
    if selector_type == "role":
        role_name, _, label = selector.partition(":")
        normalized_role = role_name.strip()
        normalized_label = label.strip().lower()
        label_tokens = tuple(
            token for token in normalized_label.replace("/", " ").split() if token
        )
        lowered_playwright = playwright.lower()
        return (
            "getByRole" in playwright
            and normalized_role in lowered_playwright
            and (
                not label_tokens
                or all(token in lowered_playwright for token in label_tokens)
            )
        )
    return f"#{selector}" in playwright


def _validate_actions(
    actions: Any,
    repo_root: Path,
) -> tuple[list[str], Counter[str], list[dict[str, Any]]]:
    errors: list[str] = []
    counts: Counter[str] = Counter()
    runtime_requirements: list[dict[str, Any]] = []
    if not isinstance(actions, list):
        return (
            ["FAIL [ACTION-MATRIX-SCHEMA-003]: actions must be an array."],
            counts,
            runtime_requirements,
        )

    seen_ids: set[str] = set()
    content_cache: dict[Path, str] = {}

    required_fields = (
        "action_id",
        "route",
        "selector_type",
        "selector",
        "playwright",
        "expected_result",
        "test_type",
        "spec_id",
        "paths",
    )
    for index, action in enumerate(actions):
        prefix = f"actions[{index}]"
        if not isinstance(action, dict):
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-004]: {prefix} must be an object."
            )
            continue

        missing_fields = [field for field in required_fields if field not in action]
        if missing_fields:
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-005]: {prefix} missing fields: {', '.join(missing_fields)}."
            )
            continue

        action_id = action["action_id"]
        route = action["route"]
        selector_type = action["selector_type"]
        selector = action["selector"]
        playwright = action["playwright"]
        expected_result = action["expected_result"]
        test_type = action["test_type"]
        spec_id = action["spec_id"]
        paths = action["paths"]

        if not isinstance(action_id, str) or not action_id.strip():
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-006]: {prefix}.action_id must be a non-empty string."
            )
            continue
        if action_id in seen_ids:
            errors.append(
                f"FAIL [ACTION-MATRIX-UNIQUE-001]: duplicate action_id `{action_id}`."
            )
        seen_ids.add(action_id)

        if not isinstance(route, str) or not route.strip():
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-015]: {prefix}.route must be a non-empty string."
            )

        if not isinstance(expected_result, str) or not expected_result.strip():
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-016]: {prefix}.expected_result must be a non-empty string."
            )

        if test_type not in {
            "mocked",
            "real-backend",
            "live",
            "a11y",
            "cross-browser-smoke",
        }:
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-017]: {prefix}.test_type `{test_type}` is invalid."
            )

        if not isinstance(spec_id, str) or not spec_id.strip():
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-018]: {prefix}.spec_id must be a non-empty string."
            )
        runtime_evidence = action.get("runtime_evidence")
        if test_type == "real-backend":
            if not isinstance(runtime_evidence, dict):
                errors.append(
                    f"FAIL [ACTION-MATRIX-SCHEMA-019]: {prefix}.runtime_evidence must be an object for real-backend actions."
                )
            else:
                runtime_action_id = runtime_evidence.get("action_id")
                required_layers = runtime_evidence.get("required_layers")
                runtime_action_id_ok = isinstance(runtime_action_id, str) and bool(
                    runtime_action_id.strip()
                )
                if not runtime_action_id_ok:
                    errors.append(
                        f"FAIL [ACTION-MATRIX-SCHEMA-020]: {prefix}.runtime_evidence.action_id must be a non-empty string."
                    )
                elif runtime_action_id != action_id:
                    errors.append(
                        "FAIL [ACTION-MATRIX-SCHEMA-021]: "
                        f"{prefix}.runtime_evidence.action_id `{runtime_action_id}` must match action_id `{action_id}`."
                    )

                valid_layers: list[str] = []
                if not isinstance(required_layers, list) or not required_layers:
                    errors.append(
                        f"FAIL [ACTION-MATRIX-SCHEMA-022]: {prefix}.runtime_evidence.required_layers must be a non-empty array."
                    )
                else:
                    for layer_index, layer in enumerate(required_layers):
                        if (
                            not isinstance(layer, str)
                            or layer not in ALLOWED_RUNTIME_LAYERS
                        ):
                            errors.append(
                                "FAIL [ACTION-MATRIX-SCHEMA-023]: "
                                f"{prefix}.runtime_evidence.required_layers[{layer_index}] `{layer}` is invalid."
                            )
                            continue
                        valid_layers.append(layer)
                if runtime_action_id_ok and valid_layers:
                    runtime_requirements.append(
                        {
                            "action_id": runtime_action_id,
                            "spec_id": spec_id,
                            "required_layers": set(valid_layers),
                        }
                    )
        elif runtime_evidence is not None and not isinstance(runtime_evidence, dict):
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-024]: {prefix}.runtime_evidence must be an object when present."
            )

        if selector_type not in ALLOWED_SELECTOR_TYPES:
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-007]: {prefix}.selector_type `{selector_type}` is invalid."
            )
            continue
        if not isinstance(selector, str) or not selector.strip():
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-008]: {prefix}.selector must be a non-empty string."
            )
            continue
        if not isinstance(playwright, str) or not playwright.strip():
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-009]: {prefix}.playwright must be a non-empty string."
            )
            continue

        if not _validate_playwright(selector_type, selector, playwright):
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-010]: {prefix}.playwright does not match selector `{selector}`."
            )

        counts[selector_type] += 1

        if not isinstance(paths, list) or not paths:
            errors.append(
                f"FAIL [ACTION-MATRIX-SCHEMA-011]: {prefix}.paths must be a non-empty array."
            )
            continue

        found_selector = False
        for path_index, raw_path in enumerate(paths):
            if not isinstance(raw_path, str) or not raw_path.strip():
                errors.append(
                    f"FAIL [ACTION-MATRIX-SCHEMA-012]: {prefix}.paths[{path_index}] must be a non-empty string."
                )
                continue
            if raw_path.startswith("/") or raw_path.startswith("../"):
                errors.append(
                    f"FAIL [ACTION-MATRIX-PATH-001]: {prefix}.paths[{path_index}] must be repo-relative: `{raw_path}`."
                )
                continue

            file_path = (repo_root / raw_path).resolve()
            if not file_path.is_file():
                errors.append(
                    f"FAIL [ACTION-MATRIX-PATH-002]: {prefix}.paths[{path_index}] does not exist: `{raw_path}`."
                )
                continue

            if file_path not in content_cache:
                content_cache[file_path] = file_path.read_text(encoding="utf-8")
            if _selector_present(selector_type, selector, content_cache[file_path]):
                found_selector = True

        if not found_selector:
            errors.append(
                "FAIL [ACTION-MATRIX-EVIDENCE-001]: "
                f"{prefix} selector `{selector_type}:{selector}` not found in any declared path."
            )

    return errors, counts, runtime_requirements


def _validate_runtime_evidence(
    runtime_payload: dict[str, Any],
    runtime_requirements: list[dict[str, Any]],
) -> tuple[list[str], int]:
    errors: list[str] = []
    entries = runtime_payload.get("entries")
    if not isinstance(entries, list):
        return (
            [
                "FAIL [ACTION-MATRIX-RUNTIME-003]: runtime evidence must contain an `entries` array."
            ],
            0,
        )

    indexed_entries: dict[str, list[dict[str, Any]]] = {}
    for index, entry in enumerate(entries):
        prefix = f"entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(
                f"FAIL [ACTION-MATRIX-RUNTIME-004]: {prefix} must be an object."
            )
            continue
        action_id = entry.get("action_id")
        spec_id = entry.get("spec_id")
        layers = entry.get("layers")
        if not isinstance(action_id, str) or not action_id.strip():
            errors.append(
                f"FAIL [ACTION-MATRIX-RUNTIME-005]: {prefix}.action_id must be a non-empty string."
            )
            continue
        if not isinstance(spec_id, str) or not spec_id.strip():
            errors.append(
                f"FAIL [ACTION-MATRIX-RUNTIME-006]: {prefix}.spec_id must be a non-empty string."
            )
            continue
        if not isinstance(layers, list) or not layers:
            errors.append(
                f"FAIL [ACTION-MATRIX-RUNTIME-007]: {prefix}.layers must be a non-empty array."
            )
            continue

        parsed_layers: set[str] = set()
        has_invalid_layer = False
        for layer_index, layer in enumerate(layers):
            if not isinstance(layer, str) or layer not in ALLOWED_RUNTIME_LAYERS:
                errors.append(
                    "FAIL [ACTION-MATRIX-RUNTIME-008]: "
                    f"{prefix}.layers[{layer_index}] `{layer}` is invalid."
                )
                has_invalid_layer = True
                continue
            parsed_layers.add(layer)
        if has_invalid_layer:
            continue
        indexed_entries.setdefault(action_id, []).append(
            {"spec_id": spec_id, "layers": parsed_layers}
        )

    validated_count = 0
    for requirement in runtime_requirements:
        action_id = requirement["action_id"]
        spec_id = requirement["spec_id"]
        required_layers = requirement["required_layers"]
        action_entries = indexed_entries.get(action_id, [])
        if not action_entries:
            errors.append(
                "FAIL [ACTION-MATRIX-RUNTIME-009]: "
                f"runtime evidence missing action_id `{action_id}`."
            )
            continue
        spec_entries = [
            entry for entry in action_entries if entry["spec_id"] == spec_id
        ]
        if not spec_entries:
            errors.append(
                "FAIL [ACTION-MATRIX-RUNTIME-010]: "
                f"runtime evidence action_id `{action_id}` missing spec_id `{spec_id}`."
            )
            continue
        if not any(required_layers.issubset(entry["layers"]) for entry in spec_entries):
            required = ", ".join(sorted(required_layers))
            errors.append(
                "FAIL [ACTION-MATRIX-RUNTIME-011]: "
                f"runtime evidence action_id `{action_id}` missing required layers [{required}]."
            )
            continue
        validated_count += 1

    return errors, validated_count


def _validate_matrix(
    payload: dict[str, Any], repo_root: Path
) -> tuple[list[str], dict[str, int], list[dict[str, Any]]]:
    errors: list[str] = []

    version = payload.get("version")
    if not isinstance(version, str) or not version.strip():
        errors.append(
            "FAIL [ACTION-MATRIX-SCHEMA-013]: version must be a non-empty string."
        )

    meta = payload.get("meta")
    if not isinstance(meta, dict):
        errors.append("FAIL [ACTION-MATRIX-SCHEMA-014]: meta must be an object.")
        meta = {}

    expected_counts, count_schema_errors = _validate_expected_counts(
        meta.get("expected_counts")
    )
    errors.extend(count_schema_errors)

    action_errors, observed_counts, runtime_requirements = _validate_actions(
        payload.get("actions"), repo_root
    )
    errors.extend(action_errors)

    observed_total = (
        observed_counts.get("data-testid", 0)
        + observed_counts.get("id", 0)
        + observed_counts.get("role", 0)
    )
    if expected_counts:
        if observed_total != expected_counts["total"]:
            errors.append(
                "FAIL [ACTION-MATRIX-COUNT-001]: "
                f"total mismatch expected={expected_counts['total']} observed={observed_total}."
            )
        if observed_counts.get("data-testid", 0) != expected_counts["data-testid"]:
            errors.append(
                "FAIL [ACTION-MATRIX-COUNT-002]: "
                "data-testid mismatch "
                f"expected={expected_counts['data-testid']} observed={observed_counts.get('data-testid', 0)}."
            )
        if observed_counts.get("id", 0) != expected_counts["id"]:
            errors.append(
                "FAIL [ACTION-MATRIX-COUNT-003]: "
                f"id mismatch expected={expected_counts['id']} observed={observed_counts.get('id', 0)}."
            )
        if observed_counts.get("role", 0) != expected_counts["role"]:
            errors.append(
                "FAIL [ACTION-MATRIX-COUNT-004]: "
                f"role mismatch expected={expected_counts['role']} observed={observed_counts.get('role', 0)}."
            )

    return (
        errors,
        {
            "total": observed_total,
            "data-testid": observed_counts.get("data-testid", 0),
            "id": observed_counts.get("id", 0),
            "role": observed_counts.get("role", 0),
        },
        runtime_requirements,
    )


def main() -> int:
    args = build_parser().parse_args()
    repo_root = _resolve_repo_root(args.repo_root)
    matrix_path = _resolve_matrix_path(repo_root, args.matrix)
    runtime_evidence_path = _resolve_optional_path(repo_root, args.runtime_evidence)

    try:
        payload = _load_json(matrix_path, label="matrix file")
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL [ACTION-MATRIX-LOAD-001]: {exc}")
        return 2

    errors, stats, runtime_requirements = _validate_matrix(payload, repo_root)
    runtime_summary = "runtime=skipped"
    if runtime_evidence_path is not None:
        try:
            runtime_payload = _load_json(
                runtime_evidence_path, label="runtime evidence file"
            )
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
            print(f"FAIL [ACTION-MATRIX-RUNTIME-001]: {exc}")
            return 1
        runtime_errors, runtime_validated_count = _validate_runtime_evidence(
            runtime_payload, runtime_requirements
        )
        errors.extend(runtime_errors)
        runtime_summary = (
            f"runtime={runtime_validated_count}/{len(runtime_requirements)} validated"
        )
    elif args.require_runtime_evidence and runtime_requirements:
        errors.append(
            "FAIL [ACTION-MATRIX-RUNTIME-002]: runtime evidence is required but --runtime-evidence was not provided."
        )
    elif runtime_requirements:
        runtime_summary = (
            f"runtime=not-provided ({len(runtime_requirements)} required actions)"
        )

    if errors:
        for error in errors:
            print(error)
        return 1

    print(
        "PASS [ACTION-MATRIX-001]: "
        f"validated selectors total={stats['total']} "
        f"(data-testid={stats['data-testid']}, id={stats['id']}, role={stats['role']}) "
        f"{runtime_summary} "
        f"from `{matrix_path}`."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
