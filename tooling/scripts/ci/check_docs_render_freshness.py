#!/usr/bin/env python3
"""Ensure generated governance docs are fresh and remain within declared scope."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _is_under_any_root(path: Path, roots: list[Path]) -> bool:
    return any(root == path or root in path.parents for root in roots)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="config/docs/render-manifest.json")
    parser.add_argument("--scope-registry", default="config/docs/scope-registry.json")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from tooling.scripts.ci.render_governance_docs import TARGET_OUTPUTS, render_target

    manifest = _load_json((repo_root / args.manifest).resolve())
    scope = _load_json((repo_root / args.scope_registry).resolve())

    generated_documents = manifest.get("generated_documents", [])
    if not isinstance(generated_documents, list):
        raise ValueError("generated_documents must be a list")

    first_party_roots = [
        (repo_root / item).resolve() for item in scope.get("first_party_doc_roots", [])
    ]
    excluded_roots = [
        (repo_root / item).resolve() for item in scope.get("excluded_roots", [])
    ]

    failures: list[str] = []
    for item in generated_documents:
        if not isinstance(item, dict):
            failures.append("render manifest entries must be objects")
            continue

        target = str(item.get("renderer", "")).strip()
        path = (repo_root / str(item.get("path", "")).strip()).resolve()
        if not target or target not in TARGET_OUTPUTS:
            failures.append(
                f"unknown render target in manifest: {target or '<missing>'}"
            )
            continue
        if path != TARGET_OUTPUTS[target]:
            failures.append(
                f"manifest path mismatch for renderer {target}: expected {TARGET_OUTPUTS[target]}, got {path}"
            )
            continue
        if not _is_under_any_root(path, first_party_roots):
            failures.append(
                f"generated doc escapes first-party docs scope: {path.relative_to(repo_root)}"
            )
        if _is_under_any_root(path, excluded_roots):
            failures.append(
                f"generated doc is declared under excluded scope: {path.relative_to(repo_root)}"
            )
        if not path.is_file():
            failures.append(f"generated doc missing: {path.relative_to(repo_root)}")
            continue

        expected = render_target(target)
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            failures.append(
                f"generated doc stale: {path.relative_to(repo_root)} (run `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/render_governance_docs.py --write all`)"
            )
        if "<!-- AUTO-GENERATED: DO NOT EDIT DIRECTLY. -->" not in actual:
            failures.append(
                f"generated doc missing auto-generated marker: {path.relative_to(repo_root)}"
            )

    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        return 1

    print(
        f"PASS: generated governance docs are fresh and within declared scope ({len(generated_documents)} files checked)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
