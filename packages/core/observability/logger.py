"""Unified logger runtime and process-level bindings."""

from __future__ import annotations

import os
import sys
from typing import Any

from loguru import logger as _base_logger

from .context import (
    artifact_group_ctx,
    command_id_ctx,
    job_kind_ctx,
    request_id_ctx,
    run_id_ctx,
    test_id_ctx,
    trace_id_ctx,
    user_id_ctx,
)

logger = _base_logger


def _resolve_process_log_dir() -> str:
    return os.getenv("OPEN_NOTEBOOK_LOG_DIR", "").strip()


def _inject_context(record: Any) -> None:
    if not isinstance(record, dict):
        return
    extra = record.setdefault("extra", {})
    if not isinstance(extra, dict):
        return

    extra.setdefault("run_id", run_id_ctx.get())
    extra.setdefault("request_id", request_id_ctx.get())
    extra.setdefault("trace_id", trace_id_ctx.get())
    extra.setdefault("user_id", user_id_ctx.get())
    extra.setdefault("test_id", test_id_ctx.get())
    extra.setdefault("artifact_group", artifact_group_ctx.get())
    extra.setdefault("command_id", command_id_ctx.get())
    extra.setdefault("job_kind", job_kind_ctx.get())
    extra.setdefault("component", "-")
    extra.setdefault("service", "-")
    extra.setdefault("domain", "-")
    extra.setdefault("error_class", "-")
    extra.setdefault("error_stack", "-")
    extra.setdefault("redaction_version", "v1")
    extra.setdefault("event", record.get("message") or "-")
    if extra.get("run_id") in {None, "-"}:
        extra["run_id"] = run_id_ctx.get()
    if extra.get("request_id") in {None, "-"}:
        extra["request_id"] = request_id_ctx.get()
    if extra.get("trace_id") in {None, "-"}:
        extra["trace_id"] = trace_id_ctx.get()
    if extra.get("user_id") in {None, "-"}:
        extra["user_id"] = user_id_ctx.get()
    if extra.get("test_id") in {None, "-"}:
        extra["test_id"] = test_id_ctx.get()
    if extra.get("artifact_group") in {None, "-"}:
        extra["artifact_group"] = artifact_group_ctx.get()
    if extra.get("command_id") in {None, "-"}:
        extra["command_id"] = command_id_ctx.get()
    if extra.get("job_kind") in {None, "-"}:
        extra["job_kind"] = job_kind_ctx.get()


def configure_process_logging(
    *,
    service: str,
    component: str,
    domain: str,
    level: str = "INFO",
    serialize: bool = False,
) -> None:
    """Configure the single process-wide logger sink."""

    logger.remove()
    logger.configure(
        extra={
            "run_id": run_id_ctx.get(),
            "request_id": "-",
            "trace_id": "-",
            "user_id": "-",
            "test_id": "-",
            "artifact_group": "-",
            "command_id": "-",
            "job_kind": "-",
            "component": component,
            "service": service,
            "domain": domain,
            "error_class": "-",
            "error_stack": "-",
            "redaction_version": "v1",
            "event": "-",
        },
        patcher=_inject_context,
    )
    logger.add(
        sys.stdout,
        level=level,
        serialize=serialize,
        backtrace=False,
        diagnose=False,
        format=(
            "{time:YYYY-MM-DDTHH:mm:ss.SSSZ} | {level: <8} | "
            "run_id={extra[run_id]} request_id={extra[request_id]} "
            "trace_id={extra[trace_id]} user_id={extra[user_id]} "
            "test_id={extra[test_id]} artifact_group={extra[artifact_group]} "
            "command_id={extra[command_id]} job_kind={extra[job_kind]} "
            "component={extra[component]} service={extra[service]} "
            "domain={extra[domain]} redaction_version={extra[redaction_version]} | "
            "{name}:{function}:{line} - {message}"
        ),
    )

    log_dir = _resolve_process_log_dir()
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        logger.add(
            os.path.join(log_dir, "events.jsonl"),
            level=level,
            serialize=True,
            backtrace=False,
            diagnose=False,
        )
