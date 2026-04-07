#!/usr/bin/env python3
"""Fail when current-facing docs regress to known stale canonical paths."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

CURRENT_FACING_DOCS = (
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "tests/README.md",
    "docs/index.md",
    "docs/installation.md",
    "docs/configuration.md",
    "docs/development.md",
    "docs/architecture.md",
    ".github/ISSUE_TEMPLATE/installation_issue.yml",
)

FORBIDDEN_TOKENS = (
    "services/services/api",
    "packages/packages/prompts",
    "tooling/tooling/scripts",
    ".runtime-cache/artifacts/staging",
    "frontend/",
)

BAD_BACKEND_COVERAGE_XML_PATH = "/".join(
    (
        ".runtime-cache/test/coverage/backend",
        ".runtime-cache/test/coverage/backend/coverage.xml",
    )
)

STRICT_COVERAGE_PATH_TARGETS = (
    "CLAUDE.md",
    "Makefile",
    "tests/README.md",
)

STRICT_EXECUTION_SURFACES = (
    ".devcontainer/postCreate.sh",
    "Makefile",
)

FORBIDDEN_EXECUTION_TOKENS = (
    'cd "${ROOT_DIR}/frontend"',
    "lfnovo/open_notebook",
    "ghcr.io/lfnovo/open-notebook",
)


def main() -> int:
    failures: list[str] = []

    for rel_path in CURRENT_FACING_DOCS:
        path = REPO_ROOT / rel_path
        if not path.exists():
            failures.append(
                f"missing current-facing doc tracked by path-truth gate: {rel_path}"
            )
            continue
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            if token in text:
                failures.append(
                    f"{rel_path} contains stale canonical path token: {token}"
                )

    for rel_path in STRICT_COVERAGE_PATH_TARGETS:
        path = REPO_ROOT / rel_path
        if not path.exists():
            failures.append(
                f"missing strict coverage path target tracked by path-truth gate: {rel_path}"
            )
            continue
        text = path.read_text(encoding="utf-8")
        if BAD_BACKEND_COVERAGE_XML_PATH in text:
            failures.append(f"{rel_path} contains duplicated backend coverage XML path")

    for rel_path in STRICT_EXECUTION_SURFACES:
        path = REPO_ROOT / rel_path
        if not path.exists():
            failures.append(
                f"missing strict execution surface tracked by path-truth gate: {rel_path}"
            )
            continue
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_EXECUTION_TOKENS:
            if token in text:
                failures.append(f"{rel_path} contains stale execution token: {token}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: current-facing docs are free of known stale canonical path tokens.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
