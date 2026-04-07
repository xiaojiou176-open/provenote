#!/usr/bin/env python3
"""Render governance docs from structured repo-side fact sources."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_CONTRACT_PATH = REPO_ROOT / "config" / "env-contract.json"
RUNTIME_SURFACES_PATH = REPO_ROOT / "config" / "runtime" / "runtime-surfaces.json"
ACTION_MATRIX_PATH = REPO_ROOT / "apps/web" / "e2e" / "action-matrix.json"

TARGET_OUTPUTS = {
    "env-contract-ssot": REPO_ROOT
    / "docs"
    / "5-CONFIGURATION"
    / "env-contract-ssot.md",
    "environment-reference": REPO_ROOT
    / "docs"
    / "5-CONFIGURATION"
    / "environment-reference.md",
    "critical-interaction-matrix": REPO_ROOT
    / "docs"
    / "quality"
    / "critical-interaction-matrix.md",
    "artifact-evidence-index": REPO_ROOT
    / "docs"
    / "ops"
    / "artifact-evidence-index.md",
    "upstream-compatibility-matrix": REPO_ROOT
    / "docs"
    / "ops"
    / "upstream-compatibility-matrix.md",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _format_default(value: Any) -> str:
    if value is None:
        return "_unset_"
    return str(value)


def _render_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _render_generated_header(source_paths: list[str]) -> list[str]:
    joined_sources = ", ".join(f"`{item}`" for item in source_paths)
    return [
        "<!-- AUTO-GENERATED: DO NOT EDIT DIRECTLY. -->",
        f"<!-- Render command: `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/render_governance_docs.py --write all` -->",
        f"<!-- Source inputs: {joined_sources} -->",
        "",
    ]


def _runtime_entries(env_contract: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for bucket_name in ("required", "optional"):
        bucket = env_contract.get(bucket_name, [])
        if not isinstance(bucket, list):
            raise ValueError(f"{bucket_name} must be a list")
        for item in bucket:
            if not isinstance(item, dict):
                raise ValueError(f"{bucket_name} entries must be objects")
            entries.append(item)
    return entries


def render_env_contract_ssot() -> str:
    env_contract = _load_json(ENV_CONTRACT_PATH)
    required_rows = [
        [f"`{item['name']}`", item["purpose"]] for item in env_contract["required"]
    ]
    optional_rows = [
        [f"`{item['name']}`", item["purpose"]] for item in env_contract["optional"]
    ]
    forbidden_rows = [
        [f"`{item['name']}`", item["why"]] for item in env_contract["forbidden"]
    ]

    lines = _render_generated_header(["config/env-contract.json"])
    lines.extend(
        [
            "# Environment Contract SSOT",
            "",
            "> Status: authoritative semantic contract rendered from `config/env-contract.json`.",
            "> Scope: runtime naming and governance semantics only.",
            "",
            "## Required Variables",
            "",
            _render_table(["Variable", "Purpose"], required_rows),
            "",
            "## Optional Variables",
            "",
            _render_table(["Variable", "Purpose"], optional_rows),
            "",
            "## Forbidden Variables",
            "",
            _render_table(["Variable", "Why Forbidden"], forbidden_rows),
            "",
            "## Hard Rules",
            "",
            "1. **Single-name rule**: one semantic field maps to one variable name only.",
            "2. **No historical-name contract**: forbidden names must not reappear in runtime ENV, docs contract, CI variables, or examples.",
            "3. **No variable-chain contract**: contract docs must not describe fallback chains such as `PRIMARY -> LEGACY`.",
            "4. **No hidden compatibility escape hatch**: compatibility behavior may exist only as explicit migration code, never as a canonical contract.",
            "",
            "## Enforcement Reference",
            "",
            "- Machine-readable source: `config/env-contract.json`",
            "- Drift gate: `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_env_contract_drift.py`",
            "- Render freshness gate: `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_render_freshness.py`",
        ]
    )
    return "\n".join(lines) + "\n"


def render_environment_reference() -> str:
    env_contract = _load_json(ENV_CONTRACT_PATH)
    runtime_rows = [
        [
            f"`{item['name']}`",
            f"`{_format_default(item.get('default'))}`"
            if item.get("default") is not None
            else "_unset_",
            item["purpose"],
        ]
        for item in _runtime_entries(env_contract)
    ]
    runtime_allowlist = [
        f"{idx}. `{item['name']}`"
        for idx, item in enumerate(_runtime_entries(env_contract), start=1)
    ]
    blocked_list = [
        f"- `{name}`" for name in env_contract["blocked_legacy_provider_env_vars"]
    ]

    lines = _render_generated_header(["config/env-contract.json"])
    lines.extend(
        [
            "# Environment Reference",
            "",
            "This reference is generated from `config/env-contract.json` and aligned with runtime reads in `packages/core/settings.py`.",
            "",
            "`phase1_ssot_naming(canonical_only)`",
            "",
            "## Resolution Rules",
            "",
            "- Environment values use a single canonical `{VAR}` lookup, then code default.",
            "- Empty strings are treated as unset for `read_env`-based values.",
            "- Public/browser paths use `API_URL`; server-side API clients use `INTERNAL_API_URL`.",
            "",
            "## Runtime Variables",
            "",
            _render_table(["Variable", "Default", "Description"], runtime_rows),
            "",
            "## Authentication Semantics",
            "",
            "When `OPEN_NOTEBOOK_PASSWORD` is configured:",
            "",
            "- Requests must include `Authorization: Bearer <password>`.",
            "- Missing/invalid header returns `401` with `WWW-Authenticate: Bearer`.",
            "",
            "When `OPEN_NOTEBOOK_PASSWORD` is unset or empty, password auth fails closed:",
            "",
            "- Protected endpoints return `401` (`Authentication is not configured`).",
            "- Only explicitly excluded paths (`/`, `/health`, `/docs`, `/openapi.json`, `/redoc`) remain accessible without password auth.",
            "",
            "## Provider Credential Governance",
            "",
            "- Required runtime key: `GEMINI_API_KEY`",
            "- Allowed Google runtime variable: `GEMINI_MODEL`",
            "- Startup probe resolution order: `GEMINI_API_KEY` first, then DB credential path.",
            "- Non-Google provider key/base-url ENV injection is forbidden.",
            "",
            f"## Runtime Allowlist ({len(runtime_allowlist)})",
            "",
            f"`runtime_allowlist({len(runtime_allowlist)})` is the governance baseline for runtime/env review.",
            "",
        ]
    )
    lines.extend(runtime_allowlist)
    lines.extend(
        [
            "",
            f"## Blocked List ({len(blocked_list)})",
            "",
            f"`blocked_list({len(blocked_list)})` lists forbidden legacy non-Google provider ENV variables.",
            "",
        ]
    )
    lines.extend(blocked_list)
    lines.extend(
        [
            "",
            "## Migration Guidance",
            "",
            "1. Remove all blocked legacy provider ENV vars from process env and local `.env`.",
            "2. Keep only canonical runtime names from this document.",
            "3. Run `bash tooling/scripts/ci/check_env_governance.sh` and `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_env_contract_drift.py` before startup or CI submission.",
        ]
    )
    return "\n".join(lines) + "\n"


def _collect_routes(actions: list[dict[str, Any]]) -> list[str]:
    routes: set[str] = set()
    for action in actions:
        raw_route = str(action.get("route", "")).strip()
        if not raw_route:
            continue
        if raw_route.startswith("multi:"):
            _, _, suffix = raw_route.partition(":")
            routes.update(part.strip() for part in suffix.split(",") if part.strip())
            continue
        routes.add(raw_route)
    return sorted(routes)


def render_critical_interaction_matrix() -> str:
    matrix = _load_json(ACTION_MATRIX_PATH)
    meta = matrix.get("meta") or {}
    actions = matrix.get("actions") or []
    if not isinstance(meta, dict) or not isinstance(actions, list):
        raise ValueError("apps/web/e2e/action-matrix.json must contain meta/actions")

    expected_counts = meta.get("expected_counts") or {}
    if not isinstance(expected_counts, dict):
        raise ValueError("action matrix meta.expected_counts must be an object")

    routes = _collect_routes(actions)
    spec_counts = Counter(
        str(action.get("spec_id", "")).strip()
        for action in actions
        if str(action.get("spec_id", "")).strip()
    )

    target_rows = [
        [f"`{spec}`", str(count)] for spec, count in sorted(spec_counts.items())
    ]

    lines = _render_generated_header(["apps/web/e2e/action-matrix.json"])
    lines.extend(
        [
            "# Frontend Critical Interaction Matrix",
            "",
            "Render-only reference for the Playwright action matrix contract.",
            "",
            "## Matrix Snapshot",
            "",
            f"- Total actions: `{expected_counts.get('total', 0)}`",
            f"- Selector split: `data-testid={expected_counts.get('data-testid', 0)}`, `id={expected_counts.get('id', 0)}`, `role={expected_counts.get('role', 0)}`",
            f"- Covered routes: `{len(routes)}`",
        ]
    )
    lines.extend(f"  - `{route}`" for route in routes)
    lines.extend(
        [
            "",
            "## Contract Requirements",
            "",
            "### Selector count contract",
            "",
            "- Source: `meta.expected_counts` in `apps/web/e2e/action-matrix.json`",
            "- Required keys: `total`, `data-testid`, `id`, `role`",
            "- Contract validator: `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_action_matrix.py`",
            "",
            "### Runtime evidence contract",
            "",
            "- Applies to actions where `test_type=real-backend`.",
            "- Each action must define `runtime_evidence.action_id` and `runtime_evidence.required_layers`.",
            "- Strict validation command:",
            "",
            "```bash",
            "bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_action_matrix.py \\",
            "  --runtime-evidence .runtime-cache/runs/current/evidence/apps-web/action-runtime-evidence.json \\",
            "  --require-runtime-evidence",
            "```",
            "",
            "## Target Spec Action Counts",
            "",
            _render_table(["Spec", "Action count"], target_rows),
        ]
    )
    return "\n".join(lines) + "\n"


def render_artifact_evidence_index() -> str:
    registry = _load_json(RUNTIME_SURFACES_PATH)
    surfaces = registry.get("surfaces", [])
    if not isinstance(surfaces, list):
        raise ValueError("runtime surfaces registry must contain a surfaces list")

    evidence_surfaces = [
        item for item in surfaces if isinstance(item, dict) and item.get("workflow")
    ]
    runtime_only_surfaces = [
        item for item in surfaces if isinstance(item, dict) and not item.get("workflow")
    ]

    critical_rows = [
        [
            item.get("job", item["producer"]),
            f"`{item['name']}`",
            f"`{item['workflow']}` / `{item['job']}`",
            f"`{item['canonical_path']}`",
            item["producer"],
            item["consumer"],
            item["retention_class"],
            "`required`" if item["run_correlation_required"] else "`optional`",
            item["kind"],
        ]
        for item in evidence_surfaces
    ]
    optional_rows = [
        [
            f"`{item['name']}`",
            item["kind"],
            f"`{item['canonical_path']}`",
            item["producer"],
            item["consumer"],
            item["retention_class"],
            "`required`" if item["run_correlation_required"] else "`optional`",
            "repo-owned runtime-only surface",
        ]
        for item in runtime_only_surfaces
    ]

    lines = _render_generated_header(["config/runtime/runtime-surfaces.json"])
    lines.extend(
        [
            "# Artifact Evidence Index",
            "",
            "Render-only index for CI evidence artifacts and repo-owned runtime surfaces.",
            "",
            "## Policy",
            "",
            "- Critical workflow evidence must use canonical runtime surfaces only.",
            "- Runtime-only surfaces are listed to prevent hidden output paths and side-channel caches.",
            "",
            "## Indexed Artifacts",
            "",
            _render_table(
                [
                    "Gate / Topic",
                    "Artifact Name",
                    "Source Workflow / Job",
                    "Canonical Path",
                    "Producer",
                    "Consumer",
                    "Retention Class",
                    "Run Correlation",
                    "Surface Kind",
                ],
                critical_rows,
            ),
            "",
            "## Runtime-Only Surfaces",
            "",
            _render_table(
                [
                    "Surface",
                    "Kind",
                    "Canonical Path",
                    "Producer",
                    "Consumer",
                    "Retention Class",
                    "Run Correlation",
                    "Why Listed",
                ],
                optional_rows,
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def render_upstream_compatibility_matrix() -> str:
    registry = _load_json(REPO_ROOT / "config" / "upstream" / "external-surfaces.json")
    rows = [
        [
            f"`{item['name']}`",
            f"`{item['kind']}`",
            f"`{item['pin']}`",
            f"`{item['checksum_or_digest'] or '(n/a)'}`",
            item["verification_lane"],
            item["upgrade_playbook"],
            item["rollback_path"],
        ]
        for item in registry["surfaces"]
    ]

    lines = _render_generated_header(["config/upstream/external-surfaces.json"])
    lines.extend(
        [
            "# Upstream Compatibility Matrix",
            "",
            "Render-only matrix for external runtime, image, binary, and upstream repo surfaces.",
            "",
            "## Policy",
            "",
            "- Every external surface must be pinned, owned, and traceable.",
            "- No `latest`, floating tag, or unverifiable download is allowed on the blocking path.",
            "- Verification lanes and rollback paths are part of the contract, not tribal knowledge.",
            "",
            "## Declared Surfaces",
            "",
            _render_table(
                [
                    "Surface",
                    "Kind",
                    "Pin",
                    "Checksum / Digest",
                    "Verification Lane",
                    "Upgrade Playbook",
                    "Rollback Path",
                ],
                rows,
            ),
        ]
    )
    return "\n".join(lines) + "\n"


RENDERERS = {
    "env-contract-ssot": render_env_contract_ssot,
    "environment-reference": render_environment_reference,
    "critical-interaction-matrix": render_critical_interaction_matrix,
    "artifact-evidence-index": render_artifact_evidence_index,
    "upstream-compatibility-matrix": render_upstream_compatibility_matrix,
}


def render_target(target: str) -> str:
    try:
        renderer = RENDERERS[target]
    except KeyError as exc:
        raise SystemExit(f"Unknown render target: {target}") from exc
    return renderer()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=["all", *sorted(RENDERERS)],
        help="Render a single governance doc or all generated docs.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write rendered output back to tracked markdown files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    targets = sorted(RENDERERS) if args.target == "all" else [args.target]

    for target in targets:
        output = render_target(target)
        if args.write:
            TARGET_OUTPUTS[target].write_text(output, encoding="utf-8")
        else:
            print(output, end="" if output.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
