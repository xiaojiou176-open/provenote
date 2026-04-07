#!/usr/bin/env python3
"""Enforce mutation-testing quality gate and print explicit anti-false-green metrics."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


def _env_or_default(name: str, default: str) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip()
    return normalized if normalized else default


def _env_float(name: str, default: float) -> float:
    return float(_env_or_default(name, str(default)))


def _env_int(name: str, default: int) -> int:
    return int(_env_or_default(name, str(default)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stats-path",
        default="mutants/mutmut-cicd-stats.json",
        help="Path to mutmut export-cicd-stats JSON output.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=_env_float("MUTATION_MIN_SCORE", 80.0),
        help="Minimum mutation score required. Default from MUTATION_MIN_SCORE or 80.",
    )
    parser.add_argument(
        "--max-no-tests",
        type=int,
        default=_env_int("MUTATION_MAX_NO_TESTS", 0),
        help="Maximum allowed no_tests mutants. Default from MUTATION_MAX_NO_TESTS or 0.",
    )
    parser.add_argument(
        "--baseline-stats",
        default=_env_or_default("MUTATION_BASELINE_STATS", ""),
        help=(
            "Optional baseline stats JSON path. When provided, "
            "the current run must not regress versus baseline."
        ),
    )
    parser.add_argument(
        "--max-survived-regression",
        type=int,
        default=_env_int("MUTATION_MAX_SURVIVED_REGRESSION", 0),
        help=(
            "Maximum allowed increase of survived mutants versus baseline. "
            "Default from MUTATION_MAX_SURVIVED_REGRESSION or 0."
        ),
    )
    parser.add_argument(
        "--max-score-regression",
        type=float,
        default=_env_float("MUTATION_MAX_SCORE_REGRESSION", 0.0),
        help=(
            "Maximum allowed mutation-score drop (percentage points) versus baseline. "
            "Default from MUTATION_MAX_SCORE_REGRESSION or 0."
        ),
    )
    parser.add_argument(
        "--max-survived",
        type=int,
        default=_env_int("MUTATION_MAX_SURVIVED", -1),
        help=(
            "Maximum allowed absolute survived mutants. "
            "Use -1 to disable. Default from MUTATION_MAX_SURVIVED or -1."
        ),
    )
    parser.add_argument(
        "--max-skipped",
        type=int,
        default=_env_int("MUTATION_MAX_SKIPPED", 0),
        help="Maximum allowed skipped mutants. Default from MUTATION_MAX_SKIPPED or 0.",
    )
    parser.add_argument(
        "--max-suspicious",
        type=int,
        default=_env_int("MUTATION_MAX_SUSPICIOUS", 0),
        help=(
            "Maximum allowed suspicious mutants. "
            "Default from MUTATION_MAX_SUSPICIOUS or 0."
        ),
    )
    parser.add_argument(
        "--max-timeout",
        type=int,
        default=_env_int("MUTATION_MAX_TIMEOUT", 0),
        help="Maximum allowed timeout mutants. Default from MUTATION_MAX_TIMEOUT or 0.",
    )
    parser.add_argument(
        "--report-json",
        default=_env_or_default("MUTATION_GUARD_REPORT_PATH", ""),
        help=(
            "Optional JSON path for auditable mutation guard report. "
            "Default from MUTATION_GUARD_REPORT_PATH."
        ),
    )
    return parser


def _load_stats(path: Path) -> dict[str, int]:
    if not path.is_file():
        raise FileNotFoundError(f"mutation stats file not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    keys = [
        "killed",
        "survived",
        "total",
        "no_tests",
        "skipped",
        "suspicious",
        "timeout",
        "check_was_interrupted_by_user",
        "segfault",
    ]
    return {key: int(raw.get(key, 0)) for key in keys}


MUTANT_KEY_RE = re.compile(r"^(?P<module>.+)\.x(?P<function>.+)__mutmut_(?P<id>\d+)$")


def _collect_meta_paths(stats_path: Path) -> list[Path]:
    root = stats_path.parent
    if not root.is_dir():
        return []
    meta_paths: list[Path] = []
    for path in root.rglob("*.py.meta"):
        rel = path.relative_to(root)
        # Skip nested mirror workspace to avoid duplicate accounting.
        if rel.parts and rel.parts[0] == "mutants":
            continue
        meta_paths.append(path)
    return sorted(meta_paths)


def _build_surface_summary(stats_path: Path) -> dict[str, object]:
    by_module: dict[str, dict[str, int]] = {}
    by_function: dict[str, int] = {}
    meta_paths = _collect_meta_paths(stats_path)
    for meta_path in meta_paths:
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        exit_code_by_key = payload.get("exit_code_by_key", {})
        if not isinstance(exit_code_by_key, dict):
            continue
        for key, raw_exit_code in exit_code_by_key.items():
            if not isinstance(key, str):
                continue
            matched = MUTANT_KEY_RE.match(key)
            if not matched:
                continue
            module_name = matched.group("module")
            function_name = matched.group("function")
            exit_code = int(raw_exit_code)
            status_bucket = "other"
            if exit_code == 1:
                status_bucket = "killed"
            elif exit_code == 0:
                status_bucket = "survived"
            module_bucket = by_module.setdefault(
                module_name,
                {"total": 0, "killed": 0, "survived": 0, "other": 0},
            )
            module_bucket["total"] += 1
            module_bucket[status_bucket] += 1
            if status_bucket == "survived":
                function_key = f"{module_name}.{function_name}"
                by_function[function_key] = by_function.get(function_key, 0) + 1

    module_breakdown: list[dict[str, object]] = []
    for module_name in sorted(by_module.keys()):
        item = by_module[module_name]
        total = item["total"]
        killed = item["killed"]
        kill_rate = (killed / total) * 100.0 if total else 0.0
        module_breakdown.append(
            {
                "module": module_name,
                "total": total,
                "killed": killed,
                "survived": item["survived"],
                "other": item["other"],
                "kill_rate_percent": round(kill_rate, 2),
            }
        )

    top_survived_functions = [
        {"function": name, "survived": count}
        for name, count in sorted(
            by_function.items(), key=lambda pair: (-pair[1], pair[0])
        )[:20]
    ]

    return {
        "meta_files": [str(path) for path in meta_paths],
        "module_breakdown": module_breakdown,
        "top_survived_functions": top_survived_functions,
    }


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    stats_path = Path(args.stats_path)

    try:
        stats = _load_stats(stats_path)
    except Exception as exc:  # pragma: no cover - defensive path
        print(f"[mutation-guard] FAIL: unable to load stats: {exc}")
        return 2

    total = stats["total"]
    killed = stats["killed"]
    no_tests = stats["no_tests"]
    interrupted = stats["check_was_interrupted_by_user"]
    segfault = stats["segfault"]

    if total <= 0:
        print(
            "[mutation-guard] FAIL: total mutants is 0, mutation testing did not run correctly."
        )
        return 1

    score = (killed / total) * 100.0
    exercised = ((total - no_tests) / total) * 100.0
    survived_ratio = (stats["survived"] / total) * 100.0

    print("[mutation-guard] anti-false-green summary")
    print(f"[mutation-guard] stats_path={stats_path}")
    print(f"[mutation-guard] score={score:.2f}% min_required={args.min_score:.2f}%")
    print(
        f"[mutation-guard] kill_rate={score:.2f}% survived_ratio={survived_ratio:.2f}%"
    )
    print(
        f"[mutation-guard] exercised_mutants={exercised:.2f}% (no_tests={no_tests}/{total})"
    )
    print(
        "[mutation-guard] details: "
        f"killed={stats['killed']} survived={stats['survived']} skipped={stats['skipped']} "
        f"suspicious={stats['suspicious']} timeout={stats['timeout']} segfault={segfault}"
    )

    errors: list[str] = []
    baseline_summary: dict[str, object] = {}
    if score < args.min_score:
        errors.append(
            f"mutation score {score:.2f}% below threshold {args.min_score:.2f}%"
        )
    if no_tests > args.max_no_tests:
        errors.append(
            f"no_tests mutants {no_tests} exceed allowed maximum {args.max_no_tests}"
        )
    if args.max_survived >= 0 and stats["survived"] > args.max_survived:
        errors.append(
            "survived mutants "
            f"{stats['survived']} exceed allowed maximum {args.max_survived}"
        )
    if stats["skipped"] > args.max_skipped:
        errors.append(
            f"skipped mutants {stats['skipped']} exceed allowed maximum {args.max_skipped}"
        )
    if stats["suspicious"] > args.max_suspicious:
        errors.append(
            "suspicious mutants "
            f"{stats['suspicious']} exceed allowed maximum {args.max_suspicious}"
        )
    if stats["timeout"] > args.max_timeout:
        errors.append(
            f"timeout mutants {stats['timeout']} exceed allowed maximum {args.max_timeout}"
        )
    if interrupted > 0:
        errors.append("mutation run was interrupted")
    if segfault > 0:
        errors.append("mutation run reported segfaults")

    baseline_arg = args.baseline_stats.strip()
    if baseline_arg:
        baseline_path = Path(baseline_arg)
        try:
            baseline = _load_stats(baseline_path)
        except Exception as exc:
            errors.append(f"unable to load baseline stats from {baseline_path}: {exc}")
        else:
            baseline_total = baseline["total"]
            if baseline_total > 0:
                baseline_score = (baseline["killed"] / baseline_total) * 100.0
                score_regression = baseline_score - score
                survived_regression = stats["survived"] - baseline["survived"]
                print(
                    "[mutation-guard] baseline: "
                    f"path={baseline_path} score={baseline_score:.2f}% survived={baseline['survived']}"
                )
                print(
                    "[mutation-guard] delta: "
                    f"score_regression={score_regression:.2f}pp "
                    f"survived_regression={survived_regression}"
                )
                baseline_summary = {
                    "path": str(baseline_path),
                    "score_percent": round(baseline_score, 2),
                    "survived": int(baseline["survived"]),
                    "score_regression_pp": round(score_regression, 2),
                    "survived_regression": int(survived_regression),
                }
                if score_regression > args.max_score_regression:
                    errors.append(
                        "mutation score regression "
                        f"{score_regression:.2f}pp exceeds allowed {args.max_score_regression:.2f}pp"
                    )
                if survived_regression > args.max_survived_regression:
                    errors.append(
                        "survived mutants regression "
                        f"{survived_regression} exceeds allowed {args.max_survived_regression}"
                    )
            else:
                errors.append(
                    f"baseline stats at {baseline_path} has total=0 and cannot be used"
                )

    report_path_arg = args.report_json.strip()
    if report_path_arg:
        report_path = Path(report_path_arg)
        report_payload: dict[str, object] = {
            "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "status": "fail" if errors else "pass",
            "stats_path": str(stats_path),
            "thresholds": {
                "min_score": float(args.min_score),
                "max_no_tests": int(args.max_no_tests),
                "max_survived": int(args.max_survived),
                "max_skipped": int(args.max_skipped),
                "max_suspicious": int(args.max_suspicious),
                "max_timeout": int(args.max_timeout),
                "max_survived_regression": int(args.max_survived_regression),
                "max_score_regression": float(args.max_score_regression),
            },
            "current": {
                "total": int(total),
                "killed": int(killed),
                "survived": int(stats["survived"]),
                "no_tests": int(no_tests),
                "skipped": int(stats["skipped"]),
                "suspicious": int(stats["suspicious"]),
                "timeout": int(stats["timeout"]),
                "score_percent": round(score, 2),
                "kill_rate_percent": round(score, 2),
                "survived_ratio_percent": round(survived_ratio, 2),
                "exercised_mutants_percent": round(exercised, 2),
            },
            "baseline": baseline_summary,
            "errors": errors,
            "mutation_surface": _build_surface_summary(stats_path),
            "operator_coverage": {
                "supported": False,
                "reason": (
                    "mutmut export does not expose mutator operator taxonomy in "
                    "cicd-stats/meta outputs; function/module surface is exported instead."
                ),
            },
        }
        try:
            _write_report(report_path, report_payload)
            print(f"[mutation-guard] report_json={report_path}")
        except Exception as exc:  # pragma: no cover - defensive path
            print(f"[mutation-guard] WARN: unable to write report: {exc}")

    if errors:
        print("[mutation-guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[mutation-guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
