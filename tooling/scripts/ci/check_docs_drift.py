#!/usr/bin/env python3
"""Backward-compatible entrypoint for docs drift checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    commands = [
        [sys.executable, "tooling/scripts/ci/check_env_contract_drift.py"],
        [sys.executable, "tooling/scripts/ci/check_docs_render_freshness.py"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=repo_root, check=False)
        if result.returncode != 0:
            return result.returncode
    print("PASS: env contract drift + docs render freshness checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
