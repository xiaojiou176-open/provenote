from unittest.mock import AsyncMock, patch

import pytest

from packages.core.application.models import AuditableBatchResponse


@pytest.fixture
def client(api_client):
    return api_client


@patch(
    "services.api.routers.auditable_runs.auditable_service.create_batch",
    new_callable=AsyncMock,
)
def test_batch_happy_path(mock_create_batch, client):
    mock_create_batch.return_value = AuditableBatchResponse(
        run_ids=["auditable_run:1", "auditable_run:2"]
    )

    response = client.post(
        "/api/auditable-runs/batch",
        json={"source_ids": ["source:1", "source:2"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["run_ids"] == ["auditable_run:1", "auditable_run:2"]


def test_batch_invalid_input_empty_source_ids(client):
    response = client.post(
        "/api/auditable-runs/batch",
        json={"source_ids": []},
    )

    assert response.status_code == 422
