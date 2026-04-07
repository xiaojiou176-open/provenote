import pytest
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from services.api.auth import PasswordAuthMiddleware, check_api_password


def _build_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(
        PasswordAuthMiddleware,
        excluded_paths=["/health"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/protected")
    async def protected() -> dict[str, str]:
        return {"status": "ok"}

    @app.options("/api/protected")
    async def protected_options() -> dict[str, str]:
        return {"status": "preflight-ok"}

    return TestClient(app)


def test_password_middleware_rejects_missing_authorization_header(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "expected-password")
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)

    with _build_client() as client:
        response = client.get("/api/protected")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing authorization header"}


def test_password_middleware_rejects_invalid_authorization_header_format(
    monkeypatch,
) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "expected-password")
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)

    with _build_client() as client:
        response = client.get(
            "/api/protected",
            headers={"Authorization": "Token expected-password"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authorization header format"}


def test_password_middleware_rejects_invalid_password(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "expected-password")
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)

    with _build_client() as client:
        response = client.get(
            "/api/protected",
            headers={"Authorization": "Bearer wrong-password"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid password"}


def test_password_middleware_allows_valid_bearer_token(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "expected-password")
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)

    with _build_client() as client:
        response = client.get(
            "/api/protected",
            headers={"Authorization": "Bearer expected-password"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_password_middleware_skips_options_preflight(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "expected-password")
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)

    with _build_client() as client:
        response = client.options("/api/protected")

    assert response.status_code == 200
    assert response.json() == {"status": "preflight-ok"}


def test_check_api_password_allows_open_mode_without_configured_password(
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD", raising=False)
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)

    with TestClient(FastAPI()):
        assert check_api_password(None) is True


def test_check_api_password_rejects_missing_credentials(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "expected-password")
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)

    with TestClient(FastAPI()):
        with pytest.raises(HTTPException) as exc_info:
            check_api_password(None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing authorization header"


def test_check_api_password_rejects_non_bearer_scheme(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "expected-password")
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)

    credentials = HTTPAuthorizationCredentials(
        scheme="Basic",
        credentials="expected-password",
    )
    with TestClient(FastAPI()):
        with pytest.raises(HTTPException) as exc_info:
            check_api_password(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authorization scheme, expected Bearer"


def test_check_api_password_rejects_mismatched_password(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "expected-password")
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="wrong-password",
    )
    with TestClient(FastAPI()):
        with pytest.raises(HTTPException) as exc_info:
            check_api_password(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid password"


def test_check_api_password_accepts_valid_credentials(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "expected-password")
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="expected-password",
    )
    with TestClient(FastAPI()):
        assert check_api_password(credentials) is True
