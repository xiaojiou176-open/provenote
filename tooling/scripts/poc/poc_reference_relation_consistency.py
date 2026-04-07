#!/usr/bin/env python3
"""
PoC: verify relation direction/field consistency fixes.

This script demonstrates:
1) Legacy (buggy) expectations now fail.
2) Fixed expectations pass.
"""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api.routers.notebooks import remove_source_from_notebook
from services.api.routers.sources_service import retry_source_processing_service


class _FakeRetrySource:
    def __init__(self) -> None:
        self.id = "source:1"
        self.command = None
        self.asset = None
        self.full_text = "retry text"
        self.saved = False

    async def save(self) -> None:
        self.saved = True

    async def get_embedded_chunks(self) -> int:
        return 0


def _expect_legacy_failure(actual: str, legacy_expected: str, label: str) -> None:
    try:
        assert actual == legacy_expected
    except AssertionError:
        print(
            f"[EXPECTED FAIL] {label}: legacy pattern does not match current behavior"
        )
        return
    raise AssertionError(
        f"{label}: legacy pattern unexpectedly matched current behavior"
    )


async def _capture_remove_query() -> str:
    with (
        patch(
            "services.api.routers.notebooks.Notebook.get",
            new=AsyncMock(return_value=SimpleNamespace(id="notebook:1")),
        ),
        patch(
            "services.api.routers.notebooks.repo_query", new=AsyncMock(return_value=[])
        ) as mock_repo_query,
    ):
        await remove_source_from_notebook("notebook:1", "source:1")
        repo_query_call = mock_repo_query.await_args
        if repo_query_call is None:
            raise AssertionError("Expected repo_query to be awaited at least once")
        return repo_query_call.args[0]


async def _capture_retry_query_and_payload() -> tuple[str, dict]:
    fake_source = _FakeRetrySource()
    with (
        patch(
            "services.api.routers.sources_service.Source.get",
            new=AsyncMock(return_value=fake_source),
        ),
        patch(
            "services.api.routers.sources_service.repo_query",
            new=AsyncMock(return_value=[{"notebook_id": "notebook:1"}]),
        ) as mock_repo_query,
        patch(
            "services.api.routers.sources_service.CommandService.submit_command_job",
            new=AsyncMock(return_value="cmd-1"),
        ) as mock_submit_command_job,
        patch(
            "services.api.routers.sources_service.build_source_response",
            return_value={"status": "queued", "ok": True},
        ),
    ):
        await retry_source_processing_service("source:1")
        repo_query_call = mock_repo_query.await_args
        if repo_query_call is None:
            raise AssertionError("Expected repo_query to be awaited at least once")
        submit_command_job_call = mock_submit_command_job.await_args
        if submit_command_job_call is None:
            raise AssertionError(
                "Expected submit_command_job to be awaited at least once"
            )
        query = repo_query_call.args[0]
        payload = submit_command_job_call.args[2]
        return query, payload


async def main() -> None:
    print("=== PoC: reference/refers_to consistency ===")

    remove_query = await _capture_remove_query()
    _expect_legacy_failure(
        remove_query,
        "DELETE FROM reference WHERE out = $notebook_id AND in = $source_id",
        "Notebook source unlink direction",
    )
    assert (
        remove_query
        == "DELETE FROM reference WHERE out = $source_id AND in = $notebook_id"
    )
    print("[PASS] Notebook source unlink uses source -> notebook direction")

    retry_query, retry_payload = await _capture_retry_query_and_payload()
    _expect_legacy_failure(
        retry_query,
        "SELECT notebook FROM reference WHERE source = $source_id",
        "Retry relation query fields",
    )
    assert (
        retry_query == "SELECT in AS notebook_id FROM reference WHERE out = $source_id"
    )
    assert retry_payload["notebook_ids"] == ["notebook:1"]
    print(
        "[PASS] Retry uses in/out relation fields and extracts notebook_ids correctly"
    )

    print("=== PoC completed successfully ===")


if __name__ == "__main__":
    asyncio.run(main())
