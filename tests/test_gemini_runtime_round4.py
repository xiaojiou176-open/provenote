from types import SimpleNamespace

from packages.core.ai import gemini_runtime
from packages.core.ai.gemini_features import GeminiFeaturesConfig


def test_resolve_strict_features_prefers_env_override(monkeypatch):
    features = GeminiFeaturesConfig(strict_features=False)

    monkeypatch.setenv("GEMINI_STRICT_FEATURES", "true")
    assert gemini_runtime._resolve_strict_features(features) is True

    monkeypatch.setenv("GEMINI_STRICT_FEATURES", "0")
    assert gemini_runtime._resolve_strict_features(features) is False


def test_bind_thought_signature_falls_back_to_camel_case() -> None:
    bind_calls: list[dict] = []

    class _FakeModel:
        def bind(self, **kwargs):
            bind_calls.append(kwargs)
            if "thought_signature" in kwargs:
                raise RuntimeError("snake_case not supported")
            if "thoughtSignature" in kwargs:
                return "bound-model"
            return self

    model = _FakeModel()
    bound = gemini_runtime._bind_thought_signature(model, "sig-1")

    assert bound == "bound-model"
    assert bind_calls == [
        {"thought_signature": "sig-1"},
        {"thoughtSignature": "sig-1"},
    ]


def test_build_cache_key_prefers_explicit_configurable_key() -> None:
    config = {"configurable": {"gemini_context_cache_key": "explicit-key"}}
    key = gemini_runtime._build_cache_key(
        content="payload",
        model_id="model-x",
        default_type="ask",
        config=config,
    )
    assert key == "explicit-key"


def test_extract_gemini_response_artifacts_collects_thoughts_when_enabled() -> None:
    response = SimpleNamespace(
        content=[
            {"thought": True, "text": "thinking a"},
            {"thinking": True, "text": "thinking b"},
            {"text": "ignored"},
        ],
        additional_kwargs={
            "tool_calls": [{"name": "lookup"}],
            "thought_signature": "sig-out",
        },
    )

    extracted = gemini_runtime.extract_gemini_response_artifacts(
        response, include_thoughts=True
    )

    assert extracted["tool_calls"] == [{"name": "lookup"}]
    assert extracted["thought_signature"] == "sig-out"
    assert extracted["thoughts"] == ["thinking a", "thinking b"]
