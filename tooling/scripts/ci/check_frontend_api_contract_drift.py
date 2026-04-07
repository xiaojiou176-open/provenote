#!/usr/bin/env python3
"""Ensure the generated frontend API contract metadata matches the tracked OpenAPI contract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tooling.scripts.api.generate_frontend_api_contract import _render


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        default="contracts/api/openapi.yaml",
        help="Tracked OpenAPI contract path",
    )
    parser.add_argument(
        "--generated",
        default="apps/web/src/lib/api/generated/openapi-contract.ts",
        help="Generated frontend contract metadata path",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    contract_path = (REPO_ROOT / args.contract).resolve()
    generated_path = (REPO_ROOT / args.generated).resolve()
    if not generated_path.is_file():
        print(f"FAIL: generated frontend API contract missing: {generated_path}")
        return 1
    payload = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    expected = _render(payload)
    actual = generated_path.read_text(encoding="utf-8")
    if actual != expected:
        print(
            "FAIL: frontend API contract drift detected. Run `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/api/generate_frontend_api_contract.py --write`."
        )
        return 1
    print("PASS: generated frontend API contract matches tracked OpenAPI contract.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
