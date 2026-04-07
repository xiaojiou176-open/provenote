from typing import Any, Optional

from packages.core.application.models import (
    AssetModel,
    SourceListResponse,
    SourceResponse,
)
from packages.core.domain.notebook import Source


def _asset_from_mapping(asset: Optional[dict[str, Any]]) -> Optional[AssetModel]:
    if not asset:
        return None
    return AssetModel(
        file_path=asset.get("file_path"),
        url=asset.get("url"),
    )


def _asset_from_source(source: Source) -> Optional[AssetModel]:
    if not source.asset:
        return None
    return AssetModel(
        file_path=source.asset.file_path,
        url=source.asset.url,
    )


def build_source_list_response(row: dict[str, Any]) -> SourceListResponse:
    command = row.get("command")
    command_id = None
    status = None
    processing_info = None

    if command and isinstance(command, dict):
        command_id = str(command.get("id")) if command.get("id") else None
        status = command.get("status")
        result_data = command.get("result")
        execution_metadata = (
            result_data.get("execution_metadata", {})
            if isinstance(result_data, dict)
            else {}
        )
        processing_info = {
            "started_at": execution_metadata.get("started_at"),
            "completed_at": execution_metadata.get("completed_at"),
            "error": command.get("error_message"),
        }
    elif command:
        command_id = str(command)
        status = "unknown"

    return SourceListResponse(
        id=row["id"],
        title=row.get("title"),
        topics=row.get("topics") or [],
        asset=_asset_from_mapping(row.get("asset")),
        embedded=row.get("embedded", False),
        embedded_chunks=0,
        insights_count=row.get("insights_count", 0),
        created=str(row["created"]),
        updated=str(row["updated"]),
        command_id=command_id,
        status=status,
        processing_info=processing_info,
    )


def build_source_response(
    source: Source,
    embedded_chunks: int,
    *,
    command_id: Optional[str] = None,
    status: Optional[str] = None,
    processing_info: Optional[dict[str, Any]] = None,
    notebooks: Optional[list[str]] = None,
    file_available: Optional[bool] = None,
) -> SourceResponse:
    return SourceResponse(
        id=source.id or "",
        title=source.title,
        topics=source.topics or [],
        asset=_asset_from_source(source),
        full_text=source.full_text,
        embedded=embedded_chunks > 0,
        embedded_chunks=embedded_chunks,
        created=str(source.created),
        updated=str(source.updated),
        command_id=command_id,
        status=status,
        processing_info=processing_info,
        notebooks=notebooks,
        file_available=file_available,
    )
