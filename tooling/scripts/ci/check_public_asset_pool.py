#!/usr/bin/env python3
"""Guard the tracked public-facing asset pool."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

ALLOWED_PUBLIC_ASSET_PREFIXES = (
    "docs/assets/hero/",
    "docs/assets/demo/",
    "docs/assets/proof/",
    "docs/assets/architecture/",
    "docs/assets/social/",
)

ALLOWED_PUBLIC_ASSET_FILES = {
    "docs/assets/architecture/notebooklab-architecture.png",
    "docs/assets/architecture/notebooklab-architecture.svg",
    "docs/assets/demo/notebooklab-quick-result-overview.png",
    "docs/assets/demo/notebooklab-quick-result-overview.svg",
    "docs/assets/hero/notebooklab-hero.png",
    "docs/assets/hero/notebooklab-hero.svg",
    "docs/assets/proof/notebooklab-proof-stack.png",
    "docs/assets/proof/notebooklab-proof-stack.svg",
    "docs/assets/social/notebooklab-social-preview.png",
    "docs/assets/social/notebooklab-social-preview.svg",
}

DISALLOWED_BASENAMES = {
    "notebooklab-quick-result-storyboard.gif",
}


def git_ls_files(*patterns: str) -> list[str]:
    cmd = ["git", "ls-files", *patterns]
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    failures: list[str] = []

    tracked_assets = sorted(
        rel_path
        for rel_path in git_ls_files("docs/assets/**")
        if (REPO_ROOT / rel_path).exists()
    )
    for rel_path in tracked_assets:
        if not rel_path.startswith(ALLOWED_PUBLIC_ASSET_PREFIXES):
            failures.append(
                f"{rel_path} is outside the allowed public asset pool prefixes."
            )
            continue
        if Path(rel_path).name in DISALLOWED_BASENAMES:
            failures.append(
                f"{rel_path} is explicitly blocked from the public asset pool."
            )
            continue
        if rel_path not in ALLOWED_PUBLIC_ASSET_FILES:
            failures.append(
                f"{rel_path} is not registered in the allowed public asset pool manifest."
            )

    for required in sorted(ALLOWED_PUBLIC_ASSET_FILES):
        if required not in tracked_assets:
            failures.append(
                f"Required public asset missing from tracked tree: {required}"
            )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: tracked public-facing assets stay inside the approved asset pool.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
