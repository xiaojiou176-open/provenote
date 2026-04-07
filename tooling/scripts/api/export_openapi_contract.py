#!/usr/bin/env python3
"""Export runtime OpenAPI schema into the tracked API contract."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip volatile fields so the tracked contract stays deterministic."""
    normalized = json.loads(json.dumps(payload))
    normalized.pop("servers", None)
    schemas = normalized.get("components", {}).get("schemas", {})
    if isinstance(schemas, dict):
        rename_map: dict[str, str] = {}
        deduped: dict[str, Any] = {}
        for name, schema in schemas.items():
            canonical_name = name.split("__")[-1] if "__" in name else name
            if canonical_name in deduped:
                rename_map[name] = canonical_name
                continue
            rename_map[name] = canonical_name
            deduped[canonical_name] = schema

        def rewrite(value: Any) -> Any:
            if isinstance(value, dict):
                updated = {}
                for key, item in value.items():
                    if key == "$ref" and isinstance(item, str):
                        prefix = "#/components/schemas/"
                        if item.startswith(prefix):
                            schema_name = item[len(prefix) :]
                            item = prefix + rename_map.get(schema_name, schema_name)
                    updated[key] = rewrite(item)
                return updated
            if isinstance(value, list):
                return [rewrite(item) for item in value]
            return value

        normalized = rewrite(normalized)
        normalized["components"]["schemas"] = {
            key: deepcopy(value) for key, value in deduped.items()
        }
    return normalized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="contracts/api/openapi.yaml",
        help="Tracked OpenAPI contract path",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the normalized runtime OpenAPI contract to disk",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    from services.api.main import app

    contract = _normalize(app.openapi())
    rendered = yaml.safe_dump(
        contract,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )
    output_path = (REPO_ROOT / args.output).resolve()
    if args.write:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"PASS: wrote OpenAPI contract to {output_path}")
        return 0

    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
