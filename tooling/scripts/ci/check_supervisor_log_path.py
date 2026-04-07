#!/usr/bin/env python3
"""Validate the canonical single-container supervisor contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SUPERVISOR_CONFIG = REPO_ROOT / "ops" / "supervisor" / "supervisord.single.conf"
SUPERVISOR_RUNTIME_CONFIG = REPO_ROOT / "ops" / "supervisor" / "supervisord.conf"
DOCKERFILE_SINGLE = REPO_ROOT / "ops" / "docker" / "Dockerfile.single"
RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "space-governance.md"
RUNTIME_SURFACES = REPO_ROOT / "config" / "runtime" / "runtime-surfaces.json"

CANONICAL_SURFACE_NAME = "single-container-logs"
CANONICAL_RELATIVE_PATH = ".runtime-cache/runs/current/logs/single-container"
CANONICAL_CONTAINER_PATH = f"/app/{CANONICAL_RELATIVE_PATH}"
EXPECTED_LOG_BINDINGS = {
    "logfile": f"{CANONICAL_CONTAINER_PATH}/supervisord.log",
    "stdout_logfile": (
        f"{CANONICAL_CONTAINER_PATH}/surrealdb.stdout.log",
        f"{CANONICAL_CONTAINER_PATH}/services.api.stdout.log",
        f"{CANONICAL_CONTAINER_PATH}/worker.stdout.log",
        f"{CANONICAL_CONTAINER_PATH}/apps.web.stdout.log",
    ),
    "stderr_logfile": (
        f"{CANONICAL_CONTAINER_PATH}/surrealdb.stderr.log",
        f"{CANONICAL_CONTAINER_PATH}/services.api.stderr.log",
        f"{CANONICAL_CONTAINER_PATH}/worker.stderr.log",
        f"{CANONICAL_CONTAINER_PATH}/apps.web.stderr.log",
    ),
}


def main() -> int:
    failures: list[str] = []

    supervisor_text = SUPERVISOR_CONFIG.read_text(encoding="utf-8")
    runtime_supervisor_text = SUPERVISOR_RUNTIME_CONFIG.read_text(encoding="utf-8")
    dockerfile_text = DOCKERFILE_SINGLE.read_text(encoding="utf-8")
    runbook_text = RUNBOOK.read_text(encoding="utf-8")
    runtime_surfaces = json.loads(RUNTIME_SURFACES.read_text(encoding="utf-8"))

    entry = next(
        (
            item
            for item in runtime_surfaces.get("surfaces", [])
            if item.get("name") == CANONICAL_SURFACE_NAME
        ),
        None,
    )
    if entry is None:
        failures.append(f"missing runtime surface entry: {CANONICAL_SURFACE_NAME}")
    elif entry.get("canonical_path") != CANONICAL_RELATIVE_PATH:
        failures.append(
            f"{CANONICAL_SURFACE_NAME} must point to {CANONICAL_RELATIVE_PATH}, got {entry.get('canonical_path')}"
        )

    bound_values: dict[str, list[str]] = {
        "logfile": [],
        "stdout_logfile": [],
        "stderr_logfile": [],
    }
    for key, value in re.findall(
        r"^(logfile|stdout_logfile|stderr_logfile)=(.+)$",
        supervisor_text,
        flags=re.MULTILINE,
    ):
        bound_values[key].append(value.strip())

    for config_name, text in (
        ("supervisord.single.conf", supervisor_text),
        ("supervisord.conf", runtime_supervisor_text),
    ):
        program_names = re.findall(r"^\[program:([^\]]+)\]$", text, flags=re.MULTILINE)
        invalid_program_names = [
            program_name
            for program_name in program_names
            if "/" in program_name or ":" in program_name
        ]
        if invalid_program_names:
            failures.append(
                f"{config_name} program names must not contain '/' or ':' characters: "
                + ", ".join(sorted(invalid_program_names))
            )

    expected_logfile = EXPECTED_LOG_BINDINGS["logfile"]
    if bound_values["logfile"] != [expected_logfile]:
        failures.append(
            f"supervisord.single.conf must bind logfile to {expected_logfile}"
        )

    for key in ("stdout_logfile", "stderr_logfile"):
        expected_values = sorted(EXPECTED_LOG_BINDINGS[key])
        actual_values = sorted(bound_values[key])
        if actual_values != expected_values:
            failures.append(
                f"supervisord.single.conf must bind {key} entries to canonical single-container log files under {CANONICAL_CONTAINER_PATH}"
            )

    if "/tmp/" in "\n".join(
        bound_values["logfile"]
        + bound_values["stdout_logfile"]
        + bound_values["stderr_logfile"]
    ):
        failures.append("supervisord.single.conf must not emit log files under /tmp")

    mkdir_token = f"mkdir -p /app/{CANONICAL_RELATIVE_PATH}"
    if mkdir_token not in dockerfile_text:
        failures.append(
            f"Dockerfile.single must create the canonical single-container log directory via `{mkdir_token}`"
        )

    for token in (
        f"`/app/{CANONICAL_RELATIVE_PATH}/`",
        f"`.runtime-cache/runs/current/logs/single-container/`",
        "`/tmp/*.log` is not a source of truth",
    ):
        if token not in runbook_text:
            failures.append(
                f"space-governance.md missing single-container log token: {token}"
            )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        "PASS: single-container supervisor config uses safe program names and canonical runtime log paths."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
