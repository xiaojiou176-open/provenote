from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_runtime_surfaces_authority_fields_are_present() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/runtime/runtime-surfaces.json").read_text(encoding="utf-8")
    )
    surfaces = payload["surfaces"]
    assert surfaces
    for item in surfaces:
        for field in (
            "scope",
            "rebuildable",
            "ttl_policy",
            "cleanup_owner",
            "root_cleanliness_required",
        ):
            assert field in item, (
                f"missing runtime authority field {field} for {item['name']}"
            )


def test_root_cleanliness_required_surfaces_live_under_runtime_cache() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/runtime/runtime-surfaces.json").read_text(encoding="utf-8")
    )
    required_surfaces = [
        item for item in payload["surfaces"] if item["root_cleanliness_required"]
    ]
    assert required_surfaces
    for item in required_surfaces:
        assert item["canonical_path"].startswith(".runtime-cache/")
