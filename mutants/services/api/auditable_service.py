from __future__ import annotations

from typing import Any, cast

from surrealdb import RecordID  # type: ignore

from packages.core.ai.model_strategy import GEMINI_MODEL_PRO_31
from packages.core.application.models import (
    AuditableBatchRequest,
    AuditableBatchResponse,
    AuditableMetrics,
    AuditableRunCreateRequest,
    AuditableRunResponse,
)
from packages.core.database.repository import (
    ensure_record_id,
    repo_create,
    repo_query,
    repo_upsert,
)
from packages.core.domain.notebook import Source
from packages.core.exceptions import InvalidInputError, NotFoundError
from packages.core.graphs.auditable_transformation import graph as auditable_graph
from packages.core.observability.logger import logger


class AuditableService:
    @staticmethod
    def _normalize_source_id(source_id: str) -> str:
        return source_id if source_id.startswith("source:") else f"source:{source_id}"

    @staticmethod
    def _normalize_run_id(run_id: str) -> str:
        return (
            run_id if run_id.startswith("auditable_run:") else f"auditable_run:{run_id}"
        )

    @staticmethod
    def _source_id_from_record(source_value: Any) -> str:
        if isinstance(source_value, dict):
            source_id = source_value.get("id")
            return str(source_id) if source_id else ""
        if isinstance(source_value, RecordID):
            return str(source_value)
        if source_value is None:
            return ""
        return str(source_value)

    @staticmethod
    def _default_metrics(record: dict[str, Any]) -> AuditableMetrics:
        coverage_json = record.get("coverage_json", {}) or {}
        coverage_rate = float(coverage_json.get("coverage_rate", 0.0))
        missing_count = len(coverage_json.get("missing_pids", []))
        duplicate_count = len(coverage_json.get("duplicate_pids", []))
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
    def _to_response(record: dict[str, Any]) -> AuditableRunResponse:
        raw_metrics = record.get("metrics")
        metrics = AuditableService._default_metrics(record)
        if isinstance(raw_metrics, dict):
            try:
                metrics = AuditableMetrics.model_validate(raw_metrics)
            except Exception:
                logger.warning(
                    "Invalid auditable metrics payload; falling back to default metrics"
                )
        return AuditableRunResponse(
            id=str(record["id"]),
            source_id=AuditableService._source_id_from_record(record.get("source")),
            status=record.get("status", "completed"),
            model_id=record.get("model_id", GEMINI_MODEL_PRO_31),
            language=record.get("language", "zh-CN"),
            near_dedup_threshold=float(record.get("near_dedup_threshold", 0.97)),
            metrics=metrics,
            coverage_json=record.get("coverage_json", {}),
            dedup_json=record.get("dedup_json", {}),
            result_markdown=record.get("result_markdown", ""),
            source_paragraphs=record.get("source_paragraphs", []),
            sections=record.get("sections", []),
            claims=record.get("claims", []),
            dedup_entries=record.get("dedup_entries", []),
            created=str(record.get("created", "")),
            updated=str(record.get("updated", "")),
        )

    @staticmethod
    def _extract_record(result: Any) -> dict[str, Any]:
        if isinstance(result, list):
            if not result:
                raise NotFoundError("Record was not created")
            return result[0]
        if isinstance(result, dict):
            return result
        raise InvalidInputError("Unexpected database response format")

    async def _upsert_source_paragraphs(
        self,
        *,
        source_record_id: RecordID,
        source_paragraphs: list[dict[str, Any]],
    ) -> list[str]:
        source_key = str(source_record_id).replace(":", "_")
        paragraph_record_ids: list[str] = []
        for paragraph in source_paragraphs:
            pid = str(paragraph.get("pid", ""))
            paragraph_record_id = f"source_paragraph:{source_key}__{pid}"
            await repo_upsert(
                "source_paragraph",
                paragraph_record_id,
                {
                    "source": source_record_id,
                    "pid": pid,
                    "order": int(paragraph.get("order", 0)),
                    "raw_text": paragraph.get("raw_text", ""),
                    "canonical_text": paragraph.get("canonical_text", ""),
                    "canonical_hash": paragraph.get("canonical_hash", ""),
                },
                add_timestamp=True,
            )
            paragraph_record_ids.append(paragraph_record_id)
        return paragraph_record_ids

    async def create_run(
        self, source_id: str, request: AuditableRunCreateRequest
    ) -> AuditableRunResponse:
        full_source_id = self._normalize_source_id(source_id)
        source = await Source.get(full_source_id)
        if not source:
            raise NotFoundError("Source not found")
        if not source.full_text or not source.full_text.strip():
            raise InvalidInputError("Source full_text is empty")

        graph_result = await auditable_graph.ainvoke(
            cast(
                Any,
                {
                    "input_text": source.full_text,
                    "model": request.model_id,
                    "language": request.language,
                    "near_dedup_threshold": request.near_dedup_threshold,
                },
            )
        )
        output = graph_result["output"]

        source_record_id = ensure_record_id(source.id or full_source_id)
        source_paragraphs = output.get("source_paragraphs", [])
        paragraph_record_ids: list[str] = []
        try:
            paragraph_record_ids = await self._upsert_source_paragraphs(
                source_record_id=source_record_id,
                source_paragraphs=source_paragraphs,
            )

            record_data = {
                "source": source_record_id,
                "status": "completed",
                "model_id": output.get("model_id", request.model_id),
                "language": output.get("language", request.language),
                "near_dedup_threshold": output.get(
                    "near_dedup_threshold", request.near_dedup_threshold
                ),
                "metrics": output.get("metrics", {}),
                "coverage_json": output.get("coverage_json", {}),
                "dedup_json": output.get("dedup_json", {}),
                "result_markdown": output.get("result_markdown", ""),
                "source_paragraphs": source_paragraphs,
                "sections": output.get("sections", []),
                "claims": output.get("claims", []),
                "dedup_entries": output.get("dedup_entries", []),
            }

            created = self._extract_record(
                await repo_create("auditable_run", record_data)
            )
            return self._to_response(created)
        except Exception:
            for paragraph_record_id in paragraph_record_ids:
                try:
                    await repo_query(
                        "DELETE $id",
                        {"id": ensure_record_id(paragraph_record_id)},
                    )
                except Exception as cleanup_error:
                    logger.warning(
                        "Failed to rollback source paragraph {}: {}",
                        paragraph_record_id,
                        cleanup_error,
                    )
            raise

    async def get_run(self, run_id: str) -> AuditableRunResponse:
        full_run_id = self._normalize_run_id(run_id)
        result = await repo_query(
            "SELECT * FROM $id FETCH source",
            {"id": ensure_record_id(full_run_id)},
        )
        if not result:
            raise NotFoundError("Auditable run not found")
        return self._to_response(result[0])

    async def list_runs_by_source(self, source_id: str) -> list[AuditableRunResponse]:
        full_source_id = self._normalize_source_id(source_id)
        result = await repo_query(
            "SELECT * FROM auditable_run WHERE source = $source ORDER BY created DESC FETCH source",
            {"source": ensure_record_id(full_source_id)},
        )
        return [self._to_response(record) for record in result]

    async def get_markdown(self, run_id: str) -> str:
        run = await self.get_run(run_id)
        return run.result_markdown

    async def create_batch(
        self, request: AuditableBatchRequest
    ) -> AuditableBatchResponse:
        run_ids: list[str] = []
        for source_id in request.source_ids:
            try:
                run = await self.create_run(
                    source_id,
                    AuditableRunCreateRequest(
                        model_id=request.model_id,
                        language=request.language,
                        near_dedup_threshold=request.near_dedup_threshold,
                    ),
                )
                run_ids.append(run.id)
            except (
                Exception
            ) as exc:  # pragma: no cover - error branch exercised in API tests
                logger.warning(
                    f"Auditable batch failed for source {source_id}: {str(exc)}"
                )
        return AuditableBatchResponse(run_ids=run_ids)


auditable_service = AuditableService()
