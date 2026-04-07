from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from services.api.routers import sources_helpers


@pytest.mark.asyncio
async def test_save_uploaded_file_sanitizes_traversal_filename(
    monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(tmp_path))
    upload = UploadFile(filename="../escape.txt", file=BytesIO(b"payload"))

    saved_path = await sources_helpers.save_uploaded_file(upload)
    resolved_saved_path = Path(saved_path).resolve()

    assert resolved_saved_path.parent == tmp_path.resolve()
    assert resolved_saved_path.name == "escape.txt"
    assert resolved_saved_path.read_bytes() == b"payload"


@pytest.mark.asyncio
async def test_save_uploaded_file_sanitizes_absolute_filename(
    monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(tmp_path))
    upload = UploadFile(filename="/tmp/absolute.txt", file=BytesIO(b"x"))

    saved_path = await sources_helpers.save_uploaded_file(upload)
    resolved_saved_path = Path(saved_path).resolve()

    assert resolved_saved_path.parent == tmp_path.resolve()
    assert resolved_saved_path.name == "absolute.txt"
    assert resolved_saved_path.read_bytes() == b"x"


@pytest.mark.asyncio
async def test_save_uploaded_file_rejects_empty_payload(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(tmp_path))
    upload = UploadFile(filename="empty.txt", file=BytesIO(b""))

    with pytest.raises(ValueError, match="Uploaded file is empty"):
        await sources_helpers.save_uploaded_file(upload)


@pytest.mark.asyncio
async def test_resolve_source_file_blocks_parent_traversal_path(
    monkeypatch, tmp_path: Path
):
    uploads_root = tmp_path / "uploads"
    uploads_root.mkdir(parents=True)
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("outside", encoding="utf-8")
    escaped_path = uploads_root / ".." / "outside.txt"

    source = SimpleNamespace(asset=SimpleNamespace(file_path=str(escaped_path)))
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(uploads_root))
    monkeypatch.setattr(sources_helpers.Source, "get", AsyncMock(return_value=source))

    with pytest.raises(HTTPException) as exc_info:
        await sources_helpers.resolve_source_file("source:1")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_resolve_source_file_blocks_absolute_path(monkeypatch, tmp_path: Path):
    uploads_root = tmp_path / "uploads"
    uploads_root.mkdir(parents=True)
    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("secret", encoding="utf-8")

    source = SimpleNamespace(
        asset=SimpleNamespace(file_path=str(outside_file.resolve()))
    )
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(uploads_root))
    monkeypatch.setattr(sources_helpers.Source, "get", AsyncMock(return_value=source))

    with pytest.raises(HTTPException) as exc_info:
        await sources_helpers.resolve_source_file("source:2")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_resolve_source_file_blocks_prefix_collision_directory(
    monkeypatch, tmp_path: Path
):
    uploads_root = tmp_path / "uploads"
    uploads_root.mkdir(parents=True)
    colliding_root = tmp_path / "uploads-evil"
    colliding_root.mkdir(parents=True)
    colliding_file = colliding_root / "steal.txt"
    colliding_file.write_text("stolen", encoding="utf-8")

    source = SimpleNamespace(asset=SimpleNamespace(file_path=str(colliding_file)))
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(uploads_root))
    monkeypatch.setattr(sources_helpers.Source, "get", AsyncMock(return_value=source))

    with pytest.raises(HTTPException) as exc_info:
        await sources_helpers.resolve_source_file("source:3")
    assert exc_info.value.status_code == 404


def test_is_source_file_available_blocks_prefix_collision_directory(
    monkeypatch, tmp_path: Path
):
    uploads_root = tmp_path / "uploads"
    uploads_root.mkdir(parents=True)
    colliding_root = tmp_path / "uploads-evil"
    colliding_root.mkdir(parents=True)
    colliding_file = colliding_root / "steal.txt"
    colliding_file.write_text("stolen", encoding="utf-8")

    source = SimpleNamespace(asset=SimpleNamespace(file_path=str(colliding_file)))
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(uploads_root))

    assert sources_helpers.is_source_file_available(source) is False


@pytest.mark.asyncio
async def test_save_uploaded_file_rejects_unsupported_extension(
    monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(tmp_path))
    upload = UploadFile(filename="payload.exe", file=BytesIO(b"x"))

    with pytest.raises(ValueError, match="Unsupported file type"):
        await sources_helpers.save_uploaded_file(upload)


@pytest.mark.asyncio
async def test_save_uploaded_file_rejects_oversized_payload(
    monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(sources_helpers, "UPLOADS_FOLDER", str(tmp_path))
    monkeypatch.setenv("OPEN_NOTEBOOK_MAX_UPLOAD_BYTES", "4")
    upload = UploadFile(filename="small.txt", file=BytesIO(b"12345"))

    with pytest.raises(ValueError, match="File size exceeds limit"):
        await sources_helpers.save_uploaded_file(upload)
