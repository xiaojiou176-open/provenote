#!/usr/bin/env python3
"""Fail closed on tracked sensitive surfaces such as local machine paths and personal identity."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY = REPO_ROOT / "config/runtime/sensitive-surface-policy.json"
SKIP_PARTS = {".git", "node_modules", ".venv", "__pycache__", "dist"}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _literal_from_codepoints(points: Sequence[int]) -> str:
    return "".join(chr(point) for point in points)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy",
        default=str(DEFAULT_POLICY),
        help="Path to the sensitive surface policy JSON file",
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        default=None,
        help="Optional repo-relative tracked paths to scan instead of all tracked files",
    )
    return parser


def _git_tracked_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _iter_target_files(
    repo_root: Path, tracked_files: Sequence[str] | None
) -> Iterable[str]:
    if tracked_files is not None:
        for rel_path in tracked_files:
            rel = rel_path.strip().replace("\\", "/")
            if rel:
                yield rel
        return
    yield from _git_tracked_files(repo_root)


def _should_scan(rel_path: str, scan_roots: Sequence[str]) -> bool:
    for root in scan_roots:
        normalized = root.strip().rstrip("/")
        if not normalized:
            continue
        if rel_path == normalized or rel_path.startswith(f"{normalized}/"):
            return True
    return False


def collect_failures(
    repo_root: Path = REPO_ROOT,
    tracked_files: Sequence[str] | None = None,
    *,
    policy_path: Path = DEFAULT_POLICY,
) -> list[str]:
    policy = _load_json(policy_path)
    failures: list[str] = []
    scan_roots = tuple(policy.get("content_scan_roots", []))
    path_rules = [
        (re.compile(item["pattern"]), item["reason"])
        for item in policy.get("tracked_path_forbidden_patterns", [])
    ]
    content_rules = [
        (re.compile(item["pattern"]), item["reason"])
        for item in policy.get("forbidden_content_patterns", [])
    ]
    content_rules.extend(
        (
            (
                re.compile(
                    re.escape(
                        _literal_from_codepoints(
                            (
                                89,
                                105,
                                102,
                                101,
                                110,
                                103,
                                32,
                                40,
                                84,
                                101,
                                114,
                                114,
                                121,
                                41,
                                32,
                                89,
                                117,
                            )
                        )
                    )
                ),
                "hardcoded maintainer name",
            ),
            (
                re.compile(
                    re.escape(
                        _literal_from_codepoints(
                            (
                                49,
                                50,
                                53,
                                53,
                                56,
                                49,
                                54,
                                53,
                                55,
                                43,
                                120,
                                105,
                                97,
                                111,
                                106,
                                105,
                                111,
                                117,
                                49,
                                55,
                                54,
                                64,
                                117,
                                115,
                                101,
                                114,
                                115,
                                46,
                                110,
                                111,
                                114,
                                101,
                                112,
                                108,
                                121,
                                46,
                                103,
                                105,
                                116,
                                104,
                                117,
                                98,
                                46,
                                99,
                                111,
                                109,
                            )
                        )
                    )
                ),
                "hardcoded maintainer GitHub noreply email",
            ),
            (
                re.compile(
                    re.escape(
                        _literal_from_codepoints(
                            (
                                120,
                                105,
                                97,
                                111,
                                49,
                                55,
                                54,
                                106,
                                105,
                                111,
                                117,
                                64,
                                103,
                                109,
                                97,
                                105,
                                108,
                                46,
                                99,
                                111,
                                109,
                            )
                        )
                    )
                ),
                "hardcoded maintainer Gmail address",
            ),
        )
    )

    for rel_path in _iter_target_files(repo_root, tracked_files):
        file_path = (repo_root / rel_path).resolve()
        if not file_path.exists() or not file_path.is_file():
            continue
        if file_path == policy_path.resolve():
            continue
        if any(part in SKIP_PARTS for part in file_path.parts):
            continue

        normalized_rel = rel_path.replace("\\", "/")
        for regex, reason in path_rules:
            if regex.search(normalized_rel):
                failures.append(f"{normalized_rel}: {reason}")

        if not _should_scan(normalized_rel, scan_roots):
            continue

        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for regex, reason in content_rules:
            for match in regex.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                line = text.splitlines()[line_no - 1].strip()
                failures.append(f"{normalized_rel}:{line_no}: {reason} -> {line}")

    return sorted(dict.fromkeys(failures))


def main() -> int:
    args = build_parser().parse_args()
    failures = collect_failures(
        tracked_files=args.paths,
        policy_path=Path(args.policy).resolve(),
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        "PASS: tracked sources are free of forbidden personal identity, machine-specific path, and tracked artifact leakage."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
