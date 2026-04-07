from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Literal

from pydantic import BaseModel, Field

ArtifactKind = Literal["playwright-report", "test-results"]


class ArtifactFileEntry(BaseModel):
    kind: ArtifactKind
    relative_path: str
    size_bytes: int
    sha256: str


class ArtifactSourceSummary(BaseModel):
    root_dir: str
    file_count: int = 0
    total_bytes: int = 0
    bundle_sha256: str


class ArtifactManifest(BaseModel):
    generated_at: datetime
    root_dir: str
    files: list[ArtifactFileEntry] = Field(default_factory=list)
    total_files: int = 0
    total_bytes: int = 0
    kind_counts: dict[str, int] = Field(default_factory=dict)
    sources: dict[str, ArtifactSourceSummary] = Field(default_factory=dict)


def _sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        while True:
            block = handle.read(8192)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _iter_files(dir_path: Path) -> Iterable[Path]:
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            yield file_path


def _bundle_sha256(entries: list[tuple[str, str]], *, source_exists: bool) -> str:
    digest = hashlib.sha256()
    digest.update(b"present\n" if source_exists else b"missing\n")
    for relative_path, item_hash in entries:
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\n")
        digest.update(item_hash.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def build_artifact_manifest(
    base_dir: str | Path = ".",
    artifact_dirs: tuple[ArtifactKind, ...] = ("playwright-report", "test-results"),
) -> ArtifactManifest:
    root_dir = Path(base_dir).resolve()
    entries: list[ArtifactFileEntry] = []
    sources: dict[str, ArtifactSourceSummary] = {}

    for kind in artifact_dirs:
        target_dir = root_dir / kind
        source_exists = target_dir.exists()
        source_files = list(_iter_files(target_dir)) if source_exists else []
        source_entries: list[tuple[str, str]] = []
        source_total_bytes = 0

        for file_path in source_files:
            file_sha256 = _sha256_file(file_path)
            source_entries.append(
                (file_path.relative_to(target_dir).as_posix(), file_sha256)
            )
            source_total_bytes += file_path.stat().st_size
            entries.append(
                ArtifactFileEntry(
                    kind=kind,
                    relative_path=file_path.relative_to(root_dir).as_posix(),
                    size_bytes=file_path.stat().st_size,
                    sha256=file_sha256,
                )
            )
        sources[kind] = ArtifactSourceSummary(
            root_dir=target_dir.as_posix(),
            file_count=len(source_files),
            total_bytes=source_total_bytes,
            bundle_sha256=_bundle_sha256(source_entries, source_exists=source_exists),
        )

    kind_counts: dict[str, int] = {}
    for item in entries:
        kind_counts[item.kind] = kind_counts.get(item.kind, 0) + 1

    total_bytes = sum(item.size_bytes for item in entries)
    return ArtifactManifest(
        generated_at=datetime.now(UTC),
        root_dir=root_dir.as_posix(),
        files=entries,
        total_files=len(entries),
        total_bytes=total_bytes,
        kind_counts=kind_counts,
        sources=sources,
    )


def write_artifact_manifest(
    manifest: ArtifactManifest, output_path: str | Path
) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    return target
