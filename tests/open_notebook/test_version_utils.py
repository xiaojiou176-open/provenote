from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest
import requests

from packages.core.utils.version_utils import (
    get_version_from_github,
    get_version_from_github_async,
)


class _FakeResponse:
    def __init__(self, *, text: str, error: Exception | None = None):
        self.text = text
        self._error = error

    def raise_for_status(self) -> None:
        if self._error is not None:
            raise self._error


def test_get_version_from_github_reads_poetry_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    def _fake_get(url: str, timeout: int):
        captured["url"] = url
        captured["timeout"] = timeout
        return _FakeResponse(text='[tool.poetry]\nversion = "1.2.3"\n')

    monkeypatch.setattr("packages.core.utils.version_utils.requests.get", _fake_get)

    version = get_version_from_github("https://github.com/acme/demo")

    assert version == "1.2.3"
    assert captured["timeout"] == 10
    assert (
        captured["url"]
        == "https://raw.githubusercontent.com/acme/demo/main/pyproject.toml"
    )


def test_get_version_from_github_reads_project_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_get(url: str, timeout: int):
        _ = (url, timeout)
        return _FakeResponse(text='[project]\nversion = "2.0.1"\n')

    monkeypatch.setattr("packages.core.utils.version_utils.requests.get", _fake_get)

    version = get_version_from_github("https://github.com/acme/demo")

    assert version == "2.0.1"


def test_get_version_from_github_uses_custom_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    def _fake_get(url: str, timeout: int):
        captured["url"] = url
        _ = timeout
        return _FakeResponse(text='[project]\nversion = "0.0.1"\n')

    monkeypatch.setattr("packages.core.utils.version_utils.requests.get", _fake_get)

    version = get_version_from_github(
        repo_url="https://github.com/acme/demo", branch="release/v1"
    )

    assert version == "0.0.1"
    assert (
        captured["url"]
        == "https://raw.githubusercontent.com/acme/demo/release/v1/pyproject.toml"
    )


def test_get_version_from_github_raises_when_version_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_get(url: str, timeout: int):
        _ = (url, timeout)
        return _FakeResponse(text='[tool.poetry]\nname = "demo"\n')

    monkeypatch.setattr("packages.core.utils.version_utils.requests.get", _fake_get)

    with pytest.raises(KeyError, match="Version not found in pyproject.toml"):
        get_version_from_github("https://github.com/acme/demo")


def test_get_version_from_github_bubbles_http_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_get(url: str, timeout: int):
        _ = (url, timeout)
        return _FakeResponse(text="", error=requests.HTTPError("404"))

    monkeypatch.setattr("packages.core.utils.version_utils.requests.get", _fake_get)

    with pytest.raises(requests.HTTPError, match="404"):
        get_version_from_github("https://github.com/acme/demo")


@pytest.mark.asyncio
async def test_get_version_from_github_async_reads_poetry_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    class _AsyncClient:
        def __init__(self, timeout: float):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            _ = (exc_type, exc, tb)
            return False

        async def get(self, url: str):
            captured["url"] = url
            return _FakeResponse(text='[tool.poetry]\nversion = "3.4.5"\n')

    fake_httpx = SimpleNamespace(AsyncClient=_AsyncClient)
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)

    version = await get_version_from_github_async("https://github.com/acme/demo")

    assert version == "3.4.5"
    assert captured["timeout"] == 10.0
    assert (
        captured["url"]
        == "https://raw.githubusercontent.com/acme/demo/main/pyproject.toml"
    )


@pytest.mark.asyncio
async def test_get_version_from_github_async_reads_project_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _AsyncClient:
        def __init__(self, timeout: float):
            _ = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            _ = (exc_type, exc, tb)
            return False

        async def get(self, url: str):
            _ = url
            return _FakeResponse(text='[project]\nversion = "9.9.9"\n')

    fake_httpx = SimpleNamespace(AsyncClient=_AsyncClient)
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)

    version = await get_version_from_github_async("https://github.com/acme/demo")

    assert version == "9.9.9"


@pytest.mark.asyncio
async def test_get_version_from_github_async_raises_when_version_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _AsyncClient:
        def __init__(self, timeout: float):
            _ = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            _ = (exc_type, exc, tb)
            return False

        async def get(self, url: str):
            _ = url
            return _FakeResponse(text='[project]\nname = "demo"\n')

    fake_httpx = SimpleNamespace(AsyncClient=_AsyncClient)
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)

    with pytest.raises(KeyError, match="Version not found in pyproject.toml"):
        await get_version_from_github_async("https://github.com/acme/demo")


@pytest.mark.asyncio
async def test_get_version_from_github_async_bubbles_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _AsyncClient:
        def __init__(self, timeout: float):
            _ = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            _ = (exc_type, exc, tb)
            return False

        async def get(self, url: str):
            _ = url
            return _FakeResponse(text="", error=RuntimeError("upstream failed"))

    fake_httpx = SimpleNamespace(AsyncClient=_AsyncClient)
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)

    with pytest.raises(RuntimeError, match="upstream failed"):
        await get_version_from_github_async("https://github.com/acme/demo")


@pytest.mark.asyncio
async def test_get_version_from_github_async_validates_url() -> None:
    with pytest.raises(ValueError, match="Not a GitHub URL"):
        await get_version_from_github_async("https://example.com/acme/demo")

    with pytest.raises(ValueError, match="Invalid GitHub repository URL"):
        await get_version_from_github_async("https://github.com/")
