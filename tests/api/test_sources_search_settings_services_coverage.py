from __future__ import annotations

from types import SimpleNamespace

import pytest

from packages.core.domain.content_settings import ContentSettings
from packages.core.domain.notebook import Asset, Source
from services.api.search_service import SearchService
from services.api.settings_service import SettingsService
from services.api.sources_service import (
    SourceProcessingResult,
    SourcesService,
    SourceWithMetadata,
)


def test_sources_get_all_and_get_source_support_dict_and_list(monkeypatch):
    service = SourcesService()

    sources_payload = [
        {
            "id": "source:1",
            "title": "A",
            "topics": ["t1"],
            "asset": {"file_path": "/tmp/a.txt", "url": None},
            "created": "2026-01-01",
            "updated": "2026-01-02",
            "embedded_chunks": 3,
        },
        {
            "id": "source:2",
            "title": "B",
            "topics": [],
            "asset": None,
            "created": "2026-01-03",
            "updated": "2026-01-04",
        },
    ]
    monkeypatch.setattr(
        "services.api.sources_service.api_client.get_sources",
        lambda notebook_id=None: sources_payload,
    )
    monkeypatch.setattr(
        "services.api.sources_service.api_client.get_source",
        lambda _source_id: [  # list response branch
            {
                "id": "source:3",
                "title": "C",
                "topics": ["x"],
                "full_text": "body",
                "asset": {"file_path": None, "url": "https://example.com"},
                "created": "2026-01-05",
                "updated": "2026-01-06",
                "embedded_chunks": 5,
            }
        ],
    )

    all_sources = service.get_all_sources(notebook_id="nb:1")
    assert len(all_sources) == 2
    assert isinstance(all_sources[0], SourceWithMetadata)
    assert all_sources[0].id == "source:1"
    assert all_sources[0].embedded_chunks == 3
    assert all_sources[1].asset is None
    assert all_sources[1].embedded_chunks == 0

    source = service.get_source("source:3")
    assert source.id == "source:3"
    assert source.full_text == "body"
    assert source.asset.url == "https://example.com"
    assert source.embedded_chunks == 5


def test_source_with_metadata_property_setter_updates_underlying_source():
    wrapped = SourceWithMetadata(source=Source(title="before"), embedded_chunks=0)
    wrapped.title = "after"
    assert wrapped.source.title == "after"


def test_sources_create_source_sync_and_async_branches(monkeypatch):
    service = SourcesService()

    sync_response = {
        "id": "source:10",
        "title": "Sync",
        "topics": None,  # exercises fallback to []
        "full_text": "text",
        "asset": None,
        "created": "2026-01-07",
        "updated": "2026-01-08",
    }
    async_response = {
        "id": "source:11",
        "title": "Async",
        "topics": ["a"],
        "full_text": "text",
        "asset": {"file_path": "/tmp/f.txt", "url": None},
        "created": "2026-01-09",
        "updated": "2026-01-10",
        "command_id": "cmd:1",
        "status": "processing",
        "processing_info": {"stage": "queued"},
    }

    create_source_stub = SimpleNamespace(calls=0)

    def _create_source(**kwargs):
        create_source_stub.calls += 1
        return sync_response if create_source_stub.calls == 1 else async_response

    monkeypatch.setattr(
        "services.api.sources_service.api_client.create_source", _create_source
    )

    sync_result = service.create_source(content="sync", source_type="text")
    assert isinstance(sync_result, Source)
    assert sync_result.id == "source:10"
    assert sync_result.topics == []

    async_result = service.create_source(content="async", source_type="text")
    assert isinstance(async_result, SourceProcessingResult)
    assert async_result.is_async is True
    assert async_result.command_id == "cmd:1"
    assert async_result.status == "processing"
    assert async_result.source.asset.file_path == "/tmp/f.txt"


def test_sources_create_source_async_fallback_wraps_source(monkeypatch):
    service = SourcesService()
    source = Source(title="fallback")
    source.id = "source:12"

    monkeypatch.setattr(service, "create_source", lambda **_: source)

    result = service.create_source_async(content="x")
    assert isinstance(result, SourceProcessingResult)
    assert result.source.id == "source:12"
    assert result.is_async is False


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("completed", True),
        ("failed", True),
        (None, True),
        ("processing", False),
        ("queued", False),
        ("unknown", False),
        ("error", False),
    ],
)
def test_sources_is_processing_complete_status_matrix(monkeypatch, status, expected):
    service = SourcesService()
    monkeypatch.setattr(service, "get_source_status", lambda _sid: {"status": status})
    assert service.is_source_processing_complete("source:1") is expected


def test_sources_is_processing_complete_returns_false_on_error(monkeypatch):
    service = SourcesService()
    monkeypatch.setattr(
        service,
        "get_source_status",
        lambda _sid: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert service.is_source_processing_complete("source:1") is False


def test_sources_get_status_update_and_delete_paths(monkeypatch):
    service = SourcesService()

    monkeypatch.setattr(
        "services.api.sources_service.api_client.get_source_status",
        lambda _sid: [{"status": "completed"}],  # list response branch
    )
    assert service.get_source_status("source:20") == {"status": "completed"}

    src = Source(title="old", topics=["a"], asset=Asset(file_path=None, url=None))
    src.id = "source:20"
    monkeypatch.setattr(
        "services.api.sources_service.api_client.update_source",
        lambda _sid, **_updates: [
            {"title": "new", "topics": ["b"], "updated": "2026-02-01"}
        ],
    )
    updated = service.update_source(src)
    assert updated.title == "new"
    assert updated.topics == ["b"]
    assert updated.updated == "2026-02-01"

    deleted = {"called": False}

    def _delete_source(_sid):
        deleted["called"] = True

    monkeypatch.setattr(
        "services.api.sources_service.api_client.delete_source", _delete_source
    )
    assert service.delete_source("source:20") is True
    assert deleted["called"] is True


def test_sources_update_source_requires_id():
    service = SourcesService()
    with pytest.raises(ValueError, match="Source ID is required for update"):
        service.update_source(Source(title="x"))


def test_search_service_search_and_ask_paths(monkeypatch):
    service = SearchService()

    monkeypatch.setattr(
        "services.api.search_service.api_client.search",
        lambda **_: {"results": [{"id": "r1"}]},
    )
    assert service.search("q") == [{"id": "r1"}]

    monkeypatch.setattr(
        "services.api.search_service.api_client.search", lambda **_: ["not-dict"]
    )
    assert service.search("q") == []

    expected = {"answer": "ok"}
    monkeypatch.setattr(
        "services.api.search_service.api_client.ask_simple", lambda **_: expected
    )
    assert (
        service.ask_knowledge_base("q", "strategy-model", "answer-model", "final-model")
        == expected
    )


def test_settings_service_get_and_update_settings_dict_and_list(monkeypatch):
    service = SettingsService()

    get_dict_response = {
        "default_content_processing_engine_doc": "docling",
        "default_content_processing_engine_url": "jina",
        "default_embedding_option": "always",
        "auto_delete_files": "no",
        "youtube_preferred_languages": ["en", "zh"],
    }
    monkeypatch.setattr(
        "services.api.settings_service.api_client.get_settings",
        lambda: get_dict_response,
    )
    settings = service.get_settings()
    assert isinstance(settings, ContentSettings)
    assert settings.default_content_processing_engine_doc == "docling"
    assert settings.youtube_preferred_languages == ["en", "zh"]

    update_response = [
        {
            "default_content_processing_engine_doc": "simple",
            "default_content_processing_engine_url": "firecrawl",
            "default_embedding_option": "never",
            "auto_delete_files": "yes",
            "youtube_preferred_languages": ["fr"],
        }
    ]
    captured = {}

    def _update_settings(**kwargs):
        captured.update(kwargs)
        return update_response

    monkeypatch.setattr(
        "services.api.settings_service.api_client.update_settings", _update_settings
    )

    updated = service.update_settings(settings)
    assert captured["default_content_processing_engine_doc"] == "docling"
    assert captured["default_content_processing_engine_url"] == "jina"
    assert updated.default_content_processing_engine_doc == "simple"
    assert updated.default_content_processing_engine_url == "firecrawl"
    assert updated.default_embedding_option == "never"
    assert updated.auto_delete_files == "yes"
    assert updated.youtube_preferred_languages == ["fr"]
