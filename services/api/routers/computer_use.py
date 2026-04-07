from fastapi import APIRouter

from packages.core.application.computer_use_service import computer_use_service
from packages.core.application.models import (
    ComputerUseConfirmRequest,
    ComputerUseConfirmResponse,
    ComputerUseSessionCreateRequest,
    ComputerUseSessionResponse,
)
from services.api.routers.error_handler import with_router_error_handling

router = APIRouter()


@router.post("/computer-use/sessions", response_model=ComputerUseSessionResponse)
@with_router_error_handling(
    log_template="Error creating computer-use session",
    detail_template="Error creating computer-use session",
)
async def create_computer_use_session(request: ComputerUseSessionCreateRequest):
    return await computer_use_service.create_session(request)


@router.get(
    "/computer-use/sessions/{session_id}", response_model=ComputerUseSessionResponse
)
@with_router_error_handling(
    log_template="Error getting computer-use session {session_id}",
    detail_template="Error fetching computer-use session",
)
async def get_computer_use_session(session_id: str):
    return await computer_use_service.get_session(session_id)


@router.post(
    "/computer-use/sessions/{session_id}/confirm",
    response_model=ComputerUseConfirmResponse,
)
@with_router_error_handling(
    log_template="Error confirming computer-use session {session_id}",
    detail_template="Error confirming computer-use session",
)
async def confirm_computer_use_action(
    session_id: str, request: ComputerUseConfirmRequest
):
    return await computer_use_service.confirm_action(session_id, request)
