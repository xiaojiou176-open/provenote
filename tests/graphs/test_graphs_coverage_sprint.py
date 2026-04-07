from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from packages.core.exceptions import OpenNotebookError
from packages.core.graphs import auditable_transformation as auditable_graph
from packages.core.graphs import chat as chat_graph
from packages.core.graphs import prompt as prompt_graph
from packages.core.graphs import transformation as transformation_graph


class _ImmediateFuture:
    def __init__(self, value):
        self._value = value

    def result(self):
        return self._value


class _ImmediateExecutor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def submit(self, fn):
        return _ImmediateFuture(fn())


def _fake_artifact(label: str) -> SimpleNamespace:
    class _Dumpable:
        def __init__(self, value: dict, **attrs):
            self._value = value
            for key, attr_value in attrs.items():
                setattr(self, key, attr_value)

        def model_dump(self) -> dict:
            return self._value

    return SimpleNamespace(
        model_id=f"model-{label}",
        language="zh-CN",
        near_dedup_threshold=0.97,
        source_paragraphs=[_Dumpable({"pid": f"P-{label}"}, pid=f"P-{label}")],
        sections=[_Dumpable({"title": f"Section-{label}"})],
        claims=[_Dumpable({"text": f"Claim-{label}"})],
        dedup_entries=[_Dumpable({"pid": f"P-{label}", "status": "core"})],
        metrics=_Dumpable({"coverage_rate": 1.0}),
        coverage_json=_Dumpable({"covered_pids": 1}),
        dedup_json=_Dumpable({"group_count": 0}),
        result_markdown=f"markdown-{label}",
    )


def test_chat_call_model_with_messages_uses_asyncio_run_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provision_mock = AsyncMock()
    fake_model = SimpleNamespace(
        invoke=lambda payload: AIMessage(content="<think>hidden</think>clean answer")
    )
    provision_mock.return_value = fake_model

    monkeypatch.setattr(chat_graph, "provision_langchain_model", provision_mock)
    monkeypatch.setattr(
        chat_graph.asyncio,
        "get_running_loop",
        MagicMock(side_effect=RuntimeError("no loop")),
    )
    monkeypatch.setattr(
        chat_graph.Prompter,
        "render",
        lambda self, data: "system-prompt",
    )

    result = chat_graph.call_model_with_messages(
        {
            "messages": [AIMessage(content="hello")],
            "model_override": "state-model",
        },
        RunnableConfig(configurable={"model_id": "config-model"}),
    )

    assert result["messages"].content == "clean answer"
    provision_mock.assert_awaited_once()
    assert provision_mock.await_args.args[1] == "config-model"


def test_chat_call_model_with_messages_uses_threadpool_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provision_mock = AsyncMock(
        return_value=SimpleNamespace(
            invoke=lambda payload: AIMessage(content="thread-path-response")
        )
    )
    monkeypatch.setattr(chat_graph, "provision_langchain_model", provision_mock)
    monkeypatch.setattr(chat_graph.asyncio, "get_running_loop", lambda: object())
    monkeypatch.setattr(
        "concurrent.futures.ThreadPoolExecutor",
        _ImmediateExecutor,
    )
    monkeypatch.setattr(
        chat_graph.Prompter,
        "render",
        lambda self, data: "system-prompt",
    )

    result = chat_graph.call_model_with_messages(
        {
            "messages": [AIMessage(content="hello")],
            "model_override": "state-only-model",
        },
        RunnableConfig(configurable={}),
    )

    assert result["messages"].content == "thread-path-response"
    assert provision_mock.await_args.args[1] == "state-only-model"


def test_chat_call_model_with_messages_error_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        chat_graph,
        "provision_langchain_model",
        AsyncMock(side_effect=OpenNotebookError("rethrow-me")),
    )
    monkeypatch.setattr(
        chat_graph.asyncio,
        "get_running_loop",
        MagicMock(side_effect=RuntimeError("no loop")),
    )
    monkeypatch.setattr(chat_graph.Prompter, "render", lambda self, data: "sys")

    with pytest.raises(OpenNotebookError, match="rethrow-me"):
        chat_graph.call_model_with_messages(
            {"messages": [], "model_override": "m"},
            RunnableConfig(configurable={}),
        )

    class _ClassifiedError(Exception):
        pass

    monkeypatch.setattr(
        chat_graph,
        "provision_langchain_model",
        AsyncMock(side_effect=RuntimeError("boom")),
    )
    monkeypatch.setattr(
        chat_graph,
        "classify_error",
        lambda exc: (_ClassifiedError, "friendly-message"),
    )

    with pytest.raises(_ClassifiedError, match="friendly-message"):
        chat_graph.call_model_with_messages(
            {"messages": [], "model_override": "m"},
            RunnableConfig(configurable={}),
        )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('{"a": 1}', {"a": 1}),
        ('prefix {"a": 2} suffix', {"a": 2}),
        ('["x"]', None),
        ("no-json-here", None),
    ],
)
def test_auditable_extract_json_payload(raw: str, expected: dict | None) -> None:
    assert auditable_graph._extract_json_payload(raw) == expected


@pytest.mark.asyncio
async def test_auditable_generate_llm_output_handles_invalid_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chain = SimpleNamespace(
        ainvoke=AsyncMock(return_value=SimpleNamespace(content="definitely-not-json"))
    )
    monkeypatch.setattr(
        auditable_graph,
        "provision_langchain_model",
        AsyncMock(return_value=chain),
    )

    result = await auditable_graph._generate_llm_output(
        model_id="m1",
        input_text="input",
        candidate_pids=["P1"],
    )

    assert result is None


@pytest.mark.asyncio
async def test_run_auditable_transformation_prefers_llm_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_artifact = _fake_artifact("base")
    llm_artifact = _fake_artifact("llm")
    build_mock = MagicMock(side_effect=[base_artifact, llm_artifact])
    monkeypatch.setattr(auditable_graph, "build_auditable_artifact", build_mock)
    monkeypatch.setattr(
        auditable_graph,
        "_generate_llm_output",
        AsyncMock(return_value=SimpleNamespace(sections=[], claims=[])),
    )

    result = await auditable_graph.run_auditable_transformation(
        {"input_text": "hello world"}
    )

    assert result["output"]["model_id"] == "model-llm"
    assert build_mock.call_count == 2
    assert "llm_output" in build_mock.call_args_list[1].kwargs


@pytest.mark.asyncio
async def test_run_auditable_transformation_falls_back_on_llm_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_artifact = _fake_artifact("fallback")
    monkeypatch.setattr(
        auditable_graph,
        "build_auditable_artifact",
        MagicMock(return_value=base_artifact),
    )
    monkeypatch.setattr(
        auditable_graph,
        "_generate_llm_output",
        AsyncMock(side_effect=RuntimeError("llm failed")),
    )
    warning_mock = MagicMock()
    monkeypatch.setattr(auditable_graph.logger, "warning", warning_mock)

    result = await auditable_graph.run_auditable_transformation(
        {"input_text": "hello world"}
    )

    assert result["output"]["model_id"] == "model-fallback"
    warning_mock.assert_called_once()


def test_transformation_prompt_pack_resolution_and_input_parts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    prompt_file = tmp_path / "extract.jinja"
    prompt_file.write_text("PACK CONTENT", encoding="utf-8")
    monkeypatch.setattr(
        transformation_graph,
        "PROMPT_PACKS",
        {"extract": prompt_file},
    )

    assert (
        transformation_graph._resolve_prompt_pack("@prompt-pack:extract")
        == "PACK CONTENT"
    )
    assert transformation_graph._resolve_prompt_pack("plain prompt") == "plain prompt"

    warning_mock = MagicMock()
    monkeypatch.setattr(transformation_graph.logger, "warning", warning_mock)
    assert (
        transformation_graph._resolve_prompt_pack("@prompt-pack:unknown")
        == "@prompt-pack:unknown"
    )
    warning_mock.assert_called_once()

    explicit_parts = transformation_graph._build_input_parts(
        "ignored",
        {
            "input_parts": [
                {"type": "text", "text": "explicit"},
                "drop-me",
            ]
        },
    )
    assert explicit_parts == [{"type": "text", "text": "explicit"}]

    default_parts = transformation_graph._build_input_parts(
        "fallback",
        {"input_parts": ["only-non-dict"]},
    )
    assert default_parts[0]["text"] == "fallback"
    assert default_parts[0]["metadata"]["media_resolution"] == "low"


@pytest.mark.asyncio
async def test_run_transformation_wraps_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _ClassifiedTransformationError(Exception):
        pass

    monkeypatch.setattr(
        transformation_graph.DefaultPrompts,
        "get_instance",
        AsyncMock(return_value=SimpleNamespace(transformation_instructions="")),
    )
    monkeypatch.setattr(
        transformation_graph.Prompter,
        "render",
        lambda self, data: "system prompt",
    )
    monkeypatch.setattr(
        transformation_graph,
        "provision_with_gemini_features",
        AsyncMock(side_effect=RuntimeError("provision boom")),
    )
    monkeypatch.setattr(
        transformation_graph,
        "classify_error",
        lambda exc: (_ClassifiedTransformationError, "friendly-transform-error"),
    )

    with pytest.raises(
        _ClassifiedTransformationError, match="friendly-transform-error"
    ):
        await transformation_graph.run_transformation(
            {
                "input_text": "raw text",
                "source": None,
                "transformation": SimpleNamespace(prompt="prompt", title="summary"),
            },
            RunnableConfig(configurable={}),
        )


@pytest.mark.asyncio
async def test_prompt_call_model_cleans_thinking_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chain = SimpleNamespace(
        ainvoke=AsyncMock(
            return_value=SimpleNamespace(content="<think>x</think>answer")
        )
    )
    provision_mock = AsyncMock(return_value=chain)
    monkeypatch.setattr(prompt_graph, "provision_langchain_model", provision_mock)
    monkeypatch.setattr(
        prompt_graph.Prompter,
        "render",
        lambda self, data: "rendered-system-prompt",
    )

    result = await prompt_graph.call_model(
        {
            "prompt": "Template: {{ input_text }}",
            "parser": None,
            "input_text": "hello",
        },
        RunnableConfig(configurable={"model_id": "prompt-model"}),
    )

    assert result["output"] == "answer"
    provision_mock.assert_awaited_once()
    assert provision_mock.await_args.args[1] == "prompt-model"
