#!/usr/bin/env python3
"""Guard current-facing public identity surfaces from upstream self-link drift."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_FILES: tuple[str, ...] = (
    "NOTICE.md",
    "MAINTAINERS.md",
)

REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    "README.md": (
        "This repository is a deep, productized fork of the upstream Open Notebook project.",
        "[NOTICE.md](NOTICE.md)",
        "[MAINTAINERS.md](MAINTAINERS.md)",
        "[SUPPORT.md](SUPPORT.md)",
        "[SECURITY.md](SECURITY.md)",
        "[CONTRIBUTING.md](CONTRIBUTING.md)",
    ),
    "SECURITY.md": (
        "[NOTICE.md](NOTICE.md)",
        "[MAINTAINERS.md](MAINTAINERS.md)",
        "this repository's GitHub `Security` tab",
    ),
    "SUPPORT.md": (
        "[SECURITY.md](SECURITY.md)",
        "[MAINTAINERS.md](MAINTAINERS.md)",
    ),
    "CONTRIBUTING.md": (
        "[NOTICE.md](NOTICE.md)",
        "[MAINTAINERS.md](MAINTAINERS.md)",
        "[SUPPORT.md](SUPPORT.md)",
        "[SECURITY.md](SECURITY.md)",
    ),
    "CODEOWNERS": (
        "MAINTAINERS.md",
        "avoids routing review to upstream maintainers",
    ),
    ".github/ISSUE_TEMPLATE/config.yml": (
        "SUPPORT.md",
        "SECURITY.md",
        "Avoid hard-coded upstream contact links",
    ),
    ".github/pull_request_template.md": (
        "[NOTICE.md](../NOTICE.md)",
        "[MAINTAINERS.md](../MAINTAINERS.md)",
        "[SECURITY.md](../SECURITY.md)",
        "[CONTRIBUTING.md](../CONTRIBUTING.md)",
    ),
    ".github/ISSUE_TEMPLATE/installation_issue.yml": (
        "../../docs/installation.md",
        "../../docs/configuration.md",
        "../../SUPPORT.md",
    ),
    ".github/ISSUE_TEMPLATE/bug_report.yml": ("../../CONTRIBUTING.md",),
    ".github/ISSUE_TEMPLATE/feature_request.yml": ("../../CONTRIBUTING.md",),
    "pyproject.toml": (
        "[tool.open_notebook.public_identity]",
        "Current fork public stewardship is repo-local; see MAINTAINERS.md and NOTICE.md.",
        "No off-repo canonical public URL is declared in-tree for this fork; use repo-local docs plus repository GitHub tabs.",
    ),
    "NOTICE.md": (
        "lfnovo/open-notebook",
        "[MAINTAINERS.md](MAINTAINERS.md)",
    ),
    "MAINTAINERS.md": (
        "Current Fork Public Stewardship",
        "[NOTICE.md](NOTICE.md)",
        "[SECURITY.md](SECURITY.md)",
        "[SUPPORT.md](SUPPORT.md)",
    ),
}

FORBIDDEN_CURRENT_FACING_TOKENS: tuple[str, ...] = (
    "https://github.com/lfnovo/open-notebook",
    "lfnovo/open-notebook",
    "@lfnovo",
    "https://www.open-notebook.ai",
    "https://discord.gg/37XJPXfz2w",
    "https://chatgpt.com/g/g-68776e2765b48191bd1bae3f30212631-open-notebook-installation-assistant",
    "https://zdoc.app/",
    "https://api.star-history.com/svg?repos=lfnovo/open-notebook",
    "https://www.star-history.com/#lfnovo/open-notebook",
    "open-notebook-private",
)

CURRENT_FACING_FILES: tuple[str, ...] = (
    "README.md",
    "SECURITY.md",
    "SUPPORT.md",
    "CONTRIBUTING.md",
    "CODEOWNERS",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/installation_issue.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/pull_request_template.md",
)


def _read_text(repo_root: Path, rel_path: str) -> str:
    return (repo_root / rel_path).read_text(encoding="utf-8")


def collect_failures(repo_root: Path = REPO_ROOT) -> list[str]:
    failures: list[str] = []

    for rel_path in REQUIRED_FILES:
        if not (repo_root / rel_path).is_file():
            failures.append(f"required fork stewardship file missing: {rel_path}")

    for rel_path, tokens in REQUIRED_TOKENS.items():
        path = repo_root / rel_path
        if not path.is_file():
            failures.append(f"required public identity surface missing: {rel_path}")
            continue
        text = _read_text(repo_root, rel_path)
        for token in tokens:
            if token not in text:
                failures.append(f"{rel_path} must include token: {token!r}")

    for rel_path in CURRENT_FACING_FILES:
        path = repo_root / rel_path
        if not path.is_file():
            failures.append(f"required current-facing surface missing: {rel_path}")
            continue
        text = _read_text(repo_root, rel_path)
        for token in FORBIDDEN_CURRENT_FACING_TOKENS:
            if token in text:
                failures.append(
                    f"{rel_path} must not contain upstream self-link token: {token!r}"
                )

    return failures


def main() -> int:
    failures = collect_failures()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: current-facing public identity surfaces point to the current fork.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
