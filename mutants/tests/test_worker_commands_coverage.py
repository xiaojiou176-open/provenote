from __future__ import annotations

import ipaddress
import socket
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel
from surreal_commands import ExecutionContext

from packages.core.application.commands.embedding_commands import (
    CreateInsightInput,
    EmbedInsightInput,
    EmbedNoteInput,
    EmbedSourceInput,
    RebuildEmbeddingsInput,
    collect_items_for_rebuild,
    create_insight_command,
    embed_insight_command,
    embed_note_command,
    embed_source_command,
    get_command_id,
    rebuild_embeddings_command,
)
from packages.core.application.commands.embedding_commands import (
    _record_command_failure as embedding_record_command_failure,
)
from packages.core.application.commands.example_commands import (
    DataAnalysisInput,
    analyze_data_command,
    process_text_command,
)
from packages.core.application.commands.podcast_commands import (
    PodcastGenerationInput,
    generate_podcast_command,
)
from packages.core.application.commands.podcast_commands import (
    full_model_dump as podcast_full_model_dump,
)
from packages.core.application.commands.source_commands import (
    RunTransformationInput,
    SourceProcessingInput,
    process_source_command,
    run_transformation_command,
    validate_source_link_url,
)
from packages.core.application.commands.source_commands import (
    _record_command_failure as source_record_command_failure,
)
from packages.core.application.commands.source_commands import (
    full_model_dump as source_full_model_dump,
)


@pytest.mark.asyncio
async def test_process_text_command_covers_all_supported_operations() -> None:
    upper = await process_text_command(
        input_data=type(
            "Input",
            (),
            {"text": "Hello", "operation": "uppercase", "delay_seconds": None},
        )()
    )
    lower = await process_text_command(
        input_data=type(
            "Input",
            (),
            {"text": "Hello", "operation": "lowercase", "delay_seconds": None},
        )()
    )
    reverse = await process_text_command(
        input_data=type(
            "Input",
            (),
            {"text": "Hello", "operation": "reverse", "delay_seconds": None},
        )()
    )
    count = await process_text_command(
        input_data=type(
            "Input",
            (),
            {"text": "one two three", "operation": "word_count", "delay_seconds": None},
        )()
    )

    assert upper.success and upper.processed_text == "HELLO"
    assert lower.success and lower.processed_text == "hello"
    assert reverse.success and reverse.processed_text == "olleH"
    assert count.success and count.word_count == 3


@pytest.mark.asyncio
async def test_process_text_command_returns_failure_for_unknown_operation() -> None:
    result = await process_text_command(
        input_data=type(
            "Input",
            (),
            {"text": "Hello", "operation": "unknown", "delay_seconds": None},
        )()
    )

    assert result.success is False
    assert "Unknown operation" in (result.error_message or "")


@pytest.mark.asyncio
async def test_analyze_data_command_success_and_empty_error_paths() -> None:
    success = await analyze_data_command(
        DataAnalysisInput(numbers=[1, 2, 3], analysis_type="basic")
    )
    failure = await analyze_data_command(
        DataAnalysisInput(numbers=[], analysis_type="basic")
    )

    assert success.success is True
    assert success.count == 3
    assert success.sum == 6
    assert success.average == 2
    assert success.min_value == 1
    assert success.max_value == 3

    assert failure.success is False
    assert failure.count == 0
    assert "No numbers provided" in (failure.error_message or "")


def test_get_command_id_handles_missing_execution_context() -> None:
    unknown = get_command_id(EmbedNoteInput(note_id="note:1"))
    known = get_command_id(
        EmbedNoteInput(
            note_id="note:1",
            execution_context=ExecutionContext(
                command_id="command:abc",
                execution_started_at=datetime.now(timezone.utc),
                app_name="open_notebook",
                command_name="embed_note",
                user_context=None,
            ),
        )
    )

    assert unknown == "unknown"
    assert known == "command:abc"


@pytest.mark.asyncio
async def test_collect_items_for_rebuild_handles_existing_and_all_modes() -> None:
    responses = [
        ["source:1", "source:2"],
        [{"id": "note:1"}],
        [{"id": "insight:1"}],
        [{"id": "source:3"}],
        [{"id": "note:2"}],
        [{"id": "insight:2"}],
    ]

    with patch(
        "packages.core.application.commands.embedding_commands.repo_query",
        new=AsyncMock(side_effect=responses),
    ):
        existing = await collect_items_for_rebuild("existing", True, True, True)
        all_mode = await collect_items_for_rebuild("all", True, True, True)

    assert existing == {
        "sources": ["source:1", "source:2"],
        "notes": ["note:1"],
        "insights": ["insight:1"],
    }
    assert all_mode == {
        "sources": ["source:3"],
        "notes": ["note:2"],
        "insights": ["insight:2"],
    }


@pytest.mark.asyncio
async def test_create_insight_command_success_and_value_error_paths() -> None:
    repo_query = AsyncMock(return_value=[{"id": "source_insight:1"}])
    submit_job = AsyncMock(return_value="command:embed-insight")
    with (
        patch(
            "packages.core.application.commands.embedding_commands.repo_query",
            new=repo_query,
        ),
        patch(
            "packages.core.application.commands.embedding_commands.CommandService.submit_command_job",
            new=submit_job,
        ),
    ):
        success = await create_insight_command(
            CreateInsightInput(
                source_id="source:1", insight_type="summary", content="hello"
            )
        )

    assert success.success is True
    assert success.insight_id == "source_insight:1"

    with patch(
        "packages.core.application.commands.embedding_commands.repo_query",
        new=AsyncMock(return_value=[]),
    ):
        failure = await create_insight_command(
            CreateInsightInput(
                source_id="source:1", insight_type="summary", content="hello"
            )
        )

    assert failure.success is False
    assert "no result returned" in (failure.error_message or "")


@pytest.mark.asyncio
async def test_embed_note_and_insight_commands_cover_success_and_validation_failures() -> (
    None
):
    note = SimpleNamespace(content="note body")
    insight = SimpleNamespace(content="insight body")

    with (
        patch(
            "packages.core.application.commands.embedding_commands.Note.get",
            new=AsyncMock(return_value=note),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.SourceInsight.get",
            new=AsyncMock(return_value=insight),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.generate_embedding",
            new=AsyncMock(return_value=[0.1, 0.2]),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.repo_query",
            new=AsyncMock(return_value=None),
        ),
    ):
        note_result = await embed_note_command(EmbedNoteInput(note_id="note:1"))
        insight_result = await embed_insight_command(
            EmbedInsightInput(insight_id="insight:1")
        )

    assert note_result.success is True
    assert insight_result.success is True

    with patch(
        "packages.core.application.commands.embedding_commands.Note.get",
        new=AsyncMock(return_value=None),
    ):
        note_missing = await embed_note_command(EmbedNoteInput(note_id="note:missing"))
    with patch(
        "packages.core.application.commands.embedding_commands.SourceInsight.get",
        new=AsyncMock(return_value=None),
    ):
        insight_missing = await embed_insight_command(
            EmbedInsightInput(insight_id="insight:missing")
        )
    with patch(
        "packages.core.application.commands.embedding_commands.SourceInsight.get",
        new=AsyncMock(return_value=SimpleNamespace(content="   ")),
    ):
        insight_empty = await embed_insight_command(
            EmbedInsightInput(insight_id="insight:empty")
        )

    assert note_missing.success is False
    assert "not found" in (note_missing.error_message or "")
    assert insight_missing.success is False
    assert "not found" in (insight_missing.error_message or "")
    assert insight_empty.success is False
    assert "no content" in (insight_empty.error_message or "")

    with (
        patch(
            "packages.core.application.commands.embedding_commands.SourceInsight.get",
            new=AsyncMock(return_value=SimpleNamespace(content="content")),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.generate_embedding",
            new=AsyncMock(side_effect=RuntimeError("retry insight")),
        ),
    ):
        with pytest.raises(RuntimeError, match="retry insight"):
            await embed_insight_command(EmbedInsightInput(insight_id="insight:retry"))


@pytest.mark.asyncio
async def test_embed_source_command_success_and_embedding_count_mismatch() -> None:
    source = SimpleNamespace(
        full_text="alpha beta gamma",
        asset=SimpleNamespace(file_path="source.md"),
    )

    with (
        patch(
            "packages.core.application.commands.embedding_commands.Source.get",
            new=AsyncMock(return_value=source),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.repo_query",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.detect_content_type",
            return_value=SimpleNamespace(value="markdown"),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.chunk_text",
            return_value=["c1", "c2"],
        ),
        patch(
            "packages.core.application.commands.embedding_commands.generate_embeddings",
            new=AsyncMock(return_value=[[1.0], [2.0]]),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.repo_insert",
            new=AsyncMock(return_value=None),
        ),
    ):
        success = await embed_source_command(EmbedSourceInput(source_id="source:1"))

    assert success.success is True
    assert success.chunks_created == 2

    with (
        patch(
            "packages.core.application.commands.embedding_commands.Source.get",
            new=AsyncMock(return_value=source),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.repo_query",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.detect_content_type",
            return_value=SimpleNamespace(value="markdown"),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.chunk_text",
            return_value=["c1", "c2"],
        ),
        patch(
            "packages.core.application.commands.embedding_commands.generate_embeddings",
            new=AsyncMock(return_value=[[1.0]]),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.repo_insert",
            new=AsyncMock(return_value=None),
        ),
    ):
        mismatch = await embed_source_command(EmbedSourceInput(source_id="source:1"))

    assert mismatch.success is False
    assert "Embedding count mismatch" in (mismatch.error_message or "")

    no_asset_source = SimpleNamespace(full_text="alpha beta", asset=None)
    with (
        patch(
            "packages.core.application.commands.embedding_commands.Source.get",
            new=AsyncMock(return_value=no_asset_source),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.repo_query",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.detect_content_type",
            return_value=SimpleNamespace(value="plain"),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.chunk_text",
            return_value=[],
        ),
    ):
        no_chunks = await embed_source_command(
            EmbedSourceInput(source_id="source:no-chunks")
        )

    assert no_chunks.success is False
    assert "No chunks created" in (no_chunks.error_message or "")


@pytest.mark.asyncio
async def test_rebuild_embeddings_command_covers_empty_and_partial_submission_failures() -> (
    None
):
    with (
        patch(
            "packages.core.application.commands.embedding_commands.model_manager.get_embedding_model",
            new=AsyncMock(return_value="gemini-embedding-001"),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.collect_items_for_rebuild",
            new=AsyncMock(return_value={"sources": [], "notes": [], "insights": []}),
        ),
    ):
        empty_result = await rebuild_embeddings_command(
            RebuildEmbeddingsInput(
                mode="existing",
                include_sources=True,
                include_notes=True,
                include_insights=True,
            )
        )

    assert empty_result.success is True
    assert empty_result.total_items == 0

    async def _submit(module_name: str, command_name: str, command_args: dict) -> str:
        if command_args.get("note_id") == "note:bad":
            raise RuntimeError("submit failed")
        return f"{module_name}:{command_name}"

    with (
        patch(
            "packages.core.application.commands.embedding_commands.model_manager.get_embedding_model",
            new=AsyncMock(return_value="gemini-embedding-001"),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.collect_items_for_rebuild",
            new=AsyncMock(
                return_value={
                    "sources": ["source:1"],
                    "notes": ["note:good", "note:bad"],
                    "insights": ["insight:1"],
                }
            ),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.CommandService.submit_command_job",
            new=AsyncMock(side_effect=_submit),
        ),
    ):
        partial = await rebuild_embeddings_command(
            RebuildEmbeddingsInput(
                mode="all",
                include_sources=True,
                include_notes=True,
                include_insights=True,
            )
        )

    assert partial.success is True
    assert partial.total_items == 4
    assert partial.jobs_submitted == 3
    assert partial.failed_submissions == 1
    assert partial.sources_submitted == 1


def test_source_and_podcast_full_model_dump_cover_dict_and_list_shapes() -> None:
    class _Model(BaseModel):
        value: int

    payload = {
        "items": [{"nested": [_Model(value=1), {"value": 2}]}],
        "plain": "ok",
    }

    assert podcast_full_model_dump(payload) == {
        "items": [{"nested": [{"value": 1}, {"value": 2}]}],
        "plain": "ok",
    }
    assert source_full_model_dump(payload) == {
        "items": [{"nested": [{"value": 1}, {"value": 2}]}],
        "plain": "ok",
    }


def test_validate_source_link_url_rejects_missing_hostname_and_private_ip() -> None:
    with pytest.raises(ValueError, match="hostname could not be determined"):
        validate_source_link_url("https:///missing-host")

    with pytest.raises(ValueError, match="blocked loopback/private"):
        validate_source_link_url("https://127.0.0.1/path")

    assert (
        __import__(
            "packages.core.application.commands.source_commands",
            fromlist=["_is_disallowed_source_ip"],
        )._is_disallowed_source_ip(ipaddress.ip_address("::ffff:127.0.0.1"))
        is True
    )


def test_validate_source_link_url_handles_invalid_dns_candidates_and_empty_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "packages.core.application.commands.source_commands.socket.getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, None, None, None, ("not-an-ip", 0)),
            (socket.AF_INET, None, None, None, ("8.8.8.8", 0)),
        ],
    )
    assert (
        validate_source_link_url("https://safe-host.example/path")
        == "https://safe-host.example/path"
    )

    monkeypatch.setattr(
        "packages.core.application.commands.source_commands.socket.getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, None, None, None, ("not-an-ip", 0))
        ],
    )
    with pytest.raises(ValueError, match="did not resolve to an IP address"):
        validate_source_link_url("https://safe-host.example/path")


@pytest.mark.asyncio
async def test_process_source_command_success_and_validation_paths() -> None:
    source = SimpleNamespace(id="source:1", command=None, save=AsyncMock())
    processed_source = SimpleNamespace(
        id="source:done", get_insights=AsyncMock(return_value=[1, 2])
    )
    transformation = SimpleNamespace(id="transformation:1")

    with (
        patch(
            "packages.core.application.commands.source_commands.validate_source_link_url",
            return_value="https://example.com",
        ),
        patch(
            "packages.core.application.commands.source_commands.Transformation.get",
            new=AsyncMock(return_value=transformation),
        ),
        patch(
            "packages.core.application.commands.source_commands.Source.get",
            new=AsyncMock(return_value=source),
        ),
        patch(
            "packages.core.application.commands.source_commands.source_graph.ainvoke",
            new=AsyncMock(return_value={"source": processed_source}),
        ),
    ):
        result = await process_source_command(
            SourceProcessingInput(
                source_id="source:1",
                content_state={"url": "https://example.com"},
                notebook_ids=["notebook:1"],
                transformations=["transformation:1"],
                embed=True,
                execution_context=ExecutionContext(
                    command_id="command:1",
                    execution_started_at=datetime.now(timezone.utc),
                    app_name="open_notebook",
                    command_name="process_source",
                    user_context=None,
                ),
            )
        )

    assert result.success is True
    assert result.source_id == "source:done"
    assert result.insights_created == 2
    source.save.assert_awaited_once()

    with patch(
        "packages.core.application.commands.source_commands._record_command_failure",
        new=AsyncMock(),
    ) as record_failure:
        bad_url_type = await process_source_command(
            SourceProcessingInput(
                source_id="source:1",
                content_state={"url": 123},
                notebook_ids=[],
                transformations=[],
                embed=False,
            )
        )

    assert bad_url_type.success is False
    assert "expected string value" in (bad_url_type.error_message or "")
    record_failure.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_source_command_missing_dependencies_and_transient_error_paths() -> (
    None
):
    with patch(
        "packages.core.application.commands.source_commands.Transformation.get",
        new=AsyncMock(return_value=None),
    ):
        missing_transformation = await process_source_command(
            SourceProcessingInput(
                source_id="source:1",
                content_state={"content": "hello"},
                notebook_ids=[],
                transformations=["transformation:missing"],
                embed=False,
            )
        )
    assert missing_transformation.success is False
    assert "Transformation 'transformation:missing' not found" in (
        missing_transformation.error_message or ""
    )

    with (
        patch(
            "packages.core.application.commands.source_commands.Transformation.get",
            new=AsyncMock(return_value=SimpleNamespace(id="t1")),
        ),
        patch(
            "packages.core.application.commands.source_commands.Source.get",
            new=AsyncMock(return_value=None),
        ),
    ):
        missing_source = await process_source_command(
            SourceProcessingInput(
                source_id="source:missing",
                content_state={"content": "hello"},
                notebook_ids=[],
                transformations=["transformation:1"],
                embed=False,
            )
        )
    assert missing_source.success is False
    assert "Source 'source:missing' not found" in (missing_source.error_message or "")

    with (
        patch(
            "packages.core.application.commands.source_commands.Transformation.get",
            new=AsyncMock(return_value=SimpleNamespace(id="t1")),
        ),
        patch(
            "packages.core.application.commands.source_commands.Source.get",
            new=AsyncMock(
                return_value=SimpleNamespace(
                    id="source:1", command=None, save=AsyncMock()
                )
            ),
        ),
        patch(
            "packages.core.application.commands.source_commands.source_graph.ainvoke",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ),
    ):
        with pytest.raises(RuntimeError, match="boom"):
            await process_source_command(
                SourceProcessingInput(
                    source_id="source:1",
                    content_state={"content": "hello"},
                    notebook_ids=[],
                    transformations=["transformation:1"],
                    embed=False,
                )
            )


@pytest.mark.asyncio
async def test_run_transformation_command_success_failure_and_transient_paths() -> None:
    source = SimpleNamespace(id="source:1")
    transformation = SimpleNamespace(id="transformation:1")

    with (
        patch(
            "packages.core.application.commands.source_commands.Source.get",
            new=AsyncMock(return_value=source),
        ),
        patch(
            "packages.core.application.commands.source_commands.Transformation.get",
            new=AsyncMock(return_value=transformation),
        ),
        patch(
            "packages.core.application.commands.source_commands.transform_graph.ainvoke",
            new=AsyncMock(return_value=None),
        ),
    ):
        success = await run_transformation_command(
            RunTransformationInput(
                source_id="source:1", transformation_id="transformation:1"
            )
        )
    assert success.success is True

    with patch(
        "packages.core.application.commands.source_commands.Source.get",
        new=AsyncMock(return_value=None),
    ):
        missing_source = await run_transformation_command(
            RunTransformationInput(
                source_id="source:missing", transformation_id="transformation:1"
            )
        )
    assert missing_source.success is False
    assert "Source 'source:missing' not found" in (missing_source.error_message or "")

    with (
        patch(
            "packages.core.application.commands.source_commands.Source.get",
            new=AsyncMock(return_value=source),
        ),
        patch(
            "packages.core.application.commands.source_commands.Transformation.get",
            new=AsyncMock(return_value=None),
        ),
    ):
        missing_transformation = await run_transformation_command(
            RunTransformationInput(
                source_id="source:1", transformation_id="transformation:missing"
            )
        )
    assert missing_transformation.success is False
    assert "Transformation 'transformation:missing' not found" in (
        missing_transformation.error_message or ""
    )

    with (
        patch(
            "packages.core.application.commands.source_commands.Source.get",
            new=AsyncMock(return_value=source),
        ),
        patch(
            "packages.core.application.commands.source_commands.Transformation.get",
            new=AsyncMock(return_value=transformation),
        ),
        patch(
            "packages.core.application.commands.source_commands.transform_graph.ainvoke",
            new=AsyncMock(side_effect=RuntimeError("retry me")),
        ),
    ):
        with pytest.raises(RuntimeError, match="retry me"):
            await run_transformation_command(
                RunTransformationInput(
                    source_id="source:1", transformation_id="transformation:1"
                )
            )


@pytest.mark.asyncio
async def test_generate_podcast_command_missing_profiles_and_runtime_error_paths(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    execution_context = ExecutionContext(
        command_id="command:podcast",
        execution_started_at=datetime.now(timezone.utc),
        app_name="open_notebook",
        command_name="generate_podcast",
        user_context=None,
    )

    with (
        patch(
            "packages.core.application.commands.podcast_commands.EpisodeProfile.get_by_name",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.CommandService.record_command_failure_event",
            new=AsyncMock(),
        ) as record_failure,
    ):
        with pytest.raises(ValueError, match="Episode profile 'missing' not found"):
            await generate_podcast_command(
                PodcastGenerationInput(
                    episode_profile="missing",
                    speaker_profile="speaker",
                    episode_name="episode",
                    content="content",
                    execution_context=execution_context,
                )
            )
    record_failure.assert_awaited_once()

    episode_profile = SimpleNamespace(
        name="google-ep",
        speaker_config="speaker-1",
        outline_provider="google",
        transcript_provider="google",
        default_briefing="brief",
        model_dump=lambda: {"name": "google-ep"},
    )
    speaker_profile = SimpleNamespace(
        name="speaker-1",
        tts_provider="google",
        model_dump=lambda: {"name": "speaker-1"},
    )
    monkeypatch.setattr(
        "services.api.podcast_service.PODCAST_EPISODES_OUTPUT_DIR",
        (tmp_path / "podcasts").resolve(),
    )

    with (
        patch(
            "packages.core.application.commands.podcast_commands.EpisodeProfile.get_by_name",
            new=AsyncMock(return_value=episode_profile),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.SpeakerProfile.get_by_name",
            new=AsyncMock(return_value=speaker_profile),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.repo_query",
            new=AsyncMock(return_value=[{"name": "profile"}]),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.PodcastEpisode.save",
            new=AsyncMock(),
        ),
        patch("packages.core.application.commands.podcast_commands.configure"),
        patch(
            "packages.core.application.commands.podcast_commands.create_podcast",
            new=AsyncMock(side_effect=RuntimeError("Invalid json output")),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.CommandService.record_command_failure_event",
            new=AsyncMock(),
        ) as record_failure,
    ):
        with pytest.raises(RuntimeError, match="Gemini-compatible"):
            await generate_podcast_command(
                PodcastGenerationInput(
                    episode_profile="google-ep",
                    speaker_profile="speaker-1",
                    episode_name="episode",
                    content="content",
                    briefing_suffix="extra",
                    execution_context=execution_context,
                )
            )
    assert record_failure.await_count == 1

    episode_profile = SimpleNamespace(
        name="google-ep",
        speaker_config="speaker-1",
        outline_provider="google",
        transcript_provider="google",
        default_briefing="brief",
        model_dump=lambda: {"name": "google-ep"},
    )
    speaker_profile = SimpleNamespace(
        name="speaker-1",
        tts_provider="google",
        model_dump=lambda: {"name": "speaker-1"},
    )
    with (
        patch(
            "packages.core.application.commands.podcast_commands.EpisodeProfile.get_by_name",
            new=AsyncMock(return_value=episode_profile),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.SpeakerProfile.get_by_name",
            new=AsyncMock(return_value=speaker_profile),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.repo_query",
            new=AsyncMock(side_effect=[[{"name": "ep"}], [{"name": "speaker"}]]),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.PodcastEpisode.save",
            new=AsyncMock(),
        ),
        patch("packages.core.application.commands.podcast_commands.configure"),
        patch(
            "packages.core.application.commands.podcast_commands.create_podcast",
            new=AsyncMock(side_effect=RuntimeError("upstream unavailable")),
        ),
    ):
        with pytest.raises(RuntimeError, match="upstream unavailable"):
            await generate_podcast_command(
                PodcastGenerationInput(
                    episode_profile="google-ep",
                    speaker_profile="speaker-1",
                    episode_name="episode",
                    content="content",
                )
            )


@pytest.mark.asyncio
async def test_generate_podcast_command_handles_missing_audio_path_and_speaker_profile() -> (
    None
):
    episode_profile = SimpleNamespace(
        name="google-ep",
        speaker_config="speaker-1",
        outline_provider="google",
        transcript_provider="google",
        default_briefing="brief",
        model_dump=lambda: {"name": "google-ep"},
    )
    with (
        patch(
            "packages.core.application.commands.podcast_commands.EpisodeProfile.get_by_name",
            new=AsyncMock(return_value=episode_profile),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.SpeakerProfile.get_by_name",
            new=AsyncMock(return_value=None),
        ),
    ):
        with pytest.raises(ValueError, match="Speaker profile 'speaker-1' not found"):
            await generate_podcast_command(
                PodcastGenerationInput(
                    episode_profile="google-ep",
                    speaker_profile="speaker-1",
                    episode_name="episode",
                    content="content",
                )
            )

    speaker_profile = SimpleNamespace(
        name="speaker-1",
        tts_provider="google",
        model_dump=lambda: {"name": "speaker-1"},
    )
    episode_record = SimpleNamespace(
        id="podcast_episode:1",
        audio_file=None,
        transcript=None,
        outline=None,
        save=AsyncMock(),
    )
    with (
        patch(
            "packages.core.application.commands.podcast_commands.EpisodeProfile.get_by_name",
            new=AsyncMock(return_value=episode_profile),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.SpeakerProfile.get_by_name",
            new=AsyncMock(return_value=speaker_profile),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.repo_query",
            new=AsyncMock(side_effect=[[{"name": "ep"}], [{"name": "speaker"}]]),
        ),
        patch(
            "packages.core.application.commands.podcast_commands.PodcastEpisode",
            return_value=episode_record,
        ),
        patch("packages.core.application.commands.podcast_commands.configure"),
        patch(
            "packages.core.application.commands.podcast_commands.create_podcast",
            new=AsyncMock(return_value={"transcript": None, "outline": None}),
        ),
    ):
        result = await generate_podcast_command(
            PodcastGenerationInput(
                episode_profile="google-ep",
                speaker_profile="speaker-1",
                episode_name="episode",
                content="content",
            )
        )
    assert result.success is True
    assert result.audio_file_path is None


@pytest.mark.asyncio
async def test_embedding_command_transient_and_rebuild_failure_paths() -> None:
    source = SimpleNamespace(
        full_text="alpha", asset=SimpleNamespace(file_path="source.md")
    )
    with (
        patch(
            "packages.core.application.commands.embedding_commands.Source.get",
            new=AsyncMock(return_value=source),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.repo_query",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.detect_content_type",
            return_value=SimpleNamespace(value="markdown"),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.chunk_text",
            return_value=["c1"],
        ),
        patch(
            "packages.core.application.commands.embedding_commands.generate_embeddings",
            new=AsyncMock(side_effect=RuntimeError("retry")),
        ),
    ):
        with pytest.raises(RuntimeError, match="retry"):
            await embed_source_command(EmbedSourceInput(source_id="source:1"))

    with (
        patch(
            "packages.core.application.commands.embedding_commands.model_manager.get_embedding_model",
            new=AsyncMock(return_value=None),
        ),
    ):
        no_model = await rebuild_embeddings_command(
            RebuildEmbeddingsInput(
                mode="existing",
                include_sources=True,
                include_notes=False,
                include_insights=False,
            )
        )
    assert no_model.success is False
    assert "No embedding model configured" in (no_model.error_message or "")

    many_sources = [f"source:{i}" for i in range(50)]
    with (
        patch(
            "packages.core.application.commands.embedding_commands.model_manager.get_embedding_model",
            new=AsyncMock(return_value="gemini-embedding-001"),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.collect_items_for_rebuild",
            new=AsyncMock(
                return_value={"sources": many_sources, "notes": [], "insights": []}
            ),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.CommandService.submit_command_job",
            new=AsyncMock(return_value="command:ok"),
        ),
    ):
        bulk = await rebuild_embeddings_command(
            RebuildEmbeddingsInput(
                mode="all",
                include_sources=True,
                include_notes=False,
                include_insights=False,
            )
        )
    assert bulk.success is True
    assert bulk.total_items == 50
    assert bulk.jobs_submitted == 50

    with patch(
        "packages.core.application.commands.embedding_commands.repo_query",
        new=AsyncMock(return_value=[]),
    ):
        empty_existing = await collect_items_for_rebuild("existing", True, False, False)
    assert empty_existing == {"sources": [], "notes": [], "insights": []}

    blank_note = SimpleNamespace(content="   ")
    with patch(
        "packages.core.application.commands.embedding_commands.Note.get",
        new=AsyncMock(return_value=blank_note),
    ):
        blank_note_result = await embed_note_command(
            EmbedNoteInput(note_id="note:blank")
        )
    assert blank_note_result.success is False
    assert "no content" in (blank_note_result.error_message or "")

    with (
        patch(
            "packages.core.application.commands.embedding_commands.Note.get",
            new=AsyncMock(return_value=SimpleNamespace(content="content")),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.generate_embedding",
            new=AsyncMock(side_effect=RuntimeError("retry note")),
        ),
    ):
        with pytest.raises(RuntimeError, match="retry note"):
            await embed_note_command(EmbedNoteInput(note_id="note:retry"))

    with patch(
        "packages.core.application.commands.embedding_commands.Source.get",
        new=AsyncMock(return_value=None),
    ):
        missing_source = await embed_source_command(
            EmbedSourceInput(source_id="source:missing")
        )
    assert missing_source.success is False
    assert "not found" in (missing_source.error_message or "")

    with patch(
        "packages.core.application.commands.embedding_commands.Source.get",
        new=AsyncMock(
            return_value=SimpleNamespace(
                full_text="   ", asset=SimpleNamespace(file_path="source.md")
            )
        ),
    ):
        blank_source = await embed_source_command(
            EmbedSourceInput(source_id="source:blank")
        )
    assert blank_source.success is False
    assert "no text" in (blank_source.error_message or "")

    with (
        patch(
            "packages.core.application.commands.embedding_commands.repo_query",
            new=AsyncMock(return_value=[{}]),
        ),
    ):
        missing_id = await create_insight_command(
            CreateInsightInput(
                source_id="source:1", insight_type="summary", content="hello"
            )
        )
    assert missing_id.success is False
    assert "no ID in result" in (missing_id.error_message or "")

    with patch(
        "packages.core.application.commands.embedding_commands.repo_query",
        new=AsyncMock(side_effect=RuntimeError("retry create")),
    ):
        with pytest.raises(RuntimeError, match="retry create"):
            await create_insight_command(
                CreateInsightInput(
                    source_id="source:1", insight_type="summary", content="hello"
                )
            )

    note_ids = [f"note:{i}" for i in range(50)]
    insight_ids = [f"insight:{i}" for i in range(50)]
    with (
        patch(
            "packages.core.application.commands.embedding_commands.model_manager.get_embedding_model",
            new=AsyncMock(return_value="gemini-embedding-001"),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.collect_items_for_rebuild",
            new=AsyncMock(
                return_value={"sources": [], "notes": note_ids, "insights": insight_ids}
            ),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.CommandService.submit_command_job",
            new=AsyncMock(return_value="command:ok"),
        ),
    ):
        note_and_insight_bulk = await rebuild_embeddings_command(
            RebuildEmbeddingsInput(
                mode="all",
                include_sources=False,
                include_notes=True,
                include_insights=True,
            )
        )
    assert note_and_insight_bulk.success is True
    assert note_and_insight_bulk.notes_submitted == 50
    assert note_and_insight_bulk.insights_submitted == 50

    with (
        patch(
            "packages.core.application.commands.embedding_commands.model_manager.get_embedding_model",
            new=AsyncMock(return_value="gemini-embedding-001"),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.collect_items_for_rebuild",
            new=AsyncMock(return_value={"sources": [], "notes": [], "insights": []}),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.CommandService.submit_command_job",
            new=AsyncMock(),
        ),
    ):
        skips = await rebuild_embeddings_command(
            RebuildEmbeddingsInput(
                mode="all",
                include_sources=False,
                include_notes=False,
                include_insights=False,
            )
        )
    assert skips.success is True
    assert skips.total_items == 0

    with (
        patch(
            "packages.core.application.commands.embedding_commands.model_manager.get_embedding_model",
            new=AsyncMock(return_value="gemini-embedding-001"),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.collect_items_for_rebuild",
            new=AsyncMock(
                return_value={"sources": [], "notes": ["note:1"], "insights": []}
            ),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.CommandService.submit_command_job",
            new=AsyncMock(side_effect=RuntimeError("submit note failed")),
        ),
    ):
        failed_note = await rebuild_embeddings_command(
            RebuildEmbeddingsInput(
                mode="all",
                include_sources=False,
                include_notes=True,
                include_insights=False,
            )
        )
    assert failed_note.success is True
    assert failed_note.failed_submissions == 1

    with (
        patch(
            "packages.core.application.commands.embedding_commands.model_manager.get_embedding_model",
            new=AsyncMock(return_value="gemini-embedding-001"),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.collect_items_for_rebuild",
            new=AsyncMock(
                return_value={"sources": [], "notes": [], "insights": ["insight:1"]}
            ),
        ),
        patch(
            "packages.core.application.commands.embedding_commands.CommandService.submit_command_job",
            new=AsyncMock(side_effect=RuntimeError("submit insight failed")),
        ),
    ):
        failed_insight = await rebuild_embeddings_command(
            RebuildEmbeddingsInput(
                mode="all",
                include_sources=False,
                include_notes=False,
                include_insights=True,
            )
        )
    assert failed_insight.success is True
    assert failed_insight.failed_submissions == 1


@pytest.mark.asyncio
async def test_worker_record_failure_helpers_forward_execution_context() -> None:
    execution_context = ExecutionContext(
        command_id="command:ctx",
        execution_started_at=datetime.now(timezone.utc),
        app_name="open_notebook",
        command_name="test",
        user_context=None,
    )
    input_with_context = EmbedNoteInput(
        note_id="note:1", execution_context=execution_context
    )

    with patch(
        "packages.core.application.commands.embedding_commands.CommandService.record_command_failure_event",
        new=AsyncMock(),
    ) as embedding_record:
        await embedding_record_command_failure(
            input_with_context,
            command_name="embed_note",
            error_message="boom",
        )
    embedding_record.assert_awaited_once()

    with patch(
        "packages.core.application.commands.source_commands.CommandService.record_command_failure_event",
        new=AsyncMock(),
    ) as source_record:
        await source_record_command_failure(
            input_with_context,
            command_name="process_source",
            error_message="boom",
        )
    source_record.assert_awaited_once()
