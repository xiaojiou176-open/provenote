#!/usr/bin/env python3
"""Validate the structured log contract and critical runtime bindings."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_LOG_FIELDS = [
    "timestamp",
    "level",
    "event",
    "component",
    "service",
    "domain",
    "run_id",
    "request_id",
    "trace_id",
    "user_id",
    "test_id",
    "artifact_group",
    "command_id",
    "job_kind",
    "error_class",
    "error_stack",
    "redaction_version",
]

FILE_REQUIRED_SNIPPETS = {
    "apps/web/src/lib/log.ts": (
        "component: `apps/web.${scope}`",
        'service: "open-notebook-web"',
        'domain: "frontend"',
        'redaction_version: "v1"',
    ),
    "apps/web/src/lib/observability/run-context.ts": (
        "run_id:",
        "trace_id:",
        "browser_session_id:",
        'source_kind: "frontend"',
        "workflow_name:",
        "job_name:",
    ),
    "packages/core/observability/context.py": (
        "run_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "user_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "test_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "artifact_group_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "command_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "job_kind_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
    ),
    "packages/core/observability/logger.py": (
        'extra.setdefault("run_id", run_id_ctx.get())',
        'extra.setdefault("request_id", request_id_ctx.get())',
        'extra.setdefault("trace_id", trace_id_ctx.get())',
        'extra.setdefault("artifact_group", artifact_group_ctx.get())',
        'extra.setdefault("command_id", command_id_ctx.get())',
        'extra.setdefault("job_kind", job_kind_ctx.get())',
        '"redaction_version": "v1"',
    ),
    "services/api/main.py": (
        "configure_process_logging(",
        "component=COMPONENT_NAME",
        "service=SERVICE_NAME",
        "domain=DOMAIN_NAME",
        'response.headers["X-Request-ID"] = request_id',
        'response.headers["X-Trace-ID"] = trace_id',
    ),
    "services/worker/__init__.py": (
        "configure_process_logging(",
        'service="notebooklab-worker"',
        'component="services.worker.runner"',
        'domain="worker"',
    ),
}

RUNTIME_SURFACES_PATH = "config/runtime/runtime-surfaces.json"
WITNESS_BACKED_LOG_SURFACES = {
    "local-logs": {
        "truth_basis": "witness-backed",
        "verification_lane": "tooling/scripts/ci/check_log_contract.py",
        "witness_test_name": "test_process_logger_emits_runtime_witness_with_bound_context",
    },
    "ci-logs": {
        "truth_basis": "witness-backed",
        "verification_lane": "tooling/scripts/ci/check_log_contract.py",
        "witness_test_name": "test_process_logger_emits_runtime_witness_with_bound_context",
    },
    "single-container-logs": {
        "truth_basis": "witness-backed",
        "verification_lane": "tooling/scripts/ci/check_log_contract.py",
        "witness_test_name": "test_supervisor_log_path_guard_passes_for_current_repo_state",
    },
}
WITNESS_TEST_FILES = {
    "test_process_logger_emits_runtime_witness_with_bound_context": (
        "tests/ci/test_observability_runtime_witness.py"
    ),
    "test_supervisor_log_path_guard_passes_for_current_repo_state": (
        "tests/ci/test_supervisor_log_path_contract.py"
    ),
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--schema",
        default="contracts/observability/log-event.schema.json",
        help="Path to structured log contract schema",
    )
    return parser


def _run_nested_guard(repo_root: Path, rel_path: str) -> list[str]:
    script_path = repo_root / rel_path
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return []

    output = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    errors = [line.strip() for line in result.stderr.splitlines() if line.strip()]
    combined = output + errors
    if not combined:
        combined = [f"{rel_path} exited with code {result.returncode} without output"]
    return [f"{rel_path}: {line}" for line in combined]


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    schema_path = (repo_root / args.schema).resolve()
    schema = _load_json(schema_path)
    runtime_surfaces = _load_json((repo_root / RUNTIME_SURFACES_PATH).resolve())
    required = schema.get("required", [])
    failures: list[str] = []

    if not isinstance(required, list):
        failures.append("log event schema required list must be an array")
        required = []

    for field in REQUIRED_LOG_FIELDS:
        if field not in required:
            failures.append(f"log event schema missing required field: {field}")
    for field in (
        "source_kind",
        "route",
        "browser_session_id",
        "workflow_name",
        "job_name",
    ):
        if field not in schema.get("properties", {}):
            failures.append(f"log event schema missing declared property: {field}")

    for rel_path, snippets in FILE_REQUIRED_SNIPPETS.items():
        file_path = repo_root / rel_path
        if not file_path.exists():
            failures.append(f"missing log contract file: {rel_path}")
            continue
        text = file_path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                failures.append(
                    f"{rel_path} missing log contract binding snippet: {snippet}"
                )

    truth_note = str(runtime_surfaces.get("truth_classification_note", "")).strip()
    if "witness-backed" not in truth_note or "static-only" not in truth_note:
        failures.append(
            "runtime surfaces registry must explain witness-backed vs static-only truth classification"
        )

    surfaces_by_name = {
        item.get("name"): item for item in runtime_surfaces.get("surfaces", [])
    }
    for surface_name, expected in WITNESS_BACKED_LOG_SURFACES.items():
        payload = surfaces_by_name.get(surface_name)
        if not isinstance(payload, dict):
            failures.append(
                f"missing witness-backed log surface declaration: {surface_name}"
            )
            continue
        for key, value in expected.items():
            if str(payload.get(key, "")).strip() != value:
                failures.append(f"{surface_name} must declare {key}={value!r}")
        witness_test_name = expected["witness_test_name"]
        witness_file = repo_root / WITNESS_TEST_FILES[witness_test_name]
        if not witness_file.exists():
            failures.append(
                f"witness-backed log surface {surface_name} references missing witness file: {WITNESS_TEST_FILES[witness_test_name]}"
            )
        else:
            witness_text = witness_file.read_text(encoding="utf-8")
            if witness_test_name not in witness_text:
                failures.append(
                    f"witness-backed log surface {surface_name} missing witness test name {witness_test_name}"
                )

    failures.extend(
        _run_nested_guard(repo_root, "tooling/scripts/ci/check_supervisor_log_path.py")
    )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        "PASS: structured log contract schema and shared observability runtime bindings are present."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
