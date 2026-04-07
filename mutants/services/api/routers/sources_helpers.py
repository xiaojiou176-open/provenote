import json
import os
import re
from pathlib import Path
from typing import Optional

from fastapi import File, Form, HTTPException, UploadFile

from packages.core.application.models import SourceCreate
from packages.core.config import UPLOADS_FOLDER
from packages.core.domain.notebook import Source
from packages.core.observability.logger import logger

UPLOAD_CHUNK_SIZE_BYTES = 1024 * 1024
DEFAULT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".csv",
    ".json",
    ".html",
}
SAFE_UPLOAD_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._() -]{0,255}$")


def _extract_safe_basename(filename: str) -> str:
    normalized = filename.replace("\\", "/")
    basename = normalized.rsplit("/", maxsplit=1)[-1]
    if basename in {"", ".", ".."} or not SAFE_UPLOAD_NAME_RE.fullmatch(basename):
        raise ValueError("Invalid filename provided")
    return basename


def _resolve_named_path_inside_directory(
    path_value: str,
    directory: str,
    *,
    must_exist: bool = False,
    require_file: bool = False,
) -> Path:
    uploads_root = Path(directory)
    safe_filename = _extract_safe_basename(path_value)
    if must_exist:
        try:
            for candidate in uploads_root.iterdir():
                if candidate.name != safe_filename:
                    continue
                if require_file and (not candidate.is_file() or candidate.is_symlink()):
                    raise ValueError("Resolved path is not a file")
                return candidate
        except FileNotFoundError:
            pass
        raise ValueError("Resolved path does not exist")

    return uploads_root / safe_filename


def _is_path_within_directory(path: str, directory: str) -> bool:
    resolved_path = Path(path).resolve(strict=False)
    resolved_directory = Path(directory).resolve(strict=False)
    try:
        resolved_path.relative_to(resolved_directory)
        return True
    except ValueError:
        return False


def generate_unique_filename(original_filename: str, upload_folder: str) -> str:
    """Generate unique filename like Streamlit app (append counter if file exists)."""
    file_path = Path(upload_folder)
    file_path.mkdir(parents=True, exist_ok=True)

    safe_filename = _extract_safe_basename(original_filename)
    stem = Path(safe_filename).stem
    suffix = Path(safe_filename).suffix

    counter = 0
    while True:
        if counter == 0:
            new_filename = safe_filename
        else:
            new_filename = f"{stem} ({counter}){suffix}"

        full_path = file_path / new_filename
        resolved_path = _resolve_named_path_inside_directory(full_path.name, upload_folder)
        if not resolved_path.exists():
            return str(resolved_path)
        counter += 1


def _max_upload_bytes() -> int:
    raw = os.getenv("OPEN_NOTEBOOK_MAX_UPLOAD_BYTES")
    if raw is None:
        return DEFAULT_MAX_UPLOAD_BYTES
    try:
        parsed = int(raw)
    except ValueError:
        return DEFAULT_MAX_UPLOAD_BYTES
    return max(parsed, 1)


def _validate_upload_filename(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix and suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {suffix}. "
            f"Allowed types: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}"
        )


async def save_uploaded_file(upload_file: UploadFile) -> str:
    """Save uploaded file to uploads folder and return file path."""
    if not upload_file.filename:
        raise ValueError("No filename provided")
    _validate_upload_filename(upload_file.filename)

    file_path = generate_unique_filename(upload_file.filename, UPLOADS_FOLDER)

    try:
        max_upload_bytes = _max_upload_bytes()
        bytes_written = 0
        with open(file_path, "wb") as file_handle:
            while True:
                chunk = await upload_file.read(UPLOAD_CHUNK_SIZE_BYTES)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > max_upload_bytes:
                    raise ValueError(
                        f"File size exceeds limit ({max_upload_bytes} bytes)"
                    )
                file_handle.write(chunk)
        if bytes_written == 0:
            raise ValueError("Uploaded file is empty")

        logger.info(f"Saved uploaded file to: {file_path}")
        return file_path
    except Exception as exc:
        logger.error(f"Failed to save uploaded file: {exc}")
        if os.path.exists(file_path):
            os.unlink(file_path)
        raise


def cleanup_uploaded_file(
    file_path: Optional[str], upload_file: Optional[UploadFile]
) -> None:
    """Best-effort cleanup for uploaded temp files."""
    if not (file_path and upload_file):
        return
    try:
        resolved_path = _resolve_named_path_inside_directory(
            file_path,
            UPLOADS_FOLDER,
            must_exist=True,
            require_file=True,
        )
        os.unlink(resolved_path)
    except Exception:
        pass


def parse_source_form_data(
    type: str = Form(...),
    notebook_id: Optional[str] = Form(None),
    notebooks: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    transformations: Optional[str] = Form(None),
    embed: str = Form("false"),
    delete_source: str = Form("false"),
    async_processing: str = Form("false"),
    file: Optional[UploadFile] = File(None),
) -> tuple[SourceCreate, Optional[UploadFile]]:
    """Parse form data into SourceCreate model and return upload file separately."""

    def str_to_bool(value: str) -> bool:
        return value.lower() in ("true", "1", "yes", "on")

    embed_bool = str_to_bool(embed)
    delete_source_bool = str_to_bool(delete_source)
    async_processing_bool = str_to_bool(async_processing)

    notebooks_list = None
    if notebooks:
        try:
            notebooks_list = json.loads(notebooks)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in notebooks field: {notebooks}")
            raise ValueError("Invalid JSON in notebooks field")

    transformations_list = []
    if transformations:
        try:
            transformations_list = json.loads(transformations)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in transformations field: {transformations}")
            raise ValueError("Invalid JSON in transformations field")

    source_data = SourceCreate(
        type=type,
        notebook_id=notebook_id,
        notebooks=notebooks_list,
        url=url,
        content=content,
        title=title,
        file_path=None,
        transformations=transformations_list,
        embed=embed_bool,
        delete_source=delete_source_bool,
        async_processing=async_processing_bool,
    )

    return source_data, file


async def resolve_source_file(source_id: str) -> tuple[str, str]:
    source = await Source.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    file_path = source.asset.file_path if source.asset else None
    if not file_path:
        raise HTTPException(status_code=404, detail="Source has no file to download")

    try:
        resolved_path_obj = _resolve_named_path_inside_directory(
            file_path,
            UPLOADS_FOLDER,
        )
    except ValueError:
        resolved_path = str(Path(file_path).resolve(strict=False))
        logger.warning(
            f"Blocked download outside uploads directory for source {source_id}: {resolved_path}"
        )
        raise HTTPException(status_code=403, detail="Access to file denied")

    if not resolved_path_obj.exists() or not resolved_path_obj.is_file():
        raise HTTPException(status_code=404, detail="File not found on server")

    resolved_path = str(resolved_path_obj)
    filename = os.path.basename(resolved_path)
    return resolved_path, filename


def is_source_file_available(source: Source) -> Optional[bool]:
    if not source or not source.asset or not source.asset.file_path:
        return None

    file_path = source.asset.file_path
    try:
        resolved_path = _resolve_named_path_inside_directory(file_path, UPLOADS_FOLDER)
    except ValueError:
        return False
    return resolved_path.exists()
