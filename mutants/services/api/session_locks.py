import asyncio
import time
from collections import OrderedDict
from datetime import datetime, timedelta

# LRU + TTL based session lock registry to prevent memory leaks
_SESSION_LOCKS: OrderedDict[str, tuple[asyncio.Lock, float | datetime]] = OrderedDict()
_SESSION_LOCKS_GUARD = asyncio.Lock()

# Resource limits
MAX_SESSION_LOCKS = 1000  # Maximum concurrent sessions
LOCK_TTL = timedelta(hours=1)  # Locks expire after 1 hour of inactivity


class SessionLockCapacityError(RuntimeError):
    """Raised when the lock registry is full and no idle lock can be evicted."""


async def get_session_lock(session_id: str) -> asyncio.Lock:
    """Return a shared per-session lock with LRU eviction and TTL expiry.

    Resource management:
    - Maximum 1000 concurrent session locks (LRU eviction)
    - Locks expire after 1 hour of inactivity
    - Stale locks are evicted on each access
    - Inactivity age is tracked with a monotonic clock to avoid wall-clock skew
    """
    async with _SESSION_LOCKS_GUARD:
        _evict_stale_locks()
        now_monotonic = _now_monotonic()

        # Existing lock - move to end (MRU)
        if session_id in _SESSION_LOCKS:
            lock, _ = _SESSION_LOCKS[session_id]
            _SESSION_LOCKS.move_to_end(session_id)
            # Update timestamp
            _SESSION_LOCKS[session_id] = (lock, now_monotonic)
            return lock

        # LRU eviction if at capacity
        if len(_SESSION_LOCKS) >= MAX_SESSION_LOCKS:
            if not _evict_oldest_unlocked_lock():
                raise SessionLockCapacityError(
                    "Session lock capacity reached "
                    f"({MAX_SESSION_LOCKS}) and all locks are currently in use."
                )

        # Create new lock
        lock = asyncio.Lock()
        _SESSION_LOCKS[session_id] = (lock, now_monotonic)
        return lock


def _now_monotonic() -> float:
    """Return monotonic timestamp for lock inactivity tracking."""
    return time.monotonic()


def _entry_age_seconds(last_access_timestamp: float | datetime) -> float:
    """Compute entry age in seconds with compatibility for legacy datetime values."""
    if isinstance(last_access_timestamp, datetime):
        age_seconds = (datetime.now() - last_access_timestamp).total_seconds()
        return max(age_seconds, 0.0)
    age_seconds = _now_monotonic() - last_access_timestamp
    return max(age_seconds, 0.0)


def _evict_oldest_unlocked_lock() -> bool:
    """Evict the oldest lock entry that is currently not locked."""
    for session_key, (lock, _) in list(_SESSION_LOCKS.items()):
        if lock.locked():
            continue
        _SESSION_LOCKS.pop(session_key, None)
        return True
    return False


def _evict_stale_locks() -> None:
    """Remove unlocked locks that have expired based on TTL."""
    lock_ttl_seconds = LOCK_TTL.total_seconds()
    to_remove = [
        session_id
        for session_id, (lock, timestamp) in _SESSION_LOCKS.items()
        if _entry_age_seconds(timestamp) > lock_ttl_seconds and not lock.locked()
    ]
    for session_id in to_remove:
        _SESSION_LOCKS.pop(session_id, None)


def reset_session_locks() -> None:
    """Testing helper to reset lock registry between test cases."""
    _SESSION_LOCKS.clear()


def get_session_locks_stats() -> dict:
    """Get current session locks statistics for monitoring.

    Returns:
        dict with keys: total_locks, oldest_lock_age_seconds, capacity_usage_percent
    """
    if not _SESSION_LOCKS:
        return {
            "total_locks": 0,
            "oldest_lock_age_seconds": 0,
            "capacity_usage_percent": 0.0,
        }

    oldest_age = max(_entry_age_seconds(ts) for _, ts in _SESSION_LOCKS.values())

    return {
        "total_locks": len(_SESSION_LOCKS),
        "oldest_lock_age_seconds": oldest_age,
        "capacity_usage_percent": (len(_SESSION_LOCKS) / MAX_SESSION_LOCKS) * 100,
    }
