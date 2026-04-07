from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "tooling/scripts/ci/check_layer_boundaries.py"
)
SPEC = importlib.util.spec_from_file_location("check_layer_boundaries", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_find_boundary_violations_allows_domain_to_application_import(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "packages/core/domain/example.py",
        "from packages.core.application.client import api_client\n",
    )
    path_layers = [
        {"prefix": "services/api/", "layer": "api"},
        {"prefix": "packages/core/application/", "layer": "application"},
        {"prefix": "packages/core/", "layer": "open_notebook"},
    ]
    rules = {
        "api": ["api", "application", "open_notebook"],
        "application": ["application", "open_notebook"],
        "open_notebook": ["open_notebook", "application"],
    }

    violations = GUARD.find_boundary_violations(
        tmp_path,
        path_layers=path_layers,
        layer_import_rules=rules,
        exception_imports=[],
    )

    assert violations == []


def test_find_boundary_violations_blocks_application_to_api_import(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "packages/core/application/example.py",
        "from services.api.routers.notes import router\n",
    )
    path_layers = [
        {"prefix": "services/api/", "layer": "api"},
        {"prefix": "packages/core/application/", "layer": "application"},
        {"prefix": "packages/core/", "layer": "open_notebook"},
    ]
    rules = {
        "api": ["api", "application", "open_notebook"],
        "application": ["application", "open_notebook"],
        "open_notebook": ["open_notebook", "application"],
    }

    violations = GUARD.find_boundary_violations(
        tmp_path,
        path_layers=path_layers,
        layer_import_rules=rules,
        exception_imports=[],
    )

    assert violations == [
        "packages/core/application/example.py:1: layer 'application' must not import 'services.api.routers.notes' (target layer 'api')"
    ]


def test_layer_boundaries_registry_declares_zero_exception_debt() -> None:
    payload = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "config/architecture/layer-boundaries.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["exception_imports"] == []
