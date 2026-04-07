from fastapi import APIRouter, HTTPException

from packages.core.application.models import (
    NoteResponse,
    SaveAsNoteRequest,
    SourceInsightResponse,
)
from packages.core.domain.notebook import SourceInsight
from services.api.routers.error_handler import with_router_error_handling

router = APIRouter()


@router.get("/insights/{insight_id}", response_model=SourceInsightResponse)
@with_router_error_handling(
    log_template="Error fetching insight {insight_id}",
    detail_template="Error fetching insight",
    include_exception_detail=False,
)
async def get_insight(insight_id: str):
    """Get a specific insight by ID."""
    insight = await SourceInsight.get(insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Get source ID from the insight relationship
    source = await insight.get_source()

    return SourceInsightResponse(
        id=insight.id or "",
        source_id=source.id or "",
        insight_type=insight.insight_type,
        content=insight.content,
        created=str(insight.created),
        updated=str(insight.updated),
    )


@router.delete("/insights/{insight_id}")
@with_router_error_handling(
    log_template="Error deleting insight {insight_id}",
    detail_template="Error deleting insight",
    include_exception_detail=False,
)
async def delete_insight(insight_id: str):
    """Delete a specific insight."""
    insight = await SourceInsight.get(insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    await insight.delete()

    return {"message": "Insight deleted successfully"}


@router.post("/insights/{insight_id}/save-as-note", response_model=NoteResponse)
@with_router_error_handling(
    log_template="Error saving insight {insight_id} as note",
    detail_template="Error saving insight as note",
    include_exception_detail=False,
)
async def save_insight_as_note(insight_id: str, request: SaveAsNoteRequest):
    """Convert an insight to a note."""
    insight = await SourceInsight.get(insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Use the existing save_as_note method from the domain model
    note = await insight.save_as_note(request.notebook_id)

    return NoteResponse(
        id=note.id or "",
        title=note.title,
        content=note.content,
        note_type=note.note_type,
        created=str(note.created),
        updated=str(note.updated),
    )
