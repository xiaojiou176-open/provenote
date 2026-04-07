from typing import Any

from fastapi import APIRouter
from fastapi.responses import Response

from packages.core.application.models import (
    DraftCreateRequest,
    DraftRerunRequest,
    DraftResponse,
    ErrorResponse,
)
from services.api.draft_service import draft_service
from services.api.routers.error_handler import with_router_error_handling

router = APIRouter()


class MarkdownDownloadResponse(Response):
    media_type = "text/markdown; charset=utf-8"


class DraftBundleResponse(Response):
    media_type = "application/zip"


_DRAFT_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Invalid draft request"},
    404: {"model": ErrorResponse, "description": "Draft or notebook not found"},
    500: {"model": ErrorResponse, "description": "Unexpected draft error"},
}


@router.post(
    "/notebooks/{notebook_id}/drafts",
    response_model=DraftResponse,
    responses=_DRAFT_ERROR_RESPONSES,
)
@with_router_error_handling(
    log_template="Error creating draft for notebook {notebook_id}",
    detail_template="Error creating draft",
)
async def create_draft(notebook_id: str, request: DraftCreateRequest):
    return await draft_service.create_draft(notebook_id, request)


@router.get(
    "/notebooks/{notebook_id}/drafts",
    response_model=list[DraftResponse],
    responses=_DRAFT_ERROR_RESPONSES,
)
@with_router_error_handling(
    log_template="Error listing drafts for notebook {notebook_id}",
    detail_template="Error listing drafts",
)
async def list_notebook_drafts(notebook_id: str):
    return await draft_service.list_drafts_by_notebook(notebook_id)


@router.get(
    "/drafts/{draft_id}",
    response_model=DraftResponse,
    responses=_DRAFT_ERROR_RESPONSES,
)
@with_router_error_handling(
    log_template="Error getting draft {draft_id}",
    detail_template="Error fetching draft",
)
async def get_draft(draft_id: str):
    return await draft_service.get_draft(draft_id)


@router.post(
    "/drafts/{draft_id}/rerun",
    response_model=DraftResponse,
    responses=_DRAFT_ERROR_RESPONSES,
)
@with_router_error_handling(
    log_template="Error rerunning draft {draft_id}",
    detail_template="Error rerunning draft",
)
async def rerun_draft(draft_id: str, request: DraftRerunRequest):
    return await draft_service.rerun_draft(draft_id, request)


@router.post(
    "/drafts/{draft_id}/verify",
    response_model=DraftResponse,
    responses=_DRAFT_ERROR_RESPONSES,
)
@with_router_error_handling(
    log_template="Error verifying draft {draft_id}",
    detail_template="Error verifying draft",
)
async def verify_draft(draft_id: str):
    return await draft_service.verify_draft(draft_id)


@router.get(
    "/drafts/{draft_id}/markdown",
    response_class=MarkdownDownloadResponse,
    responses={
        200: {
            "content": {"text/markdown": {}},
            "description": "Draft markdown download",
        },
        **_DRAFT_ERROR_RESPONSES,
    },
)
@with_router_error_handling(
    log_template="Error getting markdown for draft {draft_id}",
    detail_template="Error fetching draft markdown",
)
async def get_draft_markdown(draft_id: str):
    markdown = await draft_service.get_markdown(draft_id)
    filename = f"draft-{draft_id.replace(':', '_')}.md"
    return MarkdownDownloadResponse(
        content=markdown,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/drafts/{draft_id}/bundle",
    response_class=DraftBundleResponse,
    responses={
        200: {
            "content": {"application/zip": {}},
            "description": "Draft export bundle",
        },
        **_DRAFT_ERROR_RESPONSES,
    },
)
@with_router_error_handling(
    log_template="Error getting export bundle for draft {draft_id}",
    detail_template="Error fetching draft export bundle",
)
async def get_draft_bundle(draft_id: str):
    filename, bundle_bytes = await draft_service.get_export_bundle(draft_id)
    return DraftBundleResponse(
        content=bundle_bytes,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
