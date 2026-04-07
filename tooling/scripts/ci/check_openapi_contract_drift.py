#!/usr/bin/env python3
"""Ensure tracked OpenAPI contract matches the runtime schema export."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tooling.scripts.api.export_openapi_contract import _normalize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        default="contracts/api/openapi.yaml",
        help="Tracked OpenAPI contract path",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    contract_path = (REPO_ROOT / args.contract).resolve()
    if not contract_path.is_file():
        print(f"FAIL: tracked OpenAPI contract missing: {contract_path}")
        return 1

    from services.api.main import app

    expected = _normalize(app.openapi())
    actual = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    if actual != expected:
        print(
            "FAIL: OpenAPI contract drift detected. Run `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/api/export_openapi_contract.py --write`."
        )
        return 1

    print("PASS: tracked OpenAPI contract matches runtime schema export.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
