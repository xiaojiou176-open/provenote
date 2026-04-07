from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from packages.core.application.models import AuditableRepairRequest
from services.api import auditable_service as auditable_service_module


@pytest.mark.asyncio
async def test_repair_run_target_creates_new_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        auditable_service_module.auditable_service,
        "get_run",
        AsyncMock(
            return_value=SimpleNamespace(
                id="auditable_run:1",
                source_id="source:1",
                model_id="model-auditable",
                language="zh-CN",
                near_dedup_threshold=0.97,
                source_paragraphs=[
                    {
                        "pid": "P000001",
                        "order": 1,
                        "raw_text": "Alpha",
                        "canonical_text": "Alpha",
                        "canonical_hash": "hash-1",
                    }
                ],
                sections=[
                    {"title": "Summary", "bullets": ["Old"], "source_pids": ["P000001"]}
                ],
                claims=[{"text": "Old claim", "source_pids": ["P000001"]}],
                dedup_entries=[{"pid": "P000001", "text": "Alpha", "status": "core"}],
                dedup_json={"exact_groups": [], "near_groups": [], "group_count": 0},
            )
        ),
    )
    monkeypatch.setattr(
        auditable_service_module.Source,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="source:1")),
    )
    monkeypatch.setattr(
        auditable_service_module,
        "_repair_with_llm",
        AsyncMock(return_value={"text": "New claim", "source_pids": ["P000001"]}),
    )
    monkeypatch.setattr(
        auditable_service_module,
        "repo_create",
        AsyncMock(
            return_value=[
                {
                    "id": "auditable_run:2",
                    "source": "source:1",
                    "status": "completed",
                    "model_id": "model-auditable",
                    "language": "zh-CN",
                    "near_dedup_threshold": 0.97,
                    "metrics": {
                        "coverage_rate": 1.0,
                        "missing_count": 0,
                        "duplicate_count": 0,
                        "uncited_claims_count": 0,
                        "dedup_group_count": 0,
                        "unknown_pid_count": 0,
                        "unclassified_count": 0,
                    },
                    "coverage_json": {},
                    "dedup_json": {
                        "exact_groups": [],
                        "near_groups": [],
                        "group_count": 0,
                    },
                    "result_markdown": "# Auditable Long Text Run",
                    "source_paragraphs": [],
                    "sections": [],
                    "claims": [{"text": "New claim", "source_pids": ["P000001"]}],
                    "dedup_entries": [],
                    "created": "2026-01-01T00:00:00+00:00",
                    "updated": "2026-01-01T00:00:00+00:00",
                }
            ]
        ),
    )

    response = await auditable_service_module.auditable_service.repair_run_target(
        "auditable_run:1",
        AuditableRepairRequest(target_index=0),
        target_type="claim",
    )

    assert response.id == "auditable_run:2"
    assert response.claims[0]["text"] == "New claim"
