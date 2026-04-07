from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


def test_get_insight_success(api_client) -> None:
    insight = SimpleNamespace(
        id="source_insight:1",
        insight_type="summary",
        content="key points",
        created="2026-01-01T00:00:00Z",
        updated="2026-01-01T00:01:00Z",
        get_source=AsyncMock(return_value=SimpleNamespace(id="source:1")),
    )

    with patch(
        "services.api.routers.insights.SourceInsight.get",
        new=AsyncMock(return_value=insight),
    ):
        response = api_client.get("/api/insights/source_insight:1")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "source_insight:1"
    assert body["source_id"] == "source:1"
    assert body["insight_type"] == "summary"


def test_get_insight_not_found_returns_404(api_client) -> None:
    with patch(
        "services.api.routers.insights.SourceInsight.get",
        new=AsyncMock(return_value=None),
    ):
        response = api_client.get("/api/insights/source_insight:missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Insight not found"


def test_get_insight_internal_error_hides_exception_detail(api_client) -> None:
    with patch(
        "services.api.routers.insights.SourceInsight.get",
        new=AsyncMock(side_effect=RuntimeError("db credentials leaked")),
    ):
        response = api_client.get("/api/insights/source_insight:1")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    assert "credentials" not in response.text


def test_delete_insight_success(api_client) -> None:
    insight = SimpleNamespace(delete=AsyncMock(return_value=None))
    with patch(
        "services.api.routers.insights.SourceInsight.get",
        new=AsyncMock(return_value=insight),
    ):
        response = api_client.delete("/api/insights/source_insight:1")

    assert response.status_code == 200
    assert response.json()["message"] == "Insight deleted successfully"


def test_save_insight_as_note_success_forwards_notebook_id(api_client) -> None:
    note = SimpleNamespace(
        id="note:from-insight",
        title="From insight",
        content="body",
        note_type="ai",
        created="2026-01-01T00:00:00Z",
        updated="2026-01-01T00:00:00Z",
    )
    insight = SimpleNamespace(save_as_note=AsyncMock(return_value=note))

    with patch(
        "services.api.routers.insights.SourceInsight.get",
        new=AsyncMock(return_value=insight),
    ):
        response = api_client.post(
            "/api/insights/source_insight:1/save-as-note",
            json={"notebook_id": "notebook:1"},
        )

    assert response.status_code == 200
    assert response.json()["id"] == "note:from-insight"
    insight.save_as_note.assert_awaited_once_with("notebook:1")


def test_save_insight_as_note_internal_error_hides_detail(api_client) -> None:
    with patch(
        "services.api.routers.insights.SourceInsight.get",
        new=AsyncMock(side_effect=RuntimeError("private stacktrace")),
    ):
        response = api_client.post(
            "/api/insights/source_insight:1/save-as-note",
            json={"notebook_id": "notebook:1"},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    assert "stacktrace" not in response.text
