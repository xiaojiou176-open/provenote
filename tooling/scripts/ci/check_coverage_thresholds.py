#!/usr/bin/env python3
"""Enforce global and key-module coverage thresholds for backend and apps/web."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

BACKEND_GLOBAL_MIN = 95.0
FRONTEND_GLOBAL_MIN = 95.0
KEY_MODULE_MIN = 95.0
KEY_MODULE_BRANCH_MIN = 95.0

KEY_BACKEND_MODULES_PHASE0 = {
    "services/api/routers/auditable_runs.py": KEY_MODULE_MIN,
    "packages/core/auditable/dedup_engine.py": KEY_MODULE_MIN,
    "packages/core/auditable/pipeline.py": KEY_MODULE_MIN,
}

KEY_BACKEND_MODULES_PHASE1 = {
    **KEY_BACKEND_MODULES_PHASE0,
    "services/api/auth.py": KEY_MODULE_MIN,
}

KEY_FRONTEND_MODULES = {
    "src/lib/api/client.ts": KEY_MODULE_MIN,
    "src/lib/utils/error-handler.ts": KEY_MODULE_MIN,
}


def _resolve_backend_key_modules(scope: str) -> dict[str, float]:
    if scope == "phase0":
        return KEY_BACKEND_MODULES_PHASE0
    if scope == "phase1":
        return KEY_BACKEND_MODULES_PHASE1
    raise ValueError(f"unsupported backend coverage scope: {scope}")


@dataclass(frozen=True)
class CoverageResult:
    global_line_rate: float
    global_branch_rate: float
    per_file_line_rate: dict[str, float]
    per_file_branch_rate: dict[str, float]


def _normalize_backend_path(value: str) -> str:
    path = value.replace("\\\\", "/").lstrip("./")
    api_marker = "/api/"
    notebook_marker = "/packages/core/"
    if api_marker in path:
        suffix = path.split(api_marker, 1)[1]
        return f"services/api/{suffix}"
    if notebook_marker in path:
        suffix = path.split(notebook_marker, 1)[1]
        return f"packages/core/{suffix}"
    if path.startswith("services/api/"):
        return path
    if path.startswith("routers/"):
        return f"services/api/{path}"
    if "/" not in path and path.endswith(".py"):
        return f"services/api/{path}"
    return path


def _parse_backend_coverage_xml(path: Path) -> CoverageResult:
    root = ET.parse(path).getroot()
    global_line_rate = float(root.attrib.get("line-rate", 0.0)) * 100.0
    global_branch_rate = float(root.attrib.get("branch-rate", 0.0)) * 100.0

    per_file: dict[str, float] = {}
    per_file_branch: dict[str, float] = {}
    for cls in root.findall(".//class"):
        raw_filename = cls.attrib.get("filename", "")
        filename = _normalize_backend_path(raw_filename)
        if not filename:
            continue
        per_file[filename] = float(cls.attrib.get("line-rate", 0.0)) * 100.0
        per_file_branch[filename] = float(cls.attrib.get("branch-rate", 0.0)) * 100.0

    return CoverageResult(
        global_line_rate=global_line_rate,
        global_branch_rate=global_branch_rate,
        per_file_line_rate=per_file,
        per_file_branch_rate=per_file_branch,
    )


def _normalize_frontend_path(value: str) -> str:
    path = value.replace("\\\\", "/")
    marker = "/apps/web/"
    if marker in path:
        return path.split(marker, 1)[1]
    return path.lstrip("./")


def _parse_frontend_lcov(path: Path) -> CoverageResult:
    content = path.read_text(encoding="utf-8").splitlines()
    per_file_hits: dict[str, tuple[int, int]] = {}
    per_file_branch_hits: dict[str, tuple[int, int]] = {}

    current_file: str | None = None
    total_hit = 0
    total_found = 0
    total_branch_hit = 0
    total_branch_found = 0
    file_hit = 0
    file_found = 0
    file_branch_hit = 0
    file_branch_found = 0

    def flush() -> None:
        nonlocal current_file, file_hit, file_found, file_branch_hit, file_branch_found
        if current_file is None:
            return
        per_file_hits[current_file] = (file_hit, file_found)
        per_file_branch_hits[current_file] = (file_branch_hit, file_branch_found)
        current_file = None
        file_hit = 0
        file_found = 0
        file_branch_hit = 0
        file_branch_found = 0

    for raw in content:
        line = raw.strip()
        if line.startswith("SF:"):
            flush()
            current_file = _normalize_frontend_path(line[3:])
            continue

        if line.startswith("DA:") and current_file:
            _, rest = line.split(":", 1)
            _, hit_str = rest.split(",", 1)
            hit_count = int(hit_str)
            file_found += 1
            total_found += 1
            if hit_count > 0:
                file_hit += 1
                total_hit += 1
            continue

        if line.startswith("BRDA:") and current_file:
            _, rest = line.split(":", 1)
            _, _, _, taken_str = rest.split(",", 3)
            file_branch_found += 1
            total_branch_found += 1
            if taken_str != "-" and int(taken_str) > 0:
                file_branch_hit += 1
                total_branch_hit += 1
            continue

        if line == "end_of_record":
            flush()

    flush()

    per_file = {
        filename: ((hit / found) * 100.0 if found else 0.0)
        for filename, (hit, found) in per_file_hits.items()
    }
    per_file_branch = {
        filename: ((hit / found) * 100.0 if found else 0.0)
        for filename, (hit, found) in per_file_branch_hits.items()
    }
    global_rate = (total_hit / total_found) * 100.0 if total_found else 0.0
    global_branch_rate = (
        (total_branch_hit / total_branch_found) * 100.0 if total_branch_found else 0.0
    )
    return CoverageResult(
        global_line_rate=global_rate,
        global_branch_rate=global_branch_rate,
        per_file_line_rate=per_file,
        per_file_branch_rate=per_file_branch,
    )


def _check_thresholds(
    result: CoverageResult,
    *,
    label: str,
    global_min: float,
    key_modules: dict[str, float],
) -> list[str]:
    errors: list[str] = []

    if result.global_line_rate < global_min:
        errors.append(
            f"{label} global line coverage {result.global_line_rate:.2f}% is below {global_min:.2f}%"
        )
    for module, threshold in key_modules.items():
        module_rate = result.per_file_line_rate.get(module)
        module_branch_rate = result.per_file_branch_rate.get(module)
        if module_rate is None:
            errors.append(f"{label} key module missing from coverage report: {module}")
            continue
        if module_branch_rate is None:
            errors.append(
                f"{label} key module missing branch coverage report: {module}"
            )
            continue
        if module_rate < threshold:
            errors.append(
                f"{label} key module {module} coverage {module_rate:.2f}% is below {threshold:.2f}%"
            )
        if module_branch_rate < KEY_MODULE_BRANCH_MIN:
            errors.append(
                f"{label} key module {module} branch coverage {module_branch_rate:.2f}% is below {KEY_MODULE_BRANCH_MIN:.2f}%"
            )

    return errors


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend-xml",
        default=".runtime-cache/test/coverage/backend/coverage.xml",
        help="Backend coverage XML report path (default: .runtime-cache/test/coverage/backend/coverage.xml)",
    )
    parser.add_argument(
        "--frontend-lcov",
        dest="frontend_lcov",
        default=".runtime-cache/test/coverage/apps/web/lcov.info",
        help="Frontend lcov report path (default: .runtime-cache/test/coverage/apps/web/lcov.info)",
    )
    parser.add_argument(
        "--backend-scope",
        choices=("phase0", "phase1"),
        default="phase1",
        help="Backend coverage scope for key-module policy (default: phase1)",
    )
    parser.add_argument(
        "--skip-backend",
        action="store_true",
        help="Skip backend coverage checks",
    )
    parser.add_argument(
        "--skip-apps/web",
        dest="skip_frontend",
        action="store_true",
        help="Skip apps/web coverage checks",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    backend_path = Path(args.backend_xml)
    frontend_path = Path(args.frontend_lcov)
    check_backend = not args.skip_backend
    check_frontend = not args.skip_frontend

    if not check_backend and not check_frontend:
        print("ERROR: at least one coverage domain must be enabled")
        return 2

    if check_backend and not backend_path.is_file():
        print(f"ERROR: backend coverage report not found: {backend_path}")
        return 2
    if check_frontend and not frontend_path.is_file():
        print(f"ERROR: apps/web coverage report not found: {frontend_path}")
        return 2

    backend_result = (
        _parse_backend_coverage_xml(backend_path) if check_backend else None
    )
    frontend_result = _parse_frontend_lcov(frontend_path) if check_frontend else None

    errors = []
    backend_key_modules = _resolve_backend_key_modules(args.backend_scope)
    if backend_result is not None:
        errors.extend(
            _check_thresholds(
                backend_result,
                label="backend",
                global_min=BACKEND_GLOBAL_MIN,
                key_modules=backend_key_modules,
            )
        )
    if frontend_result is not None:
        errors.extend(
            _check_thresholds(
                frontend_result,
                label="apps/web",
                global_min=FRONTEND_GLOBAL_MIN,
                key_modules=KEY_FRONTEND_MODULES,
            )
        )

    if backend_result is not None:
        print(f"backend scope: {args.backend_scope}")
        print(f"backend global line coverage: {backend_result.global_line_rate:.2f}%")
        print(
            f"backend global branch coverage: {backend_result.global_branch_rate:.2f}%"
        )
        for module, _ in backend_key_modules.items():
            rate = backend_result.per_file_line_rate.get(module)
            branch_rate = backend_result.per_file_branch_rate.get(module)
            if rate is not None:
                print(f"backend {module}: {rate:.2f}%")
            if branch_rate is not None:
                print(f"backend {module} branch: {branch_rate:.2f}%")

    if frontend_result is not None:
        print(f"apps/web global line coverage: {frontend_result.global_line_rate:.2f}%")
        print(
            f"apps/web global branch coverage: {frontend_result.global_branch_rate:.2f}%"
        )
        for module, _ in KEY_FRONTEND_MODULES.items():
            rate = frontend_result.per_file_line_rate.get(module)
            branch_rate = frontend_result.per_file_branch_rate.get(module)
            if rate is not None:
                print(f"apps/web {module}: {rate:.2f}%")
            if branch_rate is not None:
                print(f"apps/web {module} branch: {branch_rate:.2f}%")

    if errors:
        print("FAIL: coverage thresholds not met")
        for item in errors:
            print(f"- {item}")
        return 1

    print("PASS: coverage thresholds satisfied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
