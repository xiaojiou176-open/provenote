#!/usr/bin/env python3
"""Enforce first-party source file length guardrails."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any, cast


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="tooling/scripts/ci/first_party_file_length_baseline.json",
        help="Path to the file length guard config JSON.",
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root directory. Defaults to the current repository root.",
    )
    parser.add_argument(
        "--show-top",
        type=int,
        default=10,
        help="Show the top N largest scanned files.",
    )
    return parser


def load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.is_file():
        raise FileNotFoundError(f"config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    required_keys = {"global_max_lines", "warning_threshold", "roots", "extensions"}
    missing = sorted(required_keys - set(data.keys()))
    if missing:
        raise ValueError(f"config missing required keys: {', '.join(missing)}")

    return data


def is_excluded(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def count_lines(file_path: Path) -> int:
    with file_path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def scan_files(
    repo_root: Path, config: dict[str, Any]
) -> tuple[list[tuple[str, int]], list[str]]:
    roots_raw = config["roots"]
    extensions_raw = config["extensions"]
    excludes_raw = config.get("exclude_globs", [])
    missing_roots: list[str] = []
    scanned: list[tuple[str, int]] = []

    if not isinstance(roots_raw, list) or not all(
        isinstance(root, str) for root in roots_raw
    ):
        raise ValueError("config.roots must be a list of strings")
    roots = cast(list[str], roots_raw)
    if not isinstance(extensions_raw, list) or not all(
        isinstance(ext, str) for ext in extensions_raw
    ):
        raise ValueError("config.extensions must be a list of strings")
    extensions = set(cast(list[str], extensions_raw))
    if not isinstance(excludes_raw, list) or not all(
        isinstance(item, str) for item in excludes_raw
    ):
        raise ValueError("config.exclude_globs must be a list of strings")
    excludes = cast(list[str], excludes_raw)

    for root in roots:
        root_path = repo_root / root
        if not root_path.is_dir():
            missing_roots.append(root)
            continue

        for file_path in sorted(root_path.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.suffix not in extensions:
                continue
            relative_path = file_path.relative_to(repo_root).as_posix()
            if is_excluded(relative_path, excludes):
                continue
            scanned.append((relative_path, count_lines(file_path)))

    scanned.sort(key=lambda item: item[1], reverse=True)
    return scanned, missing_roots


def main() -> int:
    args = build_arg_parser().parse_args()
    default_repo_root = Path(__file__).resolve().parents[3]
    repo_root = Path(args.repo_root).resolve() if args.repo_root else default_repo_root
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    config_path = config_path.resolve()

    try:
        config = load_config(config_path)
        scanned, missing_roots = scan_files(repo_root, config)
    except (
        FileNotFoundError,
        ValueError,
        json.JSONDecodeError,
        UnicodeDecodeError,
    ) as exc:
        print(f"FAIL [FILE-LEN-BOOT-001]: {exc}")
        return 2

    global_max_raw = config["global_max_lines"]
    warning_threshold_raw = config["warning_threshold"]
    frozen_raw = config.get("frozen_file_max_lines", {})
    if not isinstance(global_max_raw, int):
        raise ValueError("config.global_max_lines must be an integer")
    if not isinstance(warning_threshold_raw, int):
        raise ValueError("config.warning_threshold must be an integer")
    if not isinstance(frozen_raw, dict):
        raise ValueError("config.frozen_file_max_lines must be an object")

    global_max = global_max_raw
    warning_threshold = warning_threshold_raw
    frozen: dict[str, int] = {}
    for path, limit in frozen_raw.items():
        if not isinstance(path, str) or not isinstance(limit, int):
            raise ValueError(
                "config.frozen_file_max_lines entries must map strings to integers"
            )
        frozen[path] = limit

    global_violations: list[tuple[str, int]] = []
    frozen_violations: list[tuple[str, int, int]] = []
    warnings: list[tuple[str, int]] = []

    for path, lines in scanned:
        if path not in frozen and lines > global_max:
            global_violations.append((path, lines))
        if path in frozen and lines > frozen[path]:
            frozen_violations.append((path, lines, frozen[path]))
        if lines >= warning_threshold:
            warnings.append((path, lines))

    if missing_roots:
        print("WARN [FILE-LEN-NOTE-001]: configured roots not found:")
        for root in missing_roots:
            print(f"- {root}")
        print()

    top_n = max(0, int(args.show_top))
    if top_n > 0:
        print(f"INFO [FILE-LEN-TOP-001]: top {top_n} largest scanned files")
        for path, lines in scanned[:top_n]:
            print(f"- {path}: {lines}")
        print()

    if warnings:
        print(
            f"WARN [FILE-LEN-WARN-001]: files at or above warning threshold ({warning_threshold} lines)."
        )
        for path, lines in warnings:
            print(f"- {path}: {lines}")
        print()

    frozen_missing = sorted(
        path for path in frozen if path not in {item[0] for item in scanned}
    )
    if frozen_missing:
        print("WARN [FILE-LEN-NOTE-002]: frozen files not found in scan scope:")
        for path in frozen_missing:
            print(f"- {path}")
        print()

    failed = False
    if global_violations:
        failed = True
        print(
            f"FAIL [FILE-LEN-001]: file length exceeds global limit ({global_max} lines)."
        )
        for path, lines in global_violations:
            print(f"- {path}: {lines}")
        print()

    if frozen_violations:
        failed = True
        print("FAIL [FILE-LEN-002]: frozen near-threshold files grew beyond their cap.")
        for path, lines, cap in frozen_violations:
            print(f"- {path}: {lines} > {cap}")
        print()

    if failed:
        return 1

    print("PASS: first-party file length guard passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
