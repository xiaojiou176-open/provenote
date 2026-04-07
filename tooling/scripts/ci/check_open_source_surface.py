#!/usr/bin/env python3
"""Validate the minimum public collaboration surface for this repository."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_ROOT_FILES = (
    "LICENSE",
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "CODEOWNERS",
    "SUPPORT.md",
)


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def main() -> int:
    failures: list[str] = []

    for rel_path in REQUIRED_ROOT_FILES:
        if not (REPO_ROOT / rel_path).exists():
            failures.append(f"missing required public collaboration file: {rel_path}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    readme = _read("README.md")
    contributing = _read("CONTRIBUTING.md")
    issue_config = _read(".github/ISSUE_TEMPLATE/config.yml")
    security = _read("SECURITY.md")
    support = _read("SUPPORT.md")

    readme_tokens = ("SECURITY.md", "SUPPORT.md", "CODE_OF_CONDUCT.md", "CODEOWNERS")
    for token in readme_tokens:
        if token not in readme:
            failures.append(f"README.md must route users to {token}")

    contributing_tokens = ("SUPPORT.md", "SECURITY.md", "CODE_OF_CONDUCT.md")
    for token in contributing_tokens:
        if token not in contributing:
            failures.append(f"CONTRIBUTING.md must route contributors to {token}")

    issue_config_tokens = (
        "security/policy",
        "SUPPORT.md",
    )
    for token in issue_config_tokens:
        if token not in issue_config:
            failures.append(
                f".github/ISSUE_TEMPLATE/config.yml must include routing token: {token}"
            )

    if (
        "Report a vulnerability" not in security
        and "report a vulnerability" not in security
    ):
        failures.append(
            "SECURITY.md must describe a private vulnerability reporting path"
        )

    if "Security Reports" not in support and "SECURITY.md" not in support:
        failures.append(
            "SUPPORT.md must route security-sensitive issues to SECURITY.md"
        )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: minimum open-source collaboration surface is present and routed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
