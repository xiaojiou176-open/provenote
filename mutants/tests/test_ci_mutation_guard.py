from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "tooling/scripts/ci/check_mutation_guard.py"
)
SPEC = importlib.util.spec_from_file_location("check_mutation_guard", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GUARD
SPEC.loader.exec_module(GUARD)


def _write_stats(
    path: Path, *, killed: int, survived: int, total: int, no_tests: int = 0
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "killed": killed,
        "survived": survived,
        "total": total,
        "no_tests": no_tests,
        "skipped": 0,
        "suspicious": 0,
        "timeout": 0,
        "check_was_interrupted_by_user": 0,
        "segfault": 0,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _run_guard(
    stats_path: Path,
    *,
    min_score: float = 80,
    max_no_tests: int = 0,
    baseline_stats: Path | None = None,
    max_survived_regression: int = 0,
    max_score_regression: float = 0,
) -> int:
    original_argv = sys.argv[:]
    try:
        sys.argv = [
            str(SCRIPT_PATH),
            "--stats-path",
            str(stats_path),
            "--min-score",
            str(min_score),
            "--max-no-tests",
            str(max_no_tests),
            "--max-survived-regression",
            str(max_survived_regression),
            "--max-score-regression",
            str(max_score_regression),
        ]
        if baseline_stats is not None:
            sys.argv.extend(["--baseline-stats", str(baseline_stats)])
        return GUARD.main()
    finally:
        sys.argv = original_argv


def test_mutation_guard_passes_when_score_and_no_tests_are_within_threshold(
    tmp_path: Path,
) -> None:
    stats_path = tmp_path / "mutmut-cicd-stats.json"
    _write_stats(stats_path, killed=80, survived=20, total=100, no_tests=0)

    assert _run_guard(stats_path, min_score=80, max_no_tests=0) == 0


def test_mutation_guard_fails_when_score_below_threshold(tmp_path: Path) -> None:
    stats_path = tmp_path / "mutmut-cicd-stats.json"
    _write_stats(stats_path, killed=70, survived=30, total=100, no_tests=0)

    assert _run_guard(stats_path, min_score=80, max_no_tests=0) == 1


def test_mutation_guard_fails_when_no_tests_exceeds_limit(tmp_path: Path) -> None:
    stats_path = tmp_path / "mutmut-cicd-stats.json"
    _write_stats(stats_path, killed=85, survived=15, total=100, no_tests=1)

    assert _run_guard(stats_path, min_score=80, max_no_tests=0) == 1


def test_mutation_guard_fails_on_survived_regression_against_baseline(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    _write_stats(baseline, killed=84, survived=16, total=100, no_tests=0)
    _write_stats(current, killed=84, survived=18, total=100, no_tests=0)

    assert (
        _run_guard(
            current,
            min_score=80,
            max_no_tests=0,
            baseline_stats=baseline,
            max_survived_regression=0,
            max_score_regression=0,
        )
        == 1
    )


def test_mutation_guard_fails_on_score_regression_against_baseline(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    _write_stats(baseline, killed=86, survived=14, total=100, no_tests=0)
    _write_stats(current, killed=84, survived=16, total=100, no_tests=0)

    assert (
        _run_guard(
            current,
            min_score=80,
            max_no_tests=0,
            baseline_stats=baseline,
            max_survived_regression=5,
            max_score_regression=0,
        )
        == 1
    )


def test_mutation_guard_allows_controlled_regression_budget(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    _write_stats(baseline, killed=85, survived=15, total=100, no_tests=0)
    _write_stats(current, killed=84, survived=16, total=100, no_tests=0)

    assert (
        _run_guard(
            current,
            min_score=80,
            max_no_tests=0,
            baseline_stats=baseline,
            max_survived_regression=1,
            max_score_regression=1.1,
        )
        == 0
    )


def test_mutation_guard_fails_when_timeout_mutants_exist(tmp_path: Path) -> None:
    stats_path = tmp_path / "mutmut-cicd-stats.json"
    payload = {
        "killed": 90,
        "survived": 10,
        "total": 100,
        "no_tests": 0,
        "skipped": 0,
        "suspicious": 0,
        "timeout": 1,
        "check_was_interrupted_by_user": 0,
        "segfault": 0,
    }
    stats_path.write_text(json.dumps(payload), encoding="utf-8")
    assert _run_guard(stats_path, min_score=80, max_no_tests=0) == 1


def test_mutation_guard_fails_when_survived_exceeds_cap(tmp_path: Path) -> None:
    stats_path = tmp_path / "mutmut-cicd-stats.json"
    _write_stats(stats_path, killed=84, survived=16, total=100, no_tests=0)

    original_argv = sys.argv[:]
    try:
        sys.argv = [
            str(SCRIPT_PATH),
            "--stats-path",
            str(stats_path),
            "--min-score",
            "80",
            "--max-no-tests",
            "0",
            "--max-survived",
            "15",
        ]
        assert GUARD.main() == 1
    finally:
        sys.argv = original_argv


def test_mutation_guard_writes_auditable_report_on_pass(tmp_path: Path) -> None:
    stats_path = tmp_path / "mutmut-cicd-stats.json"
    report_path = tmp_path / "mutation-guard-report.json"
    _write_stats(stats_path, killed=90, survived=10, total=100, no_tests=0)

    original_argv = sys.argv[:]
    try:
        sys.argv = [
            str(SCRIPT_PATH),
            "--stats-path",
            str(stats_path),
            "--min-score",
            "80",
            "--max-no-tests",
            "0",
            "--report-json",
            str(report_path),
        ]
        assert GUARD.main() == 0
    finally:
        sys.argv = original_argv

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert payload["current"]["score_percent"] == 90.0
    assert payload["errors"] == []


def test_mutation_guard_writes_auditable_report_on_fail(tmp_path: Path) -> None:
    stats_path = tmp_path / "mutmut-cicd-stats.json"
    report_path = tmp_path / "mutation-guard-report.json"
    _write_stats(stats_path, killed=70, survived=30, total=100, no_tests=0)

    original_argv = sys.argv[:]
    try:
        sys.argv = [
            str(SCRIPT_PATH),
            "--stats-path",
            str(stats_path),
            "--min-score",
            "80",
            "--max-no-tests",
            "0",
            "--report-json",
            str(report_path),
        ]
        assert GUARD.main() == 1
    finally:
        sys.argv = original_argv

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "fail"
    assert payload["errors"]
