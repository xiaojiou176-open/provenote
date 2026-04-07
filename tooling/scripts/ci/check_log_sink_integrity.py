#!/usr/bin/env python3
"""Validate run-scoped log and evidence sink bindings in authoritative entrypoints."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_SNIPPETS = {
    "tooling/scripts/dev/common.sh": (
        'LOG_DIR="$(resolve_open_notebook_runtime_logs_dir "${root_dir}" "local")"',
        'export OPEN_NOTEBOOK_LOG_DIR="${LOG_DIR}"',
    ),
    "packages/core/observability/logger.py": (
        'return os.getenv("OPEN_NOTEBOOK_LOG_DIR", "").strip()',
        'os.path.join(log_dir, "events.jsonl")',
    ),
    "tooling/scripts/ci/run_with_retry.sh": (
        'LOG_DIR="$(resolve_open_notebook_runtime_reports_dir "${ROOT_DIR}" "test-retry")"',
    ),
    "tooling/scripts/ci/generate_release_proof.py": (
        'default=".runtime-cache/runs/current/evidence/release-proof"',
    ),
    "tooling/scripts/ci/run_uiux_gemini_gate.py": (
        'default=".runtime-cache/runs/current/evidence/uiux-gemini/manifest.json"',
        'default=".runtime-cache/runs/current/evidence/uiux-gemini/evaluator.json"',
        'default=".runtime-cache/runs/current/evidence/playwright/report"',
        'default=".runtime-cache/runs/current/evidence/playwright/results"',
    ),
    "apps/web/package.json": (
        "../../.runtime-cache/runs/current/evidence/apps-web/action-runtime-evidence.json",
    ),
    "apps/web/playwright.config.ts": (
        "../../.runtime-cache/runs/current/evidence/playwright/report",
        "../../.runtime-cache/runs/current/evidence/playwright/results",
    ),
    "apps/web/playwright.live.config.ts": (
        "../../.runtime-cache/runs/current/evidence/playwright/report",
        "../../.runtime-cache/runs/current/evidence/playwright/results",
    ),
}


def main() -> int:
    failures: list[str] = []
    for rel_path, snippets in REQUIRED_SNIPPETS.items():
        path = REPO_ROOT / rel_path
        if not path.is_file():
            failures.append(f"missing authoritative sink file: {rel_path}")
            continue
        content = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in content:
                failures.append(f"{rel_path} missing sink binding snippet: {snippet}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        "PASS: authoritative log and evidence entrypoints use run-scoped canonical sink paths."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
