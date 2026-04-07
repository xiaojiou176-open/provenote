from unittest.mock import AsyncMock, patch

import pytest

from packages.core.application.models import AuditableMetrics, AuditableRunResponse
from packages.core.exceptions import NotFoundError


@pytest.fixture
def client(api_client):
    return api_client


def _build_run_response() -> AuditableRunResponse:
    return AuditableRunResponse(
        id="auditable_run:1",
        source_id="source:1",
        status="completed",
        model_id="gemini-3.1-pro-preview",
        language="zh-CN",
        near_dedup_threshold=0.97,
        metrics=AuditableMetrics(
            coverage_rate=1.0,
            missing_count=0,
            duplicate_count=1,
            uncited_claims_count=0,
            dedup_group_count=1,
            unknown_pid_count=0,
            unclassified_count=0,
        ),
        coverage_json={"coverage_rate": 1.0, "missing_pids": []},
        dedup_json={"group_count": 1, "exact_groups": [], "near_groups": []},
        result_markdown="# Auditable Long Text Run\n",
        source_paragraphs=[
            {
                "pid": "P000001",
                "order": 1,
                "raw_text": "A",
                "canonical_text": "A",
                "canonical_hash": "hash-a",
            }
        ],
        sections=[{"title": "摘要", "bullets": ["A"], "source_pids": ["P000001"]}],
        claims=[{"text": "Claim A", "source_pids": ["P000001"]}],
        dedup_entries=[
            {
                "pid": "P000001",
                "text": "A",
                "status": "core",
                "duplicate_of": None,
                "similarity": None,
            }
        ],
        created="2026-01-01T00:00:00+00:00",
        updated="2026-01-01T00:00:00+00:00",
    )


@patch(
    "services.api.routers.auditable_runs.auditable_service.create_run",
    new_callable=AsyncMock,
)
def test_create_auditable_run_happy_path(mock_create_run, client):
    mock_create_run.return_value = _build_run_response()

    response = client.post(
        "/api/sources/source:1/auditable-runs",
        json={
            "model_id": "gemini-3.1-pro-preview",
            "language": "zh-CN",
            "near_dedup_threshold": 0.97,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "auditable_run:1"
    assert data["model_id"] == "gemini-3.1-pro-preview"
    assert data["metrics"]["coverage_rate"] == 1.0
    mock_create_run.assert_awaited_once()
    source_id, request = mock_create_run.call_args.args
    assert source_id == "source:1"
    assert request.model_id == "gemini-3.1-pro-preview"
    assert request.language == "zh-CN"
    assert request.near_dedup_threshold == pytest.approx(0.97)


@patch(
    "services.api.routers.auditable_runs.auditable_service.get_run",
    new_callable=AsyncMock,
)
def test_get_auditable_run_happy_path(mock_get_run, client):
    mock_get_run.return_value = _build_run_response()

    response = client.get("/api/auditable-runs/auditable_run:1")

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "source:1"
    assert data["status"] == "completed"
    mock_get_run.assert_awaited_once_with("auditable_run:1")


@patch(
    "services.api.routers.auditable_runs.auditable_service.list_runs_by_source",
    new_callable=AsyncMock,
)
def test_list_auditable_runs_by_source_happy_path(mock_list_runs_by_source, client):
    mock_list_runs_by_source.return_value = [_build_run_response()]

    response = client.get("/api/sources/source:1/auditable-runs")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "auditable_run:1"
    mock_list_runs_by_source.assert_awaited_once_with("source:1")


@patch(
    "services.api.routers.auditable_runs.auditable_service.get_markdown",
    new_callable=AsyncMock,
)
def test_get_auditable_markdown_happy_path(mock_get_markdown, client):
    mock_get_markdown.return_value = "# Auditable Long Text Run\n\n## Core\n"

    response = client.get("/api/auditable-runs/auditable_run:1/markdown")

    assert response.status_code == 200
    assert response.text.startswith("# Auditable Long Text Run")
    assert response.headers["content-type"].startswith("text/markdown")
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="auditable-auditable_run_1.md"'
    )
    mock_get_markdown.assert_awaited_once_with("auditable_run:1")


def test_create_auditable_run_invalid_input_threshold(client):
    response = client.post(
        "/api/sources/source:1/auditable-runs",
        json={"near_dedup_threshold": 1.5},
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(
        err["loc"][-1] == "near_dedup_threshold" and err["type"] == "less_than_equal"
        for err in errors
    )


@patch(
    "services.api.routers.auditable_runs.auditable_service.get_run",
    new_callable=AsyncMock,
)
def test_get_auditable_run_not_found(mock_get_run, client):
    mock_get_run.side_effect = NotFoundError("Auditable run not found")

    response = client.get("/api/auditable-runs/auditable_run:missing")

    assert response.status_code == 404
    assert "Auditable run not found" in response.json()["detail"]


@patch(
    "services.api.routers.auditable_runs.auditable_service.create_batch",
    new_callable=AsyncMock,
)
def test_create_auditable_runs_batch_happy_path(mock_create_batch, client):
    mock_create_batch.return_value = {"run_ids": ["auditable_run:1", "auditable_run:2"]}

    response = client.post(
        "/api/auditable-runs/batch",
        json={
            "source_ids": [" source:1 ", "source:2 "],
            "model_id": "gemini-3.1-pro-preview",
            "language": "zh-CN",
            "near_dedup_threshold": 0.96,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"run_ids": ["auditable_run:1", "auditable_run:2"]}
    mock_create_batch.assert_awaited_once()
    request = mock_create_batch.call_args.args[0]
    assert request.source_ids == ["source:1", "source:2"]
    assert request.model_id == "gemini-3.1-pro-preview"
    assert request.language == "zh-CN"
    assert request.near_dedup_threshold == pytest.approx(0.96)


def test_create_auditable_runs_batch_rejects_blank_source_ids(client):
    response = client.post(
        "/api/auditable-runs/batch",
        json={"source_ids": [" ", "\t"], "near_dedup_threshold": 0.97},
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(
        err["loc"][-1] == "source_ids" and "cannot be empty" in err["msg"]
        for err in errors
    )


@patch(
    "services.api.routers.auditable_runs.auditable_service.get_markdown",
    new_callable=AsyncMock,
)
def test_get_auditable_markdown_returns_500_for_unexpected_error(
    mock_get_markdown, client
):
    mock_get_markdown.side_effect = RuntimeError("backend boom")

    response = client.get("/api/auditable-runs/auditable_run:1/markdown")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    mock_get_markdown.assert_awaited_once_with("auditable_run:1")


@patch(
    "services.api.routers.auditable_runs.auditable_service.repair_run_target",
    new_callable=AsyncMock,
)
def test_repair_auditable_claim_and_section_routes(mock_repair_run_target, client):
    mock_repair_run_target.return_value = _build_run_response()

    claim_response = client.post(
        "/api/auditable-runs/auditable_run:1/repair-claim",
        json={"target_index": 0},
    )
    section_response = client.post(
        "/api/auditable-runs/auditable_run:1/repair-section",
        json={"target_index": 1},
    )

    assert claim_response.status_code == 200
    assert section_response.status_code == 200
    assert mock_repair_run_target.await_count == 2
    first_call = mock_repair_run_target.await_args_list[0]
    second_call = mock_repair_run_target.await_args_list[1]
    assert first_call.args[0] == "auditable_run:1"
    assert first_call.kwargs["target_type"] == "claim"
    assert second_call.kwargs["target_type"] == "section"
