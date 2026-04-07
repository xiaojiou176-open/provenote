import pytest
from starlette.requests import Request

from services.api import main as api_main


def _make_request(origin: str | None = None) -> Request:
    headers = []
    if origin:
        headers.append((b"origin", origin.encode("utf-8")))
    return Request({"type": "http", "headers": headers})


def test_load_cors_config_fails_fast_in_production_without_allowlist(monkeypatch):
    monkeypatch.setenv("OPEN_NOTEBOOK_ENV", "production")
    monkeypatch.setenv("OPEN_NOTEBOOK_CORS_ALLOW_ORIGINS", "")
    monkeypatch.setenv("OPEN_NOTEBOOK_CORS_ALLOW_CREDENTIALS", "true")

    with pytest.raises(RuntimeError) as exc_info:
        api_main._load_cors_config()
    assert "OPEN_NOTEBOOK_CORS_ALLOW_ORIGINS" in str(exc_info.value)


def test_load_cors_config_rejects_wildcard_with_credentials(monkeypatch):
    monkeypatch.setenv("OPEN_NOTEBOOK_ENV", "development")
    monkeypatch.setenv("OPEN_NOTEBOOK_CORS_ALLOW_ORIGINS", "*")
    monkeypatch.setenv("OPEN_NOTEBOOK_CORS_ALLOW_CREDENTIALS", "true")

    with pytest.raises(RuntimeError) as exc_info:
        api_main._load_cors_config()
    assert "wildcard origin '*'" in str(exc_info.value)


def test_load_cors_config_allows_wildcard_without_credentials(monkeypatch):
    monkeypatch.setenv("OPEN_NOTEBOOK_ENV", "development")
    monkeypatch.setenv("OPEN_NOTEBOOK_CORS_ALLOW_ORIGINS", "*")
    monkeypatch.setenv("OPEN_NOTEBOOK_CORS_ALLOW_CREDENTIALS", "false")

    config = api_main._load_cors_config()

    assert config.allow_origins == ("*",)
    assert config.allow_credentials is False


def test_cors_headers_only_returned_for_allowed_origin(monkeypatch):
    monkeypatch.setattr(
        api_main,
        "CORS_CONFIG",
        api_main.CorsConfig(
            allow_origins=("https://app.example.com",),
            allow_credentials=True,
        ),
    )

    allowed_headers = api_main._cors_headers(_make_request("https://app.example.com"))
    denied_headers = api_main._cors_headers(_make_request("https://evil.example.com"))

    assert allowed_headers["Access-Control-Allow-Origin"] == "https://app.example.com"
    assert allowed_headers["Access-Control-Allow-Credentials"] == "true"
    assert "Access-Control-Allow-Origin" not in denied_headers


def test_cors_headers_support_wildcard_origin_without_credentials(monkeypatch):
    monkeypatch.setattr(
        api_main,
        "CORS_CONFIG",
        api_main.CorsConfig(
            allow_origins=("*",),
            allow_credentials=False,
        ),
    )

    headers = api_main._cors_headers(_make_request("https://any.example.com"))

    assert headers["Access-Control-Allow-Origin"] == "*"
    assert "Access-Control-Allow-Credentials" not in headers
