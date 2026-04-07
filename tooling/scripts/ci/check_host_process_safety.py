"""Fail closed on broad host-process and desktop automation primitives."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SKIP_DIRS = {
    ".git",
    ".runtime-cache",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".venv",
    "__pycache__",
}
DEFAULT_SCAN_PATHS = (
    REPO_ROOT / "Makefile",
    REPO_ROOT / ".github" / "workflows",
    REPO_ROOT / "tooling",
    REPO_ROOT / "packages",
    REPO_ROOT / "apps",
    REPO_ROOT / "services",
    REPO_ROOT / "tests",
)
ALLOWLIST_FILES = {
    REPO_ROOT / "tooling/scripts/ci/check_host_process_safety.py",
    REPO_ROOT / "tests/ci/test_host_process_safety_contract.py",
}
TEXT_FILE_SUFFIXES = {
    "",
    ".bash",
    ".cjs",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
    ".zsh",
}
NODE_PROCESS_KILL_SUFFIXES = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}
FORBIDDEN_LINE_RULES = (
    ("pkill", re.compile(r"\bpkill\b")),
    ("killall", re.compile(r"\bkillall\b")),
    ("kill -9", re.compile(r"(^|[^0-9A-Za-z_])kill\s+-9\b")),
    ("xargs kill", re.compile(r"\bxargs\s+kill(?:\s+-9|\s+-KILL)?\b")),
    ("osascript", re.compile(r"\bosascript\b")),
    ("System Events", re.compile(r"System Events")),
    ("loginwindow", re.compile(r"\bloginwindow\b")),
    ("showForceQuitPanel", re.compile(r"showForceQuitPanel")),
    ("os.killpg", re.compile(r"\bos\.killpg\s*\(")),
)
NODE_PROCESS_KILL = re.compile(r"process\.kill\s*\(")
ALLOWED_NODE_PROCESS_KILL = re.compile(r"process\.kill\s*\(\s*[^,\n]+,\s*0\s*\)")


def _iter_files(paths: list[Path]) -> list[Path]:
    collected: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_dir():
            for candidate in sorted(path.rglob("*")):
                if candidate.is_dir():
                    continue
                if any(part in SKIP_DIRS for part in candidate.parts):
                    continue
                if candidate in ALLOWLIST_FILES:
                    continue
                if (
                    candidate.suffix.lower() in TEXT_FILE_SUFFIXES
                    or candidate.name == "Makefile"
                ):
                    collected.append(candidate)
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path in ALLOWLIST_FILES:
            continue
        if path.suffix.lower() in TEXT_FILE_SUFFIXES or path.name == "Makefile":
            collected.append(path)
    return collected


def _normalize_scan_paths(raw_paths: list[str]) -> list[Path]:
    if not raw_paths:
        return list(DEFAULT_SCAN_PATHS)

    normalized: list[Path] = []
    for raw in raw_paths:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = (REPO_ROOT / candidate).resolve()
        normalized.append(candidate)
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paths",
        nargs="*",
        default=[],
        help="Optional repo-relative file or directory paths to scan.",
    )
    args = parser.parse_args()

    scan_paths = _normalize_scan_paths(args.paths)
    failures: list[str] = []

    for file_path in _iter_files(scan_paths):
        try:
            relative_path = file_path.relative_to(REPO_ROOT)
        except ValueError:
            relative_path = file_path
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for label, pattern in FORBIDDEN_LINE_RULES:
                if pattern.search(line):
                    failures.append(
                        f"{relative_path}:{line_number}: forbidden host-process primitive: {label}"
                    )
            if (
                file_path.suffix.lower() in NODE_PROCESS_KILL_SUFFIXES
                and NODE_PROCESS_KILL.search(line)
                and not ALLOWED_NODE_PROCESS_KILL.search(line)
            ):
                failures.append(
                    f"{relative_path}:{line_number}: direct Node process.kill is forbidden unless it is a liveness probe with signal 0"
                )

    if failures:
        print(
            "FAIL: forbidden host-process or desktop-automation primitives detected.",
            file=sys.stderr,
        )
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1

    print(
        "PASS: broad host-process and desktop-automation primitives are absent from the scanned paths."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
