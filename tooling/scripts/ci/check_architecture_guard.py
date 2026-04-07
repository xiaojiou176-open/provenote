#!/usr/bin/env python3
"""Architecture guardrails for layering and implementation convergence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

BROAD_EXCEPTION_PATTERN = re.compile(
    r"^\s*except\s*(Exception(\s+as\s+[A-Za-z_]\w*)?\s*)?:\s*(#.*)?$"
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        default="tooling/scripts/ci/architecture_guard_baseline.json",
        help="Path to architecture guard baseline JSON",
    )
    return parser


def find_duplicate_service_modules(repo_root: Path) -> dict[str, list[str]]:
    by_filename: dict[str, list[str]] = defaultdict(list)
    api_dir = repo_root / "services" / "api"

    if not api_dir.is_dir():
        return {}

    for service_file in sorted(api_dir.rglob("*_service.py")):
        by_filename[service_file.name].append(
            service_file.relative_to(repo_root).as_posix()
        )

    duplicates = {name: paths for name, paths in by_filename.items() if len(paths) > 1}
    return duplicates


def load_baseline(path: Path) -> tuple[dict[str, list[str]], dict[str, object]]:
    if not path.is_file():
        raise FileNotFoundError(f"baseline file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if "broad_exception_baseline" not in data:
        raise ValueError("baseline JSON missing key: broad_exception_baseline")

    broad_exception_baseline = data["broad_exception_baseline"]
    if not isinstance(broad_exception_baseline, dict):
        raise ValueError("baseline.broad_exception_baseline must be an object")

    duplicate_service_baseline = data.get("duplicate_service_baseline", {})
    if not isinstance(duplicate_service_baseline, dict):
        raise ValueError("baseline.duplicate_service_baseline must be an object")

    normalized_duplicate_baseline: dict[str, list[str]] = {}
    for service_name, paths in duplicate_service_baseline.items():
        if not isinstance(paths, list) or not all(
            isinstance(path, str) for path in paths
        ):
            raise ValueError(
                "baseline.duplicate_service_baseline entries must be string arrays"
            )
        normalized_duplicate_baseline[service_name] = sorted(dict.fromkeys(paths))

    return normalized_duplicate_baseline, broad_exception_baseline


def compare_duplicate_service_modules_with_baseline(
    baseline: dict[str, list[str]],
    current: dict[str, list[str]],
) -> tuple[list[str], list[str], list[str], list[str]]:
    regressions: list[str] = []
    reductions: list[str] = []
    notes: list[str] = []
    unchanged: list[str] = []

    for service_name, current_paths in sorted(current.items()):
        if service_name not in baseline:
            regressions.append(
                f"- {service_name}: new duplicate service module set detected ({len(current_paths)} files)"
            )
            for path in current_paths:
                regressions.append(f"  - {path}")
            continue

        baseline_paths = baseline[service_name]
        baseline_count = len(baseline_paths)
        current_count = len(current_paths)

        if current_count > baseline_count:
            regressions.append(
                f"- {service_name}: duplicate service modules increased {baseline_count} -> {current_count}"
            )
            for path in sorted(set(current_paths) - set(baseline_paths)):
                regressions.append(f"  - added: {path}")
            continue

        if current_count < baseline_count:
            reductions.append(
                f"- {service_name}: duplicate service modules reduced {baseline_count} -> {current_count}"
            )
            continue

        if set(current_paths) == set(baseline_paths):
            unchanged.append(
                f"- {service_name}: unchanged at {current_count} duplicate modules (baseline debt)"
            )
        else:
            notes.append(
                f"- WARN: {service_name} duplicate set changed without count increase; refresh baseline if intentional."
            )

    for service_name, baseline_paths in sorted(baseline.items()):
        if service_name not in current:
            reductions.append(
                f"- {service_name}: duplicate service modules resolved {len(baseline_paths)} -> 0"
            )

    return regressions, reductions, notes, unchanged


def scan_broad_exception_counts(
    repo_root: Path, roots: list[str]
) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}

    for root in roots:
        root_path = repo_root / root
        file_counts: dict[str, int] = {}

        if not root_path.is_dir():
            result[root] = {"total": 0, "files": {}}
            continue

        for py_file in sorted(root_path.rglob("*.py")):
            count = 0
            for line in py_file.read_text(encoding="utf-8").splitlines():
                if BROAD_EXCEPTION_PATTERN.match(line):
                    count += 1
            if count > 0:
                file_counts[py_file.relative_to(repo_root).as_posix()] = count

        result[root] = {
            "total": sum(file_counts.values()),
            "files": file_counts,
        }

    return result


def compare_with_baseline(
    baseline: dict[str, object], current: dict[str, dict[str, object]]
) -> tuple[list[str], list[str], list[str]]:
    regressions: list[str] = []
    reductions: list[str] = []
    notes: list[str] = []

    for root, baseline_entry in baseline.items():
        if root not in current:
            notes.append(f"- WARN: baseline root missing in current scan: {root}")
            continue

        if not isinstance(baseline_entry, dict) or "files" not in baseline_entry:
            notes.append(f"- WARN: baseline entry malformed for root: {root}")
            continue

        baseline_files = baseline_entry["files"]
        if not isinstance(baseline_files, dict):
            notes.append(f"- WARN: baseline files malformed for root: {root}")
            continue

        current_files = current[root]["files"]
        if not isinstance(current_files, dict):
            notes.append(f"- WARN: current files malformed for root: {root}")
            continue

        baseline_total_raw = baseline_entry.get("total", 0)
        current_total_raw = current[root].get("total", 0)
        if not isinstance(baseline_total_raw, int) or not isinstance(
            current_total_raw, int
        ):
            notes.append(f"- WARN: total counts malformed for root: {root}")
            continue
        baseline_total = baseline_total_raw
        current_total = current_total_raw

        if current_total < baseline_total:
            reductions.append(
                f"- {root}: broad exceptions reduced {baseline_total} -> {current_total}"
            )
        elif current_total > baseline_total:
            regressions.append(
                f"- {root}: broad exceptions increased {baseline_total} -> {current_total}"
            )

        all_files = set(baseline_files) | set(current_files)
        for file_path in sorted(all_files):
            before_raw = baseline_files.get(file_path, 0)
            after_raw = current_files.get(file_path, 0)
            if not isinstance(before_raw, int) or not isinstance(after_raw, int):
                notes.append(
                    f"- WARN: file count malformed for root: {root} file: {file_path}"
                )
                continue
            before = before_raw
            after = after_raw
            if after > before:
                regressions.append(
                    f"  - {file_path}: broad exceptions {before} -> {after}"
                )
            elif after < before:
                reductions.append(
                    f"  - {file_path}: broad exceptions {before} -> {after}"
                )

    return regressions, reductions, notes


def main() -> int:
    args = build_arg_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    baseline_path = (repo_root / args.baseline).resolve()

    try:
        duplicate_baseline, broad_exception_baseline = load_baseline(baseline_path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL [ARCH-BOOT-001]: unable to load baseline: {exc}")
        return 2

    duplicates = find_duplicate_service_modules(repo_root)
    dual_regressions, dual_reductions, dual_notes, dual_unchanged = (
        compare_duplicate_service_modules_with_baseline(
            duplicate_baseline,
            duplicates,
        )
    )

    current = scan_broad_exception_counts(
        repo_root, sorted(broad_exception_baseline.keys())
    )
    regressions, reductions, notes = compare_with_baseline(
        broad_exception_baseline, current
    )
    notes = [*dual_notes, *notes]
    reductions = [*dual_reductions, *reductions]

    failed = False

    if dual_regressions:
        failed = True
        print("FAIL [ARCH-DUAL-001]: duplicate *_service.py footprint regressed.")
        print(
            "Only historical baseline debt is allowed. New or expanded duplicate services are blocked."
        )
        for item in dual_regressions:
            print(item)
        print()

    if regressions:
        failed = True
        print("FAIL [ARCH-EXC-001]: broad exception footprint regressed.")
        print("Do not add new `except Exception` or bare `except:` blocks.")
        for item in regressions:
            print(item)
        print()

    if notes:
        print("WARN [ARCH-NOTE-001]: baseline consistency notes:")
        for note in notes:
            print(note)
        print()

    if dual_unchanged:
        print(
            "INFO [ARCH-DUAL-BASELINE-001]: duplicate service debt is unchanged from baseline."
        )
        for item in dual_unchanged:
            print(item)
        print()

    if reductions:
        print("INFO [ARCH-IMPROVE-001]: architecture debt reduced.")
        for item in reductions:
            print(item)
        print()

    if failed:
        return 1

    print(
        "PASS: architecture guard checks passed (no new dual-impl or broad-exception regressions)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
