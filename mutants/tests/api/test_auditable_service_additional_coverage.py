from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import services.api.auditable_service as auditable_service_module
from packages.core.application.models import (
    AuditableBatchRequest,
    AuditableRunCreateRequest,
)
from packages.core.exceptions import InvalidInputError, NotFoundError
from services.api.auditable_service import AuditableService


def test_auditable_service_helper_methods_cover_normalization_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert AuditableService._normalize_source_id("source:1") == "source:1"
    assert AuditableService._normalize_source_id("1") == "source:1"
    assert AuditableService._normalize_run_id("auditable_run:1") == "auditable_run:1"
    assert AuditableService._normalize_run_id("1") == "auditable_run:1"

    assert AuditableService._source_id_from_record({"id": "source:3"}) == "source:3"
    assert AuditableService._source_id_from_record({"id": None}) == ""
    assert AuditableService._source_id_from_record(None) == ""
    assert AuditableService._source_id_from_record("source:4") == "source:4"

    class FakeRecordID:
        def __init__(self, value: str) -> None:
            self.value = value

        def __str__(self) -> str:
            return self.value

    monkeypatch.setattr(auditable_service_module, "RecordID", FakeRecordID)
    assert (
        AuditableService._source_id_from_record(FakeRecordID("source:2")) == "source:2"
    )


def test_extract_record_supports_list_and_dict_and_rejects_invalid() -> None:
    assert AuditableService._extract_record([{"id": "auditable_run:1"}]) == {
        "id": "auditable_run:1"
    }
    assert AuditableService._extract_record({"id": "auditable_run:2"}) == {
        "id": "auditable_run:2"
    }
    with pytest.raises(NotFoundError, match="Record was not created"):
        AuditableService._extract_record([])
    with pytest.raises(InvalidInputError, match="Unexpected database response format"):
        AuditableService._extract_record("invalid")


@pytest.mark.asyncio
async def test_upsert_source_paragraphs_builds_ids_and_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upsert_mock = AsyncMock()
    monkeypatch.setattr(auditable_service_module, "repo_upsert", upsert_mock)
    service = AuditableService()

    ids = await service._upsert_source_paragraphs(
        source_record_id="source:abc",
        source_paragraphs=[
            {
                "pid": "P1",
                "order": 1,
                "raw_text": "raw1",
                "canonical_text": "canon1",
                "canonical_hash": "h1",
            },
            {"pid": "P2"},
        ],
    )

    assert ids == ["source_paragraph:source_abc__P1", "source_paragraph:source_abc__P2"]
    assert upsert_mock.await_count == 2


@pytest.mark.asyncio
async def test_create_run_raises_for_missing_or_empty_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuditableService()
    request = AuditableRunCreateRequest()

    monkeypatch.setattr(
        auditable_service_module.Source, "get", AsyncMock(return_value=None)
    )
    with pytest.raises(NotFoundError, match="Source not found"):
        await service.create_run("source:missing", request)

    monkeypatch.setattr(
        auditable_service_module.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1", full_text="   ")),
    )
    with pytest.raises(InvalidInputError, match="Source full_text is empty"):
        await service.create_run("source:1", request)


@pytest.mark.asyncio
async def test_create_run_success_happy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuditableService()
    request = AuditableRunCreateRequest(
        model_id="gemini-3.1-pro-preview",
        language="zh-CN",
        near_dedup_threshold=0.91,
    )
    monkeypatch.setattr(
        auditable_service_module.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1", full_text="input text")),
    )
    monkeypatch.setattr(
        auditable_service_module.auditable_graph,
        "ainvoke",
        AsyncMock(
            return_value={
                "output": {
                    "source_paragraphs": [
                        {
                            "pid": "P1",
                            "order": 1,
                            "raw_text": "raw",
                            "canonical_text": "canon",
                            "canonical_hash": "hash",
                        }
                    ],
                    "coverage_json": {"coverage_rate": 0.5},
                    "dedup_json": {"group_count": 1},
                    "result_markdown": "# result",
                }
            }
        ),
    )
    monkeypatch.setattr(
        auditable_service_module, "ensure_record_id", lambda value: value
    )
    monkeypatch.setattr(
        auditable_service_module, "repo_upsert", AsyncMock(return_value={})
    )

    async def _repo_create(table: str, data: dict):
        assert table == "auditable_run"
        return [
            {
                "id": "auditable_run:1",
                **data,
                "created": "2026-01-01T00:00:00Z",
                "updated": "2026-01-01T00:00:01Z",
            }
        ]

    monkeypatch.setattr(auditable_service_module, "repo_create", _repo_create)

    response = await service.create_run("source:1", request)

    assert response.id == "auditable_run:1"
    assert response.source_id == "source:1"
    assert response.result_markdown == "# result"


@pytest.mark.asyncio
async def test_create_run_rolls_back_paragraphs_and_logs_cleanup_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuditableService()
    request = AuditableRunCreateRequest()
    warning_mock = MagicMock()
    monkeypatch.setattr(auditable_service_module.logger, "warning", warning_mock)
    monkeypatch.setattr(
        auditable_service_module.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1", full_text="input text")),
    )
    monkeypatch.setattr(
        auditable_service_module.auditable_graph,
        "ainvoke",
        AsyncMock(
            return_value={
                "output": {
                    "source_paragraphs": [{"pid": "P1"}, {"pid": "P2"}],
                }
            }
        ),
    )
    monkeypatch.setattr(
        auditable_service_module, "ensure_record_id", lambda value: value
    )
    monkeypatch.setattr(
        auditable_service_module, "repo_upsert", AsyncMock(return_value={})
    )
    monkeypatch.setattr(
        auditable_service_module,
        "repo_create",
        AsyncMock(side_effect=RuntimeError("create failed")),
    )

    cleanup_calls: list[tuple[str, dict | None]] = []

    async def _repo_query(query: str, params: dict | None = None):
        cleanup_calls.append((query, params))
        if len(cleanup_calls) == 2:
            raise RuntimeError("cleanup failed")
        return []

    monkeypatch.setattr(
        auditable_service_module,
        "repo_query",
        AsyncMock(side_effect=_repo_query),
    )

    with pytest.raises(RuntimeError, match="create failed"):
        await service.create_run("source:1", request)

    assert len(cleanup_calls) == 2
    warning_mock.assert_called_once()


@pytest.mark.asyncio
async def test_get_run_list_runs_get_markdown_and_create_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuditableService()
    sample_record = {
        "id": "auditable_run:1",
        "source": "source:1",
        "status": "completed",
        "model_id": "gemini-3.1-pro-preview",
        "language": "zh-CN",
        "near_dedup_threshold": 0.97,
        "coverage_json": {"coverage_rate": 1.0},
        "dedup_json": {"group_count": 0},
        "metrics": {
            "coverage_rate": 1.0,
            "missing_count": 0,
            "duplicate_count": 0,
            "uncited_claims_count": 0,
            "dedup_group_count": 0,
            "unknown_pid_count": 0,
            "unclassified_count": 0,
        },
        "result_markdown": "ok",
        "source_paragraphs": [],
        "sections": [],
        "claims": [],
        "dedup_entries": [],
        "created": "2026-01-01T00:00:00Z",
        "updated": "2026-01-01T00:00:00Z",
    }

    monkeypatch.setattr(
        auditable_service_module,
        "repo_query",
        AsyncMock(return_value=[sample_record]),
    )
    monkeypatch.setattr(
        auditable_service_module, "ensure_record_id", lambda value: value
    )

    run = await service.get_run("1")
    assert run.id == "auditable_run:1"
    assert await service.get_markdown("1") == "ok"

    runs = await service.list_runs_by_source("1")
    assert len(runs) == 1
    assert runs[0].source_id == "source:1"

    monkeypatch.setattr(
        service,
        "create_run",
        AsyncMock(
            side_effect=[
                SimpleNamespace(id="auditable_run:1"),
                RuntimeError("failed source"),
                SimpleNamespace(id="auditable_run:3"),
            ]
        ),
    )
    warning_mock = MagicMock()
    monkeypatch.setattr(auditable_service_module.logger, "warning", warning_mock)
    batch = await service.create_batch(
        AuditableBatchRequest(source_ids=["source:1", "source:2", "source:3"])
    )
    assert batch.run_ids == ["auditable_run:1", "auditable_run:3"]
    warning_mock.assert_called_once()


@pytest.mark.asyncio
async def test_get_run_raises_not_found_for_empty_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AuditableService()
    monkeypatch.setattr(
        auditable_service_module, "repo_query", AsyncMock(return_value=[])
    )
    monkeypatch.setattr(
        auditable_service_module, "ensure_record_id", lambda value: value
    )

    with pytest.raises(NotFoundError, match="Auditable run not found"):
        await service.get_run("missing")
