"""Shared observability context fields."""

from __future__ import annotations

import contextvars
import os
import uuid
from contextlib import contextmanager

PROCESS_RUN_ID = (
    os.getenv("OPEN_NOTEBOOK_RUN_ID")
    or os.getenv("GITHUB_RUN_ID")
    or f"local-{uuid.uuid4()}"
)

run_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "run_id", default=PROCESS_RUN_ID
)
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)
trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id", default="-"
)
user_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "user_id", default="-"
)
test_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "test_id", default="-"
)
artifact_group_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "artifact_group", default="-"
)
command_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "command_id", default="-"
)
job_kind_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "job_kind", default="-"
)


@contextmanager
def bind_observability_context(**values: str):
    """Temporarily bind observability context fields for the current task."""

    tokens: list[tuple[contextvars.ContextVar[str], contextvars.Token[str]]] = []
    mapping = {
        "run_id": run_id_ctx,
        "request_id": request_id_ctx,
        "trace_id": trace_id_ctx,
        "user_id": user_id_ctx,
        "test_id": test_id_ctx,
        "artifact_group": artifact_group_ctx,
        "command_id": command_id_ctx,
        "job_kind": job_kind_ctx,
    }
    try:
        for key, value in values.items():
            var = mapping.get(key)
            if var is None:
                continue
            tokens.append((var, var.set(value)))
        yield
    finally:
        for var, token in reversed(tokens):
            var.reset(token)
