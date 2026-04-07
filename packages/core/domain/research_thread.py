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
        return [str(item) for item in value if item]
    return [str(value)]


class ResearchThread(ObjectModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    table_name: ClassVar[str] = "research_thread"
    nullable_fields: ClassVar[set[str]] = set()

    notebook: Union[str, RecordID]
    title: str
    seed_kind: str
    source_ids: List[Union[str, RecordID]] = Field(default_factory=list)
    note_ids: List[Union[str, RecordID]] = Field(default_factory=list)
    entries: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise InvalidInputError("Research thread title cannot be empty")
        return normalized

    @field_validator("notebook", mode="before")
    @classmethod
    def normalize_notebook(
        cls, value: Optional[Union[str, RecordID]]
    ) -> Optional[Union[str, RecordID]]:
        if value is None or value == "":
            return None
        return ensure_record_id(value)

    @field_validator("source_ids", "note_ids", mode="before")
    @classmethod
    def normalize_record_lists(cls, value: Any) -> list[Union[str, RecordID]]:
        return [ensure_record_id(item) for item in _stringify_record_list(value)]

    def _prepare_save_data(self) -> Dict[str, Any]:
        data = super()._prepare_save_data()
        data["notebook"] = ensure_record_id(self.notebook)
        data["source_ids"] = [
            ensure_record_id(item) for item in _stringify_record_list(self.source_ids)
        ]
        data["note_ids"] = [
            ensure_record_id(item) for item in _stringify_record_list(self.note_ids)
        ]
        return data

    @classmethod
    async def list_by_notebook(cls, notebook_id: str) -> List["ResearchThread"]:
        try:
            result = await repo_query(
                "SELECT * FROM research_thread WHERE notebook = $notebook ORDER BY updated DESC",
                {"notebook": ensure_record_id(notebook_id)},
            )
            return [ResearchThread(**record) for record in result]
        except Exception as exc:
            logger.error(
                "Error listing research threads for notebook {}: {}", notebook_id, exc
            )
            raise DatabaseOperationError(exc)
