from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


def test_get_transformation_returns_404_when_missing(api_client) -> None:
    with patch(
        "services.api.routers.transformations.Transformation.get",
        new=AsyncMock(return_value=None),
    ):
        response = api_client.get("/api/transformations/tr-missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Transformation not found"


def test_delete_transformation_returns_404_when_missing(api_client) -> None:
    with patch(
        "services.api.routers.transformations.Transformation.get",
        new=AsyncMock(return_value=None),
    ):
        response = api_client.delete("/api/transformations/tr-missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Transformation not found"


def test_execute_transformation_returns_404_when_transformation_missing(
    api_client,
) -> None:
    with patch(
        "services.api.routers.transformations.Transformation.get",
        new=AsyncMock(return_value=None),
    ):
        response = api_client.post(
            "/api/transformations/execute",
            json={
                "transformation_id": "tr-missing",
                "model_id": "model-1",
                "input_text": "hello",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Transformation not found"


def test_execute_transformation_returns_404_when_model_missing(api_client) -> None:
    with (
        patch(
            "services.api.routers.transformations.Transformation.get",
            new=AsyncMock(
                return_value=SimpleNamespace(
                    id="tr-1",
                    name="n",
                    title="t",
                    description="d",
                    prompt="p",
                    apply_default=False,
                    created="2026-01-01T00:00:00Z",
                    updated="2026-01-01T00:00:00Z",
                )
            ),
        ),
        patch(
            "services.api.routers.transformations.Model.get",
            new=AsyncMock(return_value=None),
        ),
    ):
        response = api_client.post(
            "/api/transformations/execute",
            json={
                "transformation_id": "tr-1",
                "model_id": "model-missing",
                "input_text": "hello",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Model not found"
