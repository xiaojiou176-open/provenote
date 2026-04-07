from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field
from surreal_commands import registry

from packages.core.application.command_service import (
    CommandConflictError,
    CommandNotFoundError,
    CommandService,
)
from packages.core.observability.logger import logger

router = APIRouter()


class CommandExecutionRequest(BaseModel):
    command: str = Field(
        ..., description="Command function name (e.g., 'process_text')"
    )
    app: str = Field(..., description="Application name (e.g., 'open_notebook')")
    input: Dict[str, Any] = Field(..., description="Arguments to pass to the command")
    idempotency_key: Optional[str] = Field(
        None,
        description="Idempotency key to guarantee at-most-once submission semantics",
    )


class CommandJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class CommandJobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None


class CommandCancelResponse(BaseModel):
    job_id: str
    cancelled: bool
    status: str
    message: str


class DeadLetterRequeueResponse(BaseModel):
    entry_id: str
    command_id: str
    message: str


@router.post("/commands/jobs", response_model=CommandJobResponse)
async def execute_command(
    request: CommandExecutionRequest,
    idempotency_key_header: Optional[str] = Header(
        default=None,
        alias="Idempotency-Key",
    ),
):
    """
    Submit a command for background processing.
    Returns immediately with job ID for status tracking.

    Example request:
    {
        "command": "process_text",
        "app": "open_notebook",
        "input": {
            "text": "Hello world",
            "operation": "uppercase"
        }
    }
    """
    try:
        idempotency_key = request.idempotency_key or idempotency_key_header
        # Submit command using app name (not module name)
        job_id = await CommandService.submit_command_job(
            module_name=request.app,  # This should be "open_notebook"
            command_name=request.command,
            command_args=request.input,
            idempotency_key=idempotency_key,
        )

        return CommandJobResponse(
            job_id=job_id,
            status="submitted",
            message=f"Command '{request.command}' submitted successfully",
        )

    except CommandConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting command: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit command")


@router.get("/commands/jobs/{job_id}", response_model=CommandJobStatusResponse)
async def get_command_job_status(job_id: str):
    """Get the status of a specific command job"""
    try:
        status_data = await CommandService.get_command_status(job_id)
        return CommandJobStatusResponse(**status_data)

    except Exception as e:
        logger.error(f"Error fetching job status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch job status")


@router.get("/commands/jobs", response_model=List[Dict[str, Any]])
async def list_command_jobs(
    app_filter: Optional[str] = Query(None, description="Filter by app name"),
    command_filter: Optional[str] = Query(None, description="Filter by command name"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of jobs to return"),
    offset: int = Query(0, description="Pagination offset"),
):
    """List command jobs with optional filtering"""
    try:
        jobs = await CommandService.list_command_jobs(
            module_filter=app_filter,
            command_filter=command_filter,
            status_filter=status_filter,
            limit=limit,
            offset=offset,
        )
        return jobs

    except Exception as e:
        logger.error(f"Error listing command jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list command jobs")


@router.delete("/commands/jobs/{job_id}", response_model=CommandCancelResponse)
async def cancel_command_job(job_id: str):
    """Cancel a running command job"""
    try:
        return await CommandService.cancel_command_job(job_id)
    except CommandNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CommandConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling command job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel command job")


@router.get("/commands/dead-letter", response_model=List[Dict[str, Any]])
async def list_dead_letter_jobs(
    limit: int = Query(50, description="Maximum number of dead-letter entries"),
    offset: int = Query(0, description="Pagination offset"),
):
    """List dead-letter command entries."""
    try:
        return await CommandService.list_dead_letter_entries(limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Error listing dead-letter entries: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to list dead-letter entries"
        )


@router.post(
    "/commands/dead-letter/{entry_id}/requeue",
    response_model=DeadLetterRequeueResponse,
)
async def requeue_dead_letter_job(entry_id: str):
    """Requeue a dead-letter command entry."""
    try:
        return await CommandService.requeue_dead_letter(entry_id)
    except CommandNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CommandConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error requeuing dead-letter entry {entry_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to requeue dead-letter entry"
        )


@router.get("/commands/registry/debug")
async def debug_registry():
    """Debug endpoint to see what commands are registered"""
    try:
        # Get all registered commands
        all_items = registry.get_all_commands()

        # Create JSON-serializable data
        command_items = []
        for item in all_items:
            try:
                command_items.append(
                    {
                        "app_id": item.app_id,
                        "name": item.name,
                        "full_id": f"{item.app_id}.{item.name}",
                    }
                )
            except Exception as item_error:
                logger.error(f"Error processing item: {item_error}")

        # Get the basic command structure
        try:
            commands_dict: dict[str, list[str]] = {}
            for item in all_items:
                if item.app_id not in commands_dict:
                    commands_dict[item.app_id] = []
                commands_dict[item.app_id].append(item.name)
        except Exception:
            commands_dict = {}

        return {
            "total_commands": len(all_items),
            "commands_by_app": commands_dict,
            "command_items": command_items,
        }

    except Exception as e:
        logger.error("Error debugging registry error_type={}", type(e).__name__)
        return {
            "error": "Failed to inspect command registry",
            "total_commands": 0,
            "commands_by_app": {},
            "command_items": [],
        }
