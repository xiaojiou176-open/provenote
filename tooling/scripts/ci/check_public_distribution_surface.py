#!/usr/bin/env python3
"""Guard current-facing public distribution and support surfaces."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

TARGET_FILES = (
    "README.md",
    "docs/index.html",
    "docs/distribution.md",
    "docs/index.md",
    "docs/installation.md",
    "docs/configuration.md",
    "docs/development.md",
    "docs/architecture.md",
    "SUPPORT.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    ".github/workflows/build-and-release.yml",
    ".github/workflows/build-dev.yml",
)

FORBIDDEN_PATTERNS = (
    "lfnovo/open_notebook",
    "ghcr.io/lfnovo/open-notebook",
    "discord.gg/37XJPXfz2w",
    "https://github.com/lfnovo/open-notebook/issues",
)

REQUIRED_FILES = (
    ".github/repo-settings/required-checks.snapshot.md",
    ".github/repo-settings/registry-ownership.snapshot.md",
    ".github/repo-settings/code-quality.snapshot.md",
    ".github/repo-settings/public-surface.snapshot.md",
)

REQUIRED_NEEDLES = {
    "README.md": (
        "live websiteUrl-backed `provenote-mcp` entry",
    ),
    "docs/project-status.md": (
        "live Official MCP Registry entry for `provenote-mcp`",
    ),
    "docs/distribution.md": (
        "live Official MCP Registry entry for `provenote-mcp`",
        "package-backed public artifact is still a later packaging upgrade",
    ),
    "docs/mcp.md": (
        "live websiteUrl-backed entry for `provenote-mcp`",
        "the honest boundary is `live registry entry: yes`, `package-backed public artifact: no`, and `other host marketplace listing: no`",
    ),
}


def main() -> int:
    failures: list[str] = []

    for rel_path in TARGET_FILES:
        text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_PATTERNS:
            if forbidden in text:
                failures.append(
                    f"{rel_path} still contains forbidden current-facing public distribution/support marker: {forbidden}"
                )

    for rel_path in REQUIRED_FILES:
        if not (REPO_ROOT / rel_path).exists():
            failures.append(
                f"required public distribution boundary artifact missing: {rel_path}"
            )

    for rel_path, needles in REQUIRED_NEEDLES.items():
        text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                failures.append(
                    f"{rel_path} missing required distribution truth marker: {needle}"
                )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        "PASS: current-facing public distribution and support surfaces match the repo-local boundary."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
