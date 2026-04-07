from __future__ import annotations

import pytest

from packages.core.application.computer_use_service import ComputerUseService
from packages.core.application.models import (
    ComputerUseConfirmRequest,
    ComputerUseSessionCreateRequest,
)
from packages.core.exceptions import InvalidInputError, NotFoundError


@pytest.mark.asyncio
async def test_create_session_without_confirmation_is_ready() -> None:
    service = ComputerUseService()
    request = ComputerUseSessionCreateRequest(
        objective="open docs",
        require_confirmation=False,
        dry_run=True,
    )

    response = await service.create_session(request)

    assert response.status == "ready"
    assert response.confirmation_required is False
    assert response.pending_action_id is None


@pytest.mark.asyncio
async def test_create_and_confirm_session_supports_idempotent_reconfirm() -> None:
    service = ComputerUseService()
    request = ComputerUseSessionCreateRequest(
        objective="open docs",
        require_confirmation=True,
        dry_run=True,
    )
    created = await service.create_session(request)
    stored = await service.get_session(created.session_id)

    assert stored.confirmation_required is True
    assert stored.pending_action_id.startswith(f"{created.session_id}:action:")

    token = service._sessions[created.session_id].confirmation_token
    confirm_request = ComputerUseConfirmRequest(
        confirmation_token=token,
        action_idempotency_key="idem-1",
    )
    response = await service.confirm_action(created.session_id, confirm_request)

    assert response.message == "Confirmation accepted"
    with pytest.raises(InvalidInputError, match="No pending confirmation"):
        await service.confirm_action(created.session_id, confirm_request)


@pytest.mark.asyncio
async def test_confirm_action_raises_for_missing_session_and_bad_token() -> None:
    service = ComputerUseService()

    with pytest.raises(NotFoundError, match="Computer-use session not found"):
        await service.get_session("computer_use:missing")

    created = await service.create_session(
        ComputerUseSessionCreateRequest(
            objective="open docs",
            require_confirmation=True,
            dry_run=True,
        )
    )
    with pytest.raises(InvalidInputError, match="Invalid confirmation token"):
        await service.confirm_action(
            created.session_id,
            ComputerUseConfirmRequest(
                confirmation_token="wrong",
                action_idempotency_key="idem-2",
            ),
        )
