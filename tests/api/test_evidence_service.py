from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from packages.core.auditable.schemas import (
    AuditableClaim,
    AuditableSection,
    DedupEntry,
    DedupJSON,
    SourceParagraph,
)
from services.api import evidence_service as evidence_service_module


def test_evidence_helpers_cover_type_engine_and_json_paths() -> None:
    link_source = SimpleNamespace(
        asset=SimpleNamespace(url="https://example.com", file_path=None)
    )
    upload_source = SimpleNamespace(
        asset=SimpleNamespace(url=None, file_path="/tmp/x.pdf")
    )
    text_source = SimpleNamespace(asset=None)

    assert evidence_service_module._detect_source_type(link_source) == "link"
    assert evidence_service_module._detect_source_type(upload_source) == "upload"
    assert evidence_service_module._detect_source_type(text_source) == "text"
    assert (
        evidence_service_module._detect_processing_engine(
            {"result": {"engine": "auto"}}
        )
        == "auto"
    )
    assert evidence_service_module._detect_processing_engine(None) is None
    assert evidence_service_module._extract_json_payload('{"ok": true}') == {"ok": True}
    assert evidence_service_module._extract_json_payload(
        'prefix {"ok": true} suffix'
    ) == {"ok": True}
    assert evidence_service_module._extract_json_payload("not-json") is None


@pytest.mark.asyncio
async def test_repair_with_llm_and_rebuild_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_chain = SimpleNamespace(
        ainvoke=AsyncMock(
            return_value=SimpleNamespace(
                content='{"text":"Repaired","source_pids":["P000001"]}'
            )
        )
    )
    monkeypatch.setattr(
        evidence_service_module,
        "provision_langchain_model",
        AsyncMock(return_value=fake_chain),
    )

    payload = await evidence_service_module._repair_with_llm(
        model_id="model-x",
        source_paragraphs=[
            SourceParagraph(
                pid="P000001",
                order=1,
                raw_text="Alpha",
                canonical_text="Alpha",
                canonical_hash="hash",
            )
        ],
        target_type="claim",
        target_payload={"text": "Old", "source_pids": ["P000001"]},
    )
    assert payload["text"] == "Repaired"

    rebuilt = evidence_service_module.rebuild_auditable_record(
        title="Run",
        source_paragraphs=[
            SourceParagraph(
                pid="P000001",
                order=1,
                raw_text="Alpha",
                canonical_text="Alpha",
                canonical_hash="hash",
            )
        ],
        claims=[AuditableClaim(text="Repaired", source_pids=["P000001"])],
        sections=[
            AuditableSection(
                title="Summary", bullets=["Alpha"], source_pids=["P000001"]
            )
        ],
        dedup_entries=[DedupEntry(pid="P000001", text="Alpha", status="core")],
        dedup_json=DedupJSON(exact_groups=[], near_groups=[], group_count=0),
        model_id="model-x",
        language="zh-CN",
        near_dedup_threshold=0.97,
    )
    assert rebuilt["metrics"]["coverage_rate"] == 1.0
    assert rebuilt["result_markdown"].startswith("# Run")


@pytest.mark.asyncio
async def test_build_source_processing_report_legacy_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SimpleNamespace(
        id="source:1",
        title="Source Alpha",
        full_text="Only paragraph",
        command=None,
        asset=None,
        get_embedded_chunks=AsyncMock(return_value=0),
        get_insights=AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        evidence_service_module.Source,
        "get",
        AsyncMock(return_value=source),
    )
    monkeypatch.setattr(
        evidence_service_module,
        "is_source_file_available",
        lambda _source: None,
    )

    report = await evidence_service_module.build_source_processing_report("source:1")

    assert report.processing_status is None
    assert "Legacy or direct source" in report.processing_message
    assert report.paragraph_count == 1
