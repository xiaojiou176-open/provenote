from unittest.mock import MagicMock

from services.api.context_service import ContextService


def test_context_service_forwards_notebook_id_and_config(monkeypatch):
    expected = {"sources": [{"id": "source:1"}], "notes": []}
    get_context_mock = MagicMock(return_value=expected)
    monkeypatch.setattr(
        "services.api.context_service.api_client.get_notebook_context", get_context_mock
    )

    service = ContextService()
    result = service.get_notebook_context(
        "notebook-1",
        context_config={"sources": {"source:1": "insights"}},
    )

    assert result == expected
    get_context_mock.assert_called_once_with(
        notebook_id="notebook-1",
        context_config={"sources": {"source:1": "insights"}},
    )
