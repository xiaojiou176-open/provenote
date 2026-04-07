import pytest
from pydantic import ValidationError

from packages.core.application.models import (
    AuditableBatchRequest,
    SetApiKeyRequest,
    SourceCreate,
    UITestRunRequest,
    normalize_ui_test_spec_path,
)


def test_source_create_rejects_notebook_id_and_notebooks_together() -> None:
    with pytest.raises(ValidationError) as exc_info:
        SourceCreate(
            type="text",
            content="hello",
            notebook_id="notebook:legacy",
            notebooks=["notebook:new"],
        )

    error_text = str(exc_info.value)
    assert "Cannot specify both 'notebook_id' and 'notebooks'" in error_text


def test_source_create_normalizes_single_notebook_id_to_notebooks() -> None:
    payload = SourceCreate(type="link", url="https://example.com", notebook_id="nb:1")

    assert payload.notebook_id == "nb:1"
    assert payload.notebooks == ["nb:1"]


def test_source_create_defaults_notebooks_to_empty_list() -> None:
    payload = SourceCreate(type="text", content="body")

    assert payload.notebook_id is None
    assert payload.notebooks == []


def test_set_api_key_request_trims_non_empty_string_fields() -> None:
    payload = SetApiKeyRequest(
        api_key="  test-key  ",
        base_url=" https://services.api.example.com/v1 ",
        endpoint=" https://azure.example.com ",
        api_version=" 2024-10-01 ",
        endpoint_llm=" https://llm.example.com ",
        endpoint_embedding=" https://embedding.example.com ",
        endpoint_stt=" https://stt.example.com ",
        endpoint_tts=" https://tts.example.com ",
        vertex_project="  my-project  ",
        vertex_location=" us-central1 ",
        vertex_credentials_path=" /tmp/key.json ",
    )

    assert payload.api_key == "test-key"
    assert payload.base_url == "https://services.api.example.com/v1"
    assert payload.endpoint == "https://azure.example.com"
    assert payload.api_version == "2024-10-01"
    assert payload.endpoint_llm == "https://llm.example.com"
    assert payload.endpoint_embedding == "https://embedding.example.com"
    assert payload.endpoint_stt == "https://stt.example.com"
    assert payload.endpoint_tts == "https://tts.example.com"
    assert payload.vertex_project == "my-project"
    assert payload.vertex_location == "us-central1"
    assert payload.vertex_credentials_path == "/tmp/key.json"


def test_set_api_key_request_normalizes_blank_strings_to_none() -> None:
    payload = SetApiKeyRequest(
        api_key=" \t ",
        base_url="",
        endpoint="  ",
        api_version="\n",
        endpoint_llm=" \r\n ",
        endpoint_embedding=" ",
        endpoint_stt="\t",
        endpoint_tts="",
        vertex_project=" ",
        vertex_location="\t ",
        vertex_credentials_path="  ",
    )

    assert payload.api_key is None
    assert payload.base_url is None
    assert payload.endpoint is None
    assert payload.api_version is None
    assert payload.endpoint_llm is None
    assert payload.endpoint_embedding is None
    assert payload.endpoint_stt is None
    assert payload.endpoint_tts is None
    assert payload.vertex_project is None
    assert payload.vertex_location is None
    assert payload.vertex_credentials_path is None


def test_set_api_key_request_keeps_explicit_none_values() -> None:
    payload = SetApiKeyRequest(
        api_key=None,
        base_url=None,
        endpoint=None,
        api_version=None,
        endpoint_llm=None,
        endpoint_embedding=None,
        endpoint_stt=None,
        endpoint_tts=None,
        vertex_project=None,
        vertex_location=None,
        vertex_credentials_path=None,
    )

    assert payload.api_key is None
    assert payload.base_url is None
    assert payload.endpoint is None
    assert payload.api_version is None
    assert payload.endpoint_llm is None
    assert payload.endpoint_embedding is None
    assert payload.endpoint_stt is None
    assert payload.endpoint_tts is None
    assert payload.vertex_project is None
    assert payload.vertex_location is None
    assert payload.vertex_credentials_path is None


@pytest.mark.parametrize(
    ("spec", "message"),
    [
        ("   ", "non-empty relative Playwright spec path"),
        ("e2e/folder/", "spec must point to a file path"),
        ("tests/login.spec.ts", "spec must resolve under 'e2e/'"),
    ],
)
def test_normalize_ui_test_spec_path_rejects_invalid_shapes(
    spec: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        normalize_ui_test_spec_path(spec)


def test_ui_test_run_request_allows_none_spec() -> None:
    payload = UITestRunRequest(
        project="chromium", dry_run=True, spec=None, timeout_seconds=5
    )

    assert payload.spec is None


def test_auditable_batch_request_source_ids_are_normalized() -> None:
    payload = AuditableBatchRequest(source_ids=[" source:1 ", "", "  ", "source:2"])
    assert payload.source_ids == ["source:1", "source:2"]


def test_auditable_batch_request_rejects_effectively_empty_source_ids() -> None:
    with pytest.raises(ValidationError, match="source_ids cannot be empty"):
        AuditableBatchRequest(source_ids=[" ", "\t", ""])
