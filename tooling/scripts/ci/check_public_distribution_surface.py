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
        "live websiteUrl-backed `notebooklab-mcp` entry",
    ),
    "docs/project-status.md": (
        "live Official MCP Registry entry for `notebooklab-mcp`",
    ),
    "docs/distribution.md": (
        "live Official MCP Registry entry for `notebooklab-mcp`",
        "package-backed public artifact is still a later packaging upgrade",
    ),
    "docs/mcp.md": (
        "live websiteUrl-backed entry for `notebooklab-mcp`",
        "the honest boundary is `live registry entry: yes`, `package-backed public artifact: no`, and `other host marketplace listing: no`",
    ),
}

PUBLIC_FRONTDOOR_FORBIDDEN_HREFS = (
    'href="../examples/',
    'href="./examples/',
)

PUBLIC_FRONTDOOR_REQUIRED_HREFS = (
    'href="https://github.com/xiaojiou176-open/notebooklab/blob/main/examples/hosts/README.md"',
)


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

    frontdoor_text = (REPO_ROOT / "docs/index.html").read_text(encoding="utf-8")
    for forbidden in PUBLIC_FRONTDOOR_FORBIDDEN_HREFS:
        if forbidden in frontdoor_text:
            failures.append(
                f"docs/index.html exposes a repo-internal relative path on the public front door: {forbidden}"
            )
    for required in PUBLIC_FRONTDOOR_REQUIRED_HREFS:
        if required not in frontdoor_text:
            failures.append(
                f"docs/index.html missing required public frontdoor link target: {required}"
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
