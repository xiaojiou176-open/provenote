#!/usr/bin/env python3
"""Guard manual-review snapshots against stale unresolved-repo phrasing."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

FILES = {
    ".github/repo-settings/required-checks.snapshot.md": (
        "not live proof",
        "review aid",
        "Review Status:",
    ),
    ".github/repo-settings/registry-ownership.snapshot.md": (
        "manual review aid, not live proof",
        "Review Status:",
    ),
    ".github/repo-settings/code-quality.snapshot.md": (
        "manual review aid, not live proof",
        "Review Status:",
    ),
    ".github/repo-settings/public-surface.snapshot.md": (
        "manual review aid, not live proof",
        "Review Status:",
    ),
}

STALE_FAILURE_TOKENS = (
    "Repository not found",
    "Could not resolve to a Repository",
    "cannot freshly resolve",
    "no longer resolves",
)


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def main() -> int:
    failures: list[str] = []

    for rel_path, required_tokens in FILES.items():
        path = REPO_ROOT / rel_path
        if not path.exists():
            failures.append(f"missing snapshot freshness target: {rel_path}")
            continue

        text = _read(rel_path)
        for token in required_tokens:
            if token not in text:
                failures.append(f"{rel_path} missing freshness token: {token}")

        if (
            any(token in text for token in STALE_FAILURE_TOKENS)
            and "historical evidence" not in text
            and "Historical Note About" not in text
        ):
            failures.append(
                f"{rel_path} contains stale failure phrasing without historical framing"
            )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        "PASS: manual-review snapshots carry freshness framing and newer recheck markers."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
