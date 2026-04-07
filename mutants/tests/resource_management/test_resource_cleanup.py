"""Test resource management and cleanup logic."""

import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from types import MethodType
from unittest.mock import AsyncMock, patch

import pytest


async def _wait_until(
    predicate,
    *,
    timeout_seconds: float = 1.5,
    poll_interval_seconds: float = 0.01,
    failure_message: str,
) -> None:
    """Wait until predicate returns truthy to avoid hard-coded timing assumptions."""
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while asyncio.get_running_loop().time() < deadline:
        if predicate():
            return
        await asyncio.sleep(poll_interval_seconds)
    pytest.fail(failure_message)


class TestSessionLocksResourceManagement:
    """Test session locks LRU + TTL resource management."""

    @pytest.fixture(autouse=True)
    def cleanup_locks(self):
        """Cleanup locks before and after each test."""
        from services.api.session_locks import reset_session_locks

        reset_session_locks()
        yield
        reset_session_locks()

    @pytest.mark.asyncio
    async def test_session_lock_basic_functionality(self):
        """Test basic lock creation and reuse."""
        from services.api.session_locks import get_session_lock

        lock1 = await get_session_lock("session_1")
        lock2 = await get_session_lock("session_1")

        # Same session returns same lock
        assert lock1 is lock2

        lock3 = await get_session_lock("session_2")
        # Different session returns different lock
        assert lock1 is not lock3

    @pytest.mark.asyncio
    async def test_session_lock_stats(self):
        """Test session lock statistics."""
        from services.api import session_locks as session_locks_module
        from services.api.session_locks import get_session_lock, get_session_locks_stats

        # Empty state
        stats = get_session_locks_stats()
        assert stats["total_locks"] == 0
        assert stats["oldest_lock_age_seconds"] == 0
        assert stats["capacity_usage_percent"] == 0.0

        # Add some locks
        lock_1 = await get_session_lock("session_1")
        session_locks_module._SESSION_LOCKS["session_1"] = (
            lock_1,
            session_locks_module._now_monotonic() - 0.05,
        )
        await get_session_lock("session_2")

        stats = get_session_locks_stats()
        assert stats["total_locks"] == 2
        assert stats["oldest_lock_age_seconds"] >= 0.05
        assert 0 < stats["capacity_usage_percent"] < 1


class TestUITestServiceResourceManagement:
    """Test UI test service async task cleanup."""

    @pytest.mark.asyncio
    async def test_ui_test_service_shutdown(self):
        """Test that shutdown cancels active tasks and clears tracking."""
        from packages.core.application.models import UITestRunRequest
        from packages.core.application.ui_test_service import UITestService

        service = UITestService()
        request = UITestRunRequest(
            project="chromium",
            dry_run=False,
            timeout_seconds=5,
        )
        block_forever = asyncio.Event()
        task_started = asyncio.Event()
        cancellation_observed = asyncio.Event()

        async def blocking_execute(
            _self: UITestService, run_id: str, request: UITestRunRequest
        ) -> None:
            _ = run_id, request
            task_started.set()
            try:
                await block_forever.wait()
            except asyncio.CancelledError:
                cancellation_observed.set()
                raise

        service._execute = MethodType(blocking_execute, service)

        response = await service.run(request)
        assert response.status == "queued"

        await _wait_until(
            lambda: len(service._active_tasks) == 1,
            failure_message="Timed out waiting for active task registration",
        )
        await _wait_until(
            task_started.is_set,
            failure_message="Timed out waiting for test task to start",
        )

        await service.shutdown()

        assert cancellation_observed.is_set()
        assert len(service._active_tasks) == 0
        assert service._is_shutting_down is False

    @pytest.mark.asyncio
    async def test_timeout_cleanup_cancellation_still_finalizes_run(self):
        """Timeout finalizer should still mark run failed when task is cancelled."""
        from packages.core.application.models import UITestRunRequest
        from packages.core.application.ui_test_service import UITestService

        service = UITestService()

        class _FakeProcess:
            def __init__(self) -> None:
                self.returncode = None
                self.timeout_cleanup_started = asyncio.Event()
                self.stdout = None
                self.stderr = None

            async def wait(self):
                self.timeout_cleanup_started.set()
                await asyncio.sleep(0.2)
                self.returncode = 0
                return 0

            def kill(self) -> None:
                self.returncode = -9

        fake_process = _FakeProcess()
        request = UITestRunRequest(
            project="chromium",
            dry_run=False,
            timeout_seconds=1,
        )

        with patch(
            "packages.core.application.ui_test_service.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=fake_process),
        ):
            response = await service.run(request)
            run_id = response.id
            run_task = service._runs[run_id]._task
            assert run_task is not None and hasattr(run_task, "cancel")
            await _wait_until(
                fake_process.timeout_cleanup_started.is_set,
                timeout_seconds=2.5,
                poll_interval_seconds=0.02,
                failure_message=(
                    "Timed out waiting for timeout-cleanup subprocess communication"
                ),
            )

            run_task.cancel()
            await asyncio.gather(run_task, return_exceptions=True)

            report = await service.report(run_id)
            assert report.status == "failed"
            assert report.return_code == -1
            assert report.finished_at is not None and report.status == "failed"
            assert (
                "timed out" in report.stderr
                or "cancelled during shutdown" in report.stderr
            )

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_restores_accepting_new_runs(self):
        """Service should accept new runs again after shutdown completes."""
        from packages.core.application.models import UITestRunRequest
        from packages.core.application.ui_test_service import UITestService

        service = UITestService()
        request = UITestRunRequest(
            project="chromium",
            dry_run=True,
            timeout_seconds=5,
        )
        try:
            await service.shutdown()
            response = await service.run(request)
            assert response.status == "queued"
        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_timeout_keeps_unfinished_tasks_tracked(self):
        """When shutdown wait times out, unfinished tasks must remain tracked."""
        from packages.core.application.ui_test_service import UITestService

        service = UITestService()

        class _PendingTask:
            def __init__(self) -> None:
                self.cancelled = False

            def done(self) -> bool:
                return False

            def cancel(self) -> None:
                self.cancelled = True

        pending_task = _PendingTask()
        service._active_tasks.add(pending_task)

        async def _fake_gather(*_args, **_kwargs):
            return None

        async def _fake_wait_for(awaitable, timeout):
            _ = timeout
            if asyncio.iscoroutine(awaitable):
                awaitable.close()
            raise asyncio.TimeoutError

        with (
            patch(
                "packages.core.application.ui_test_service.asyncio.gather",
                new=_fake_gather,
            ),
            patch(
                "packages.core.application.ui_test_service.asyncio.wait_for",
                new=_fake_wait_for,
            ),
        ):
            await service.shutdown()

        assert pending_task.cancelled is True
        assert pending_task in service._active_tasks
        assert service._is_shutting_down is False
        service._active_tasks.clear()

    @pytest.mark.asyncio
    async def test_finalize_run_state_forces_failed_status_when_drain_times_out(self):
        """Cancelled finalization must not leave run status stuck at running."""
        from packages.core.application.ui_test_service import (
            UITestRunState,
            UITestService,
        )

        service = UITestService()
        run_id = "ui_test_run:force-finalize"
        now_iso = datetime.now().isoformat()
        service._runs[run_id] = UITestRunState(
            id=run_id,
            status="running",
            dry_run=False,
            command=["npm", "run", "test:e2e"],
            created=now_iso,
            updated=now_iso,
        )

        async def _slow_complete_run(**_kwargs):
            await asyncio.sleep(60)

        with (
            patch.object(service, "_complete_run", new=_slow_complete_run),
            patch(
                "packages.core.application.ui_test_service.PROCESS_DRAIN_TIMEOUT_SECONDS",
                0,
            ),
        ):
            finalize_task = asyncio.create_task(
                service._finalize_run_state(
                    run_id=run_id,
                    status="failed",
                    return_code=-1,
                    stdout="",
                    stderr="forced-timeout",
                    started_monotonic=asyncio.get_running_loop().time() - 0.5,
                )
            )
            await asyncio.sleep(0)
            finalize_task.cancel()
            await asyncio.gather(finalize_task, return_exceptions=True)

        report = await service.report(run_id)
        assert report.status == "failed"
        assert report.return_code == -1
        assert report.stderr == "forced-timeout"
        assert report.finished_at is not None and report.status == "failed"

    @pytest.mark.asyncio
    async def test_ui_test_service_task_tracking(self):
        """Test that tasks are properly tracked and removed on completion."""
        from packages.core.application.models import UITestRunRequest
        from packages.core.application.ui_test_service import UITestService

        service = UITestService()

        # Create a dry run (completes quickly)
        request = UITestRunRequest(
            project="chromium",
            dry_run=True,
            timeout_seconds=5,
        )

        try:
            await service.run(request)

            await _wait_until(
                lambda: len(service._active_tasks) == 0,
                failure_message="UI test task was not removed from active tracking",
            )

            # Task should be removed from tracking after completion
            # (done callback removes it)
            assert len(service._active_tasks) == 0
        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_ui_test_service_runs_stats(self):
        """Test that runs stats are properly reported."""
        from packages.core.application.models import UITestRunRequest
        from packages.core.application.ui_test_service import (
            MAX_CONCURRENT_UI_TEST_RUNS,
            MAX_RUNS,
            UITestService,
        )

        service = UITestService()

        try:
            # Initial stats
            stats = service.get_runs_stats()
            assert stats["total_runs"] == 0
            assert stats["max_runs"] == MAX_RUNS
            assert stats["active_tasks"] == 0
            assert stats["max_parallel_runs"] == MAX_CONCURRENT_UI_TEST_RUNS

            # Create a dry run
            request = UITestRunRequest(
                project="chromium",
                dry_run=True,
                timeout_seconds=5,
            )

            await service.run(request)

            stats = service.get_runs_stats()
            assert stats["total_runs"] == 1
        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_ui_test_service_limits_concurrent_execution_with_semaphore(self):
        """Non-dry runs should execute with a hard concurrency cap."""
        from packages.core.application.models import UITestRunRequest
        from packages.core.application.ui_test_service import (
            MAX_CONCURRENT_UI_TEST_RUNS,
            UITestService,
        )

        service = UITestService()
        request = UITestRunRequest(
            project="chromium",
            dry_run=False,
            timeout_seconds=5,
        )

        release_event = asyncio.Event()
        counter_lock = asyncio.Lock()
        running_count = 0
        max_running = 0

        class _FakeProcess:
            def __init__(self) -> None:
                self.stdout = None
                self.stderr = None
                self.returncode = None

            async def wait(self) -> int:
                await release_event.wait()
                self.returncode = 0
                return 0

            def kill(self) -> None:
                self.returncode = -9

        async def _fake_collect_process_output(*, process, timeout_seconds):
            _ = process, timeout_seconds
            nonlocal running_count, max_running
            async with counter_lock:
                running_count += 1
                max_running = max(max_running, running_count)
            await release_event.wait()
            async with counter_lock:
                running_count -= 1
            return 0, "", ""

        with (
            patch(
                "packages.core.application.ui_test_service.asyncio.create_subprocess_exec",
                new=AsyncMock(side_effect=lambda *_args, **_kwargs: _FakeProcess()),
            ),
            patch.object(
                service,
                "_collect_process_output",
                new=_fake_collect_process_output,
            ),
        ):
            run_ids = []
            for _ in range(MAX_CONCURRENT_UI_TEST_RUNS + 1):
                response = await service.run(request)
                run_ids.append(response.id)

            await _wait_until(
                lambda: max_running == MAX_CONCURRENT_UI_TEST_RUNS,
                failure_message="Semaphore cap was not reached in time",
            )

            # Ensure queued extra run does not increase concurrent execution above limit.
            await asyncio.sleep(0.05)
            assert max_running == MAX_CONCURRENT_UI_TEST_RUNS

            release_event.set()
            await _wait_until(
                lambda: all(
                    service._runs[run_id].status in {"completed", "failed"}
                    for run_id in run_ids
                ),
                timeout_seconds=3.0,
                failure_message="Timed out waiting for semaphore-gated runs to complete",
            )

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_ui_test_service_output_capture_is_byte_capped(self):
        """Large subprocess output should be capped with truncation markers."""
        from packages.core.application.models import UITestRunRequest
        from packages.core.application.ui_test_service import UITestService

        class _FakeStream:
            def __init__(self, payload: bytes) -> None:
                self._payload = payload
                self._offset = 0

            async def read(self, size: int) -> bytes:
                await asyncio.sleep(0)
                if self._offset >= len(self._payload):
                    return b""
                chunk = self._payload[self._offset : self._offset + size]
                self._offset += len(chunk)
                return chunk

        class _FakeProcess:
            def __init__(self, stdout_payload: bytes, stderr_payload: bytes) -> None:
                self.stdout = _FakeStream(stdout_payload)
                self.stderr = _FakeStream(stderr_payload)
                self.returncode = None

            async def wait(self) -> int:
                await asyncio.sleep(0.01)
                self.returncode = 0
                return 0

            def kill(self) -> None:
                self.returncode = -9

        service = UITestService()
        request = UITestRunRequest(
            project="chromium",
            dry_run=False,
            timeout_seconds=5,
        )

        fake_process = _FakeProcess(
            stdout_payload=b"abcdefghijk",
            stderr_payload=b"123456789",
        )
        with (
            patch(
                "packages.core.application.ui_test_service.PROCESS_OUTPUT_CAPTURE_LIMIT_BYTES",
                8,
            ),
            patch(
                "packages.core.application.ui_test_service.asyncio.create_subprocess_exec",
                new=AsyncMock(return_value=fake_process),
            ),
        ):
            response = await service.run(request)
            run_id = response.id
            await _wait_until(
                lambda: service._runs[run_id].status in {"completed", "failed"},
                failure_message="Timed out waiting for capped output run completion",
            )
            report = await service.report(run_id)

        assert report.status == "completed"
        assert report.stdout.startswith("abcdefgh")
        assert "...[stdout truncated at 8 bytes]" in report.stdout
        assert report.stderr.startswith("12345678")
        assert "...[stderr truncated at 8 bytes]" in report.stderr

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_ui_test_service_lru_eviction(self):
        """Test that old completed runs are evicted when limit is reached."""
        from packages.core.application.models import UITestRunRequest
        from packages.core.application.ui_test_service import MAX_RUNS, UITestService

        service = UITestService()

        try:
            # Create MAX_RUNS dry runs
            request = UITestRunRequest(
                project="chromium",
                dry_run=True,
                timeout_seconds=5,
            )

            run_ids = []
            for _ in range(MAX_RUNS):
                response = await service.run(request)
                run_ids.append(response.id)
            await _wait_until(
                lambda: all(
                    run_state.status in {"completed", "failed"}
                    for run_state in service._runs.values()
                ),
                timeout_seconds=3.0,
                failure_message=(
                    "Timed out waiting for queued runs to complete before eviction"
                ),
            )

            stats = service.get_runs_stats()
            assert stats["total_runs"] == MAX_RUNS

            # Add one more - should evict oldest
            response = await service.run(request)
            await _wait_until(
                lambda: service._runs.get(response.id) is not None
                and service._runs[response.id].status in {"completed", "failed"},
                failure_message="Newest run did not complete in time for eviction assertion",
            )

            stats = service.get_runs_stats()
            assert stats["total_runs"] == MAX_RUNS  # Still at limit
        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_ui_test_service_rejects_when_all_runs_active(self):
        """Reject new run when capacity is full of active tasks."""
        from packages.core.application.models import UITestRunRequest
        from packages.core.application.ui_test_service import MAX_RUNS, UITestService
        from packages.core.exceptions import RateLimitError

        service = UITestService()
        request = UITestRunRequest(project="chromium", dry_run=False, timeout_seconds=5)
        block_forever = asyncio.Event()

        async def blocking_execute(
            _self: UITestService, run_id: str, request: UITestRunRequest
        ) -> None:
            _ = run_id, request
            await block_forever.wait()

        service._execute = MethodType(blocking_execute, service)

        for _ in range(MAX_RUNS):
            await service.run(request)

        with pytest.raises(RateLimitError):
            await service.run(request)

        await service.shutdown()
        assert len(service._active_tasks) == 0


class TestTempFileCleanup:
    """Test temporary file cleanup patterns."""

    def test_tempfile_context_manager_cleanup(self):
        """Test that tempfile context managers properly cleanup."""
        temp_path = None

        with tempfile.NamedTemporaryFile(delete=True) as f:
            temp_path = f.name
            assert os.path.exists(temp_path)

        # File should be deleted after context exit
        assert not os.path.exists(temp_path)

    def test_tempdir_context_manager_cleanup(self):
        """Test that tempdir context managers properly cleanup."""
        temp_dir = None

        with tempfile.TemporaryDirectory() as d:
            temp_dir = d
            assert os.path.isdir(temp_dir)

            # Create some files inside
            Path(d, "test.txt").write_text("test")

        # Directory should be deleted after context exit
        assert not os.path.exists(temp_dir)


class TestCleanupScriptLogic:
    """Test cleanup script logic patterns."""

    def test_age_based_cleanup_logic(self):
        """Test age-based file cleanup logic."""
        max_age_days = 7
        cutoff = datetime.now() - timedelta(days=max_age_days)

        # Files older than cutoff should be cleaned
        old_file_time = datetime.now() - timedelta(days=10)
        new_file_time = datetime.now() - timedelta(days=3)

        assert old_file_time < cutoff  # Should be cleaned
        assert new_file_time > cutoff  # Should be kept

    def test_size_based_cleanup_logic(self):
        """Test size-based cleanup logic."""
        max_mb = 100
        target_percent = 80

        limit_bytes = max_mb * 1024 * 1024
        target_bytes = limit_bytes * target_percent // 100

        # If current size exceeds limit, should trim to target
        current_bytes = 120 * 1024 * 1024  # 120 MB

        assert current_bytes > limit_bytes
        assert target_bytes < limit_bytes

        # After cleanup, should be at or below target
        bytes_to_remove = current_bytes - target_bytes
        assert bytes_to_remove > 0


class TestResourceLeakPrevention:
    """Test patterns that prevent resource leaks."""

    @pytest.mark.asyncio
    async def test_asyncio_task_exception_handling(self):
        """Test that task exceptions don't cause resource leaks."""
        tasks_completed = []

        async def failing_task():
            await asyncio.sleep(0.01)
            raise ValueError("Test error")

        async def successful_task():
            await asyncio.sleep(0.01)
            tasks_completed.append(True)

        # gather with return_exceptions prevents unhandled exceptions
        results = await asyncio.gather(
            failing_task(),
            successful_task(),
            return_exceptions=True,
        )

        # Both tasks completed (one with exception)
        assert len(results) == 2
        assert isinstance(results[0], ValueError)
        assert results[1] is None
        assert len(tasks_completed) == 1

    @pytest.mark.asyncio
    async def test_asyncio_lock_release_on_exception(self):
        """Test that locks are released even when exceptions occur."""
        lock = asyncio.Lock()

        async def task_with_exception():
            async with lock:
                raise ValueError("Test error")

        with pytest.raises(ValueError):
            await task_with_exception()

        # Lock should be released after exception
        assert not lock.locked()

    def test_file_handle_cleanup_on_exception(self):
        """Test that file handles are closed on exception."""
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_path = temp_file.name
        temp_file.close()

        try:
            with open(temp_path, "w") as f:
                f.write("test")
                raise ValueError("Test error")
        except ValueError:
            pass

        # File should be closed (can be deleted)
        os.unlink(temp_path)
        assert not os.path.exists(temp_path)
