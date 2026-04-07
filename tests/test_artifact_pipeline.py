from __future__ import annotations

import hashlib
import json
from pathlib import Path

from packages.core.testing.artifact_pipeline import (
    build_artifact_manifest,
    write_artifact_manifest,
)


def _write_file(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_build_artifact_manifest_collects_playwright_and_test_results(
    tmp_path: Path,
) -> None:
    html_path = tmp_path / "playwright-report/index.html"
    png_path = tmp_path / "test-results/spec-1/screenshot.png"
    json_path = tmp_path / "test-results/results.json"
    _write_file(html_path, b"<html>report</html>")
    _write_file(png_path, b"\x89PNGdemo")
    _write_file(json_path, b'{"passed": 1}')

    manifest = build_artifact_manifest(tmp_path)

    assert manifest.total_files == 3
    assert manifest.kind_counts == {"playwright-report": 1, "test-results": 2}
    assert (
        manifest.total_bytes
        == html_path.stat().st_size + png_path.stat().st_size + json_path.stat().st_size
    )
    assert [item.relative_path for item in manifest.files] == [
        "playwright-report/index.html",
        "test-results/results.json",
        "test-results/spec-1/screenshot.png",
    ]
    digest = hashlib.sha256(b"<html>report</html>").hexdigest()
    assert manifest.files[0].sha256 == digest


def test_write_artifact_manifest_persists_json(tmp_path: Path) -> None:
    _write_file(tmp_path / "playwright-report/index.html", b"<html/>")
    manifest = build_artifact_manifest(tmp_path)
    target = write_artifact_manifest(manifest, tmp_path / "artifacts/manifest.json")

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["total_files"] == 1
    assert payload["files"][0]["relative_path"] == "playwright-report/index.html"
