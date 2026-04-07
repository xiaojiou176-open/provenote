from __future__ import annotations

import asyncio
from asyncio.subprocess import PIPE
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from packages.core.application.models import (
    UITestReportResponse,
    UITestRunRequest,
    UITestRunResponse,
    normalize_ui_test_spec_path,
)
from packages.core.exceptions import NotFoundError, RateLimitError


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Resource limits for _runs registry
MAX_RUNS = 100  # Maximum stored run records
MAX_CONCURRENT_UI_TEST_RUNS = 6
SHUTDOWN_WAIT_TIMEOUT_SECONDS = 30
PROCESS_DRAIN_TIMEOUT_SECONDS = 10
PROCESS_TERMINATE_GRACE_SECONDS = 5
PROCESS_OUTPUT_CAPTURE_LIMIT_BYTES = 256 * 1024
PROCESS_OUTPUT_READ_CHUNK_BYTES = 8 * 1024
GENERIC_EXECUTION_ERROR_MESSAGE = "playwright execution failed"


@dataclass
class UITestRunState:
    id: str
    status: str
    dry_run: bool
    command: list[str]
    created: str
    updated: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    return_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: Optional[float] = None
    _task: Optional[asyncio.Task[None]] = field(default=None, repr=False)


class UITestService:
    def __init__(self) -> None:
        self._runs: OrderedDict[str, UITestRunState] = OrderedDict()
        self._lock = asyncio.Lock()
        self._frontend_dir = Path(__file__).resolve().parents[3] / "apps" / "web"
        self._active_tasks: set[asyncio.Task] = set()
        self._is_shutting_down = False
        self._execution_semaphore = asyncio.Semaphore(MAX_CONCURRENT_UI_TEST_RUNS)

    def _track_task(self, task: asyncio.Task) -> None:
        """Track active async task for cleanup on shutdown."""
        self._active_tasks.add(task)
        task.add_done_callback(lambda t: self._active_tasks.discard(t))

    async def shutdown(self) -> None:
        """Cancel all active tasks and wait for cleanup.

        Should be called during application shutdown to prevent
        resource leaks from unfinished test executions.
        """
        async with self._lock:
            self._is_shutting_down = True
            tasks = list(self._active_tasks)

        if not tasks:
            async with self._lock:
                self._is_shutting_down = False
            return

        timed_out = False
        try:
            # Cancel all active tasks
            for task in tasks:
                if not task.done():
                    task.cancel()

            # Bound shutdown wait to avoid indefinite hangs from stuck tasks.
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=SHUTDOWN_WAIT_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            # Best-effort shutdown: continue teardown even if a task is stuck.
            timed_out = True
        finally:
            async with self._lock:
                if timed_out:
                    # Keep unfinished tasks tracked to avoid "invisible" zombie tasks
                    # when shutdown wait times out.
                    unfinished_tasks = {task for task in tasks if not task.done()}
                    self._active_tasks.update(unfinished_tasks)
                else:
                    self._active_tasks.difference_update(tasks)
                self._is_shutting_down = False

    @staticmethod
    def _build_command(request: UITestRunRequest) -> list[str]:
        command = [
            "npm",
            "run",
            "test:e2e",
            "--",
            f"--project={request.project}",
        ]
        if request.spec:
            command.append(normalize_ui_test_spec_path(request.spec))
        return command

    @staticmethod
    def _to_run_response(state: UITestRunState) -> UITestRunResponse:
        return UITestRunResponse(
            id=state.id,
            status=state.status,
            dry_run=state.dry_run,
            command=state.command,
            return_code=state.return_code,
            created=state.created,
            updated=state.updated,
        )

    @staticmethod
    def _to_report_response(state: UITestRunState) -> UITestReportResponse:
        return UITestReportResponse(
            id=state.id,
            status=state.status,
            dry_run=state.dry_run,
            command=state.command,
            return_code=state.return_code,
            stdout=state.stdout,
            stderr=state.stderr,
            started_at=state.started_at,
            finished_at=state.finished_at,
            duration_seconds=state.duration_seconds,
            created=state.created,
            updated=state.updated,
        )

    def _evict_oldest_runs(self) -> None:
        """Evict oldest completed runs when limit is reached.

        Only evicts runs that are not currently running.
        Must be called while holding self._lock.
        """
        while len(self._runs) >= MAX_RUNS:
            # Find oldest completed run to evict
            for run_id, state in list(self._runs.items()):
                if state.status in ("completed", "failed"):
                    del self._runs[run_id]
                    break
            else:
                # All runs are still running, can't evict
                break

    def get_runs_stats(self) -> dict:
        """Return statistics about stored runs for monitoring."""
        return {
            "total_runs": len(self._runs),
            "max_runs": MAX_RUNS,
            "active_tasks": len(self._active_tasks),
            "max_parallel_runs": MAX_CONCURRENT_UI_TEST_RUNS,
        }

    async def _mark_run_running(self, run_id: str) -> None:
        async with self._lock:
            state = self._runs[run_id]
            state.status = "running"
            state.started_at = _utc_now_iso()
            state.updated = state.started_at

    async def run(self, request: UITestRunRequest) -> UITestRunResponse:
        run_id = f"ui_test_run:{uuid4()}"
        now = _utc_now_iso()
        state = UITestRunState(
            id=run_id,
            status="queued",
            dry_run=request.dry_run,
            command=self._build_command(request),
            created=now,
            updated=now,
        )

        async with self._lock:
            if self._is_shutting_down:
                raise RateLimitError(
                    "UI test service is shutting down; rejecting new runs."
                )
            self._evict_oldest_runs()  # LRU eviction before adding new run
            if len(self._runs) >= MAX_RUNS:
                raise RateLimitError(
                    f"UI test run capacity reached ({MAX_RUNS}). "
                    "Wait for existing runs to finish before starting new ones."
                )
            self._runs[run_id] = state
            task = asyncio.create_task(self._execute(run_id, request))
            self._track_task(task)  # Track for shutdown cleanup
            state._task = task

        return self._to_run_response(state)

    async def get(self, run_id: str) -> UITestRunResponse:
        state = await self._get_state(run_id)
        return self._to_run_response(state)

    async def report(self, run_id: str) -> UITestReportResponse:
        state = await self._get_state(run_id)
        return self._to_report_response(state)

    async def _get_state(self, run_id: str) -> UITestRunState:
        async with self._lock:
            state = self._runs.get(run_id)
            if state is None:
                raise NotFoundError("UI test run not found")
            return state

    @staticmethod
    async def _capture_stream_with_limit(
        stream: asyncio.StreamReader | None,
    ) -> tuple[str, bool]:
        if stream is None:
            return "", False

        captured = bytearray()
        truncated = False
        while True:
            chunk = await stream.read(PROCESS_OUTPUT_READ_CHUNK_BYTES)
            if not chunk:
                break
            if len(captured) < PROCESS_OUTPUT_CAPTURE_LIMIT_BYTES:
                remaining = PROCESS_OUTPUT_CAPTURE_LIMIT_BYTES - len(captured)
                captured.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    truncated = True
            else:
                truncated = True

        return captured.decode("utf-8", errors="replace"), truncated

    @staticmethod
    def _with_truncation_marker(output: str, *, stream_name: str) -> str:
        suffix = (
            f"...[{stream_name} truncated at "
            f"{PROCESS_OUTPUT_CAPTURE_LIMIT_BYTES} bytes]"
        )
        if not output:
            return suffix
        return f"{output}\n{suffix}"

    async def _collect_process_output(
        self,
        *,
        process: asyncio.subprocess.Process,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        stdout_task = asyncio.create_task(
            self._capture_stream_with_limit(process.stdout)
        )
        stderr_task = asyncio.create_task(
            self._capture_stream_with_limit(process.stderr)
        )
        try:
            await asyncio.wait_for(process.wait(), timeout=timeout_seconds)
            stdout_text, stdout_truncated = await stdout_task
            stderr_text, stderr_truncated = await stderr_task
        except Exception:
            stdout_task.cancel()
            stderr_task.cancel()
            await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
            raise

        if stdout_truncated:
            stdout_text = self._with_truncation_marker(
                stdout_text, stream_name="stdout"
            )
        if stderr_truncated:
            stderr_text = self._with_truncation_marker(
                stderr_text, stream_name="stderr"
            )
        return_code = process.returncode if process.returncode is not None else -1
        return return_code, stdout_text, stderr_text

    async def _execute(self, run_id: str, request: UITestRunRequest) -> None:
        started_monotonic = asyncio.get_running_loop().time()
        process = None
        try:
            if request.dry_run:
                await self._mark_run_running(run_id)
                await self._complete_run(
                    run_id=run_id,
                    status="completed",
                    return_code=0,
                    stdout="dry_run: playwright execution skipped",
                    stderr="",
                    started_monotonic=started_monotonic,
                )
                return

            async with self._execution_semaphore:
                await self._mark_run_running(run_id)
                process = await asyncio.create_subprocess_exec(
                    *self._build_command(request),
                    cwd=str(self._frontend_dir),
                    stdout=PIPE,
                    stderr=PIPE,
                )

                (
                    return_code,
                    stdout_text,
                    stderr_text,
                ) = await self._collect_process_output(
                    process=process,
                    timeout_seconds=request.timeout_seconds,
                )
                status = "completed" if return_code == 0 else "failed"
                await self._complete_run(
                    run_id=run_id,
                    status=status,
                    return_code=return_code,
                    stdout=stdout_text,
                    stderr=stderr_text,
                    started_monotonic=started_monotonic,
                )
        except asyncio.TimeoutError:
            await self._finalize_timeout(
                run_id=run_id,
                timeout_seconds=request.timeout_seconds,
                process=process,
                started_monotonic=started_monotonic,
            )
        except asyncio.CancelledError:
            # Graceful shutdown - ensure process is cleaned up
            if process is not None:
                await self._terminate_process(process)
            async with self._lock:
                current_state = self._runs.get(run_id)
                should_complete = (
                    current_state is not None
                    and current_state.status
                    in {
                        "queued",
                        "running",
                    }
                )
            if should_complete:
                await self._finalize_run_state(
                    run_id=run_id,
                    status="failed",
                    return_code=-1,
                    stdout="",
                    stderr="run cancelled during shutdown",
                    started_monotonic=started_monotonic,
                )
            raise  # Re-raise to allow proper task cancellation
        except (OSError, RuntimeError, ValueError):
            # Ensure any non-cancellation failure marks the run as failed
            # so status never gets stuck at "running".
            if process is not None:
                await self._terminate_process(process)
            await self._complete_run(
                run_id=run_id,
                status="failed",
                return_code=-1,
                stdout="",
                stderr=GENERIC_EXECUTION_ERROR_MESSAGE,
                started_monotonic=started_monotonic,
            )

    async def _finalize_timeout(
        self,
        *,
        run_id: str,
        timeout_seconds: int,
        process: asyncio.subprocess.Process | None,
        started_monotonic: float,
    ) -> None:
        async def _finalizer() -> None:
            if process is not None:
                await self._terminate_process(process)
            await self._complete_run(
                run_id=run_id,
                status="failed",
                return_code=-1,
                stdout="",
                stderr=f"playwright run timed out after {timeout_seconds}s",
                started_monotonic=started_monotonic,
            )

        task = asyncio.create_task(_finalizer())
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            try:
                await asyncio.wait_for(task, timeout=PROCESS_DRAIN_TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                task.cancel()
                await self._force_complete_if_pending(
                    run_id=run_id,
                    status="failed",
                    return_code=-1,
                    stdout="",
                    stderr=f"playwright run timed out after {timeout_seconds}s",
                    started_monotonic=started_monotonic,
                )
            raise

    async def _finalize_run_state(
        self,
        *,
        run_id: str,
        status: str,
        return_code: int,
        stdout: str,
        stderr: str,
        started_monotonic: float,
    ) -> None:
        task = asyncio.create_task(
            self._complete_run(
                run_id=run_id,
                status=status,
                return_code=return_code,
                stdout=stdout,
                stderr=stderr,
                started_monotonic=started_monotonic,
            )
        )
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            try:
                await asyncio.wait_for(task, timeout=PROCESS_DRAIN_TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                task.cancel()
                await self._force_complete_if_pending(
                    run_id=run_id,
                    status=status,
                    return_code=return_code,
                    stdout=stdout,
                    stderr=stderr,
                    started_monotonic=started_monotonic,
                )
            raise

    async def _terminate_process(self, process: asyncio.subprocess.Process) -> None:
        try:
            if process.returncode is not None:
                return
            process.terminate()
            await asyncio.wait_for(
                process.wait(), timeout=PROCESS_TERMINATE_GRACE_SECONDS
            )
        except (ProcessLookupError, asyncio.TimeoutError):
            try:
                if process.returncode is not None:
                    return
                process.kill()
                await asyncio.wait_for(
                    process.wait(), timeout=PROCESS_TERMINATE_GRACE_SECONDS
                )
            except (ProcessLookupError, asyncio.TimeoutError):
                pass

    async def _complete_run(
        self,
        *,
        run_id: str,
        status: str,
        return_code: int,
        stdout: str,
        stderr: str,
        started_monotonic: float,
    ) -> None:
        finished_at = _utc_now_iso()
        duration = asyncio.get_running_loop().time() - started_monotonic
        async with self._lock:
            state = self._runs[run_id]
            state.status = status
            state.return_code = return_code
            state.stdout = stdout
            state.stderr = stderr
            state.finished_at = finished_at
            state.duration_seconds = round(duration, 3)
            state.updated = finished_at

    async def _force_complete_if_pending(
        self,
        *,
        run_id: str,
        status: str,
        return_code: int,
        stdout: str,
        stderr: str,
        started_monotonic: float,
    ) -> None:
        """Best-effort fallback: force finalize if a run is still queued/running."""
        finished_at = _utc_now_iso()
        duration = asyncio.get_running_loop().time() - started_monotonic
        async with self._lock:
            state = self._runs.get(run_id)
            if state is None or state.status not in {"queued", "running"}:
                return
            state.status = status
            state.return_code = return_code
            state.stdout = stdout
            state.stderr = stderr
            state.finished_at = finished_at
            state.duration_seconds = round(duration, 3)
            state.updated = finished_at


ui_test_service = UITestService()
