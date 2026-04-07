from typing import Any

from fastapi import APIRouter

from packages.core.application.models import (
    DraftResponse,
    ErrorResponse,
    ResearchThreadCreateRequest,
    ResearchThreadEntryRequest,
    ResearchThreadResponse,
)
from services.api.research_thread_service import research_thread_service
from services.api.routers.error_handler import with_router_error_handling

router = APIRouter()

_THREAD_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Invalid research thread request"},
    404: {
        "model": ErrorResponse,
        "description": "Research thread or notebook not found",
    },
    500: {"model": ErrorResponse, "description": "Unexpected research thread error"},
}


@router.post(
    "/notebooks/{notebook_id}/research-threads",
    response_model=ResearchThreadResponse,
    responses=_THREAD_ERROR_RESPONSES,
)
@with_router_error_handling(
    log_template="Error creating research thread for notebook {notebook_id}",
    detail_template="Error creating research thread",
)
async def create_research_thread(
    notebook_id: str, request: ResearchThreadCreateRequest
):
    return await research_thread_service.create_thread(notebook_id, request)


@router.get(
    "/notebooks/{notebook_id}/research-threads",
    response_model=list[ResearchThreadResponse],
    responses=_THREAD_ERROR_RESPONSES,
)
@with_router_error_handling(
    log_template="Error listing research threads for notebook {notebook_id}",
    detail_template="Error listing research threads",
)
async def list_research_threads(notebook_id: str):
    return await research_thread_service.list_threads_by_notebook(notebook_id)


@router.get(
    "/research-threads/{thread_id}",
    response_model=ResearchThreadResponse,
    responses=_THREAD_ERROR_RESPONSES,
)
@with_router_error_handling(
    log_template="Error getting research thread {thread_id}",
    detail_template="Error fetching research thread",
)
async def get_research_thread(thread_id: str):
    return await research_thread_service.get_thread(thread_id)


@router.post(
    "/research-threads/{thread_id}/entries",
    response_model=ResearchThreadResponse,
    responses=_THREAD_ERROR_RESPONSES,
)
@with_router_error_handling(
    log_template="Error appending entry to research thread {thread_id}",
    detail_template="Error appending research thread entry",
)
async def append_research_thread_entry(
    thread_id: str, request: ResearchThreadEntryRequest
):
    return await research_thread_service.append_entry(thread_id, request)


@router.post(
    "/research-threads/{thread_id}/drafts",
    response_model=DraftResponse,
    responses=_THREAD_ERROR_RESPONSES,
)
@with_router_error_handling(
    log_template="Error creating draft from research thread {thread_id}",
    detail_template="Error creating draft from research thread",
)
async def create_draft_from_thread(thread_id: str):
    return await research_thread_service.create_draft_from_thread(thread_id)
