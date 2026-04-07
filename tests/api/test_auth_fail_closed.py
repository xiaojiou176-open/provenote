from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.api.auth import PasswordAuthMiddleware


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

    return TestClient(app)


def test_protected_route_allows_requests_when_password_not_configured(
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD", raising=False)
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)

    with _build_client() as client:
        response = client.get("/api/protected")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_excluded_route_still_accessible_when_password_not_configured(
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD", raising=False)
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)

    with _build_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
