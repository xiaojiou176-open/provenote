from __future__ import annotations

import asyncio
import json
import os
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

import pytest

from packages.core.ai.google_genai_adapter import (
    generate_google_text,
    list_google_models,
)
from packages.core.ai.google_genai_adapter import (
    test_google_connection as verify_google_connection,
)

_LIVE_KEY_NAMES = ("GEMINI_API_KEY",)
_LIVE_SWITCH_ENV = "RUN_LIVE_TESTS"
_LIVE_SWITCH_VALUE = "1"
LIVE_CLEANUP_POLICY = "live-cleanup: read-only-no-op"
LIVE_IDEMPOTENCY_POLICY = "live-idempotency: read-only-safe-retry"
LIVE_TEARDOWN_EVIDENCE_PREFIX = "[live-teardown-evidence]"
LIVE_TEARDOWN_EVIDENCE_FILE_ENV = "LIVE_TEARDOWN_EVIDENCE_FILE"
_PLACEHOLDER_KEY_MARKERS = (
    "your_key",
    "your-api-key",
    "dummy",
    "fake",
    "changeme",
    "replace",
    "sample",
)


def _live_switch_enabled() -> bool:
    return os.getenv(_LIVE_SWITCH_ENV, "").strip() == _LIVE_SWITCH_VALUE


def _read_key_from_env() -> str | None:
    for key_name in _LIVE_KEY_NAMES:
        value = os.getenv(key_name)
        if value:
            return value
    return None


def _resolve_live_google_key() -> str | None:
    return _read_key_from_env()


def _looks_like_placeholder_key(raw_key: str) -> bool:
    normalized = raw_key.strip().lower()
    if len(normalized) < 20:
        return True
    return any(marker in normalized for marker in _PLACEHOLDER_KEY_MARKERS)


def _heartbeat_seconds() -> int:
    raw = os.getenv("LIVE_HEARTBEAT_SECONDS", "15").strip()
    try:
        parsed = int(raw)
    except ValueError:
        return 15
    return max(5, parsed)


async def _heartbeat_loop(label: str, interval_seconds: int) -> None:
    started_at = asyncio.get_running_loop().time()
    tick = 0
    while True:
        tick += 1
        elapsed = int(asyncio.get_running_loop().time() - started_at)
        print(
            f"[live-heartbeat] {label} still running "
            f"(tick={tick}, elapsed={elapsed}s, interval={interval_seconds}s)"
        )
        await asyncio.sleep(interval_seconds)


async def _run_with_heartbeat(label: str, awaitable):
    heartbeat_task = asyncio.create_task(
        _heartbeat_loop(label=label, interval_seconds=_heartbeat_seconds())
    )
    try:
        return await awaitable
    finally:
        heartbeat_task.cancel()
        with suppress(asyncio.CancelledError):
            await heartbeat_task


def _append_live_teardown_evidence(
    *, test_name: str, status: str, details: dict[str, object]
) -> None:
    record = {
        "event": "live_teardown",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "test_name": test_name,
        "status": status,
        "cleanup_policy": LIVE_CLEANUP_POLICY,
        "idempotency_policy": LIVE_IDEMPOTENCY_POLICY,
        "details": details,
    }
    serialized = json.dumps(record, ensure_ascii=True, separators=(",", ":"))
    print(f"{LIVE_TEARDOWN_EVIDENCE_PREFIX} {serialized}")

    evidence_path = os.getenv(LIVE_TEARDOWN_EVIDENCE_FILE_ENV, "").strip()
    if not evidence_path:
        return
    try:
        target = Path(evidence_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(serialized + "\n")
    except OSError as exc:
        print(f"[live-teardown-evidence-error] failed to persist evidence: {exc}")


async def _resolve_live_model_name(api_key: str) -> str:
    configured = os.getenv("LIVE_GEMINI_SMOKE_MODEL")
    if configured and configured.strip():
        return configured.strip()

    models = await list_google_models(api_key=api_key)
    language_models = [
        str(item.get("name", "")).strip()
        for item in models
        if str(item.get("model_type", "")).strip() == "language"
    ]
    for candidate in language_models:
        if "gemini" in candidate.lower():
            return candidate

    return "gemini-3-flash-preview"


def test_live_switch_enabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RUN_LIVE_TESTS", "1")
    assert _live_switch_enabled() is True


def test_live_switch_disabled_when_env_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RUN_LIVE_TESTS", raising=False)
    assert _live_switch_enabled() is False


def test_resolve_live_google_key_priority_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")

    assert _resolve_live_google_key() == "env-key"


def test_resolve_live_google_key_none_when_env_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert _resolve_live_google_key() is None


def test_placeholder_key_detection() -> None:
    key_prefix = "AIza"
    assert _looks_like_placeholder_key("your_key")
    assert _looks_like_placeholder_key("dummy-key-for-tests")
    assert _looks_like_placeholder_key("short")
    assert _looks_like_placeholder_key(key_prefix + "SyDUMMY_test_key_value_for_ci")
    assert not _looks_like_placeholder_key(
        key_prefix + "SyA12345678901234567890123456789012345"
    )


def test_heartbeat_seconds_defaults_invalid_and_minimum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LIVE_HEARTBEAT_SECONDS", raising=False)
    assert _heartbeat_seconds() == 15

    monkeypatch.setenv("LIVE_HEARTBEAT_SECONDS", "not-a-number")
    assert _heartbeat_seconds() == 15

    monkeypatch.setenv("LIVE_HEARTBEAT_SECONDS", "2")
    assert _heartbeat_seconds() == 5

    monkeypatch.setenv("LIVE_HEARTBEAT_SECONDS", "30")
    assert _heartbeat_seconds() == 30


@pytest.mark.asyncio
async def test_run_with_heartbeat_returns_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LIVE_HEARTBEAT_SECONDS", "5")

    async def _do_work() -> str:
        await asyncio.sleep(0)
        return "ok"

    result = await _run_with_heartbeat("heartbeat-test", _do_work())
    assert result == "ok"


def test_append_live_teardown_evidence_prints_and_persists_jsonl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    evidence_file = tmp_path / "teardown-evidence.jsonl"
    monkeypatch.setenv(LIVE_TEARDOWN_EVIDENCE_FILE_ENV, str(evidence_file))

    _append_live_teardown_evidence(
        test_name="test_name",
        status="passed",
        details={"teardown_action": "no-op-read-only"},
    )

    captured = capsys.readouterr()
    assert LIVE_TEARDOWN_EVIDENCE_PREFIX in captured.out

    lines = evidence_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["event"] == "live_teardown"
    assert payload["test_name"] == "test_name"
    assert payload["status"] == "passed"


def test_append_live_teardown_evidence_handles_persist_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    directory_path = tmp_path / "folder-as-file"
    directory_path.mkdir()
    monkeypatch.setenv(LIVE_TEARDOWN_EVIDENCE_FILE_ENV, str(directory_path))

    _append_live_teardown_evidence(
        test_name="test_name",
        status="failed",
        details={"teardown_action": "no-op-read-only"},
    )

    captured = capsys.readouterr()
    assert "[live-teardown-evidence-error]" in captured.out


@pytest.mark.asyncio
async def test_resolve_live_model_name_prefers_configured_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LIVE_GEMINI_SMOKE_MODEL", "gemini-custom-live")
    assert await _resolve_live_model_name("ignored") == "gemini-custom-live"


@pytest.mark.asyncio
async def test_resolve_live_model_name_auto_discovers_language_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LIVE_GEMINI_SMOKE_MODEL", raising=False)

    async def _fake_list_google_models(*, api_key: str):
        _ = api_key
        return [
            {"name": "text-embedding-004", "model_type": "embedding"},
            {"name": "gemini-3.1-pro-preview", "model_type": "language"},
        ]

    monkeypatch.setitem(
        _resolve_live_model_name.__globals__,
        "list_google_models",
        _fake_list_google_models,
    )

    assert await _resolve_live_model_name("test-key") == "gemini-3.1-pro-preview"


@pytest.mark.asyncio
@pytest.mark.live
async def test_google_live_connection_and_generation() -> None:
    # Read-only live smoke; if a future change adds writes, switch to
    # "live-cleanup: required" and add explicit teardown.
    if not _live_switch_enabled():
        pytest.skip("Set RUN_LIVE_TESTS=1 to enable live tests.")

    api_key = _resolve_live_google_key()
    validation_errors: list[str] = []
    if not api_key:
        validation_errors.append(
            "RUN_LIVE_TESTS=1 but no real key found. Set GEMINI_API_KEY."
        )
    if api_key and _looks_like_placeholder_key(api_key):
        validation_errors.append(
            "RUN_LIVE_TESTS=1 requires a real Gemini key; placeholder/test key is blocked."
        )
    assert validation_errors == [], "; ".join(validation_errors)

    model_name = await _resolve_live_model_name(api_key)
    test_status = "passed"
    try:
        success, message = await _run_with_heartbeat(
            "verify-google-connection",
            verify_google_connection(api_key=api_key, model_name=model_name),
        )
        assert success is True, f"Live connection failed for {model_name}: {message}"

        output = await _run_with_heartbeat(
            "generate-google-text",
            generate_google_text(
                api_key=api_key,
                model_name=model_name,
                prompt="Return exactly one short line proving the model responded.",
            ),
        )
        assert len(output.strip()) > 0
    except Exception:
        test_status = "failed"
        raise
    finally:
        _append_live_teardown_evidence(
            test_name="test_google_live_connection_and_generation",
            status=test_status,
            details={"teardown_action": "no-op-read-only"},
        )


@pytest.mark.asyncio
@pytest.mark.live
async def test_google_live_model_discovery_lists_language_models() -> None:
    if not _live_switch_enabled():
        pytest.skip("Set RUN_LIVE_TESTS=1 to enable live tests.")

    api_key = _resolve_live_google_key()
    validation_errors: list[str] = []
    if not api_key:
        validation_errors.append(
            "RUN_LIVE_TESTS=1 but no real key found. Set GEMINI_API_KEY."
        )
    if api_key and _looks_like_placeholder_key(api_key):
        validation_errors.append(
            "RUN_LIVE_TESTS=1 requires a real Gemini key; placeholder/test key is blocked."
        )
    assert validation_errors == [], "; ".join(validation_errors)

    test_status = "passed"
    try:
        models = await _run_with_heartbeat(
            "list-google-models",
            list_google_models(api_key=api_key),
        )
        assert len(models) > 0

        model_names = [str(item.get("name", "")).lower() for item in models]
        assert any("gemini" in name for name in model_names), (
            "Expected at least one Gemini model."
        )
    except Exception:
        test_status = "failed"
        raise
    finally:
        _append_live_teardown_evidence(
            test_name="test_google_live_model_discovery_lists_language_models",
            status=test_status,
            details={"teardown_action": "no-op-read-only"},
        )
