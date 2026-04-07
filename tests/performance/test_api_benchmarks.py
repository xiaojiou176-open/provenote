"""API endpoint performance benchmarks.

These tests establish actionable baselines for critical API endpoints.
Targets (median latency):
- Chat execution: < 3000ms
- Source upload: < 5000ms
- Search query: < 1000ms
"""

import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

_PRECHECK_SKIP_STATUS_CODES = {401, 403, 404}
_PRECHECK_CONTRACT_FAILURE_STATUS_CODES = {405, 422}
_PRECHECK_INFRA_FAILURE_STATUS_CODES = {500, 502, 503, 504}


def _allow_env_skip_enabled() -> bool:
    """Require explicit benchmark skip policy to avoid implicit fail-open behavior."""
    raw_value = os.getenv("PERF_BENCHMARK_ALLOW_ENV_SKIP", "0")
    violations = []
    if raw_value not in {"0", "1"}:
        violations.append(
            f"PERF_BENCHMARK_ALLOW_ENV_SKIP must be explicitly '0' or '1'; got {raw_value!r}"
        )
    assert not violations, violations
    return raw_value == "1"


def _assert_preflight_ready(
    response,
    endpoint: str,
    *,
    skip_status_codes: set[int] | None = None,
    contract_failure_status_codes: set[int] | None = None,
):
    """Guard benchmark execution from false-green infrastructure failures."""
    status_code = response.status_code
    effective_skip_status_codes = (
        skip_status_codes
        if skip_status_codes is not None
        else _PRECHECK_SKIP_STATUS_CODES
    )
    effective_contract_failure_status_codes = (
        contract_failure_status_codes
        if contract_failure_status_codes is not None
        else _PRECHECK_CONTRACT_FAILURE_STATUS_CODES
    )
    to_skip = None
    to_fail = None
    if status_code in effective_skip_status_codes:
        if _allow_env_skip_enabled():
            to_skip = (
                f"Benchmark preflight skipped for {endpoint}: "
                f"dependency/environment not ready (HTTP {status_code})"
            )
        else:
            to_fail = (
                f"Benchmark preflight got HTTP {status_code} for {endpoint}; "
                "set PERF_BENCHMARK_ALLOW_ENV_SKIP=1 only when running without required dependencies"
            )
    elif status_code in effective_contract_failure_status_codes:
        to_fail = (
            f"Benchmark preflight failed for {endpoint}: "
            f"request contract error (HTTP {status_code})"
        )
    elif status_code in _PRECHECK_INFRA_FAILURE_STATUS_CODES:
        if _allow_env_skip_enabled():
            to_skip = (
                f"Benchmark preflight skipped for {endpoint}: "
                f"infrastructure dependency not ready (HTTP {status_code})"
            )
        else:
            to_fail = (
                f"Benchmark preflight got infrastructure failure HTTP {status_code} for {endpoint}; "
                "set PERF_BENCHMARK_ALLOW_ENV_SKIP=1 only when running without required infrastructure"
            )
    if to_skip:
        pytest.skip(to_skip)
    assert not to_fail, to_fail
    assert 200 <= status_code < 300, (
        f"Benchmark preflight failed for {endpoint}: unexpected HTTP {status_code}"
    )


def _best_effort_delete(api_client: TestClient, path: str) -> None:
    """Delete benchmark-created resources without masking primary test failures."""
    try:
        api_client.delete(path)
    except Exception:
        # Cleanup should not hide benchmark assertion failures.
        return


def _assert_benchmark_median_under_target(
    benchmark, *, target_seconds: float, label: str
) -> None:
    """Use median latency for stability across noisy CI environments."""
    stats = benchmark.stats.stats
    median_seconds = float(stats.median)
    mean_seconds = float(stats.mean)
    assert median_seconds < target_seconds, (
        f"{label} latency median {median_seconds:.3f}s exceeds {target_seconds:.1f}s target "
        f"(mean={mean_seconds:.3f}s)"
    )


def _collect_upload_artifacts_with_prefix(filename: str) -> set[Path]:
    """Track upload artifacts so failed preflight/setup paths can still be cleaned."""
    uploads_dir = Path(".runtime-cache/state/local/data/uploads")
    if not uploads_dir.exists():
        return set()
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    pattern = f"{stem}*{suffix}"
    return {candidate.resolve() for candidate in uploads_dir.glob(pattern)}


def _cleanup_upload_artifacts_with_prefix(
    filename: str, baseline_paths: set[Path]
) -> None:
    """Best-effort cleanup for upload files created before source IDs are available."""
    uploads_dir = Path(".runtime-cache/state/local/data/uploads")
    if not uploads_dir.exists():
        return
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    pattern = f"{stem}*{suffix}"
    for candidate in uploads_dir.glob(pattern):
        resolved = candidate.resolve()
        if resolved in baseline_paths:
            continue
        try:
            candidate.unlink()
        except OSError:
            continue


def test_preflight_infra_status_fails_without_opt_in(monkeypatch):
    monkeypatch.delenv("PERF_BENCHMARK_ALLOW_ENV_SKIP", raising=False)

    class _Response:
        status_code = 500

    with pytest.raises(AssertionError):
        _assert_preflight_ready(_Response(), "POST /api/test")


def test_preflight_infra_status_skips_with_opt_in(monkeypatch):
    monkeypatch.setenv("PERF_BENCHMARK_ALLOW_ENV_SKIP", "1")

    class _Response:
        status_code = 500

    with pytest.raises(pytest.skip.Exception):
        _assert_preflight_ready(_Response(), "POST /api/test")


def _create_chat_session_for_benchmark(api_client: TestClient) -> tuple[str, str]:
    notebook_id: str | None = None
    session_id: str | None = None
    try:
        notebook_response = api_client.post(
            "/api/notebooks",
            json={
                "name": "Performance Benchmark Notebook",
                "description": "Transient benchmark notebook",
            },
        )
        _assert_preflight_ready(notebook_response, "POST /api/notebooks")
        notebook_id = notebook_response.json().get("id")
        setup_fail = None
        if not notebook_id:
            setup_fail = "Benchmark setup failed: notebook id missing in response"
        else:
            session_response = api_client.post(
                "/api/chat/sessions",
                json={
                    "notebook_id": notebook_id,
                    "title": "Performance Benchmark Session",
                },
            )
            _assert_preflight_ready(
                session_response,
                "POST /api/chat/sessions",
                contract_failure_status_codes={400, 404, 405, 422},
            )
            session_id = session_response.json().get("id")
            if not session_id:
                setup_fail = (
                    "Benchmark setup failed: chat session id missing in response"
                )
        assert not setup_fail, setup_fail
        return str(session_id), str(notebook_id)
    except Exception:
        if session_id:
            _best_effort_delete(api_client, f"/api/chat/sessions/{session_id}")
        if notebook_id:
            _best_effort_delete(api_client, f"/api/notebooks/{notebook_id}")
        raise


def test_chat_execute_latency(benchmark, api_client: TestClient):
    """Benchmark chat execution endpoint.

    Target: Median latency < 3000ms for typical chat query.
    """

    session_id, notebook_id = _create_chat_session_for_benchmark(api_client)
    payload = {
        "session_id": session_id,
        "message": "What is the main topic of the documents?",
        "context": {"sources": [], "notes": []},
    }
    try:
        preflight_response = api_client.post("/api/chat/execute", json=payload)
        _assert_preflight_ready(
            preflight_response,
            "POST /api/chat/execute",
            skip_status_codes={401, 403},
            contract_failure_status_codes={404, 405, 422},
        )

        def execute_chat():
            response = api_client.post("/api/chat/execute", json=payload)
            assert 200 <= response.status_code < 300
            return response

        benchmark(execute_chat)
        _assert_benchmark_median_under_target(
            benchmark,
            target_seconds=3.0,
            label="Chat",
        )
    finally:
        _best_effort_delete(api_client, f"/api/chat/sessions/{session_id}")
        _best_effort_delete(api_client, f"/api/notebooks/{notebook_id}")


def test_source_upload_latency(benchmark, api_client: TestClient):
    """Benchmark source upload endpoint.

    Target: Median latency < 5000ms for small file upload.
    """

    upload_filename = f"benchmark-upload-{uuid4().hex}.txt"
    upload_bytes = b"Sample content for testing"
    existing_upload_artifacts = _collect_upload_artifacts_with_prefix(upload_filename)

    preflight_response = api_client.post(
        "/api/sources",
        data={"type": "upload", "async_processing": "true"},
        files={"file": (upload_filename, upload_bytes, "text/plain")},
    )
    _assert_preflight_ready(preflight_response, "POST /api/sources")
    preflight_source_id = preflight_response.json().get("id")

    created_source_ids: set[str] = set()

    def upload_source():
        # Simulate a small file upload
        response = api_client.post(
            "/api/sources",
            data={"type": "upload", "async_processing": "true"},
            files={"file": (upload_filename, upload_bytes, "text/plain")},
        )
        source_id = None
        try:
            source_id = response.json().get("id")
        except ValueError:
            source_id = None
        if source_id:
            created_source_ids.add(str(source_id))
        assert 200 <= response.status_code < 300
        return response

    try:
        benchmark(upload_source)
        _assert_benchmark_median_under_target(
            benchmark,
            target_seconds=5.0,
            label="Upload",
        )
    finally:
        if preflight_source_id:
            _best_effort_delete(api_client, f"/api/sources/{preflight_source_id}")
        for source_id in created_source_ids:
            _best_effort_delete(api_client, f"/api/sources/{source_id}")
        _cleanup_upload_artifacts_with_prefix(
            upload_filename,
            baseline_paths=existing_upload_artifacts,
        )


def test_search_query_latency(benchmark, api_client: TestClient):
    """Benchmark search endpoint.

    Target: Median latency < 1000ms for typical search query.
    """

    payload = {
        "query": "machine learning",
        "limit": 10,
    }
    preflight_response = api_client.post("/api/search", json=payload)
    _assert_preflight_ready(preflight_response, "POST /api/search")

    def search_query():
        response = api_client.post("/api/search", json=payload)
        assert 200 <= response.status_code < 300
        return response

    benchmark(search_query)
    _assert_benchmark_median_under_target(
        benchmark,
        target_seconds=1.0,
        label="Search",
    )


def test_performance_suite_smoke():
    """Ensure benchmark suite module is wired into repository structure."""
    from pathlib import Path

    assert (Path(__file__).parents[2] / "services" / "api").exists()
