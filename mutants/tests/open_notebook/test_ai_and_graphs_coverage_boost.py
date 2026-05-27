from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

import packages.core.ai.connection_tester as connection_tester
import packages.core.ai.provision as provision
import packages.core.graphs.source as source_graph
import packages.core.graphs.source_chat as source_chat


@pytest.mark.asyncio
async def test_resolve_google_api_key_prefers_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        connection_tester,
        "read_env",
        lambda key, default=None: "env-key" if key == "GEMINI_API_KEY" else default,
    )
    get_api_key_mock = AsyncMock(return_value="db-key")
    monkeypatch.setattr(connection_tester, "get_api_key", get_api_key_mock)

    result = await connection_tester._resolve_google_api_key()

    assert result == ("env-key", "environment:GEMINI_API_KEY")
    get_api_key_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_resolve_google_api_key_falls_back_to_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(connection_tester, "read_env", lambda *_args, **_kwargs: None)
    get_api_key_mock = AsyncMock(return_value="db-key")
    monkeypatch.setattr(connection_tester, "get_api_key", get_api_key_mock)

    result = await connection_tester._resolve_google_api_key()

    assert result == ("db-key", "database:credential")
    get_api_key_mock.assert_awaited_once_with("google")


@pytest.mark.asyncio
async def test_get_default_credential_config_returns_empty_and_logs_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        connection_tester.Credential,
        "get_by_provider",
        AsyncMock(side_effect=RuntimeError("boom")),
    )
    exception_mock = MagicMock()
    monkeypatch.setattr(connection_tester.logger, "exception", exception_mock)

    result = await connection_tester._get_default_credential_config("google")

    assert result == {}
    exception_mock.assert_called_once()


@pytest.mark.asyncio
async def test_test_provider_connection_handles_unsupported_provider() -> None:
    success, message = await connection_tester.test_provider_connection("openai")

    assert success is False
    assert "Only Google provider is supported" in message


@pytest.mark.asyncio
async def test_test_provider_connection_config_id_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        connection_tester.Credential, "get", AsyncMock(side_effect=Exception("missing"))
    )
    exception_mock = MagicMock()
    monkeypatch.setattr(connection_tester.logger, "exception", exception_mock)

    success, message = await connection_tester.test_provider_connection(
        "google", config_id="cred-1"
    )

    assert success is False
    assert message == "Credential not found: cred-1"
    exception_mock.assert_called_once()


@pytest.mark.asyncio
async def test_test_provider_connection_reports_missing_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        connection_tester, "_get_default_credential_config", AsyncMock(return_value={})
    )
    monkeypatch.setattr(connection_tester, "get_api_key", AsyncMock(return_value=None))

    success, message = await connection_tester.test_provider_connection("google")

    assert success is False
    assert message == "No database credential configured for google"


@pytest.mark.asyncio
async def test_test_provider_connection_success_uses_config_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        connection_tester,
        "_get_default_credential_config",
        AsyncMock(return_value={"api_key": "k", "model": "gemini-custom"}),
    )
    test_conn_mock = AsyncMock(return_value=(True, "ok"))
    monkeypatch.setattr(connection_tester, "test_google_connection", test_conn_mock)

    result = await connection_tester.test_provider_connection("google")

    assert result == (True, "ok")
    test_conn_mock.assert_awaited_once_with("k", "gemini-custom")


@pytest.mark.asyncio
async def test_test_provider_connection_handles_missing_test_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        connection_tester,
        "_get_default_credential_config",
        AsyncMock(return_value={"api_key": "k"}),
    )
    monkeypatch.setattr(connection_tester, "get_api_key", AsyncMock(return_value="k"))
    monkeypatch.setitem(connection_tester.TEST_MODELS, "google", ("", "language"))

    success, message = await connection_tester.test_provider_connection("google")

    assert success is False
    assert message == "No test model configured for google"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_msg", "expected"),
    [
        ("401 Unauthorized", (False, "Invalid API key")),
        ("403 Forbidden", (False, "API key lacks required permissions")),
        ("Rate LIMIT reached", (True, "Rate limited - but connection works")),
        ("network failure", (False, "Connection error - check network/endpoint")),
        ("timeout happened", (False, "Connection timed out - check network/endpoint")),
        ("model not found", (True, "API key valid (test model not available)")),
    ],
)
async def test_test_provider_connection_normalizes_known_exceptions(
    monkeypatch: pytest.MonkeyPatch, error_msg: str, expected: tuple[bool, str]
) -> None:
    monkeypatch.setattr(
        connection_tester,
        "_get_default_credential_config",
        AsyncMock(return_value={"api_key": "k"}),
    )
    monkeypatch.setattr(
        connection_tester,
        "test_google_connection",
        AsyncMock(side_effect=Exception(error_msg)),
    )

    result = await connection_tester.test_provider_connection("google")

    assert result == expected


def test_generate_test_wav_has_valid_header() -> None:
    wav = connection_tester._generate_test_wav().getvalue()
    assert wav.startswith(b"RIFF")
    assert b"WAVE" in wav[:16]
    assert len(wav) > 44


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("401 Unauthorized", (False, "Invalid API key")),
        ("403 forbidden", (False, "API key lacks required permissions")),
        ("rate limit exceeded", (True, "Rate limited - but connection works")),
        ("model not found", (False, "Model not found on this provider")),
        ("network issue", (False, "Connection error - check network/endpoint")),
        ("timeout issue", (False, "Connection timed out - check network/endpoint")),
        ("other", (False, "other")),
    ],
)
def test_normalize_error_message_variants(
    message: str, expected: tuple[bool, str]
) -> None:
    assert connection_tester._normalize_error_message(message) == expected


@pytest.mark.asyncio
async def test_test_individual_model_language_and_embedding_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeModelManager:
        async def get_model(self, _model_id: str):
            async def _achat_complete(messages):
                assert messages[0]["role"] == "user"
                return SimpleNamespace(content="Hello from model")

            async def _aembed(texts):
                assert texts == ["This is a test."]
                return [[0.1, 0.2]]

            return SimpleNamespace(achat_complete=_achat_complete, aembed=_aembed)

    monkeypatch.setattr("packages.core.ai.models.ModelManager", FakeModelManager)
    language_model = SimpleNamespace(id="m1", type="language", provider="google")
    embedding_model = SimpleNamespace(id="m2", type="embedding", provider="google")

    language_result = await connection_tester.test_individual_model(language_model)
    embedding_result = await connection_tester.test_individual_model(embedding_model)

    assert language_result[0] is True and "Response:" in language_result[1]
    assert embedding_result == (True, "Embedding dimensions: 2")


@pytest.mark.asyncio
async def test_test_individual_model_tts_stt_and_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeTTS:
        available_voices = {"demo": "voice"}

        async def agenerate_speech(self, text: str, voice: str):
            assert "Notebooklab" in text
            assert voice == "Kore"
            return SimpleNamespace(content=b"abc")

    class FakeSTT:
        async def atranscribe(self, audio_file, language: str):
            assert audio_file.name == "test.wav"
            assert language == "en"
            return SimpleNamespace(text="transcribed text")

    class FakeModelManager:
        async def get_model(self, model_id: str):
            if model_id == "tts":
                return FakeTTS()
            if model_id == "stt":
                return FakeSTT()
            return object()

    monkeypatch.setattr("packages.core.ai.models.ModelManager", FakeModelManager)

    tts_model = SimpleNamespace(id="tts", type="text_to_speech", provider="google")
    stt_model = SimpleNamespace(id="stt", type="speech_to_text", provider="google")
    unsupported_model = SimpleNamespace(id="x", type="vision", provider="google")

    assert await connection_tester.test_individual_model(tts_model) == (
        True,
        "Audio generated: 3 bytes",
    )
    assert await connection_tester.test_individual_model(stt_model) == (
        True,
        "Transcription: transcribed text",
    )
    assert await connection_tester.test_individual_model(unsupported_model) == (
        False,
        "Unsupported model type: vision",
    )


@pytest.mark.asyncio
async def test_test_individual_model_handles_model_creation_and_runtime_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeModelManager:
        async def get_model(self, _model_id: str):
            return None

    monkeypatch.setattr("packages.core.ai.models.ModelManager", FakeModelManager)
    assert await connection_tester.test_individual_model(
        SimpleNamespace(id="m0", type="language", provider="google")
    ) == (False, "Could not create model instance")

    class UnauthorizedModelError(Exception):
        pass

    class RaisingModelManager:
        async def get_model(self, _model_id: str):
            raise UnauthorizedModelError("401 unauthorized")

    monkeypatch.setattr("packages.core.ai.models.ModelManager", RaisingModelManager)
    assert await connection_tester.test_individual_model(
        SimpleNamespace(id="m9", type="language", provider="google")
    ) == (False, "Invalid API key")


@pytest.mark.asyncio
async def test_provision_langchain_model_chooses_large_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeLanguageModel:
        def to_langchain(self):
            return "lc-large"

    monkeypatch.setattr(provision, "LanguageModel", FakeLanguageModel)
    monkeypatch.setattr(provision, "token_count", lambda _content: 200000)
    get_default_mock = AsyncMock(return_value=FakeLanguageModel())
    monkeypatch.setattr(provision.model_manager, "get_default_model", get_default_mock)

    result = await provision.provision_langchain_model("x", None, "chat")

    assert result == "lc-large"
    get_default_mock.assert_awaited_once_with("large_context")


@pytest.mark.asyncio
async def test_provision_langchain_model_with_explicit_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeLanguageModel:
        def to_langchain(self):
            return "lc-explicit"

    monkeypatch.setattr(provision, "LanguageModel", FakeLanguageModel)
    monkeypatch.setattr(provision, "token_count", lambda _content: 100)
    get_model_mock = AsyncMock(return_value=FakeLanguageModel())
    monkeypatch.setattr(provision.model_manager, "get_model", get_model_mock)

    result = await provision.provision_langchain_model("x", "model-1", "chat", k="v")

    assert result == "lc-explicit"
    get_model_mock.assert_awaited_once_with("model-1", k="v")


@pytest.mark.asyncio
async def test_provision_langchain_model_raises_for_missing_or_wrong_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(provision, "token_count", lambda _content: 100)
    monkeypatch.setattr(
        provision.model_manager, "get_default_model", AsyncMock(return_value=None)
    )

    with pytest.raises(provision.ConfigurationError, match="No model configured"):
        await provision.provision_langchain_model("x", None, "chat")

    class NotLanguageModel:
        pass

    monkeypatch.setattr(
        provision.model_manager,
        "get_default_model",
        AsyncMock(return_value=NotLanguageModel()),
    )
    monkeypatch.setattr(provision, "LanguageModel", tuple)
    with pytest.raises(
        provision.ConfigurationError, match="Model is not a LanguageModel"
    ):
        await provision.provision_langchain_model("x", None, "chat")


@pytest.mark.asyncio
async def test_content_process_sets_engines_and_audio_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extract_mock = AsyncMock(
        return_value=SimpleNamespace(
            content="hello", url="https://a.com", file_path="/tmp/a", title="A"
        )
    )
    monkeypatch.setattr(source_graph, "extract_content", extract_mock)
    monkeypatch.setattr(
        source_graph.ModelManager,
        "__call__",
        lambda self: self,
    )

    class FakeManager:
        async def get_defaults(self):
            return SimpleNamespace(default_speech_to_text_model="stt-1")

    monkeypatch.setattr(source_graph, "ModelManager", lambda: FakeManager())
    monkeypatch.setattr(
        source_graph.Model,
        "get",
        AsyncMock(return_value=SimpleNamespace(provider="google", name="gemini-stt")),
    )

    state = {"content_state": {"url": "https://a.com"}}
    result = await source_graph.content_process(state)

    assert result["content_state"].content == "hello"
    kwargs = extract_mock.await_args.args[0]
    assert kwargs["url_engine"] == "auto"
    assert kwargs["document_engine"] == "auto"
    assert kwargs["audio_provider"] == "google"
    assert kwargs["audio_model"] == "gemini-stt"


@pytest.mark.asyncio
async def test_content_process_error_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        source_graph,
        "ModelManager",
        lambda: SimpleNamespace(get_defaults=AsyncMock(side_effect=Exception("x"))),
    )
    warning_mock = MagicMock()
    monkeypatch.setattr(source_graph.logger, "warning", warning_mock)

    monkeypatch.setattr(
        source_graph,
        "extract_content",
        AsyncMock(
            return_value=SimpleNamespace(
                content=" ", url="https://youtube.com/v", file_path=None, title=None
            )
        ),
    )
    with pytest.raises(ValueError, match="No transcript or subtitles are available"):
        await source_graph.content_process({"content_state": {}})
    warning_mock.assert_called()

    monkeypatch.setattr(
        source_graph,
        "extract_content",
        AsyncMock(
            return_value=SimpleNamespace(
                content="", url="https://example.com", file_path=None, title=None
            )
        ),
    )
    with pytest.raises(ValueError, match="Could not extract any text content"):
        await source_graph.content_process({"content_state": {}})


@pytest.mark.asyncio
async def test_save_source_and_transform_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSource:
        def __init__(self):
            self.id = "source:1"
            self.title = "Existing"
            self.full_text = None
            self.asset = None
            self.save = AsyncMock()
            self.vectorize = AsyncMock()
            self.add_insight = AsyncMock()

    fake_source = FakeSource()
    monkeypatch.setattr(source_graph.Source, "get", AsyncMock(return_value=fake_source))

    state = {
        "content_state": SimpleNamespace(
            url="u", file_path="/tmp/a.png", content=" body ", title=None
        ),
        "source_id": "source:1",
        "embed": True,
    }
    result = await source_graph.save_source(state)
    assert result["source"] is fake_source
    assert fake_source.title == "Existing"
    fake_source.vectorize.assert_awaited_once()

    empty_state = {
        "content_state": SimpleNamespace(
            url="u", file_path="/tmp/a.mp4", content=" ", title="New"
        ),
        "source_id": "source:1",
        "embed": True,
    }
    warning_mock = MagicMock()
    monkeypatch.setattr(source_graph.logger, "warning", warning_mock)
    await source_graph.save_source(empty_state)
    assert fake_source.title == "New"
    warning_mock.assert_called_once()

    sends = source_graph.trigger_transformations(
        {"apply_transformations": [SimpleNamespace(name="x")], "source": fake_source},
        {},
    )
    assert len(sends) == 1
    assert source_graph.trigger_transformations({"apply_transformations": []}, {}) == []
    assert source_graph._derive_media_resolution_hint(fake_source) == "medium"

    monkeypatch.setattr(
        source_graph.transform_graph,
        "ainvoke",
        AsyncMock(
            return_value={
                "output": "transformed",
                "gemini_telemetry": {"model": "gemini"},
            }
        ),
    )
    transform_result = await source_graph.transform_content(
        {
            "source": fake_source,
            "transformation": SimpleNamespace(name="sum", title="Summary"),
        },
        {},
    )
    assert transform_result["transformation"][0]["transformation_name"] == "sum"
    assert transform_result["gemini_telemetry"][0]["model"] == "gemini"

    fake_source.full_text = ""
    assert (
        await source_graph.transform_content(
            {
                "source": fake_source,
                "transformation": SimpleNamespace(name="sum", title="Summary"),
            },
            {},
        )
        is None
    )


@pytest.mark.asyncio
async def test_save_source_raises_when_source_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(source_graph.Source, "get", AsyncMock(return_value=None))
    with pytest.raises(ValueError, match="Source with ID missing not found"):
        await source_graph.save_source(
            {
                "content_state": SimpleNamespace(
                    url="", file_path="", content="", title=None
                ),
                "source_id": "missing",
                "embed": False,
            }
        )


def test_format_source_context_includes_metadata_and_truncates() -> None:
    long_text = "a" * 6001
    rendered = source_chat._format_source_context(
        {
            "sources": [{"id": "s1", "title": "T", "full_text": long_text}],
            "insights": [{"id": "i1", "insight_type": "summary", "content": "c"}],
            "metadata": {"source_count": 1, "insight_count": 1},
            "total_tokens": 123,
        }
    )

    assert "## SOURCE CONTENT" in rendered
    assert "[Content truncated]" in rendered
    assert "## SOURCE INSIGHTS" in rendered
    assert "## CONTEXT METADATA" in rendered
    assert "Total tokens: 123" in rendered


def test_call_model_with_source_context_rethrows_open_notebook_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        source_chat,
        "_call_model_with_source_context_inner",
        MagicMock(side_effect=source_chat.OpenNotebookError("x")),
    )
    with pytest.raises(source_chat.OpenNotebookError):
        source_chat.call_model_with_source_context({"source_id": "s"}, {})


def test_call_model_with_source_context_wraps_unexpected_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        source_chat,
        "_call_model_with_source_context_inner",
        MagicMock(side_effect=ValueError("boom")),
    )

    class Classified(Exception):
        pass

    monkeypatch.setattr(
        source_chat, "classify_error", lambda _e: (Classified, "friendly")
    )
    with pytest.raises(Classified, match="friendly"):
        source_chat.call_model_with_source_context({"source_id": "s"}, {})


def test_call_model_with_source_context_inner_requires_source_id() -> None:
    with pytest.raises(ValueError, match="source_id is required in state"):
        source_chat._call_model_with_source_context_inner({}, {})


def test_call_model_with_source_context_inner_runtimeerror_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        source_chat.asyncio, "get_running_loop", MagicMock(side_effect=RuntimeError())
    )

    class FakeContextBuilder:
        def __init__(self, **_kwargs):
            pass

        async def build(self):
            return {
                "sources": [{"id": "s1", "title": "Title", "full_text": "Body"}],
                "insights": [
                    {"id": "i1", "insight_type": "summary", "content": "Insight"}
                ],
                "metadata": {"source_count": 1, "insight_count": 1},
                "total_tokens": 7,
            }

    class FakeSource:
        def __init__(self, **kwargs):
            self.id = kwargs["id"]
            self._data = kwargs

        def model_dump(self):
            return self._data

    class FakeInsight:
        def __init__(self, **kwargs):
            self.id = kwargs["id"]
            self._data = kwargs

        def model_dump(self):
            return self._data

    class FakePrompter:
        def __init__(self, prompt_template: str, prompt_dir: str | None = None):
            assert prompt_template == "source_chat/system"
            assert prompt_dir

        def render(self, data):
            assert data["source"]["id"] == "s1"
            return "system"

    class FakeModel:
        def invoke(self, payload):
            assert payload[0].content == "system"
            return AIMessage(content="<think>hidden</think> answer")

    provision_mock = AsyncMock(return_value=FakeModel())
    monkeypatch.setattr(source_chat, "ContextBuilder", FakeContextBuilder)
    monkeypatch.setattr(source_chat, "Source", FakeSource)
    monkeypatch.setattr(source_chat, "SourceInsight", FakeInsight)
    monkeypatch.setattr(source_chat, "Prompter", FakePrompter)
    monkeypatch.setattr(source_chat, "provision_langchain_model", provision_mock)
    monkeypatch.setattr(source_chat, "extract_text_content", lambda text: str(text))
    monkeypatch.setattr(
        source_chat,
        "clean_thinking_content",
        lambda text: text.replace("<think>hidden</think>", "").strip(),
    )

    result = source_chat._call_model_with_source_context_inner(
        {
            "source_id": "s1",
            "messages": [AIMessage(content="hello")],
            "model_override": "override",
        },
        {"configurable": {}},
    )

    assert result["messages"].content == "answer"
    assert result["context_indicators"]["sources"] == ["s1"]
    assert result["context_indicators"]["insights"] == ["i1"]
    provision_mock.assert_awaited_once()
