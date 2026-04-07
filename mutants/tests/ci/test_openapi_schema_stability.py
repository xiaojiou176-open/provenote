from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_openapi_schema_names_do_not_collide_for_discovered_models() -> None:
    payload = yaml.safe_load(
        (REPO_ROOT / "contracts/api/openapi.yaml").read_text(encoding="utf-8")
    )
    schemas = payload.get("components", {}).get("schemas", {})

    assert "DiscoveredModelResponse" in schemas
    assert "ProviderDiscoveredModelResponse" in schemas
    assert "services__api__credential_models__DiscoveredModelResponse" not in schemas
