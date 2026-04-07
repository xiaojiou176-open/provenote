from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_process_logger_emits_runtime_witness_with_bound_context(
    tmp_path: Path,
) -> None:
    log_dir = tmp_path / "runtime-logs"
    script = """
from packages.core.observability import (
    bind_observability_context,
    configure_process_logging,
    logger,
)

configure_process_logging(
    service="open-notebook-runtime-test",
    component="tests.ci.runtime_witness",
    domain="ci",
)

with bind_observability_context(
    request_id="req-witness",
    trace_id="trace-witness",
    user_id="user-witness",
    test_id="test-witness",
    artifact_group="runtime-witness",
    command_id="cmd-witness",
    job_kind="smoke",
):
    logger.info("runtime witness emitted")
"""
    env = os.environ.copy()
    env["OPEN_NOTEBOOK_LOG_DIR"] = str(log_dir)

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout or result.stderr

    events_path = log_dir / "events.jsonl"
    assert events_path.is_file()

    lines = [
        line for line in events_path.read_text(encoding="utf-8").splitlines() if line
    ]
    assert lines, "expected at least one structured log event"

    payload = json.loads(lines[-1])
    record = payload["record"]
    extra = record["extra"]

    assert record["message"] == "runtime witness emitted"
    assert extra["service"] == "open-notebook-runtime-test"
    assert extra["component"] == "tests.ci.runtime_witness"
    assert extra["domain"] == "ci"
    assert extra["request_id"] == "req-witness"
    assert extra["trace_id"] == "trace-witness"
    assert extra["user_id"] == "user-witness"
    assert extra["test_id"] == "test-witness"
    assert extra["artifact_group"] == "runtime-witness"
    assert extra["command_id"] == "cmd-witness"
    assert extra["job_kind"] == "smoke"
    assert extra["redaction_version"] == "v1"
