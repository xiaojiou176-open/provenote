from unittest.mock import AsyncMock, patch

import pytest

from packages.core.application.models import (
    ComputerUseConfirmResponse,
    ComputerUseSessionResponse,
)
from packages.core.exceptions import InvalidInputError, NotFoundError


@pytest.fixture
def client(api_client):
    return api_client


def _build_session_response() -> ComputerUseSessionResponse:
    return ComputerUseSessionResponse(
        session_id="computer_use:test",
        status="awaiting_confirmation",
        objective="open github and star repository",
        require_confirmation=True,
        dry_run=True,
        created="2026-02-22T00:00:00+00:00",
        updated="2026-02-22T00:00:00+00:00",
        confirmation_required=True,
        pending_action_id="computer_use:test:action:1",
    )


def _build_confirm_response() -> ComputerUseConfirmResponse:
    return ComputerUseConfirmResponse(
        session_id="computer_use:test",
        status="ready",
        approved=True,
        message="Confirmation accepted",
    )


@patch(
    "services.api.routers.computer_use.computer_use_service.create_session",
    new_callable=AsyncMock,
)
def test_create_computer_use_session(mock_create, client):
    mock_create.return_value = _build_session_response()
    response = client.post(
        "/api/computer-use/sessions",
        json={
            "objective": "open github and star repository",
            "require_confirmation": True,
            "dry_run": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "computer_use:test"
    assert data["confirmation_required"] is True


@patch(
    "services.api.routers.computer_use.computer_use_service.get_session",
    new_callable=AsyncMock,
)
def test_get_computer_use_session(mock_get, client):
    mock_get.return_value = _build_session_response()
    response = client.get("/api/computer-use/sessions/computer_use:test")

    assert response.status_code == 200
    assert response.json()["status"] == "awaiting_confirmation"


@patch(
    "services.api.routers.computer_use.computer_use_service.confirm_action",
    new_callable=AsyncMock,
)
def test_confirm_computer_use_action(mock_confirm, client):
    mock_confirm.return_value = _build_confirm_response()
    response = client.post(
        "/api/computer-use/sessions/computer_use:test/confirm",
        json={
            "confirmation_token": "token-1",
            "action_idempotency_key": "idem-1",
        },
    )

    assert response.status_code == 200
    assert response.json()["approved"] is True


@patch(
    "services.api.routers.computer_use.computer_use_service.get_session",
    new_callable=AsyncMock,
)
def test_get_computer_use_session_not_found(mock_get, client):
    mock_get.side_effect = NotFoundError("Computer-use session not found")
    response = client.get("/api/computer-use/sessions/missing")
    assert response.status_code == 404
    assert response.json()["detail"] == "Computer-use session not found"


@patch(
    "services.api.routers.computer_use.computer_use_service.confirm_action",
    new_callable=AsyncMock,
)
def test_confirm_computer_use_action_invalid(mock_confirm, client):
    mock_confirm.side_effect = InvalidInputError("Invalid confirmation token")
    response = client.post(
        "/api/computer-use/sessions/computer_use:test/confirm",
        json={
            "confirmation_token": "wrong",
            "action_idempotency_key": "idem-1",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid confirmation token"
