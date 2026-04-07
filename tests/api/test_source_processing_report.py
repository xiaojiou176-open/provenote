from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.api import evidence_service as evidence_service_module
from services.api.routers import sources as sources_router


@pytest.mark.asyncio
async def test_build_source_processing_report_uses_source_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SimpleNamespace(
        id="source:1",
        title="Source Alpha",
        full_text="First paragraph\n\nSecond paragraph",
        command="command:1",
        asset=SimpleNamespace(url="https://example.com", file_path="/tmp/source.pdf"),
        get_status=AsyncMock(return_value="completed"),
        get_processing_progress=AsyncMock(
            return_value={"result": {"document_engine": "docling"}}
        ),
        get_embedded_chunks=AsyncMock(return_value=3),
        get_insights=AsyncMock(return_value=[object(), object()]),
    )
    monkeypatch.setattr(
        evidence_service_module.Source,
        "get",
        AsyncMock(return_value=source),
    )
    monkeypatch.setattr(
        evidence_service_module,
        "is_source_file_available",
        lambda _source: True,
    )

    report = await evidence_service_module.build_source_processing_report("source:1")

    assert report.source_type == "link"
    assert report.processing_engine == "docling"
    assert report.paragraph_count == 2
    assert report.embedded_chunks == 3
    assert report.insights_count == 2


@pytest.mark.asyncio
async def test_sources_router_exposes_processing_report_and_reprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sources_router,
        "build_source_processing_report",
        AsyncMock(
            return_value={
                "source_id": "source:1",
                "source_type": "text",
                "title": "Source Alpha",
                "processing_status": "completed",
                "processing_message": "ok",
                "processing_engine": "auto",
                "extracted_length": 10,
                "paragraph_count": 1,
                "embedded": False,
                "embedded_chunks": 0,
                "insights_count": 0,
                "has_file": False,
                "file_available": None,
                "command_id": None,
                "processing_info": None,
            }
        ),
    )
    monkeypatch.setattr(
        sources_router,
        "retry_source_processing_service",
        AsyncMock(return_value={"id": "source:1", "status": "queued"}),
    )

    report = await sources_router.get_source_processing_report("source:1")
    reprocess = await sources_router.reprocess_source("source:1")

    assert report["processing_status"] == "completed"
    assert reprocess["status"] == "queued"
