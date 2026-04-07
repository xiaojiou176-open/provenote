#!/usr/bin/env python3
"""Validate the single runtime surfaces fact source and key producer bindings."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCAN_GLOBS = (
    "Makefile",
    ".github/workflows/*.yml",
    ".pre-commit-config.yaml",
    "apps/web/package.json",
    "apps/web/playwright.config.ts",
    "apps/web/playwright.live.config.ts",
    "apps/web/vitest.config.mts",
    "apps/web/scripts/run-batched-coverage.mjs",
    "tooling/scripts/**/*.sh",
    "tooling/scripts/**/*.py",
    "docs/**/*.md",
)

REQUIRED_SURFACES = {
    "backend-coverage-xml": ".runtime-cache/test/coverage/backend/coverage.xml",
    "apps-web-coverage-lcov": ".runtime-cache/test/coverage/apps/web/lcov.info",
    "playwright-report": ".runtime-cache/runs/current/evidence/playwright/report",
    "playwright-results": ".runtime-cache/runs/current/evidence/playwright/results",
    "uiux-gemini-bundle": ".runtime-cache/runs/current/evidence/uiux-gemini",
    "live-teardown-evidence-llm": ".runtime-cache/runs/current/evidence/live-teardown/live-llm.jsonl",
    "live-teardown-evidence-external-web": ".runtime-cache/runs/current/evidence/live-teardown/live-external-web.jsonl",
    "release-proof": ".runtime-cache/runs/current/evidence/release-proof",
    "local-logs": ".runtime-cache/runs/current/logs/local",
    "ci-logs": ".runtime-cache/runs/current/logs/ci",
}

REQUIRED_CONFIG_TOKENS = {
    "apps/web/playwright.config.ts": (
        "../../.runtime-cache/runs/current/evidence/playwright/report",
        "../../.runtime-cache/runs/current/evidence/playwright/results",
    ),
    "apps/web/playwright.live.config.ts": (
        "../../.runtime-cache/runs/current/evidence/playwright/report",
        "../../.runtime-cache/runs/current/evidence/playwright/results",
    ),
    "apps/web/vitest.config.mts": ("../../.runtime-cache/test/coverage/apps/web",),
    "apps/web/scripts/run-batched-coverage.mjs": (
        "../../.runtime-cache/test/coverage/apps/web",
    ),
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
        default="config/runtime/runtime-surfaces.json",
        help="Path to runtime surfaces registry JSON",
    )
    return parser


def _scan_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in SCAN_GLOBS:
        files.extend(repo_root.glob(pattern))
    return sorted({path.resolve() for path in files if path.is_file()})


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    registry = _load_json((repo_root / args.registry).resolve())
    surfaces = registry.get("surfaces", [])
    failures: list[str] = []

    if not isinstance(surfaces, list) or not surfaces:
        print("FAIL: runtime surfaces registry must declare a non-empty surfaces list")
        return 1

    indexed: dict[str, dict[str, Any]] = {}
    seen_paths: set[str] = set()
    for item in surfaces:
        if not isinstance(item, dict):
            failures.append("runtime surfaces entries must be objects")
            continue
        for field in (
            "name",
            "kind",
            "canonical_path",
            "producer",
            "consumer",
            "retention_class",
            "scope",
            "ttl_policy",
            "cleanup_owner",
        ):
            if not str(item.get(field, "")).strip():
                failures.append(
                    f"runtime surface missing required field {field}: {item}"
                )
        if not isinstance(item.get("run_correlation_required"), bool):
            failures.append(
                f"runtime surface missing boolean run_correlation_required: {item.get('name', '<unknown>')}"
            )
        if not isinstance(item.get("rebuildable"), bool):
            failures.append(
                f"runtime surface missing boolean rebuildable: {item.get('name', '<unknown>')}"
            )
        if not isinstance(item.get("root_cleanliness_required"), bool):
            failures.append(
                f"runtime surface missing boolean root_cleanliness_required: {item.get('name', '<unknown>')}"
            )
        name = str(item.get("name", "")).strip()
        path = str(item.get("canonical_path", "")).strip()
        if name:
            indexed[name] = item
        if path:
            if path in seen_paths:
                failures.append(f"duplicate canonical runtime surface path: {path}")
            seen_paths.add(path)

    for name, expected_path in REQUIRED_SURFACES.items():
        item = indexed.get(name)
        if item is None:
            failures.append(f"required runtime surface missing: {name}")
            continue
        if item.get("canonical_path") != expected_path:
            failures.append(
                f"runtime surface {name} must use canonical path {expected_path}, got {item.get('canonical_path')}"
            )

    forbidden_paths = registry.get("forbidden_legacy_paths", [])
    if not isinstance(forbidden_paths, list):
        failures.append("forbidden_legacy_paths must be a list")
        forbidden_paths = []

    for file_path in _scan_files(repo_root):
        rel = file_path.relative_to(repo_root).as_posix()
        text = file_path.read_text(encoding="utf-8")
        for forbidden_path in forbidden_paths:
            pattern = re.compile(
                rf"(?<![\\w./-]){re.escape(forbidden_path)}(?![\\w./-])"
            )
            if pattern.search(text):
                failures.append(
                    f"{rel}: references forbidden legacy runtime path {forbidden_path}"
                )

    for rel, tokens in REQUIRED_CONFIG_TOKENS.items():
        text = (repo_root / rel).read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                failures.append(f"{rel}: missing canonical runtime token {token}")

    for item in surfaces:
        if not isinstance(item, dict):
            continue
        workflow = str(item.get("workflow", "")).strip()
        canonical_path = str(item.get("canonical_path", "")).strip()
        consumer = str(item.get("consumer", "")).strip()
        producer = str(item.get("producer", "")).strip()
        if (
            canonical_path
            and item.get("root_cleanliness_required")
            and canonical_path.startswith(".runtime-cache/") is False
        ):
            failures.append(
                f"runtime surface {item.get('name', '<unknown>')} must stay under .runtime-cache when root_cleanliness_required=true"
            )
        if not producer or not consumer:
            failures.append(
                f"runtime surface {item.get('name', '<unknown>')} must declare both producer and consumer"
            )
        if workflow and canonical_path:
            workflow_path = repo_root / workflow
            if not workflow_path.exists():
                failures.append(f"runtime surface workflow missing: {workflow}")
            else:
                workflow_text = workflow_path.read_text(encoding="utf-8")
                if canonical_path not in workflow_text:
                    failures.append(
                        f"{workflow}: canonical runtime surface path not referenced: {canonical_path}"
                    )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        f"PASS: runtime surfaces registry is well-formed, producer configs use canonical paths, and legacy runtime paths are absent ({len(surfaces)} surfaces)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
