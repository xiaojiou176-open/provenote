from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SIZE_LIMIT_CONFIG = REPO_ROOT / "apps/web/.size-limit.json"


def test_size_limit_targets_app_local_build_root() -> None:
    config = json.loads(SIZE_LIMIT_CONFIG.read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in config}
    assert ".runtime-cache/build/next/static/chunks/*.js" in paths
    assert ".runtime-cache/build/next/static/**/*.js" in paths
    assert ".runtime-cache/build/next/static/**/*.css" in paths
    assert not any(path.startswith("../../.runtime-cache/build/next") for path in paths)
