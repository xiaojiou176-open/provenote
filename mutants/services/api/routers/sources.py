from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response

from packages.core.application.command_service import CommandService
from packages.core.application.models import (
    CreateSourceInsightRequest,
    InsightCreationResponse,
    SourceCreate,
    SourceInsightResponse,
    SourceListResponse,
    SourceResponse,
    SourceStatusResponse,
    SourceUpdate,
)
from packages.core.database.repository import ensure_record_id, repo_query
from packages.core.domain.notebook import Notebook, Source
from packages.core.domain.transformation import Transformation
from packages.core.observability.logger import logger
from services.api.routers.sources_helpers import (
    is_source_file_available,
    parse_source_form_data,
    resolve_source_file,
)
from services.api.routers.sources_serializers import (
    build_source_list_response,
    build_source_response,
)
from services.api.routers.sources_service import (
    create_source_service,
    retry_source_processing_service,
    update_source_service,
)

router = APIRouter()


@router.get("/sources", response_model=List[SourceListResponse])
async def get_sources(
    notebook_id: Optional[str] = Query(None, description="Filter by notebook ID"),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Number of sources to return (1-100)",
    ),
    offset: int = Query(0, ge=0, description="Number of sources to skip"),
    sort_by: str = Query(
        "updated", description="Field to sort by (created or updated)"
    ),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
):
    """Get sources with pagination and sorting support."""
    try:
        if sort_by not in ["created", "updated"]:
            raise HTTPException(
                status_code=400,
                detail="sort_by must be 'created' or 'updated'",
            )
        if sort_order.lower() not in ["asc", "desc"]:
            raise HTTPException(
                status_code=400,
                detail="sort_order must be 'asc' or 'desc'",
            )

        order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"

        if notebook_id:
            notebook = await Notebook.get(notebook_id)
            if not notebook:
                raise HTTPException(status_code=404, detail="Notebook not found")

            query = f"""
                SELECT id, asset, created, title, updated, topics, command,
                (SELECT VALUE count() FROM source_insight WHERE source = $parent.id GROUP ALL)[0].count OR 0 AS insights_count,
                (SELECT VALUE id FROM source_embedding WHERE source = $parent.id LIMIT 1) != [] AS embedded
                FROM (select value in from reference where out=$notebook_id)
                {order_clause}
                LIMIT $limit START $offset
                FETCH command
            """
            result = await repo_query(
                query,
                {
                    "notebook_id": ensure_record_id(notebook_id),
                    "limit": limit,
                    "offset": offset,
                },
            )
        else:
            query = f"""
                SELECT id, asset, created, title, updated, topics, command,
                (SELECT VALUE count() FROM source_insight WHERE source = $parent.id GROUP ALL)[0].count OR 0 AS insights_count,
                (SELECT VALUE id FROM source_embedding WHERE source = $parent.id LIMIT 1) != [] AS embedded
                FROM source
                {order_clause}
                LIMIT $limit START $offset
                FETCH command
            """
            result = await repo_query(query, {"limit": limit, "offset": offset})

        return [build_source_list_response(row) for row in result]
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching sources: {str(exc)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching sources: {str(exc)}"
        )


@router.post("/sources", response_model=SourceResponse)
async def create_source(
    form_data: tuple[SourceCreate, Optional[UploadFile]] = Depends(
        parse_source_form_data
    ),
):
    """Create a new source with support for both JSON and multipart form data."""
    source_data, upload_file = form_data
    return await create_source_service(source_data, upload_file)


@router.post("/sources/json", response_model=SourceResponse)
async def create_source_json(source_data: SourceCreate):
    """Create a new source using JSON payload (legacy endpoint for backward compatibility)."""
    return await create_source_service(source_data, None)


@router.get("/sources/{source_id}", response_model=SourceResponse)
async def get_source(source_id: str):
    """Get a specific source by ID."""
    try:
        source = await Source.get(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        status = None
        processing_info = None
        if source.command:
            try:
                status = await source.get_status()
                processing_info = await source.get_processing_progress()
            except Exception as exc:
                logger.warning(f"Failed to get status for source {source_id}: {exc}")
                status = "unknown"

        embedded_chunks = await source.get_embedded_chunks()

        notebooks_query = await repo_query(
            "SELECT VALUE out FROM reference WHERE in = $source_id",
            {"source_id": ensure_record_id(source.id or source_id)},
        )
        notebook_ids = (
            [str(nb_id) for nb_id in notebooks_query] if notebooks_query else []
        )

        return build_source_response(
            source,
            embedded_chunks,
            command_id=str(source.command) if source.command else None,
            status=status,
            processing_info=processing_info,
            notebooks=notebook_ids,
            file_available=is_source_file_available(source),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching source {source_id}: {str(exc)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching source: {str(exc)}"
        )


@router.head("/sources/{source_id}/download")
async def check_source_file(source_id: str):
    """Check if a source has a downloadable file."""
    try:
        await resolve_source_file(source_id)
        return Response(status_code=200)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error checking file for source {source_id}: {str(exc)}")
        raise HTTPException(status_code=500, detail="Failed to verify file")


@router.get("/sources/{source_id}/download")
async def download_source_file(source_id: str):
    """Download the original file associated with an uploaded source."""
    try:
        resolved_path, filename = await resolve_source_file(source_id)
        return FileResponse(
            path=resolved_path,
            filename=filename,
            media_type="application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error downloading file for source {source_id}: {str(exc)}")
        raise HTTPException(status_code=500, detail="Failed to download source file")


@router.get("/sources/{source_id}/status", response_model=SourceStatusResponse)
async def get_source_status(source_id: str):
    """Get processing status for a source."""
    try:
        source = await Source.get(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        if not source.command:
            return SourceStatusResponse(
                status=None,
                message="Legacy source (completed before async processing)",
                processing_info=None,
                command_id=None,
            )

        try:
            status = await source.get_status()
            processing_info = await source.get_processing_progress()

            if status == "completed":
                message = "Source processing completed successfully"
            elif status == "failed":
                message = "Source processing failed"
            elif status == "running":
                message = "Source processing in progress"
            elif status == "queued":
                message = "Source processing queued"
            elif status == "unknown":
                message = "Source processing status unknown"
            else:
                message = f"Source processing status: {status}"

            return SourceStatusResponse(
                status=status,
                message=message,
                processing_info=processing_info,
                command_id=str(source.command) if source.command else None,
            )
        except Exception as exc:
            logger.warning(f"Failed to get status for source {source_id}: {exc}")
            return SourceStatusResponse(
                status="unknown",
                message="Failed to retrieve processing status",
                processing_info=None,
                command_id=str(source.command) if source.command else None,
            )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching status for source {source_id}: {str(exc)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching source status: {str(exc)}",
        )


@router.put("/sources/{source_id}", response_model=SourceResponse)
async def update_source(source_id: str, source_update: SourceUpdate):
    """Update a source."""
    try:
        return await update_source_service(source_id, source_update)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error updating source {source_id}: {str(exc)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating source: {str(exc)}"
        )


@router.post("/sources/{source_id}/retry", response_model=SourceResponse)
async def retry_source_processing(source_id: str):
    """Retry processing for a failed or stuck source."""
    return await retry_source_processing_service(source_id)


@router.delete("/sources/{source_id}")
async def delete_source(source_id: str):
    """Delete a source."""
    try:
        source = await Source.get(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        await source.delete()
        return {"message": "Source deleted successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error deleting source {source_id}: {str(exc)}")
        raise HTTPException(
            status_code=500, detail=f"Error deleting source: {str(exc)}"
        )


@router.get("/sources/{source_id}/insights", response_model=List[SourceInsightResponse])
async def get_source_insights(source_id: str):
    """Get all insights for a specific source."""
    try:
        source = await Source.get(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        insights = await source.get_insights()
        return [
            SourceInsightResponse(
                id=insight.id or "",
                source_id=source_id,
                insight_type=insight.insight_type,
                content=insight.content,
                created=str(insight.created),
                updated=str(insight.updated),
            )
            for insight in insights
        ]
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching insights for source {source_id}: {str(exc)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching insights: {str(exc)}"
        )


@router.post(
    "/sources/{source_id}/insights",
    response_model=InsightCreationResponse,
    status_code=202,
)
async def create_source_insight(source_id: str, request: CreateSourceInsightRequest):
    """
    Start insight generation for a source by running a transformation.

    This endpoint returns immediately with a 202 Accepted status.
    The transformation runs asynchronously in the background via the job queue.
    Poll GET /sources/{source_id}/insights to see when the insight is ready.
    """
    try:
        source = await Source.get(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        transformation = await Transformation.get(request.transformation_id)
        if not transformation:
            raise HTTPException(status_code=404, detail="Transformation not found")

        command_id = await CommandService.submit_command_job(
            module_name="open_notebook",
            command_name="run_transformation",
            command_args={
                "source_id": source_id,
                "transformation_id": request.transformation_id,
            },
        )
        logger.info(
            f"Submitted run_transformation command {command_id} for source {source_id}"
        )

        return InsightCreationResponse(
            status="pending",
            message="Insight generation started",
            source_id=source_id,
            transformation_id=request.transformation_id,
            command_id=str(command_id),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error starting insight generation for source {source_id}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting insight generation: {str(exc)}",
        )
