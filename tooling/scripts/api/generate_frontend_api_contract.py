#!/usr/bin/env python3
"""Generate tracked frontend OpenAPI contract metadata from the authoritative API contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        default="contracts/api/openapi.yaml",
        help="Path to the tracked OpenAPI contract",
    )
    parser.add_argument(
        "--output",
        default="apps/web/src/lib/api/generated/openapi-contract.ts",
        help="Generated TypeScript output path",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the rendered output to disk",
    )
    return parser


def _normalize(payload: dict) -> dict:
    return json.loads(json.dumps(payload, sort_keys=True))


def _render_json_template(payload: object) -> str:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    return f"\n{rendered}\n"


def _render_byte_array(hex_value: str) -> str:
    if len(hex_value) % 2 != 0:
        raise ValueError("hex value must contain an even number of characters")
    values = [
        int(hex_value[index : index + 2], 16) for index in range(0, len(hex_value), 2)
    ]
    lines: list[str] = []
    current = "  "
    for value in values:
        rendered = f"{value},"
        candidate = f"  {rendered}" if current == "  " else f"{current} {rendered}"
        if len(candidate) > 100:
            lines.append(current)
            current = f"  {rendered}"
        else:
            current = candidate
    if current.strip():
        lines.append(current)
    return "[\n" + "\n".join(lines) + "\n]"


def _render(payload: dict) -> str:
    normalized = _normalize(payload)
    rendered_json = json.dumps(normalized, indent=2, ensure_ascii=False)
    schema_hash = hashlib.sha256(rendered_json.encode("utf-8")).hexdigest()
    operation_ids = sorted(
        details["operationId"]
        for methods in normalized.get("paths", {}).values()
        for details in methods.values()
        if isinstance(details, dict) and details.get("operationId")
    )
    operation_ids_json = _render_json_template(operation_ids)
    schema_json = _render_json_template(normalized)
    schema_hash_bytes = _render_byte_array(schema_hash)
    return f"""// AUTO-GENERATED: DO NOT EDIT DIRECTLY.
// Source: contracts/api/openapi.yaml

export const openApiContractSha256Bytes = {schema_hash_bytes} as const;
export const openApiContractSha256 = Array.from(openApiContractSha256Bytes, (byte) =>
  byte.toString(16).padStart(2, "0"),
).join("");
export const openApiOperationIds = JSON.parse(
  String.raw`{operation_ids_json}`,
) as readonly string[];
export const openApiSchema = JSON.parse(
  String.raw`{schema_json}`,
) as Readonly<Record<string, unknown>>;
"""


def main() -> int:
    args = build_parser().parse_args()
    contract_path = (REPO_ROOT / args.contract).resolve()
    payload = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    rendered = _render(payload)
    if args.write:
        output_path = (REPO_ROOT / args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"PASS: wrote frontend API contract metadata to {output_path}")
        return 0
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
