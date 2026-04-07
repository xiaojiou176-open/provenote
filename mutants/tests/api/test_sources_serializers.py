from packages.core.domain.notebook import Asset, Source
from services.api.routers.sources_serializers import (
    build_source_list_response,
    build_source_response,
)


def test_build_source_list_response_with_command_metadata() -> None:
    row = {
        "id": "source:1",
        "title": "Source One",
        "topics": ["a", "b"],
        "asset": {"file_path": "/tmp/source-one.txt", "url": "https://example.com/one"},
        "embedded": True,
        "insights_count": 3,
        "created": "2026-03-01T00:00:00+00:00",
        "updated": "2026-03-01T00:01:00+00:00",
        "command": {
            "id": "command:1",
            "status": "completed",
            "error_message": None,
            "result": {
                "execution_metadata": {
                    "started_at": "2026-03-01T00:00:00+00:00",
                    "completed_at": "2026-03-01T00:00:10+00:00",
                }
            },
        },
    }

    response = build_source_list_response(row)

    assert response.id == "source:1"
    assert response.command_id == "command:1"
    assert response.status == "completed"
    assert response.processing_info == {
        "started_at": "2026-03-01T00:00:00+00:00",
        "completed_at": "2026-03-01T00:00:10+00:00",
        "error": None,
    }
    assert (
        response.asset is not None and response.asset.file_path == "/tmp/source-one.txt"
    )


def test_build_source_list_response_handles_non_dict_command() -> None:
    row = {
        "id": "source:2",
        "title": "Source Two",
        "topics": [],
        "asset": None,
        "embedded": False,
        "insights_count": 0,
        "created": "2026-03-01T00:00:00+00:00",
        "updated": "2026-03-01T00:01:00+00:00",
        "command": "command:legacy",
    }

    response = build_source_list_response(row)

    assert response.command_id == "command:legacy"
    assert response.status == "unknown"
    assert response.processing_info is None
    assert response.asset is None


def test_build_source_list_response_handles_missing_execution_metadata() -> None:
    row = {
        "id": "source:3",
        "title": "Source Three",
        "topics": [],
        "asset": {"file_path": None, "url": None},
        "embedded": False,
        "insights_count": 0,
        "created": "2026-03-01T00:00:00+00:00",
        "updated": "2026-03-01T00:01:00+00:00",
        "command": {
            "id": "command:3",
            "status": "failed",
            "error_message": "boom",
            "result": "not-a-dict",
        },
    }

    response = build_source_list_response(row)

    assert response.processing_info == {
        "started_at": None,
        "completed_at": None,
        "error": "boom",
    }


def test_build_source_response_sets_embedded_by_chunk_count() -> None:
    source = Source(
        id="source:4",
        title="Source Four",
        topics=None,
        asset=Asset(file_path="/tmp/source-four.txt", url=None),
        full_text="hello world",
        created="2026-03-01T00:00:00+00:00",
        updated="2026-03-01T00:01:00+00:00",
    )

    response = build_source_response(
        source,
        embedded_chunks=2,
        command_id="command:4",
        status="completed",
        processing_info={"started_at": "2026-03-01T00:00:00+00:00"},
        notebooks=["notebook:1"],
        file_available=True,
    )

    assert response.id == "source:4"
    assert response.embedded is True
    assert response.embedded_chunks == 2
    assert response.topics == []
    assert (
        response.asset is not None
        and response.asset.file_path == "/tmp/source-four.txt"
    )
    assert response.notebooks == ["notebook:1"]
    assert response.file_available is True
