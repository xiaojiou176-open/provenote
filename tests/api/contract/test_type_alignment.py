"""Frontend-Backend type alignment tests."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED_CONTRACT = REPO_ROOT / "apps/web/src/lib/api/generated/openapi-contract.ts"
OPENAPI_CONTRACT = REPO_ROOT / "contracts/api/openapi.yaml"

SCRIPT_PATH = REPO_ROOT / "tooling/scripts/api/generate_frontend_api_contract.py"
SPEC = importlib.util.spec_from_file_location(
    "generate_frontend_api_contract", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


def test_generated_frontend_contract_exists() -> None:
    assert GENERATED_CONTRACT.exists(), (
        "generated frontend contract metadata must exist"
    )


def test_generated_frontend_contract_matches_openapi_hash() -> None:
    payload = yaml.safe_load(OPENAPI_CONTRACT.read_text(encoding="utf-8"))
    expected = GENERATOR._render(payload)
    actual = GENERATED_CONTRACT.read_text(encoding="utf-8")
    assert actual == expected


def test_generated_frontend_contract_exposes_operation_ids() -> None:
    content = GENERATED_CONTRACT.read_text(encoding="utf-8")
    assert "openApiOperationIds" in content
    assert "get_notebooks_api_notebooks_get" in content
