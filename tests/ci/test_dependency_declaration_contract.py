from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
VERSION_UTILS = REPO_ROOT / "packages/core/utils/version_utils.py"


def test_packaging_is_declared_when_version_utils_imports_it() -> None:
    source = VERSION_UTILS.read_text(encoding="utf-8")
    assert "from packaging.version import parse as parse_version" in source

    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]
    assert any(
        dep.startswith("packaging>=") or dep == "packaging" for dep in dependencies
    )
