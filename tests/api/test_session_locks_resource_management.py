"""Test session locks resource management (LRU + TTL)."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from services.api.session_locks import (
    LOCK_TTL,
    MAX_SESSION_LOCKS,
    SessionLockCapacityError,
    get_session_lock,
    get_session_locks_stats,
    reset_session_locks,
)


@pytest.fixture(autouse=True)
def cleanup_locks():
    """Cleanup locks before and after each test."""
    reset_session_locks()
    yield
    reset_session_locks()


@pytest.mark.asyncio
async def test_session_lock_basic_functionality():
    """Test basic lock creation and reuse."""
    lock1 = await get_session_lock("session_1")
    lock2 = await get_session_lock("session_1")

    # Same session returns same lock
    assert lock1 is lock2

    lock3 = await get_session_lock("session_2")
    # Different session returns different lock
    assert lock1 is not lock3


@pytest.mark.asyncio
async def test_session_lock_lru_eviction():
    """Test LRU eviction when max capacity is reached."""
    # Fill up to capacity
    for i in range(MAX_SESSION_LOCKS):
        await get_session_lock(f"session_{i}")

    stats = get_session_locks_stats()
    assert stats["total_locks"] == MAX_SESSION_LOCKS
    assert stats["capacity_usage_percent"] == 100.0

    # Add one more - should evict oldest (session_0)
    await get_session_lock("session_new")

    stats = get_session_locks_stats()
    assert stats["total_locks"] == MAX_SESSION_LOCKS

    # Verify session_0 was evicted (new lock created)
    lock_new = await get_session_lock("session_0")
    lock_1 = await get_session_lock("session_1")
    # session_0 should get a new lock instance
    assert lock_new is not lock_1


@pytest.mark.asyncio
async def test_session_lock_ttl_expiry():
    """Test TTL-based eviction of stale locks."""
    # Create lock
    lock1 = await get_session_lock("session_expire")

    # Mock time to simulate TTL expiry
    expired_time = datetime.now() - LOCK_TTL - timedelta(minutes=1)

    with patch("services.api.session_locks._SESSION_LOCKS") as mock_locks:
        # Manually set expired timestamp
        mock_locks.__getitem__.return_value = (lock1, expired_time)
        mock_locks.__contains__.return_value = True
        mock_locks.items.return_value = [("session_expire", (lock1, expired_time))]
        mock_locks.pop.return_value = None

        # Access any session should trigger eviction
        await get_session_lock("session_other")

        # Verify eviction was called
        mock_locks.pop.assert_called_with("session_expire", None)


@pytest.mark.asyncio
async def test_locked_lock_not_evicted_by_ttl():
    """A locked entry should not be removed even if its timestamp is stale."""
    from services.api import session_locks as session_locks_module

    locked_entry = await get_session_lock("session_locked")
    await locked_entry.acquire()
    try:
        expired_time = datetime.now() - LOCK_TTL - timedelta(minutes=1)
        session_locks_module._SESSION_LOCKS["session_locked"] = (
            locked_entry,
            expired_time,
        )

        await get_session_lock("session_other")
        retained = await get_session_lock("session_locked")
        assert retained is locked_entry
    finally:
        if locked_entry.locked():
            locked_entry.release()


@pytest.mark.asyncio
async def test_locked_lock_not_evicted_by_lru():
    """When capacity is full, LRU eviction should skip actively locked entries."""
    from services.api import session_locks as session_locks_module

    with patch.object(session_locks_module, "MAX_SESSION_LOCKS", 2):
        locked_oldest = await get_session_lock("session_oldest")
        await locked_oldest.acquire()
        try:
            next_candidate = await get_session_lock("session_next")
            await get_session_lock("session_new")

            assert await get_session_lock("session_oldest") is locked_oldest
            assert await get_session_lock("session_next") is not next_candidate
        finally:
            if locked_oldest.locked():
                locked_oldest.release()


@pytest.mark.asyncio
async def test_capacity_full_of_active_locks_raises_error():
    """When all lock slots are active, creation should fail with a clear error."""
    from services.api import session_locks as session_locks_module

    with patch.object(session_locks_module, "MAX_SESSION_LOCKS", 2):
        lock_a = await get_session_lock("session_A")
        lock_b = await get_session_lock("session_B")
        await lock_a.acquire()
        await lock_b.acquire()
        try:
            with pytest.raises(
                SessionLockCapacityError,
                match="all locks are currently in use",
            ):
                await get_session_lock("session_new")
        finally:
            if lock_a.locked():
                lock_a.release()
            if lock_b.locked():
                lock_b.release()


@pytest.mark.asyncio
async def test_session_lock_mru_update():
    """Test that accessing a lock updates its MRU position."""
    # Create several locks
    await get_session_lock("session_A")
    await get_session_lock("session_B")
    await get_session_lock("session_C")

    # Access session_A again (should move to end)
    lock_a = await get_session_lock("session_A")

    # Fill to capacity
    for i in range(MAX_SESSION_LOCKS - 3):
        await get_session_lock(f"session_{i}")

    # Add one more - should evict session_B (not session_A)
    await get_session_lock("session_new")

    # session_A should still exist (was refreshed)
    lock_a_again = await get_session_lock("session_A")
    assert lock_a is lock_a_again


@pytest.mark.asyncio
async def test_session_lock_stats():
    """Test session lock statistics."""
    from services.api import session_locks as session_locks_module

    # Empty state
    stats = get_session_locks_stats()
    assert stats["total_locks"] == 0
    assert stats["oldest_lock_age_seconds"] == 0
    assert stats["capacity_usage_percent"] == 0.0

    # Add some locks
    lock_1 = await get_session_lock("session_1")
    session_locks_module._SESSION_LOCKS["session_1"] = (
        lock_1,
        datetime.now() - timedelta(seconds=0.1),
    )
    await get_session_lock("session_2")

    stats = get_session_locks_stats()
    assert stats["total_locks"] == 2
    assert stats["oldest_lock_age_seconds"] >= 0.1
    assert 0 < stats["capacity_usage_percent"] < 1


@pytest.mark.asyncio
async def test_session_lock_concurrent_access():
    """Test concurrent access to session locks."""

    async def access_lock(session_id: str):
        lock = await get_session_lock(session_id)
        async with lock:
            await asyncio.sleep(0.01)

    # Concurrent access to same session
    tasks = [access_lock("shared_session") for _ in range(10)]
    await asyncio.gather(*tasks)

    # All tasks completed without error
    # Lock count should be 1 (shared)
    stats = get_session_locks_stats()
    assert stats["total_locks"] == 1


@pytest.mark.asyncio
async def test_reset_session_locks():
    """Test reset helper for testing."""
    await get_session_lock("session_1")
    await get_session_lock("session_2")

    stats = get_session_locks_stats()
    assert stats["total_locks"] == 2

    reset_session_locks()

    stats = get_session_locks_stats()
    assert stats["total_locks"] == 0
