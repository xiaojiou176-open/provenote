from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import packages.core.ai.model_discovery as model_discovery


@pytest.mark.asyncio
async def test_discover_google_models_returns_empty_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_api_key_mock = AsyncMock(return_value=None)
    list_models_mock = AsyncMock(return_value=[{"name": "should-not-load"}])
    monkeypatch.setattr(model_discovery, "get_api_key", get_api_key_mock)
    monkeypatch.setattr(model_discovery, "list_google_models", list_models_mock)

    result = await model_discovery.discover_google_models()

    assert result == []
    get_api_key_mock.assert_awaited_once_with("google")
    list_models_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_discover_google_models_maps_fields_and_filters_invalid_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(model_discovery, "get_api_key", AsyncMock(return_value="k"))
    monkeypatch.setattr(
        model_discovery,
        "list_google_models",
        AsyncMock(
            return_value=[
                {"name": "gemini-2.5-flash", "model_type": "language"},
                {"name": "gemini-embedding-001", "model_type": "embedding"},
                {"name": "", "model_type": "language"},
                {"model_type": "language"},
            ]
        ),
    )

    result = await model_discovery.discover_google_models()

    assert [item.name for item in result] == [
        "gemini-2.5-flash",
        "gemini-embedding-001",
    ]
    assert all(item.provider == "google" for item in result)


@pytest.mark.asyncio
async def test_discover_google_models_returns_empty_on_upstream_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(model_discovery, "get_api_key", AsyncMock(return_value="k"))
    monkeypatch.setattr(
        model_discovery,
        "list_google_models",
        AsyncMock(side_effect=RuntimeError("upstream")),
    )
    exception_mock = MagicMock()
    monkeypatch.setattr(model_discovery.logger, "exception", exception_mock)

    assert await model_discovery.discover_google_models() == []
    exception_mock.assert_called_once()


@pytest.mark.asyncio
async def test_discover_provider_models_handles_unsupported_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    warning_mock = MagicMock()
    monkeypatch.setattr(model_discovery.logger, "warning", warning_mock)

    result = await model_discovery.discover_provider_models("openai")

    assert result == []
    warning_mock.assert_called_once()


@pytest.mark.asyncio
async def test_sync_provider_models_short_circuit_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        model_discovery,
        "discover_provider_models",
        AsyncMock(
            return_value=[
                model_discovery.DiscoveredModel(
                    name="gemini-2.0-flash", provider="google", model_type="language"
                )
            ]
        ),
    )

    assert await model_discovery.sync_provider_models(
        "google", auto_register=False
    ) == (
        1,
        0,
        0,
    )

    monkeypatch.setattr(
        model_discovery,
        "discover_provider_models",
        AsyncMock(return_value=[]),
    )
    assert await model_discovery.sync_provider_models("google", auto_register=True) == (
        0,
        0,
        0,
    )


@pytest.mark.asyncio
async def test_sync_provider_models_handles_existing_and_registration_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discovered = [
        model_discovery.DiscoveredModel(
            name="gemini-existing", provider="google", model_type="language"
        ),
        model_discovery.DiscoveredModel(
            name="gemini-fail", provider="google", model_type="language"
        ),
        model_discovery.DiscoveredModel(
            name="gemini-new", provider="google", model_type="embedding"
        ),
    ]
    monkeypatch.setattr(
        model_discovery, "discover_provider_models", AsyncMock(return_value=discovered)
    )
    monkeypatch.setattr(
        model_discovery,
        "repo_query",
        AsyncMock(return_value=[{"name": "gemini-existing", "type": "language"}]),
    )

    class FakeModel:
        def __init__(self, name: str, provider: str, type: str):
            self.name = name
            self.provider = provider
            self.type = type

        async def save(self) -> None:
            if self.name == "gemini-fail":
                raise RuntimeError("write failed")

    exception_mock = MagicMock()
    monkeypatch.setattr(model_discovery, "Model", FakeModel)
    monkeypatch.setattr(model_discovery.logger, "exception", exception_mock)

    result = await model_discovery.sync_provider_models(" Google ", auto_register=True)

    assert result == (3, 1, 1)
    exception_mock.assert_called_once()


@pytest.mark.asyncio
async def test_sync_provider_models_handles_existing_model_query_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discovered = [
        model_discovery.DiscoveredModel(
            name="gemini-2.0-flash", provider="google", model_type="language"
        )
    ]
    monkeypatch.setattr(
        model_discovery, "discover_provider_models", AsyncMock(return_value=discovered)
    )
    monkeypatch.setattr(
        model_discovery,
        "repo_query",
        AsyncMock(side_effect=RuntimeError("query failed")),
    )

    class FakeModel:
        def __init__(self, name: str, provider: str, type: str):
            self.name = name
            self.provider = provider
            self.type = type

        async def save(self) -> None:
            return None

    monkeypatch.setattr(model_discovery, "Model", FakeModel)
    result = await model_discovery.sync_provider_models("google", auto_register=True)

    assert result == (1, 1, 0)


@pytest.mark.asyncio
async def test_sync_all_providers_handles_mixed_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        model_discovery,
        "PROVIDER_DISCOVERY_FUNCTIONS",
        {"google": object(), "google_backup": object()},
    )

    async def _fake_sync(provider: str, auto_register: bool = True):
        assert auto_register is True
        if provider == "google":
            return (2, 1, 1)
        raise RuntimeError("sync failed")

    error_mock = MagicMock()
    monkeypatch.setattr(model_discovery, "sync_provider_models", _fake_sync)
    monkeypatch.setattr(model_discovery.logger, "error", error_mock)

    result = await model_discovery.sync_all_providers()

    assert result["google"] == (2, 1, 1)
    assert result["google_backup"] == (0, 0, 0)
    error_mock.assert_called_once()


@pytest.mark.asyncio
async def test_get_provider_model_count_normalizes_provider_and_ignores_unknown_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_query_mock = AsyncMock(
        return_value=[
            {"type": "language", "count": 4},
            {"type": "embedding", "count": 2},
            {"type": "vision", "count": 9},
        ]
    )
    monkeypatch.setattr(model_discovery, "repo_query", repo_query_mock)

    counts = await model_discovery.get_provider_model_count("Google-Cloud")

    assert counts == {
        "language": 4,
        "embedding": 2,
        "speech_to_text": 0,
        "text_to_speech": 0,
    }
    query = repo_query_mock.await_args.args[0]
    params = repo_query_mock.await_args.args[1]
    assert "WHERE provider = $provider" in query
    assert params["provider"] == "google_cloud"
