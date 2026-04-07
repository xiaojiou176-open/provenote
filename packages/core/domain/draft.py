from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional, Union

from pydantic import ConfigDict, Field, field_validator
from surrealdb import RecordID

from packages.core.database.repository import ensure_record_id, repo_query
from packages.core.domain.base import ObjectModel
from packages.core.exceptions import DatabaseOperationError, InvalidInputError
from packages.core.observability.logger import logger


def _stringify_record_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, RecordID):
                result.append(str(item))
            elif isinstance(item, dict) and item.get("id"):
                result.append(str(item["id"]))
            elif item:
                result.append(str(item))
        return result
    if isinstance(value, RecordID):
        return [str(value)]
    return [str(value)]


class Draft(ObjectModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    table_name: ClassVar[str] = "draft"
    nullable_fields: ClassVar[set[str]] = {
        "parent_draft_id",
        "verified_brief_snapshot",
    }

    notebook: Union[str, RecordID]
    title: str
    status: str
    model_id: str
    language: str
    near_dedup_threshold: float
    source_ids: List[Union[str, RecordID]] = Field(default_factory=list)
    note_ids: List[Union[str, RecordID]] = Field(default_factory=list)
    thread_ids: List[Union[str, RecordID]] = Field(default_factory=list)
    version: int = 1
    parent_draft_id: Optional[Union[str, RecordID]] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    coverage_json: Dict[str, Any] = Field(default_factory=dict)
    dedup_json: Dict[str, Any] = Field(default_factory=dict)
    result_markdown: str = ""
    source_paragraphs: List[Dict[str, Any]] = Field(default_factory=list)
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    dedup_entries: List[Dict[str, Any]] = Field(default_factory=list)
    verified_brief_snapshot: Optional[Dict[str, Any]] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise InvalidInputError("Draft title cannot be empty")
        return normalized

    @field_validator("notebook", "parent_draft_id", mode="before")
    @classmethod
    def normalize_record_field(
        cls, value: Optional[Union[str, RecordID]]
    ) -> Optional[Union[str, RecordID]]:
        if value is None or value == "":
            return None
        return ensure_record_id(value)

    @field_validator("source_ids", "note_ids", "thread_ids", mode="before")
    @classmethod
    def normalize_record_lists(cls, value: Any) -> list[Union[str, RecordID]]:
        normalized = _stringify_record_list(value)
        return [ensure_record_id(item) for item in normalized]

    def _prepare_save_data(self) -> Dict[str, Any]:
        data = super()._prepare_save_data()
        data["notebook"] = ensure_record_id(self.notebook)
        data["source_ids"] = [
            ensure_record_id(item) for item in _stringify_record_list(self.source_ids)
        ]
        data["note_ids"] = [
            ensure_record_id(item) for item in _stringify_record_list(self.note_ids)
        ]
        data["thread_ids"] = [
            ensure_record_id(item) for item in _stringify_record_list(self.thread_ids)
        ]
        if data.get("parent_draft_id") is not None:
            data["parent_draft_id"] = ensure_record_id(data["parent_draft_id"])
        return data

    @classmethod
    async def list_by_notebook(cls, notebook_id: str) -> List["Draft"]:
        try:
            result = await repo_query(
                "SELECT * FROM draft WHERE notebook = $notebook ORDER BY updated DESC",
                {"notebook": ensure_record_id(notebook_id)},
            )
            return [Draft(**record) for record in result]
        except Exception as exc:
            logger.error("Error listing drafts for notebook {}: {}", notebook_id, exc)
            raise DatabaseOperationError(exc)
