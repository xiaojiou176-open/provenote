from __future__ import annotations

from typing import Any

from packages.core.ai.model_strategy import GEMINI_DEFAULT_FAST_PATH_MODEL
from packages.core.application.models import (
    DraftCreateRequest,
    DraftResponse,
    ResearchThreadCreateRequest,
    ResearchThreadEntryRequest,
    ResearchThreadResponse,
)
from packages.core.database.repository import ensure_record_id, repo_create, repo_query
from packages.core.domain.notebook import Notebook
from packages.core.domain.research_thread import ResearchThread
from packages.core.exceptions import InvalidInputError, NotFoundError
from services.api.draft_service import draft_service


class ResearchThreadService:
    @staticmethod
    def _normalize_thread_id(thread_id: str) -> str:
        return (
            thread_id
            if thread_id.startswith("research_thread:")
            else f"research_thread:{thread_id}"
        )

    @staticmethod
    def _to_response(record: dict[str, Any]) -> ResearchThreadResponse:
        source_ids = [str(item) for item in record.get("source_ids", [])]
        note_ids = [str(item) for item in record.get("note_ids", [])]
        entries = record.get("entries", []) or []
        notebook = record.get("notebook")
        return ResearchThreadResponse(
            id=str(record["id"]),
            notebook_id=str(notebook),
            title=record.get("title", "Untitled Thread"),
            seed_kind=record.get("seed_kind", "search"),
            source_ids=source_ids,
            note_ids=note_ids,
            entries=entries,
            entry_count=len(entries),
            created=str(record.get("created", "")),
            updated=str(record.get("updated", "")),
        )

    async def _get_notebook_or_raise(self, notebook_id: str) -> Notebook:
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise NotFoundError("Notebook not found")
        return notebook

    async def create_thread(
        self, notebook_id: str, request: ResearchThreadCreateRequest
    ) -> ResearchThreadResponse:
        await self._get_notebook_or_raise(notebook_id)
        entry_type = (
            "insight_snapshot"
            if request.seed_kind == "insight"
            else ("answer_snapshot" if request.answer else "search_result")
        )
        metadata = {
            "question": request.question,
            "search_results": request.search_results,
        }
        if request.insight_id:
            metadata["insight_id"] = request.insight_id
        if request.insight_type:
            metadata["insight_type"] = request.insight_type
        entries = [
            {
                "entry_type": entry_type,
                "title": request.title,
                "content": request.answer or request.question or "",
                "source_ids": request.source_ids,
                "note_ids": request.note_ids,
                "metadata": metadata,
            }
        ]
        created = await repo_create(
            "research_thread",
            {
                "notebook": ensure_record_id(notebook_id),
                "title": request.title,
                "seed_kind": request.seed_kind,
                "source_ids": [ensure_record_id(item) for item in request.source_ids],
                "note_ids": [ensure_record_id(item) for item in request.note_ids],
                "entries": entries,
            },
        )
        record = created[0] if isinstance(created, list) else created
        return self._to_response(record)

    async def list_threads_by_notebook(
        self, notebook_id: str
    ) -> list[ResearchThreadResponse]:
        await self._get_notebook_or_raise(notebook_id)
        threads = await ResearchThread.list_by_notebook(notebook_id)
        return [self._to_response(thread.model_dump()) for thread in threads]

    async def get_thread(self, thread_id: str) -> ResearchThreadResponse:
        full_thread_id = self._normalize_thread_id(thread_id)
        result = await repo_query(
            "SELECT * FROM $id", {"id": ensure_record_id(full_thread_id)}
        )
        if not result:
            raise NotFoundError("Research thread not found")
        return self._to_response(result[0])

    async def append_entry(
        self, thread_id: str, request: ResearchThreadEntryRequest
    ) -> ResearchThreadResponse:
        thread = await self.get_thread(thread_id)
        updated_entries = [
            *thread.entries,
            {
                "entry_type": request.entry_type,
                "title": request.title,
                "content": request.content,
                "source_ids": request.source_ids,
                "note_ids": request.note_ids,
                "metadata": request.metadata,
            },
        ]
        updated_source_ids = sorted(set([*thread.source_ids, *request.source_ids]))
        updated_note_ids = sorted(set([*thread.note_ids, *request.note_ids]))
        result = await repo_query(
            "UPDATE $id MERGE $data RETURN AFTER",
            {
                "id": ensure_record_id(self._normalize_thread_id(thread_id)),
                "data": {
                    "entries": updated_entries,
                    "source_ids": [
                        ensure_record_id(item) for item in updated_source_ids
                    ],
                    "note_ids": [ensure_record_id(item) for item in updated_note_ids],
                },
            },
        )
        return self._to_response(result[0])

    async def create_draft_from_thread(self, thread_id: str) -> DraftResponse:
        thread = await self.get_thread(thread_id)
        if not thread.source_ids:
            raise InvalidInputError(
                "Research thread must include at least one source before it can create a draft"
            )
        return await draft_service.create_draft(
            thread.notebook_id,
            DraftCreateRequest(
                title=f"{thread.title} Draft",
                source_ids=thread.source_ids,
                note_ids=thread.note_ids,
                thread_ids=[thread.id],
                model_id=GEMINI_DEFAULT_FAST_PATH_MODEL,
                language="zh-CN",
                near_dedup_threshold=0.97,
            ),
        )


research_thread_service = ResearchThreadService()
