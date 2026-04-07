from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_log_schema_declares_frontend_correlation_fields() -> None:
    payload = json.loads(
        (REPO_ROOT / "contracts/observability/log-event.schema.json").read_text(
            encoding="utf-8"
        )
    )
    for field in (
        "run_id",
        "source_kind",
        "route",
        "browser_session_id",
        "workflow_name",
        "job_name",
    ):
        assert field in payload["properties"]


def test_frontend_logger_binds_run_correlation_fields() -> None:
    log_text = (REPO_ROOT / "apps/web/src/lib/log.ts").read_text(encoding="utf-8")
    for token in (
        "run_id: context.run_id",
        "request_id: context.request_id",
        "trace_id: context.trace_id",
        "browser_session_id: context.browser_session_id",
    ):
        assert token in log_text
