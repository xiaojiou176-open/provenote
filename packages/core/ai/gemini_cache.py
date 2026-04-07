"""Gemini context cache lifecycle helpers."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from hashlib import sha1
from typing import Dict, Optional, Protocol


@dataclass(frozen=True)
class GeminiCacheEntry:
    handle: str
    expires_at: float


@dataclass(frozen=True)
class GeminiCacheResolution:
    handle: str
    status: str
    ttl_seconds: int
    expires_at: float


@dataclass(frozen=True)
class GeminiCacheTelemetry:
    max_entries: int
    active_entries: int
    provided: int
    hit: int
    miss: int
    expired: int
    invalidated: int
    evicted: int


class GeminiCacheBackend(Protocol):
    def get(self, key: str) -> Optional[GeminiCacheEntry]: ...

    def set(self, key: str, entry: GeminiCacheEntry) -> None: ...

    def delete(self, key: str) -> None: ...

    def items(self) -> Dict[str, GeminiCacheEntry]: ...


class InMemoryGeminiCacheBackend:
    def __init__(self) -> None:
        self._entries: Dict[str, GeminiCacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[GeminiCacheEntry]:
        with self._lock:
            return self._entries.get(key)

    def set(self, key: str, entry: GeminiCacheEntry) -> None:
        with self._lock:
            self._entries[key] = entry

    def delete(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def items(self) -> Dict[str, GeminiCacheEntry]:
        with self._lock:
            return dict(self._entries)


class GeminiContextCacheManager:
    def __init__(
        self,
        backend: Optional[GeminiCacheBackend] = None,
        *,
        default_ttl_seconds: int = 300,
        max_entries: int = 1024,
    ) -> None:
        self._backend = backend or InMemoryGeminiCacheBackend()
        self._default_ttl_seconds = max(default_ttl_seconds, 1)
        self._max_entries = max(max_entries, 1)
        self._lock = threading.RLock()
        self._status_counters: Dict[str, int] = {
            "provided": 0,
            "hit": 0,
            "miss": 0,
            "expired": 0,
        }
        self._invalidated_count = 0
        self._evicted_count = 0

    def resolve(
        self,
        cache_key: str,
        *,
        requested_handle: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        now: Optional[float] = None,
    ) -> GeminiCacheResolution:
        now_ts = time.time() if now is None else now
        ttl = max(int(ttl_seconds or self._default_ttl_seconds), 1)
        with self._lock:
            if requested_handle:
                return self.create(
                    cache_key,
                    handle=requested_handle,
                    ttl_seconds=ttl,
                    now=now_ts,
                    status="provided",
                )

            reused = self.reuse(cache_key, now=now_ts)
            if reused:
                return reused

            status = "expired" if self.expire(cache_key, now=now_ts) else "miss"
            return self.create(
                cache_key,
                ttl_seconds=ttl,
                now=now_ts,
                status=status,
            )

    def create(
        self,
        cache_key: str,
        *,
        handle: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        now: Optional[float] = None,
        status: str = "miss",
    ) -> GeminiCacheResolution:
        now_ts = time.time() if now is None else now
        ttl = max(int(ttl_seconds or self._default_ttl_seconds), 1)
        cache_handle = handle or self._create_handle(cache_key, now_ts)
        expires_at = now_ts + ttl
        with self._lock:
            self._backend.set(
                cache_key, GeminiCacheEntry(handle=cache_handle, expires_at=expires_at)
            )
            self._enforce_capacity(now_ts)
            self._status_counters[status] = self._status_counters.get(status, 0) + 1
            return GeminiCacheResolution(
                handle=cache_handle,
                status=status,
                ttl_seconds=ttl,
                expires_at=expires_at,
            )

    def reuse(
        self, cache_key: str, *, now: Optional[float] = None
    ) -> Optional[GeminiCacheResolution]:
        now_ts = time.time() if now is None else now
        with self._lock:
            existing = self._backend.get(cache_key)
            if not existing or existing.expires_at <= now_ts:
                return None
            self._status_counters["hit"] += 1
            return GeminiCacheResolution(
                handle=existing.handle,
                status="hit",
                ttl_seconds=max(int(existing.expires_at - now_ts), 1),
                expires_at=existing.expires_at,
            )

    def expire(self, cache_key: str, *, now: Optional[float] = None) -> bool:
        now_ts = time.time() if now is None else now
        with self._lock:
            existing = self._backend.get(cache_key)
            if not existing or existing.expires_at > now_ts:
                return False
            self._backend.delete(cache_key)
            return True

    def invalidate(self, cache_key: str) -> bool:
        with self._lock:
            existing = self._backend.get(cache_key)
            if not existing:
                return False
            self._backend.delete(cache_key)
            self._invalidated_count += 1
            return True

    def telemetry(self) -> GeminiCacheTelemetry:
        with self._lock:
            return GeminiCacheTelemetry(
                max_entries=self._max_entries,
                active_entries=len(self._backend.items()),
                provided=self._status_counters["provided"],
                hit=self._status_counters["hit"],
                miss=self._status_counters["miss"],
                expired=self._status_counters["expired"],
                invalidated=self._invalidated_count,
                evicted=self._evicted_count,
            )

    @staticmethod
    def _create_handle(cache_key: str, now_ts: float) -> str:
        digest = sha1(f"{cache_key}:{now_ts:.6f}".encode("utf-8")).hexdigest()
        return f"cache-{digest[:24]}"

    def _enforce_capacity(self, now_ts: float) -> None:
        entries = self._backend.items()
        overflow = len(entries) - self._max_entries
        if overflow <= 0:
            return

        expired_keys = [
            key for key, entry in entries.items() if entry.expires_at <= now_ts
        ]
        for key in sorted(expired_keys, key=lambda item: entries[item].expires_at):
            if overflow <= 0:
                break
            self._backend.delete(key)
            self._evicted_count += 1
            overflow -= 1

        if overflow <= 0:
            return

        remaining = self._backend.items()
        eviction_order = sorted(remaining.items(), key=lambda item: item[1].expires_at)
        for key, _entry in eviction_order[:overflow]:
            self._backend.delete(key)
            self._evicted_count += 1


_DEFAULT_CACHE_MANAGER = GeminiContextCacheManager()


def get_default_cache_manager() -> GeminiContextCacheManager:
    return _DEFAULT_CACHE_MANAGER
