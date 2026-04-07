import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from packages.core.exceptions import DatabaseOperationError, NotFoundError

embedding_stub = types.ModuleType("packages.core.utils.embedding")
embedding_stub.generate_embedding = lambda *args, **kwargs: None
embedding_stub.generate_embeddings = lambda *args, **kwargs: []
embedding_stub.mean_pool_embeddings = lambda *args, **kwargs: []
sys.modules.setdefault("packages.core.utils.embedding", embedding_stub)

import packages.core.utils.context_builder as context_builder


def test_context_item_calculates_token_count_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(context_builder, "token_count", lambda _: 123)

    item = context_builder.ContextItem(id="x", type="note", content={"text": "abc"})

    assert item.token_count == 123


def test_context_config_initializes_defaults() -> None:
    config = context_builder.ContextConfig()

    assert config.sources == {}
    assert config.notes == {}
    assert config.priority_weights == {"source": 100, "note": 50, "insight": 75}


@pytest.mark.asyncio
async def test_add_source_context_skips_when_inclusion_not_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder()
    source_get_mock = AsyncMock()
    monkeypatch.setattr(context_builder, "Source", SimpleNamespace(get=source_get_mock))

    await builder._add_source_context("1", "not in")

    source_get_mock.assert_not_called()
    assert builder.items == []


@pytest.mark.asyncio
async def test_add_source_context_adds_source_and_insights_with_prefixed_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder(include_insights=True)
    fake_insights = [
        SimpleNamespace(id="insight:1", insight_type="summary", content="s1"),
        SimpleNamespace(id="insight:2", insight_type="fact", content="s2"),
    ]
    fake_source = SimpleNamespace(
        id="source:42",
        get_context=AsyncMock(return_value={"body": "source context"}),
        get_insights=AsyncMock(return_value=fake_insights),
    )
    source_get_mock = AsyncMock(return_value=fake_source)
    monkeypatch.setattr(context_builder, "Source", SimpleNamespace(get=source_get_mock))

    await builder._add_source_context("42", "insights")

    source_get_mock.assert_awaited_once_with("source:42")
    assert len(builder.items) == 3
    assert builder.items[0].type == "source"
    assert builder.items[1].type == "insight"
    assert builder.items[2].type == "insight"


@pytest.mark.asyncio
async def test_add_source_context_uses_long_context_for_full_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder(include_insights=True)
    fake_source = SimpleNamespace(
        id="source:99",
        get_context=AsyncMock(return_value={"body": "long content"}),
        get_insights=AsyncMock(return_value=[]),
    )
    source_get_mock = AsyncMock(return_value=fake_source)
    monkeypatch.setattr(context_builder, "Source", SimpleNamespace(get=source_get_mock))

    await builder._add_source_context("source:99", "full content")

    fake_source.get_context.assert_awaited_once_with(context_size="long")
    fake_source.get_insights.assert_not_awaited()
    assert len(builder.items) == 1
    assert builder.items[0].type == "source"


@pytest.mark.asyncio
async def test_add_source_context_handles_not_found_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder()
    monkeypatch.setattr(
        context_builder,
        "Source",
        SimpleNamespace(get=AsyncMock(side_effect=NotFoundError("missing"))),
    )

    await builder._add_source_context("404", "insights")

    assert builder.items == []


@pytest.mark.asyncio
async def test_add_source_context_skips_when_source_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder()
    monkeypatch.setattr(
        context_builder, "Source", SimpleNamespace(get=AsyncMock(return_value=None))
    )

    await builder._add_source_context("missing", "insights")

    assert builder.items == []


@pytest.mark.asyncio
async def test_add_source_context_reraises_generic_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder()
    monkeypatch.setattr(
        context_builder,
        "Source",
        SimpleNamespace(get=AsyncMock(side_effect=RuntimeError("source boom"))),
    )

    with pytest.raises(RuntimeError, match="source boom"):
        await builder._add_source_context("x", "insights")


@pytest.mark.asyncio
async def test_add_notebook_context_uses_configured_sources_and_notes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = context_builder.ContextConfig(
        sources={"source:1": "insights", "source:2": "full content"},
        notes={"note:1": "full content", "note:2": "not in"},
    )
    builder = context_builder.ContextBuilder(
        notebook_id="notebook:1", context_config=config
    )
    builder._add_source_context = AsyncMock()
    builder._add_note_context = AsyncMock()
    notebook_get_mock = AsyncMock(return_value=SimpleNamespace())
    monkeypatch.setattr(
        context_builder, "Notebook", SimpleNamespace(get=notebook_get_mock)
    )

    await builder._add_notebook_context("notebook:1")

    notebook_get_mock.assert_awaited_once_with("notebook:1")
    assert builder._add_source_context.await_count == 2
    builder._add_source_context.assert_any_await("source:1", "insights")
    builder._add_source_context.assert_any_await("source:2", "full content")
    builder._add_note_context.assert_awaited_once_with("note:1", "full content")


@pytest.mark.asyncio
async def test_add_notebook_context_uses_default_notebook_sources_and_notes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder(notebook_id="notebook:1")
    builder._add_source_context = AsyncMock()
    builder._add_note_context = AsyncMock()
    notebook = SimpleNamespace(
        get_sources=AsyncMock(
            return_value=[SimpleNamespace(id="source:1"), SimpleNamespace(id=None)]
        ),
        get_notes=AsyncMock(
            return_value=[SimpleNamespace(id="note:1"), SimpleNamespace(id=None)]
        ),
    )
    monkeypatch.setattr(
        context_builder,
        "Notebook",
        SimpleNamespace(get=AsyncMock(return_value=notebook)),
    )

    await builder._add_notebook_context("notebook:1")

    builder._add_source_context.assert_awaited_once_with("source:1", "insights")
    builder._add_note_context.assert_awaited_once_with("note:1", "full content")


@pytest.mark.asyncio
async def test_add_notebook_context_skips_notes_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder(
        notebook_id="notebook:1", include_notes=False
    )
    builder._add_source_context = AsyncMock()
    builder._add_note_context = AsyncMock()
    notebook = SimpleNamespace(
        get_sources=AsyncMock(return_value=[SimpleNamespace(id="source:1")]),
        get_notes=AsyncMock(return_value=[SimpleNamespace(id="note:1")]),
    )
    monkeypatch.setattr(
        context_builder,
        "Notebook",
        SimpleNamespace(get=AsyncMock(return_value=notebook)),
    )

    await builder._add_notebook_context("notebook:1")

    builder._add_source_context.assert_awaited_once()
    builder._add_note_context.assert_not_called()


@pytest.mark.asyncio
async def test_add_notebook_context_raises_when_notebook_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder(notebook_id="notebook:missing")
    notebook_get_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(
        context_builder, "Notebook", SimpleNamespace(get=notebook_get_mock)
    )

    with pytest.raises(NotFoundError, match="Notebook notebook:missing not found"):
        await builder._add_notebook_context("notebook:missing")


@pytest.mark.asyncio
async def test_add_note_context_swallow_generic_exceptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder()
    broken_note = SimpleNamespace(
        id="note:1", get_context=lambda **_: (_ for _ in ()).throw(ValueError("boom"))
    )
    note_get_mock = AsyncMock(return_value=broken_note)
    monkeypatch.setattr(context_builder, "Note", SimpleNamespace(get=note_get_mock))

    await builder._add_note_context("1", "full content")

    assert builder.items == []
    note_get_mock.assert_awaited_once_with("note:1")


@pytest.mark.asyncio
async def test_add_note_context_skips_when_note_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder()
    monkeypatch.setattr(
        context_builder, "Note", SimpleNamespace(get=AsyncMock(return_value=None))
    )

    await builder._add_note_context("missing")

    assert builder.items == []


@pytest.mark.asyncio
async def test_add_note_context_handles_not_found_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder()
    monkeypatch.setattr(
        context_builder,
        "Note",
        SimpleNamespace(get=AsyncMock(side_effect=NotFoundError("gone"))),
    )

    await builder._add_note_context("gone")

    assert builder.items == []


@pytest.mark.asyncio
async def test_add_note_context_uses_short_context_for_non_full_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder()
    fake_note = SimpleNamespace(
        id="note:2", get_context=lambda **kwargs: {"size": kwargs["context_size"]}
    )
    note_get_mock = AsyncMock(return_value=fake_note)
    monkeypatch.setattr(context_builder, "Note", SimpleNamespace(get=note_get_mock))

    await builder._add_note_context("note:2", "summary")

    assert len(builder.items) == 1
    assert builder.items[0].type == "note"
    assert builder.items[0].content["size"] == "short"


@pytest.mark.asyncio
async def test_add_note_context_skips_when_not_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder()
    note_get_mock = AsyncMock()
    monkeypatch.setattr(context_builder, "Note", SimpleNamespace(get=note_get_mock))

    await builder._add_note_context("note:skip", "not in")

    note_get_mock.assert_not_called()
    assert builder.items == []


def test_remove_duplicates_keeps_first_item() -> None:
    builder = context_builder.ContextBuilder()
    builder.items = [
        context_builder.ContextItem(
            id="dup", type="source", content={"a": 1}, priority=100, token_count=3
        ),
        context_builder.ContextItem(
            id="dup", type="note", content={"b": 2}, priority=50, token_count=2
        ),
        context_builder.ContextItem(
            id="unique", type="note", content={"c": 3}, priority=40, token_count=1
        ),
    ]

    builder.remove_duplicates()

    assert [item.id for item in builder.items] == ["dup", "unique"]
    assert [item.type for item in builder.items] == ["source", "note"]


def test_truncate_to_fit_removes_low_priority_items_until_within_limit() -> None:
    builder = context_builder.ContextBuilder()
    builder.items = [
        context_builder.ContextItem(
            id="high", type="source", content={"x": 1}, priority=100, token_count=5
        ),
        context_builder.ContextItem(
            id="mid", type="note", content={"x": 2}, priority=50, token_count=5
        ),
        context_builder.ContextItem(
            id="low", type="insight", content={"x": 3}, priority=10, token_count=5
        ),
    ]
    builder.prioritize()

    builder.truncate_to_fit(8)

    assert [item.id for item in builder.items] == ["high"]
    assert sum(item.token_count or 0 for item in builder.items) <= 8


def test_truncate_to_fit_noop_when_limit_not_set() -> None:
    builder = context_builder.ContextBuilder()
    original_items = [
        context_builder.ContextItem(
            id="a", type="source", content={"x": 1}, priority=1, token_count=2
        )
    ]
    builder.items = list(original_items)

    builder.truncate_to_fit(0)

    assert builder.items == original_items


@pytest.mark.asyncio
async def test_build_wraps_internal_errors_as_database_operation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder(source_id="source:1")
    builder._add_source_context = AsyncMock(side_effect=RuntimeError("db failed"))
    builder._process_custom_params = AsyncMock()

    with pytest.raises(
        DatabaseOperationError, match="Failed to build context: db failed"
    ):
        await builder.build()


@pytest.mark.asyncio
async def test_build_success_formats_response_with_notebook_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = context_builder.ContextBuilder(notebook_id="notebook:1", max_tokens=100)
    builder._add_notebook_context = AsyncMock(
        side_effect=lambda _id: builder.items.extend(
            [
                context_builder.ContextItem(
                    id="source:1",
                    type="source",
                    content={"source": 1},
                    priority=100,
                    token_count=10,
                ),
                context_builder.ContextItem(
                    id="note:1",
                    type="note",
                    content={"note": 1},
                    priority=10,
                    token_count=5,
                ),
                context_builder.ContextItem(
                    id="insight:1",
                    type="insight",
                    content={"insight": 1},
                    priority=50,
                    token_count=8,
                ),
            ]
        )
    )
    builder._process_custom_params = AsyncMock()

    result = await builder.build()

    assert result["notebook_id"] == "notebook:1"
    assert result["metadata"]["source_count"] == 1
    assert result["metadata"]["note_count"] == 1
    assert result["metadata"]["insight_count"] == 1
    assert result["total_tokens"] == 23


@pytest.mark.asyncio
async def test_build_mixed_context_maps_ids_into_context_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def _fake_build(self: context_builder.ContextBuilder):
        captured["sources"] = self.context_config.sources
        captured["notes"] = self.context_config.notes
        captured["max_tokens"] = self.max_tokens
        captured["notebook_id"] = self.notebook_id
        return {"ok": True}

    monkeypatch.setattr(context_builder.ContextBuilder, "build", _fake_build)

    result = await context_builder.build_mixed_context(
        source_ids=["s1", "s2"],
        note_ids=["n1"],
        notebook_id="notebook:1",
        max_tokens=77,
    )

    assert result == {"ok": True}
    assert captured["sources"] == {"s1": "insights", "s2": "insights"}
    assert captured["notes"] == {"n1": "full content"}
    assert captured["max_tokens"] == 77
    assert captured["notebook_id"] == "notebook:1"


@pytest.mark.asyncio
async def test_process_custom_params_handles_custom_keys() -> None:
    builder = context_builder.ContextBuilder(custom_mode="x", custom_limit=3)

    await builder._process_custom_params()

    assert builder.params["custom_mode"] == "x"
    assert builder.params["custom_limit"] == 3


@pytest.mark.asyncio
async def test_build_notebook_context_convenience_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    build_mock = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(context_builder.ContextBuilder, "build", build_mock)

    result = await context_builder.build_notebook_context("notebook:1", max_tokens=5)

    assert result == {"ok": True}
    assert build_mock.await_count == 1


@pytest.mark.asyncio
async def test_build_source_context_convenience_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    build_mock = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(context_builder.ContextBuilder, "build", build_mock)

    result = await context_builder.build_source_context(
        "source:1", include_insights=False, max_tokens=9
    )

    assert result == {"ok": True}
    assert build_mock.await_count == 1
