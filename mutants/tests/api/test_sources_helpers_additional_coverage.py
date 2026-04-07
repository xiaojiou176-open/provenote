from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from services.api.routers import sources_helpers


def test_extract_safe_basename_rejects_invalid_basenames() -> None:
    for candidate in ("", ".", "..", "dir/..", "dir/."):
        with pytest.raises(ValueError, match="Invalid filename provided"):
            sources_helpers._extract_safe_basename(candidate)


def test_generate_unique_filename_adds_counter_for_existing_file(
    tmp_path: Path,
) -> None:
    first = tmp_path / "report.txt"
    first.write_text("existing", encoding="utf-8")

    unique = sources_helpers.generate_unique_filename("report.txt", str(tmp_path))

    assert Path(unique).name == "report (1).txt"


def test_generate_unique_filename_rejects_outside_upload_dir(
    monkeypatch, tmp_path: Path
) -> None:
    def _raise_outside(*_args, **_kwargs):
        raise ValueError("Resolved path is outside uploads directory")

    monkeypatch.setattr(
        sources_helpers,
        "_resolve_named_path_inside_directory",
        _raise_outside,
    )
    with pytest.raises(ValueError, match="outside uploads directory"):
        sources_helpers.generate_unique_filename("safe.txt", str(tmp_path))


def test_max_upload_bytes_uses_default_for_invalid_env(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_MAX_UPLOAD_BYTES", "not-an-int")
    assert (
        sources_helpers._max_upload_bytes() == sources_helpers.DEFAULT_MAX_UPLOAD_BYTES
    )


def test_max_upload_bytes_clamps_non_positive_values(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_MAX_UPLOAD_BYTES", "-999")
    assert sources_helpers._max_upload_bytes() == 1


@pytest.mark.asyncio
async def test_save_uploaded_file_rejects_missing_filename(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(tmp_path))
    upload = UploadFile(filename="", file=BytesIO(b"payload"))

    with pytest.raises(ValueError, match="No filename provided"):
        await sources_helpers.save_uploaded_file(upload)


def test_cleanup_uploaded_file_removes_file_when_inputs_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    saved_file = tmp_path / "to-clean.txt"
    saved_file.write_text("temp", encoding="utf-8")
    upload = UploadFile(filename="to-clean.txt", file=BytesIO(b"temp"))
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(tmp_path))

    sources_helpers.cleanup_uploaded_file(str(saved_file), upload)

    assert not saved_file.exists()


def test_parse_source_form_data_parses_json_and_boolean_flags() -> None:
    source_data, upload = sources_helpers.parse_source_form_data(
        type="text",
        notebook_id=None,
        notebooks='["notebook:1", "notebook:2"]',
        url="https://example.com",
        content="hello",
        title="Title",
        transformations='["clean"]',
        embed="yes",
        delete_source="1",
        async_processing="on",
        file=None,
    )

    assert source_data.notebooks == ["notebook:1", "notebook:2"]
    assert source_data.transformations == ["clean"]
    assert source_data.embed is True
    assert source_data.delete_source is True
    assert source_data.async_processing is True
    assert upload is None


def test_parse_source_form_data_rejects_invalid_notebooks_json() -> None:
    with pytest.raises(ValueError, match="Invalid JSON in notebooks field"):
        sources_helpers.parse_source_form_data(
            type="text",
            notebooks='{"bad":',
            embed="false",
            delete_source="false",
            async_processing="false",
        )


def test_parse_source_form_data_rejects_invalid_transformations_json() -> None:
    with pytest.raises(ValueError, match="Invalid JSON in transformations field"):
        sources_helpers.parse_source_form_data(
            type="text",
            notebooks=None,
            transformations='{"bad":',
            embed="false",
            delete_source="false",
            async_processing="false",
        )


@pytest.mark.asyncio
async def test_resolve_source_file_returns_not_found_when_source_missing(
    monkeypatch,
) -> None:
    monkeypatch.setattr(sources_helpers.Source, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await sources_helpers.resolve_source_file("source:missing")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Source not found"


@pytest.mark.asyncio
async def test_resolve_source_file_returns_not_found_when_file_path_missing(
    monkeypatch,
) -> None:
    source = SimpleNamespace(asset=None)
    monkeypatch.setattr(sources_helpers.Source, "get", AsyncMock(return_value=source))

    with pytest.raises(HTTPException) as exc_info:
        await sources_helpers.resolve_source_file("source:no-file")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Source has no file to download"


@pytest.mark.asyncio
async def test_resolve_source_file_returns_not_found_when_file_missing_on_disk(
    monkeypatch, tmp_path: Path
) -> None:
    uploads_root = tmp_path / "uploads"
    uploads_root.mkdir(parents=True)
    missing_path = uploads_root / "missing.txt"
    source = SimpleNamespace(asset=SimpleNamespace(file_path=str(missing_path)))
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(uploads_root))
    monkeypatch.setattr(sources_helpers.Source, "get", AsyncMock(return_value=source))

    with pytest.raises(HTTPException) as exc_info:
        await sources_helpers.resolve_source_file("source:missing-file")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "File not found on server"


@pytest.mark.asyncio
async def test_resolve_source_file_returns_resolved_path_and_filename(
    monkeypatch, tmp_path: Path
) -> None:
    uploads_root = tmp_path / "uploads"
    uploads_root.mkdir(parents=True)
    data_file = uploads_root / "notes.txt"
    data_file.write_text("payload", encoding="utf-8")
    source = SimpleNamespace(asset=SimpleNamespace(file_path=str(data_file)))
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(uploads_root))
    monkeypatch.setattr(sources_helpers.Source, "get", AsyncMock(return_value=source))

    resolved_path, filename = await sources_helpers.resolve_source_file("source:ok")

    assert resolved_path == str(data_file.resolve())
    assert filename == "notes.txt"


def test_is_source_file_available_returns_none_without_asset() -> None:
    source = SimpleNamespace(asset=None)
    assert sources_helpers.is_source_file_available(source) is None


def test_is_source_file_available_returns_true_for_existing_file(
    monkeypatch, tmp_path: Path
) -> None:
    uploads_root = tmp_path / "uploads"
    uploads_root.mkdir(parents=True)
    data_file = uploads_root / "in-scope.txt"
    data_file.write_text("ok", encoding="utf-8")
    source = SimpleNamespace(asset=SimpleNamespace(file_path=str(data_file)))
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(uploads_root))

    assert sources_helpers.is_source_file_available(source) is True
