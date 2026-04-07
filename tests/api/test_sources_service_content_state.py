import socket
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from packages.core.application.commands.source_commands import validate_source_link_url
from packages.core.application.models import SourceCreate
from services.api.routers import sources_service
from services.api.routers.sources_service import _build_content_state


def test_build_content_state_link_success() -> None:
    data = SourceCreate(type="link", url="https://example.com")

    content_state = _build_content_state(data, file_path=None)

    assert content_state == {"url": "https://example.com"}


def test_validate_source_link_url_allows_public_http_and_https() -> None:
    assert validate_source_link_url("https://1.1.1.1/path") == "https://1.1.1.1/path"
    assert validate_source_link_url("http://8.8.8.8:8080") == "http://8.8.8.8:8080"


@pytest.mark.parametrize(
    "blocked_url",
    [
        "ftp://example.com/file.txt",
        "http://localhost:8000/health",
        "http://127.0.0.1:8080/private",
        "https://[::1]/admin",
        "http://10.0.0.8/internal",
        "http://192.168.1.20/",
        "http://169.254.169.254/latest/meta-data",
        "http://100.100.100.200/latest/meta-data",
        "https://metadata.google.internal/computeMetadata/v1",
    ],
)
def test_build_content_state_link_rejects_ssrf_targets(blocked_url: str) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _build_content_state(SourceCreate(type="link", url=blocked_url), file_path=None)

    assert exc_info.value.status_code == 400
    assert (
        "link url" in str(exc_info.value.detail).lower()
        or "blocked" in str(exc_info.value.detail).lower()
    )


def test_validate_source_link_url_rejects_hostname_resolving_to_private_ip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "packages.core.application.commands.source_commands.socket.getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, None, None, None, ("10.9.8.7", 0))],
    )

    with pytest.raises(ValueError, match="resolves to a blocked"):
        validate_source_link_url("https://safe-host.example/path")


def test_validate_source_link_url_rejects_when_dns_resolution_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_gaierror(*_args, **_kwargs):
        raise socket.gaierror("dns failed")

    monkeypatch.setattr(
        "packages.core.application.commands.source_commands.socket.getaddrinfo",
        _raise_gaierror,
    )

    with pytest.raises(ValueError, match="could not be resolved"):
        validate_source_link_url("https://safe-host.example/path")


def test_build_content_state_upload_prefers_runtime_file_path_and_preserves_delete_source() -> (
    None
):
    data = SourceCreate(
        type="upload",
        file_path="/tmp/original.txt",
        delete_source=True,
    )

    content_state = _build_content_state(data, file_path="/tmp/runtime.txt")

    assert content_state["file_path"] == "/tmp/runtime.txt"
    assert content_state["delete_source"] is True


def test_build_content_state_upload_rejects_request_file_path_without_uploaded_file() -> (
    None
):
    data = SourceCreate(type="upload", file_path="/tmp/from-request.txt")

    with pytest.raises(HTTPException) as exc_info:
        _build_content_state(data, file_path=None)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "File upload is required for upload type"


@pytest.mark.parametrize(
    ("source_data", "expected_detail"),
    [
        (SourceCreate(type="link"), "URL is required for link type"),
        (
            SourceCreate(type="upload"),
            "File upload is required for upload type",
        ),
        (SourceCreate(type="text"), "Content is required for text type"),
        (
            SourceCreate(type="legacy"),
            "Invalid source type. Must be link, upload, or text",
        ),
    ],
)
def test_build_content_state_rejects_invalid_payloads(
    source_data: SourceCreate,
    expected_detail: str,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _build_content_state(source_data, file_path=None)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == expected_detail


class _FakeCommandResult:
    def __init__(self, *, success: bool, error_message: str = "") -> None:
        self._success = success
        self.error_message = error_message

    def is_success(self) -> bool:
        return self._success


class _FakeSource:
    def __init__(self) -> None:
        self.id = "source:test"
        self.command = "command:existing"
        self.deleted = False

    async def delete(self) -> bool:
        self.deleted = True
        return True

    async def get_status(self) -> str:
        return "running"


@pytest.mark.asyncio
async def test_process_source_sync_hides_internal_error_details() -> None:
    source_data = SourceCreate(type="text", content="hello", notebooks=[])
    fake_source = _FakeSource()
    fake_result = _FakeCommandResult(
        success=False,
        error_message="permission denied: /private/secret/path",
    )

    with patch.object(
        sources_service,
        "_create_source_shell",
        new=AsyncMock(return_value=fake_source),
    ):
        with patch.object(
            sources_service.asyncio,
            "to_thread",
            new=AsyncMock(return_value=fake_result),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await sources_service._process_source_sync(
                    source_data=source_data,
                    content_state={"content": "hello"},
                    transformation_ids=[],
                )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to process source"
    assert fake_source.deleted is True


@pytest.mark.asyncio
async def test_retry_source_processing_rejects_when_already_running() -> None:
    fake_source = _FakeSource()

    with patch.object(
        sources_service.Source, "get", new=AsyncMock(return_value=fake_source)
    ):
        with patch.object(
            sources_service, "repo_query", new=AsyncMock()
        ) as mock_repo_query:
            with pytest.raises(HTTPException) as exc_info:
                await sources_service.retry_source_processing_service("source:test")

    assert exc_info.value.status_code == 400
    assert "already processing" in exc_info.value.detail
    mock_repo_query.assert_not_called()


@pytest.mark.asyncio
async def test_retry_source_processing_rejects_blocked_asset_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_source = _FakeSource()
    fake_source.command = None
    fake_source.asset = SimpleNamespace(url="http://127.0.0.1:9000", file_path=None)
    fake_source.full_text = None

    monkeypatch.setattr(
        sources_service.Source, "get", AsyncMock(return_value=fake_source)
    )
    monkeypatch.setattr(
        sources_service,
        "repo_query",
        AsyncMock(return_value=[{"notebook_id": "notebook:1"}]),
    )
    submit_mock = AsyncMock(return_value="command:noop")
    monkeypatch.setattr(
        sources_service.CommandService, "submit_command_job", submit_mock
    )

    with pytest.raises(HTTPException) as exc_info:
        await sources_service.retry_source_processing_service("source:test")

    assert exc_info.value.status_code == 400
    assert "blocked" in str(exc_info.value.detail).lower()
    submit_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_source_service_upload_rejects_legacy_file_path_even_within_uploads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    uploads_root = tmp_path / "uploads"
    uploads_root.mkdir(parents=True)
    legacy_file = uploads_root / "legacy.txt"
    legacy_file.write_text("legacy payload", encoding="utf-8")

    monkeypatch.setattr(sources_service, "UPLOADS_FOLDER", str(uploads_root))
    monkeypatch.setattr(
        sources_service, "_validate_notebooks", AsyncMock(return_value=None)
    )
    with pytest.raises(HTTPException) as exc_info:
        await sources_service.create_source_service(
            SourceCreate(type="upload", file_path=str(legacy_file), notebooks=["n1"]),
            upload_file=None,
        )

    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == "Legacy file_path upload is no longer supported. Use multipart upload."
    )


@pytest.mark.asyncio
async def test_create_source_service_upload_rejects_legacy_file_path_outside_uploads_whitelist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    uploads_root = tmp_path / "uploads"
    uploads_root.mkdir(parents=True)
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("outside", encoding="utf-8")

    monkeypatch.setattr(sources_service, "UPLOADS_FOLDER", str(uploads_root))
    monkeypatch.setattr(
        sources_service, "_validate_notebooks", AsyncMock(return_value=None)
    )

    with pytest.raises(HTTPException) as exc_info:
        await sources_service.create_source_service(
            SourceCreate(type="upload", file_path=str(outside_file), notebooks=["n1"]),
            upload_file=None,
        )

    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == "Legacy file_path upload is no longer supported. Use multipart upload."
    )


@pytest.mark.asyncio
async def test_create_source_service_upload_prefers_multipart_file_over_legacy_file_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    uploads_root = tmp_path / "uploads"
    uploads_root.mkdir(parents=True)
    multipart_saved_file = uploads_root / "multipart.txt"
    multipart_saved_file.write_text("multipart payload", encoding="utf-8")

    monkeypatch.setattr(
        sources_service, "_validate_notebooks", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(
        sources_service, "_validate_transformations", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(
        sources_service,
        "save_uploaded_file",
        AsyncMock(return_value=str(multipart_saved_file)),
    )
    process_sync_mock = AsyncMock(return_value={"mode": "sync"})
    monkeypatch.setattr(sources_service, "_process_source_sync", process_sync_mock)

    result = await sources_service.create_source_service(
        SourceCreate(
            type="upload",
            file_path="/etc/passwd",
            notebooks=["n1"],
        ),
        upload_file=SimpleNamespace(filename="multipart.txt"),
    )

    assert result == {"mode": "sync"}
    content_state = process_sync_mock.await_args.args[1]
    assert content_state["file_path"] == str(multipart_saved_file)
