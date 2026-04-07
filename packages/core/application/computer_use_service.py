from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from packages.core.application.models import (
    ComputerUseConfirmRequest,
    ComputerUseConfirmResponse,
    ComputerUseSessionCreateRequest,
    ComputerUseSessionResponse,
)
from packages.core.exceptions import InvalidInputError, NotFoundError


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class _ComputerUseSessionState:
    session_id: str
    objective: str
    require_confirmation: bool
    dry_run: bool
    status: str
    created: str
    updated: str
    confirmation_required: bool = False
    pending_action_id: Optional[str] = None
    confirmation_token: Optional[str] = None
    approved_idempotency_key: Optional[str] = None


class ComputerUseService:
    """
    In-memory control-plane for computer-use sessions.

    This intentionally starts as an in-memory service for quick integration and tests.
    A persistence-backed implementation can replace this without changing router contracts.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, _ComputerUseSessionState] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _to_response(state: _ComputerUseSessionState) -> ComputerUseSessionResponse:
        return ComputerUseSessionResponse(
            session_id=state.session_id,
            status=state.status,
            objective=state.objective,
            require_confirmation=state.require_confirmation,
            dry_run=state.dry_run,
            created=state.created,
            updated=state.updated,
            confirmation_required=state.confirmation_required,
            pending_action_id=state.pending_action_id,
        )

    async def create_session(
        self, request: ComputerUseSessionCreateRequest
    ) -> ComputerUseSessionResponse:
        session_id = f"computer_use:{uuid4()}"
        now = _utc_now_iso()
        state = _ComputerUseSessionState(
            session_id=session_id,
            objective=request.objective,
            require_confirmation=request.require_confirmation,
            dry_run=request.dry_run,
            status="awaiting_confirmation" if request.require_confirmation else "ready",
            created=now,
            updated=now,
        )
        if request.require_confirmation:
            state.confirmation_required = True
            state.pending_action_id = f"{session_id}:action:1"
            state.confirmation_token = uuid4().hex

        async with self._lock:
            self._sessions[session_id] = state
        return self._to_response(state)

    async def get_session(self, session_id: str) -> ComputerUseSessionResponse:
        async with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                raise NotFoundError("Computer-use session not found")
            return self._to_response(state)

    async def confirm_action(
        self, session_id: str, request: ComputerUseConfirmRequest
    ) -> ComputerUseConfirmResponse:
        async with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                raise NotFoundError("Computer-use session not found")
            if not state.confirmation_required:
                raise InvalidInputError("No pending confirmation for this session")
            if state.confirmation_token != request.confirmation_token:
                raise InvalidInputError("Invalid confirmation token")
            if (
                state.approved_idempotency_key is not None
                and state.approved_idempotency_key == request.action_idempotency_key
            ):
                return ComputerUseConfirmResponse(
                    session_id=session_id,
                    status=state.status,
                    approved=True,
                    message="Already confirmed for this idempotency key",
                )

            state.approved_idempotency_key = request.action_idempotency_key
            state.confirmation_required = False
            state.confirmation_token = None
            state.pending_action_id = None
            state.status = "ready"
            state.updated = _utc_now_iso()

            return ComputerUseConfirmResponse(
                session_id=session_id,
                status=state.status,
                approved=True,
                message="Confirmation accepted",
            )


computer_use_service = ComputerUseService()
