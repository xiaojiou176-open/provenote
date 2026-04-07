from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

import packages.core.ai.models as models
import packages.core.graphs.source_chat as source_chat
from packages.core.exceptions import ConfigurationError


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("rate limit exceeded", "rate_limit"),
        ("network timeout", "network"),
        ("connection dropped", "network"),
        ("unsupported provider", "unsupported"),
        ("not implemented yet", "unsupported"),
        ("upstream 503 error", "provider_5xx"),
        ("model not found", "not_configured"),
        ("no model configured", "not_configured"),
        ("something else", "unknown"),
    ],
)
def test_classify_fallback_reason_variants(message: str, expected: str) -> None:
    assert models._classify_fallback_reason(Exception(message)) == expected


@pytest.mark.asyncio
async def test_model_crud_helpers_and_prepare_save_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_query_mock = AsyncMock(
        side_effect=[
            [{"id": "model:1", "name": "m", "provider": "google", "type": "language"}],
            [{"id": "model:2", "name": "e", "provider": "google", "type": "embedding"}],
        ]
    )
    monkeypatch.setattr(models, "repo_query", repo_query_mock)
    monkeypatch.setattr(models, "ensure_record_id", lambda rid: f"normalized:{rid}")

    by_type = await models.Model.get_models_by_type("language")
    by_credential = await models.Model.get_by_credential("cred:1")

    assert by_type[0].id == "model:1"
    assert by_credential[0].id == "model:2"

    m = models.Model(name="m", provider="google", type="language", credential="cred:1")
    prepared = m._prepare_save_data()
    assert prepared["credential"] == "normalized:cred:1"


@pytest.mark.asyncio
async def test_model_get_credential_obj_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    model_without_credential = models.Model(
        name="m", provider="google", type="language"
    )
    assert await model_without_credential.get_credential_obj() is None

    class FakeCredential:
        @staticmethod
        async def get(_credential_id: str):
            return "credential-object"

    import sys

    monkeypatch.setitem(
        sys.modules,
        "packages.core.domain.credential",
        SimpleNamespace(Credential=FakeCredential),
    )
    model_with_credential = models.Model(
        name="m", provider="google", type="language", credential="cred:1"
    )
    assert await model_with_credential.get_credential_obj() == "credential-object"

    class RaisingCredential:
        @staticmethod
        async def get(_credential_id: str):
            raise RuntimeError("cannot load")

    monkeypatch.setitem(
        sys.modules,
        "packages.core.domain.credential",
        SimpleNamespace(Credential=RaisingCredential),
    )
    warning_mock = MagicMock()
    monkeypatch.setattr(models.logger, "warning", warning_mock)
    assert await model_with_credential.get_credential_obj() is None
    warning_mock.assert_called_once()


@pytest.mark.asyncio
async def test_default_models_get_instance_handles_result_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(models, "ensure_record_id", lambda rid: rid)

    monkeypatch.setattr(
        models, "repo_query", AsyncMock(return_value=[{"default_chat_model": "m1"}])
    )
    instance_list = await models.DefaultModels.get_instance()
    assert instance_list.default_chat_model == "m1"

    monkeypatch.setattr(
        models, "repo_query", AsyncMock(return_value={"default_chat_model": "m2"})
    )
    instance_dict = await models.DefaultModels.get_instance()
    assert instance_dict.default_chat_model == "m2"

    monkeypatch.setattr(models, "repo_query", AsyncMock(return_value="unexpected"))
    instance_other = await models.DefaultModels.get_instance()
    assert instance_other.default_chat_model is None


@pytest.mark.asyncio
async def test_model_manager_get_model_validation_and_provider_guards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = models.ModelManager()

    assert await manager.get_model("") is None

    monkeypatch.setattr(
        models.Model, "get", AsyncMock(side_effect=Exception("missing"))
    )
    with pytest.raises(ConfigurationError, match="not found"):
        await manager.get_model("model:missing")

    monkeypatch.setattr(
        models.Model,
        "get",
        AsyncMock(
            return_value=SimpleNamespace(type="vision", provider="google", name="m")
        ),
    )
    with pytest.raises(ConfigurationError, match="Invalid model type"):
        await manager.get_model("model:bad-type")

    monkeypatch.setattr(
        models.Model,
        "get",
        AsyncMock(
            return_value=SimpleNamespace(type="language", provider="openai", name="m")
        ),
    )
    with pytest.raises(ConfigurationError, match="Gemini-only"):
        await manager.get_model("model:bad-provider")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model_type", "factory_attr", "expected_provider"),
    [
        ("language", "create_language", "google"),
        ("embedding", "create_embedding", "google"),
        ("speech_to_text", "create_speech_to_text", "google"),
        ("text_to_speech", "create_text_to_speech", "google"),
    ],
)
async def test_model_manager_get_model_builds_all_supported_types(
    monkeypatch: pytest.MonkeyPatch,
    model_type: str,
    factory_attr: str,
    expected_provider: str,
) -> None:
    manager = models.ModelManager()

    model_obj = SimpleNamespace(
        id="model:1",
        name="gemini-x",
        provider="google",
        type=model_type,
        credential=None,
    )
    monkeypatch.setattr(models.Model, "get", AsyncMock(return_value=model_obj))
    monkeypatch.setattr(models, "provision_provider_keys", AsyncMock())
    monkeypatch.setattr(
        models, "get_provisioned_provider_config", lambda _provider: {"api_key": "k"}
    )

    factory = SimpleNamespace()
    create_mock = MagicMock(return_value=f"created-{model_type}")
    setattr(factory, factory_attr, create_mock)
    monkeypatch.setattr(models, "AIFactory", factory)

    result = await manager.get_model("model:1", temperature=0.3)

    assert result == f"created-{model_type}"
    _, kwargs = create_mock.call_args
    assert kwargs["provider"] == expected_provider
    assert kwargs["config"]["temperature"] == 0.3


@pytest.mark.asyncio
async def test_model_manager_get_model_credential_fallback_and_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = models.ModelManager()

    credential = SimpleNamespace(
        name="cred", to_esperanto_config=lambda: {"api_key": "from-cred"}
    )
    model_obj = SimpleNamespace(
        id="model:1",
        name="gemini-x",
        provider="google",
        type="language",
        credential="cred:1",
        get_credential_obj=AsyncMock(return_value=credential),
    )
    monkeypatch.setattr(models.Model, "get", AsyncMock(return_value=model_obj))
    monkeypatch.setattr(
        models,
        "AIFactory",
        SimpleNamespace(create_language=MagicMock(return_value="ok")),
    )

    result = await manager.get_model("model:1")
    assert result == "ok"

    model_obj2 = SimpleNamespace(
        id="model:2",
        name="gemini-y",
        provider="google",
        type="language",
        credential="cred:2",
        get_credential_obj=AsyncMock(return_value=None),
    )
    monkeypatch.setattr(models.Model, "get", AsyncMock(return_value=model_obj2))
    monkeypatch.setattr(models, "provision_provider_keys", AsyncMock())
    monkeypatch.setattr(
        models,
        "get_provisioned_provider_config",
        lambda _provider: {"api_key": "fallback"},
    )

    await manager.get_model("model:2")
    models.provision_provider_keys.assert_awaited_once_with("google")


@pytest.mark.asyncio
async def test_model_manager_defaults_and_runtime_fallback_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = models.ModelManager()

    monkeypatch.setattr(
        models.DefaultModels, "get_instance", AsyncMock(return_value=None)
    )
    with pytest.raises(RuntimeError, match="Failed to load"):
        await manager.get_defaults()

    monkeypatch.setattr(
        models.DefaultModels, "get_instance", AsyncMock(return_value=SimpleNamespace())
    )
    defaults = await manager.get_defaults()
    assert isinstance(defaults, SimpleNamespace)

    monkeypatch.setattr(models, "provision_provider_keys", AsyncMock())
    monkeypatch.setattr(
        models, "get_provisioned_provider_config", lambda _provider: {"api_key": "k"}
    )
    monkeypatch.setattr(
        models,
        "AIFactory",
        SimpleNamespace(create_embedding=MagicMock(return_value="embed-model")),
    )

    assert await manager._runtime_fallback_embedding_model(extra=1) == "embed-model"

    monkeypatch.setattr(
        models,
        "AIFactory",
        SimpleNamespace(create_embedding=MagicMock(side_effect=RuntimeError("boom"))),
    )
    assert await manager._runtime_fallback_embedding_model() is None


@pytest.mark.asyncio
async def test_model_manager_get_default_model_fallback_chain_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = models.ModelManager()
    defaults = SimpleNamespace(
        default_chat_model="model:primary",
        default_transformation_model=None,
        large_context_model=None,
        default_text_to_speech_model=None,
        default_speech_to_text_model=None,
        default_embedding_model=None,
        default_tools_model=None,
    )
    monkeypatch.setattr(manager, "get_defaults", AsyncMock(return_value=defaults))

    get_model_mock = AsyncMock(side_effect=ConfigurationError("rate limit"))
    monkeypatch.setattr(manager, "get_model", get_model_mock)
    monkeypatch.setattr(
        models, "get_provider_chain_for_model_type", AsyncMock(return_value=["google"])
    )
    monkeypatch.setattr(
        models,
        "repo_query",
        AsyncMock(
            return_value=[{"provider": "google", "id": "model:fallback", "name": "x"}]
        ),
    )

    get_model_mock.side_effect = [ConfigurationError("rate limit"), "fallback-model"]
    result = await manager.get_default_model("chat")
    assert result == "fallback-model"

    get_model_mock.side_effect = ConfigurationError("still bad")
    monkeypatch.setattr(
        models, "repo_query", AsyncMock(side_effect=RuntimeError("db down"))
    )
    assert await manager.get_default_model("chat") is None

    monkeypatch.setattr(models, "repo_query", AsyncMock(return_value=[]))
    runtime_fallback_mock = AsyncMock(return_value="runtime-embed")
    monkeypatch.setattr(
        manager, "_runtime_fallback_embedding_model", runtime_fallback_mock
    )
    assert await manager.get_default_model("embedding") == "runtime-embed"

    monkeypatch.setattr(
        models, "repo_query", AsyncMock(return_value=[{"provider": "", "id": None}])
    )
    runtime_fallback_mock = AsyncMock(return_value="runtime-embed-2")
    monkeypatch.setattr(
        manager, "_runtime_fallback_embedding_model", runtime_fallback_mock
    )
    assert await manager.get_default_model("embedding") == "runtime-embed-2"


@pytest.mark.asyncio
async def test_graph_source_chat_inner_threadpool_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        source_chat.asyncio, "get_running_loop", MagicMock(return_value=object())
    )

    class FakeContextBuilder:
        def __init__(self, **_kwargs):
            pass

        async def build(self):
            return {
                "sources": [{"id": "source:1", "title": "T", "full_text": "Body"}],
                "insights": [
                    {"id": "insight:1", "insight_type": "summary", "content": "I"}
                ],
            }

    class FakeSource:
        def __init__(self, **kwargs):
            self.id = kwargs["id"]
            self._data = kwargs

        def model_dump(self):
            return self._data

    class FakeInsight(FakeSource):
        pass

    class FakePrompter:
        def __init__(self, prompt_template: str, prompt_dir: str | None = None):
            assert prompt_template == "source_chat/system"
            assert prompt_dir

        def render(self, data):
            assert data["source"]["id"] == "source:1"
            return "system-prompt"

    class FakeModel:
        def invoke(self, payload):
            assert payload[0].content == "system-prompt"
            return AIMessage(content="<think>a</think> hello")

    monkeypatch.setattr(source_chat, "ContextBuilder", FakeContextBuilder)
    monkeypatch.setattr(source_chat, "Source", FakeSource)
    monkeypatch.setattr(source_chat, "SourceInsight", FakeInsight)
    monkeypatch.setattr(source_chat, "Prompter", FakePrompter)
    monkeypatch.setattr(
        source_chat, "provision_langchain_model", AsyncMock(return_value=FakeModel())
    )
    monkeypatch.setattr(
        source_chat, "extract_text_content", lambda content: str(content)
    )
    monkeypatch.setattr(
        source_chat,
        "clean_thinking_content",
        lambda text: text.replace("<think>a</think>", "").strip(),
    )

    result = source_chat._call_model_with_source_context_inner(
        {
            "source_id": "source:1",
            "messages": [AIMessage(content="hi")],
            "model_override": "m1",
        },
        {"configurable": {}},
    )

    assert result["messages"].content == "hello"
    assert result["context_indicators"]["sources"] == ["source:1"]
