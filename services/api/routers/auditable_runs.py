from fastapi import APIRouter
from fastapi.responses import Response

from packages.core.application.models import (
    AuditableBatchRequest,
    AuditableBatchResponse,
    AuditableRepairRequest,
    AuditableRunCreateRequest,
    AuditableRunResponse,
)
from services.api.auditable_service import auditable_service
from services.api.routers.error_handler import with_router_error_handling

router = APIRouter()


@router.post("/sources/{source_id}/auditable-runs", response_model=AuditableRunResponse)
@with_router_error_handling(
    log_template="Error creating auditable run for source {source_id}",
    detail_template="Error creating auditable run",
)
async def create_auditable_run(source_id: str, request: AuditableRunCreateRequest):
    return await auditable_service.create_run(source_id, request)


@router.get(
    "/sources/{source_id}/auditable-runs", response_model=list[AuditableRunResponse]
)
@with_router_error_handling(
    log_template="Error listing auditable runs for source {source_id}",
    detail_template="Error listing auditable runs",
)
async def list_auditable_runs_by_source(source_id: str):
    return await auditable_service.list_runs_by_source(source_id)


@router.get("/auditable-runs/{run_id}", response_model=AuditableRunResponse)
@with_router_error_handling(
    log_template="Error getting auditable run {run_id}",
    detail_template="Error fetching auditable run",
)
async def get_auditable_run(run_id: str):
    return await auditable_service.get_run(run_id)


@router.get("/auditable-runs/{run_id}/markdown")
@with_router_error_handling(
    log_template="Error getting markdown for auditable run {run_id}",
    detail_template="Error fetching markdown",
)
async def get_auditable_run_markdown(run_id: str):
    markdown = await auditable_service.get_markdown(run_id)
    filename = f"auditable-{run_id.replace(':', '_')}.md"
    return Response(
        content=markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/auditable-runs/{run_id}/repair-claim", response_model=AuditableRunResponse
)
@with_router_error_handling(
    log_template="Error repairing claim for auditable run {run_id}",
    detail_template="Error repairing auditable claim",
)
async def repair_auditable_claim(run_id: str, request: AuditableRepairRequest):
    return await auditable_service.repair_run_target(
        run_id,
        request,
        target_type="claim",
    )


@router.post(
    "/auditable-runs/{run_id}/repair-section", response_model=AuditableRunResponse
)
@with_router_error_handling(
    log_template="Error repairing section for auditable run {run_id}",
    detail_template="Error repairing auditable section",
)
async def repair_auditable_section(run_id: str, request: AuditableRepairRequest):
    return await auditable_service.repair_run_target(
        run_id,
        request,
        target_type="section",
    )


@router.post("/auditable-runs/batch", response_model=AuditableBatchResponse)
@with_router_error_handling(
    log_template="Error creating batch auditable runs",
    detail_template="Error creating batch auditable runs",
)
async def create_auditable_runs_batch(request: AuditableBatchRequest):
    return await auditable_service.create_batch(request)
