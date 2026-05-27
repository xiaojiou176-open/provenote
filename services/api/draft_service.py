from __future__ import annotations

import io
import json
import re
import zipfile
from typing import Any, cast

from surrealdb import RecordID  # type: ignore

from packages.core.application.models import (
    AuditableMetrics,
    DraftCreateRequest,
    DraftRerunRequest,
    DraftResponse,
)
from packages.core.database.repository import ensure_record_id, repo_create, repo_query
from packages.core.domain.draft import Draft
from packages.core.domain.notebook import Notebook, Source
from packages.core.exceptions import InvalidInputError, NotFoundError
from packages.core.graphs.notebook_draft import (
    NotebookDraftState,
)
from packages.core.graphs.notebook_draft import (
    graph as notebook_draft_graph,
)


class DraftService:
    @staticmethod
    def _normalize_draft_id(draft_id: str) -> str:
        return draft_id if draft_id.startswith("draft:") else f"draft:{draft_id}"

    @staticmethod
    def _normalize_source_id(source_id: str) -> str:
        return source_id if source_id.startswith("source:") else f"source:{source_id}"

    @staticmethod
    def _normalize_note_id(note_id: str) -> str:
        return note_id if note_id.startswith("note:") else f"note:{note_id}"

    @staticmethod
    def _normalize_thread_id(thread_id: str) -> str:
        return (
            thread_id
            if thread_id.startswith("research_thread:")
            else f"research_thread:{thread_id}"
        )

    @staticmethod
    def _record_to_string(value: Any) -> str:
        if isinstance(value, dict):
            record_id = value.get("id")
            return str(record_id) if record_id else ""
        if isinstance(value, RecordID):
            return str(value)
        if value is None:
            return ""
        if isinstance(value, str) and value.strip().lower() in {"none", "null"}:
            return ""
        return str(value)

    @staticmethod
    def _record_list_to_strings(value: Any) -> list[str]:
        if not value:
            return []
        if isinstance(value, list):
            return [
                stringified
                for item in value
                if (stringified := DraftService._record_to_string(item))
            ]
        stringified = DraftService._record_to_string(value)
        return [stringified] if stringified else []

    @staticmethod
    def _sanitize_export_stem(value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
        return normalized or "draft-outcome"

    @staticmethod
    def _build_pid_summary(draft: DraftResponse) -> dict[str, Any]:
        claim_pids = sorted(
            {
                str(pid)
                for claim in draft.claims
                if isinstance(claim, dict)
                for pid in claim.get("source_pids", []) or []
            }
        )
        section_pids = sorted(
            {
                str(pid)
                for section in draft.sections
                if isinstance(section, dict)
                for pid in section.get("source_pids", []) or []
            }
        )
        paragraph_pids = sorted(
            {
                str(paragraph.get("pid", ""))
                for paragraph in draft.source_paragraphs
                if isinstance(paragraph, dict) and paragraph.get("pid")
            }
        )
        return {
            "claim_pid_count": len(claim_pids),
            "section_pid_count": len(section_pids),
            "source_paragraph_pid_count": len(paragraph_pids),
            "claim_pids": claim_pids,
            "section_pids": section_pids,
            "source_paragraph_pids": paragraph_pids,
        }

    @staticmethod
    def _default_metrics(record: dict[str, Any]) -> AuditableMetrics:
        coverage_json = record.get("coverage_json", {}) or {}
        coverage_rate = float(coverage_json.get("coverage_rate", 0.0))
        duplicate_count = len(coverage_json.get("duplicate_pids", []))
        missing_count = len(coverage_json.get("missing_pids", []))
        unknown_pid_count = len(coverage_json.get("unknown_pids", []))
        unclassified_count = len(coverage_json.get("unclassified_pids", []))
        dedup_json = record.get("dedup_json", {}) or {}
        return AuditableMetrics(
            coverage_rate=coverage_rate,
            missing_count=missing_count,
            duplicate_count=duplicate_count,
            uncited_claims_count=0,
            dedup_group_count=int(dedup_json.get("group_count", 0)),
            unknown_pid_count=unknown_pid_count,
            unclassified_count=unclassified_count,
        )

    @staticmethod
    def _to_response(record: dict[str, Any]) -> DraftResponse:
        raw_metrics = record.get("metrics")
        metrics = DraftService._default_metrics(record)
        if isinstance(raw_metrics, dict):
            try:
                metrics = AuditableMetrics.model_validate(raw_metrics)
            except Exception:
                metrics = DraftService._default_metrics(record)

        return DraftResponse(
            id=str(record["id"]),
            notebook_id=DraftService._record_to_string(record.get("notebook")),
            title=record.get("title", "Untitled Draft"),
            status=record.get("status", "completed"),
            model_id=record.get("model_id", ""),
            language=record.get("language", "zh-CN"),
            near_dedup_threshold=float(record.get("near_dedup_threshold", 0.97)),
            source_ids=DraftService._record_list_to_strings(record.get("source_ids")),
            note_ids=DraftService._record_list_to_strings(record.get("note_ids")),
            thread_ids=DraftService._record_list_to_strings(record.get("thread_ids")),
            version=int(record.get("version", 1)),
            parent_draft_id=DraftService._record_to_string(
                record.get("parent_draft_id")
            )
            or None,
            metrics=metrics,
            coverage_json=record.get("coverage_json", {}),
            dedup_json=record.get("dedup_json", {}),
            result_markdown=record.get("result_markdown", ""),
            source_paragraphs=record.get("source_paragraphs", []),
            sections=record.get("sections", []),
            claims=record.get("claims", []),
            dedup_entries=record.get("dedup_entries", []),
            verified_brief_snapshot=record.get("verified_brief_snapshot"),
            created=DraftService._record_to_string(record.get("created")),
            updated=DraftService._record_to_string(record.get("updated")),
        )

    async def _get_notebook_or_raise(self, notebook_id: str) -> Notebook:
        notebook = await Notebook.get(notebook_id)
        if not notebook:
            raise NotFoundError("Notebook not found")
        return notebook

    async def _resolve_selected_sources(
        self, notebook_id: str, source_ids: list[str]
    ) -> list[Source]:
        normalized_source_ids = [self._normalize_source_id(item) for item in source_ids]
        notebook = await self._get_notebook_or_raise(notebook_id)
        notebook_sources = await notebook.get_sources()
        notebook_source_map = {
            str(source.id): source for source in notebook_sources if source.id
        }

        missing = [
            source_id
            for source_id in normalized_source_ids
            if source_id not in notebook_source_map
        ]
        if missing:
            raise InvalidInputError(
                "Draft sources must belong to the notebook: " + ", ".join(missing)
            )

        resolved_sources: list[Source] = []
        for source_id in normalized_source_ids:
            source = notebook_source_map[source_id]
            if source.full_text and source.full_text.strip():
                resolved_sources.append(source)
                continue

            # Notebook list queries intentionally omit `full_text` for lighter UI payloads.
            # Draft generation needs the full source body, so re-fetch the canonical source
            # record only when the lightweight notebook view does not carry it.
            full_source = await Source.get(source_id)
            resolved_sources.append(full_source or source)
        if not resolved_sources:
            raise InvalidInputError("Draft requires at least one source")

        return resolved_sources

    async def _build_draft_record(
        self,
        *,
        notebook_id: str,
        title: str,
        request: DraftCreateRequest,
        parent_draft_id: str | None = None,
        version: int = 1,
    ) -> dict[str, Any]:
        sources = await self._resolve_selected_sources(notebook_id, request.source_ids)
        graph_input = cast(
            NotebookDraftState,
            {
                "title": title,
                "sources": sources,
                "model": request.model_id,
                "language": request.language,
                "near_dedup_threshold": request.near_dedup_threshold,
                "output": {},
            },
        )
        graph_result = await notebook_draft_graph.ainvoke(cast(Any, graph_input))
        output = graph_result["output"]
        return {
            "notebook": ensure_record_id(notebook_id),
            "title": title,
            "status": "completed",
            "model_id": output.get("model_id", request.model_id),
            "language": output.get("language", request.language),
            "near_dedup_threshold": output.get(
                "near_dedup_threshold", request.near_dedup_threshold
            ),
            "source_ids": [ensure_record_id(item) for item in request.source_ids],
            "note_ids": [ensure_record_id(item) for item in request.note_ids],
            "thread_ids": [
                ensure_record_id(self._normalize_thread_id(item))
                for item in request.thread_ids
            ],
            "version": version,
            "parent_draft_id": ensure_record_id(parent_draft_id)
            if parent_draft_id
            else None,
            "metrics": output.get("metrics", {}),
            "coverage_json": output.get("coverage_json", {}),
            "dedup_json": output.get("dedup_json", {}),
            "result_markdown": output.get("result_markdown", ""),
            "source_paragraphs": output.get("source_paragraphs", []),
            "sections": output.get("sections", []),
            "claims": output.get("claims", []),
            "dedup_entries": output.get("dedup_entries", []),
            "verified_brief_snapshot": None,
        }

    async def create_draft(
        self, notebook_id: str, request: DraftCreateRequest
    ) -> DraftResponse:
        notebook = await self._get_notebook_or_raise(notebook_id)
        title = request.title or f"{notebook.name} Draft"
        created = await repo_create(
            "draft",
            await self._build_draft_record(
                notebook_id=notebook_id,
                title=title,
                request=request,
            ),
        )
        record = created[0] if isinstance(created, list) else created
        return self._to_response(record)

    async def list_drafts_by_notebook(self, notebook_id: str) -> list[DraftResponse]:
        await self._get_notebook_or_raise(notebook_id)
        drafts = await Draft.list_by_notebook(notebook_id)
        return [self._to_response(draft.model_dump()) for draft in drafts]

    async def get_draft(self, draft_id: str) -> DraftResponse:
        full_draft_id = self._normalize_draft_id(draft_id)
        result = await repo_query(
            "SELECT * FROM $id", {"id": ensure_record_id(full_draft_id)}
        )
        if not result:
            raise NotFoundError("Draft not found")
        return self._to_response(result[0])

    async def rerun_draft(
        self, draft_id: str, request: DraftRerunRequest
    ) -> DraftResponse:
        existing = await self.get_draft(draft_id)
        create_request = DraftCreateRequest(
            title=request.title or existing.title,
            source_ids=request.source_ids or existing.source_ids,
            note_ids=request.note_ids or existing.note_ids,
            thread_ids=request.thread_ids or existing.thread_ids,
            model_id=request.model_id or existing.model_id,
            language=request.language or existing.language,
            near_dedup_threshold=(
                request.near_dedup_threshold
                if request.near_dedup_threshold is not None
                else existing.near_dedup_threshold
            ),
        )
        created = await repo_create(
            "draft",
            await self._build_draft_record(
                notebook_id=existing.notebook_id,
                title=create_request.title or existing.title,
                request=create_request,
                parent_draft_id=existing.id,
                version=existing.version + 1,
            ),
        )
        record = created[0] if isinstance(created, list) else created
        return self._to_response(record)

    async def get_markdown(self, draft_id: str) -> str:
        draft = await self.get_draft(draft_id)
        return draft.result_markdown

    async def get_export_bundle(self, draft_id: str) -> tuple[str, bytes]:
        draft = await self.get_draft(draft_id)
        bundle_stem = self._sanitize_export_stem(f"{draft.title}-{draft.version}")
        source_manifest: list[dict[str, Any]] = []
        for source_id in draft.source_ids:
            source = await Source.get(source_id)
            source_manifest.append(
                {
                    "id": source_id,
                    "title": getattr(source, "title", "") or source_id,
                    "topics": getattr(source, "topics", []) or [],
                    "embedded": bool(getattr(source, "embedded", False)),
                    "insights_count": int(getattr(source, "insights_count", 0) or 0),
                }
            )

        bundle_bytes = io.BytesIO()
        with zipfile.ZipFile(
            bundle_bytes, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            archive.writestr("draft.md", draft.result_markdown)
            archive.writestr(
                "metadata.json",
                json.dumps(
                    {
                        "draft_id": draft.id,
                        "title": draft.title,
                        "notebook_id": draft.notebook_id,
                        "status": draft.status,
                        "version": draft.version,
                        "parent_draft_id": draft.parent_draft_id,
                        "model_id": draft.model_id,
                        "language": draft.language,
                        "near_dedup_threshold": draft.near_dedup_threshold,
                        "created": draft.created,
                        "updated": draft.updated,
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
            )
            archive.writestr(
                "metrics.json",
                json.dumps(draft.metrics.model_dump(), indent=2, ensure_ascii=False),
            )
            archive.writestr(
                "pid_summary.json",
                json.dumps(
                    self._build_pid_summary(draft), indent=2, ensure_ascii=False
                ),
            )
            archive.writestr(
                "source_manifest.json",
                json.dumps(source_manifest, indent=2, ensure_ascii=False),
            )
            archive.writestr(
                "sections.json",
                json.dumps(draft.sections, indent=2, ensure_ascii=False),
            )
            archive.writestr(
                "claims.json", json.dumps(draft.claims, indent=2, ensure_ascii=False)
            )
            archive.writestr(
                "coverage.json",
                json.dumps(draft.coverage_json, indent=2, ensure_ascii=False),
            )
            archive.writestr(
                "dedup.json", json.dumps(draft.dedup_json, indent=2, ensure_ascii=False)
            )
            if draft.verified_brief_snapshot is not None:
                archive.writestr(
                    "verified_snapshot.json",
                    json.dumps(
                        draft.verified_brief_snapshot, indent=2, ensure_ascii=False
                    ),
                )
            archive.writestr(
                "README.txt",
                "\n".join(
                    [
                        "Notebooklab outcome bundle",
                        "",
                        "Contents:",
                        "- draft.md: notebook-level markdown outcome",
                        "- metadata.json: draft identity and lifecycle metadata",
                        "- metrics.json: integrity counters for this outcome",
                        "- pid_summary.json: PID coverage and citation summary",
                        "- source_manifest.json: source records included in the draft",
                        "- sections.json / claims.json: structured review surfaces",
                        "- coverage.json / dedup.json: lower-level evidence data",
                        "- verified_snapshot.json: included when this draft was verified",
                    ]
                ),
            )

        return f"{bundle_stem}.zip", bundle_bytes.getvalue()

    async def verify_draft(self, draft_id: str) -> DraftResponse:
        full_draft_id = self._normalize_draft_id(draft_id)
        draft = await self.get_draft(full_draft_id)
        verified_snapshot = {
            "draft_id": draft.id,
            "title": draft.title,
            "version": draft.version,
            "result_markdown": draft.result_markdown,
            "metrics": draft.metrics.model_dump(),
        }
        result = await repo_query(
            "UPDATE $id MERGE $data RETURN AFTER",
            {
                "id": ensure_record_id(full_draft_id),
                "data": {
                    "status": "verified",
                    "verified_brief_snapshot": verified_snapshot,
                },
            },
        )
        if not result:
            raise NotFoundError("Draft not found")
        return self._to_response(result[0])


draft_service = DraftService()
