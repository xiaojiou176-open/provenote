from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "tooling/scripts/ci/check_architecture_guard.py"
)
SPEC = importlib.util.spec_from_file_location("check_architecture_guard", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def _write_file(path: Path, content: str = "pass\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_baseline_accepts_missing_duplicate_service_key(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps({"broad_exception_baseline": {"api": {"total": 0, "files": {}}}}),
        encoding="utf-8",
    )

    duplicate_baseline, broad_exception_baseline = GUARD.load_baseline(baseline_path)

    assert duplicate_baseline == {}
    assert "api" in broad_exception_baseline


def test_find_duplicate_service_modules_reports_only_duplicate_names(
    tmp_path: Path,
) -> None:
    _write_file(tmp_path / "services/api/sources_service.py")
    _write_file(tmp_path / "services/api/routers/sources_service.py")
    _write_file(tmp_path / "services/api/chat_service.py")

    duplicates = GUARD.find_duplicate_service_modules(tmp_path)

    assert sorted(duplicates.keys()) == ["sources_service.py"]
    assert duplicates["sources_service.py"] == [
        "services/api/routers/sources_service.py",
        "services/api/sources_service.py",
    ]


def test_duplicate_service_baseline_allows_unchanged_debt() -> None:
    baseline = {
        "sources_service.py": [
            "services/api/routers/sources_service.py",
            "services/api/sources_service.py",
        ]
    }
    current = {
        "sources_service.py": [
            "services/api/routers/sources_service.py",
            "services/api/sources_service.py",
        ]
    }

    regressions, reductions, notes, unchanged = (
        GUARD.compare_duplicate_service_modules_with_baseline(
            baseline,
            current,
        )
    )

    assert regressions == []
    assert reductions == []
    assert notes == []
    assert unchanged == [
        "- sources_service.py: unchanged at 2 duplicate modules (baseline debt)"
    ]


def test_duplicate_service_guard_fails_for_new_or_expanded_duplicates() -> None:
    baseline = {
        "sources_service.py": [
            "services/api/routers/sources_service.py",
            "services/api/sources_service.py",
        ]
    }
    current = {
        "sources_service.py": [
            "services/api/routers/sources_service.py",
            "services/api/sources_service.py",
            "services/api/legacy/sources_service.py",
        ],
        "chat_service.py": [
            "services/api/chat_service.py",
            "services/api/routers/chat_service.py",
        ],
    }

    regressions, reductions, notes, unchanged = (
        GUARD.compare_duplicate_service_modules_with_baseline(
            baseline,
            current,
        )
    )

    assert any(
        "sources_service.py: duplicate service modules increased 2 -> 3" in item
        for item in regressions
    )
    assert any(
        "chat_service.py: new duplicate service module set detected (2 files)" in item
        for item in regressions
    )
    assert reductions == []
    assert notes == []
    assert unchanged == []


def test_duplicate_service_guard_marks_reduction_as_improvement() -> None:
    baseline = {
        "sources_service.py": [
            "services/api/routers/sources_service.py",
            "services/api/sources_service.py",
        ]
    }
    current: dict[str, list[str]] = {}

    regressions, reductions, notes, unchanged = (
        GUARD.compare_duplicate_service_modules_with_baseline(
            baseline,
            current,
        )
    )

    assert regressions == []
    assert reductions == [
        "- sources_service.py: duplicate service modules resolved 2 -> 0"
    ]
    assert notes == []
    assert unchanged == []
