import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from packages.core.application.models import (
    UITestReportResponse,
    UITestRunRequest,
    UITestRunResponse,
)
from packages.core.exceptions import NotFoundError, RateLimitError


@pytest.fixture
def client(api_client):
    return api_client


def _build_run_response() -> UITestRunResponse:
    return UITestRunResponse(
        id="ui_test_run:1",
        status="queued",
        dry_run=True,
        command=["npm", "run", "test:e2e", "--", "--project=chromium"],
        return_code=None,
        created="2026-02-22T00:00:00+00:00",
        updated="2026-02-22T00:00:00+00:00",
    )


def _build_report_response() -> UITestReportResponse:
    return UITestReportResponse(
        id="ui_test_run:1",
        status="completed",
        dry_run=True,
        command=["npm", "run", "test:e2e", "--", "--project=chromium"],
        return_code=0,
        stdout="dry_run: playwright execution skipped",
        stderr="",
        started_at="2026-02-22T00:00:01+00:00",
        finished_at="2026-02-22T00:00:01+00:00",
        duration_seconds=0.01,
        created="2026-02-22T00:00:00+00:00",
        updated="2026-02-22T00:00:01+00:00",
    )


@patch("services.api.routers.ui_tests.ui_test_service.run", new_callable=AsyncMock)
def test_run_ui_tests_happy_path(mock_run, client):
    mock_run.return_value = _build_run_response()

    response = client.post(
        "/api/ui-tests/run",
        json={"dry_run": True, "project": "chromium", "timeout_seconds": 60},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ui_test_run:1"
    assert data["status"] == "queued"
    assert data["dry_run"] is True


@patch("services.api.routers.ui_tests.ui_test_service.run", new_callable=AsyncMock)
def test_run_ui_tests_normalizes_valid_spec_path(mock_run, client):
    mock_run.return_value = _build_run_response()

    response = client.post(
        "/api/ui-tests/run",
        json={
            "dry_run": True,
            "project": "chromium",
            "spec": " ./apps/web/e2e/smoke.spec.ts ",
            "timeout_seconds": 60,
        },
    )

    assert response.status_code == 200
    request_payload = mock_run.await_args.args[0]
    assert request_payload.spec == "e2e/smoke.spec.ts"


def test_run_ui_tests_rejects_invalid_project(client):
    response = client.post(
        "/api/ui-tests/run",
        json={"dry_run": True, "project": "safari", "timeout_seconds": 60},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(item["loc"][-1] == "project" for item in detail)


@pytest.mark.parametrize(
    "unsafe_spec",
    [
        "/tmp/e2e/smoke.spec.ts",
        "../e2e/smoke.spec.ts",
        "e2e/../../etc/passwd",
        "-g smoke",
    ],
)
def test_run_ui_tests_rejects_unsafe_spec_path(client, unsafe_spec):
    response = client.post(
        "/api/ui-tests/run",
        json={
            "dry_run": True,
            "project": "chromium",
            "spec": unsafe_spec,
            "timeout_seconds": 60,
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(item["loc"][-1] == "spec" for item in detail)


@patch("services.api.routers.ui_tests.ui_test_service.get", new_callable=AsyncMock)
def test_get_ui_test_run_happy_path(mock_get, client):
    mock_get.return_value = _build_run_response()

    response = client.get("/api/ui-tests/ui_test_run:1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ui_test_run:1"
    assert data["command"][0] == "npm"


@patch("services.api.routers.ui_tests.ui_test_service.report", new_callable=AsyncMock)
def test_get_ui_test_report_happy_path(mock_report, client):
    mock_report.return_value = _build_report_response()

    response = client.get("/api/ui-tests/ui_test_run:1/report")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "dry_run" in data["stdout"]


@patch("services.api.routers.ui_tests.ui_test_service.get", new_callable=AsyncMock)
def test_get_ui_test_run_not_found(mock_get, client):
    mock_get.side_effect = NotFoundError("UI test run not found")

    response = client.get("/api/ui-tests/ui_test_run:missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "UI test run not found"


@patch("services.api.routers.ui_tests.ui_test_service.run", new_callable=AsyncMock)
def test_run_ui_tests_rate_limited_maps_to_429(mock_run, client):
    mock_run.side_effect = RateLimitError("UI test service is shutting down")

    response = client.post(
        "/api/ui-tests/run",
        json={"dry_run": False, "project": "chromium", "timeout_seconds": 60},
    )

    assert response.status_code == 429
    assert response.json()["detail"] == "UI test service is shutting down"


@patch("services.api.routers.ui_tests.ui_test_service.run", new_callable=AsyncMock)
def test_run_ui_tests_internal_error_hides_exception_detail(mock_run, client):
    mock_run.side_effect = RuntimeError("sensitive internals should not leak")

    response = client.post(
        "/api/ui-tests/run",
        json={"dry_run": False, "project": "chromium", "timeout_seconds": 60},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    assert "sensitive" not in response.text


def test_ui_test_service_build_command_revalidates_spec():
    from packages.core.application.ui_test_service import UITestService

    unsafe_request = UITestRunRequest.model_construct(
        dry_run=False,
        project="chromium",
        spec="--grep @smoke",
        timeout_seconds=60,
    )

    with pytest.raises(ValueError, match="spec"):
        UITestService._build_command(unsafe_request)


def test_ui_test_service_build_command_normalizes_frontend_prefixed_spec():
    from packages.core.application.ui_test_service import UITestService

    request = UITestRunRequest.model_construct(
        dry_run=False,
        project="chromium",
        spec="apps/web/e2e/smoke.spec.ts",
        timeout_seconds=60,
    )

    command = UITestService._build_command(request)
    assert command[-1] == "e2e/smoke.spec.ts"


@pytest.mark.asyncio
async def test_ui_test_service_masks_internal_error_details_in_report():
    from packages.core.application.ui_test_service import (
        GENERIC_EXECUTION_ERROR_MESSAGE,
        UITestService,
    )

    service = UITestService()
    request = UITestRunRequest(
        dry_run=False,
        project="chromium",
        spec="e2e/smoke.spec.ts",
        timeout_seconds=30,
    )

    try:
        with patch(
            "packages.core.application.ui_test_service.asyncio.create_subprocess_exec",
            new=AsyncMock(
                side_effect=OSError("permission denied: /private/secret/path")
            ),
        ):
            response = await service.run(request)
            task = service._runs[response.id]._task
            assert task is not None and (
                asyncio.iscoroutine(task) or hasattr(task, "cancel")
            )
            await task

            report = await service.report(response.id)
            assert report.status == "failed"
            assert report.return_code == -1
            assert report.stderr == GENERIC_EXECUTION_ERROR_MESSAGE
            assert "secret" not in report.stderr
    finally:
        await service.shutdown()
