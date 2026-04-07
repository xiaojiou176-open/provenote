#!/usr/bin/env python3
"""PoC: show old vs fixed behavior for upload/download path traversal checks."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def old_download_allows(upload_root: Path, candidate: Path) -> bool:
    safe_root = os.path.realpath(str(upload_root))
    resolved_candidate = os.path.realpath(str(candidate))
    return resolved_candidate.startswith(safe_root)


def fixed_download_allows(upload_root: Path, candidate: Path) -> bool:
    safe_root = Path(upload_root).resolve(strict=False)
    resolved_candidate = Path(candidate).resolve(strict=False)
    try:
        return os.path.commonpath([str(resolved_candidate), str(safe_root)]) == str(
            safe_root
        )
    except ValueError:
        return False


def fixed_upload_name(raw_filename: str) -> str:
    normalized = raw_filename.replace("\\", "/")
    basename = normalized.rsplit("/", maxsplit=1)[-1]
    if basename in {"", ".", ".."}:
        raise ValueError(f"unsafe filename: {raw_filename!r}")
    return basename


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="path-guard-poc-") as tmp:
        root = Path(tmp)
        uploads = root / "uploads"
        uploads.mkdir(parents=True, exist_ok=True)

        prefix_collision_file = root / "uploads-evil" / "steal.txt"
        prefix_collision_file.parent.mkdir(parents=True, exist_ok=True)
        prefix_collision_file.write_text("stolen", encoding="utf-8")

        print("=== Download Guard PoC ===")
        print(f"uploads_root: {uploads}")
        print(f"candidate(prefix-collision): {prefix_collision_file}")
        print(
            f"old(startswith) allows: {old_download_allows(uploads, prefix_collision_file)}"
        )
        print(
            f"fixed(commonpath) allows: {fixed_download_allows(uploads, prefix_collision_file)}"
        )

        print("\n=== Upload Filename PoC ===")
        payloads = ["../escape.txt", "/tmp/absolute.txt", "safe.txt"]
        for payload in payloads:
            old_path = uploads / payload
            new_path = uploads / fixed_upload_name(payload)
            print(f"{payload!r} -> old:{old_path} | fixed:{new_path}")


if __name__ == "__main__":
    main()
