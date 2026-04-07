from packages.core.ai.gemini_cache import GeminiContextCacheManager


def test_cache_lifecycle_miss_hit_expire() -> None:
    manager = GeminiContextCacheManager(default_ttl_seconds=10)
    key = "transformation:model-a:payload-1"

    first = manager.resolve(key, ttl_seconds=5, now=100.0)
    assert first.status == "miss"
    assert first.handle.startswith("cache-")
    assert first.ttl_seconds == 5

    second = manager.resolve(key, ttl_seconds=5, now=101.0)
    assert second.status == "hit"
    assert second.handle == first.handle
    assert second.expires_at == first.expires_at

    third = manager.resolve(key, ttl_seconds=5, now=106.0)
    assert third.status == "expired"
    assert third.handle != first.handle
    assert third.ttl_seconds == 5

    telemetry = manager.telemetry()
    assert telemetry.miss == 1
    assert telemetry.hit == 1
    assert telemetry.expired == 1


def test_cache_lifecycle_respects_provided_handle() -> None:
    manager = GeminiContextCacheManager(default_ttl_seconds=60)

    resolved = manager.resolve(
        "ask:model-a:payload",
        requested_handle="provided-handle-1",
        ttl_seconds=30,
        now=200.0,
    )
    assert resolved.status == "provided"
    assert resolved.handle == "provided-handle-1"

    hit = manager.resolve("ask:model-a:payload", now=201.0)
    assert hit.status == "hit"
    assert hit.handle == "provided-handle-1"

    telemetry = manager.telemetry()
    assert telemetry.provided == 1
    assert telemetry.hit == 1


def test_lifecycle_methods_create_reuse_expire_invalidate() -> None:
    manager = GeminiContextCacheManager(default_ttl_seconds=10, max_entries=10)
    key = "cache:key:1"

    created = manager.create(key, ttl_seconds=5, now=10.0)
    assert created.status == "miss"

    reused = manager.reuse(key, now=11.0)
    assert getattr(reused, "status", None) == "hit"
    assert getattr(reused, "handle", None) == created.handle

    assert manager.expire(key, now=16.0) is True
    assert manager.reuse(key, now=16.0) is None

    manager.create("cache:key:2", ttl_seconds=5, now=20.0)
    assert manager.invalidate("cache:key:2") is True
    assert manager.invalidate("cache:key:2") is False

    telemetry = manager.telemetry()
    assert telemetry.miss == 2
    assert telemetry.hit == 1
    assert telemetry.invalidated == 1


def test_capacity_control_evicts_expired_first_then_oldest() -> None:
    manager = GeminiContextCacheManager(default_ttl_seconds=20, max_entries=2)

    manager.create("k1", handle="h1", ttl_seconds=1, now=100.0)
    manager.create("k2", handle="h2", ttl_seconds=20, now=100.0)
    manager.create("k3", handle="h3", ttl_seconds=20, now=102.0)

    assert manager.reuse("k1", now=102.0) is None
    assert getattr(manager.reuse("k2", now=102.0), "handle", None) == "h2"
    assert getattr(manager.reuse("k3", now=102.0), "handle", None) == "h3"

    manager.create("k4", handle="h4", ttl_seconds=20, now=102.0)
    assert manager.reuse("k2", now=102.0) is None
    assert getattr(manager.reuse("k3", now=102.0), "handle", None) == "h3"
    assert getattr(manager.reuse("k4", now=102.0), "handle", None) == "h4"

    telemetry = manager.telemetry()
    assert telemetry.max_entries == 2
    assert telemetry.active_entries == 2
    assert telemetry.evicted == 2
