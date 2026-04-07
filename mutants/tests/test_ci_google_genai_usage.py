from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "tooling/scripts/ci/check_google_genai_usage.py"
)
SPEC = importlib.util.spec_from_file_location("check_google_genai_usage", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_guard_detects_illegal_google_genai_import(tmp_path: Path) -> None:
    _write(
        tmp_path / "packages/core/ai/google_genai_adapter.py",
        "from google import genai\n",
    )
    _write(tmp_path / "foo.py", "from google import genai\n")

    violations = []
    for file_path in sorted(tmp_path.rglob("*.py")):
        rel = file_path.relative_to(tmp_path).as_posix()
        if rel in GUARD.ALLOWED_FILES:
            continue
        for lineno, line in enumerate(
            file_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if GUARD.IMPORT_PATTERN.search(line):
                violations.append(f"{rel}:{lineno}: {line.strip()}")

    assert violations == ["foo.py:1: from google import genai"]
