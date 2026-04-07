import pytest

from packages.core.ai import key_provider


@pytest.mark.asyncio
async def test_provision_provider_keys_rejects_non_google_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    async def _fake_provision(provider: str) -> bool:
        called.append(provider)
        return True

    monkeypatch.setattr(key_provider, "_provision_simple_provider", _fake_provision)
    ok = await key_provider.provision_provider_keys("anthropic")

    assert ok is False
    assert called == []


@pytest.mark.asyncio
async def test_provision_provider_keys_allows_google_after_normalization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    async def _fake_provision(provider: str) -> bool:
        called.append(provider)
        return True

    monkeypatch.setattr(key_provider, "_provision_simple_provider", _fake_provision)
    ok = await key_provider.provision_provider_keys("Google")

    assert ok is True
    assert called == ["google"]
