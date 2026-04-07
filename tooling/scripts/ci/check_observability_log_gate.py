#!/usr/bin/env python3
"""Observability and logging static gate for critical backend paths."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

BROAD_EXCEPT_PATTERN = re.compile(
    r"^\s*except\s*(Exception(\s+as\s+[A-Za-z_]\w*)?|BaseException(\s+as\s+[A-Za-z_]\w*)?)\s*:\s*(#.*)?$|^\s*except\s*:\s*(#.*)?$"
)
LOGGER_CALL_PATTERN = re.compile(
    r"\blogger\.(debug|info|warning|error|critical|exception|success)\s*\("
)
LOGGER_EXCEPTION_PATTERN = re.compile(r"\blogger\.exception\s*\(")
FSTRING_LOGGER_PATTERN = re.compile(
    r"\blogger\.(debug|info|warning|error|critical|exception|success)\s*\(\s*f['\"]"
)
SENSITIVE_INTERPOLATION_PATTERN = re.compile(
    r"\blogger\.(debug|info|warning|error|critical|exception|success)\s*\(\s*f['\"][^\n]*\{[^}]*"
    r"(?:api[_-]?key|token|password|secret|authorization|bearer)[^}]*\}"
)
SENSITIVE_KV_PATTERN = re.compile(
    r"\blogger\.(debug|info|warning|error|critical|exception|success)\s*\([^\n]*\b"
    r"(?:api[_-]?key|token|password|secret|authorization|bearer)\s*="
)
SKIP_DIRS = {".git", ".venv", ".runtime-cache", "node_modules", "__pycache__"}
DEFAULT_SCAN_ROOTS = (
    "services/api",
    "services/worker",
    "packages/core",
    "tooling/scripts",
    "tests",
)
CRITICAL_GUARD_FILES = (
    "services/api/main.py",
    "services/api/auth.py",
    "services/api/routers/auth.py",
    "services/api/routers/providers.py",
    "services/api/routers/sources_service.py",
    "packages/core/ai/connection_tester.py",
    "packages/core/ai/google_genai_adapter.py",
    "packages/core/ai/model_discovery.py",
    "packages/core/application/command_service.py",
)
KEY_STRUCTURED_FILES = (
    "services/api/auth.py",
    "services/api/routers/providers.py",
    "packages/core/ai/connection_tester.py",
    "packages/core/ai/google_genai_adapter.py",
)
TRACE_CONTRACT_FILES = {
    "packages/core/observability/context.py": (
        "run_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "user_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "test_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "artifact_group_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "command_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
        "job_kind_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(",
    ),
    "packages/core/observability/logger.py": (
        'extra.setdefault("run_id", run_id_ctx.get())',
        'extra.setdefault("request_id", request_id_ctx.get())',
        'extra.setdefault("trace_id", trace_id_ctx.get())',
        'extra.setdefault("artifact_group", artifact_group_ctx.get())',
        'extra.setdefault("command_id", command_id_ctx.get())',
        'extra.setdefault("job_kind", job_kind_ctx.get())',
    ),
    "services/api/main.py": (
        "configure_process_logging(",
        'response.headers["X-Request-ID"] = request_id',
        'response.headers["X-Trace-ID"] = trace_id',
    ),
    "services/worker/__init__.py": (
        "configure_process_logging(",
        'service="provenote-worker"',
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None, help="Repository root path")
    parser.add_argument(
        "--paths",
        nargs="*",
        default=None,
        help="Optional relative file paths to scan (.py only)",
    )
    parser.add_argument(
        "--staged-only",
        action="store_true",
        help="Scan staged python files only",
    )
    return parser


def _is_skipped(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def _iter_python_files(repo_root: Path, roots: Sequence[str]) -> Iterable[Path]:
    for root in roots:
        root_path = repo_root / root
        if not root_path.exists():
            continue
        if (
            root_path.is_file()
            and root_path.suffix == ".py"
            and not _is_skipped(root_path)
        ):
            yield root_path
            continue
        if not root_path.is_dir():
            continue
        for py_file in sorted(root_path.rglob("*.py")):
            if _is_skipped(py_file):
                continue
            yield py_file


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _leading_spaces(text: str) -> int:
    return len(text) - len(text.lstrip(" "))


def _block_has_logger(lines: Sequence[str], start_index: int) -> bool:
    except_line = lines[start_index]
    except_indent = _leading_spaces(except_line)

    for j in range(start_index + 1, len(lines)):
        line = lines[j]
        stripped = line.strip()

        if not stripped:
            continue

        indent = _leading_spaces(line)
        if indent <= except_indent and not line.lstrip().startswith("#"):
            break

        if LOGGER_CALL_PATTERN.search(line):
            return True

    return False


def _block_has_logger_exception(lines: Sequence[str], start_index: int) -> bool:
    except_line = lines[start_index]
    except_indent = _leading_spaces(except_line)

    for j in range(start_index + 1, len(lines)):
        line = lines[j]
        stripped = line.strip()

        if not stripped:
            continue

        indent = _leading_spaces(line)
        if indent <= except_indent and not line.lstrip().startswith("#"):
            break

        if LOGGER_EXCEPTION_PATTERN.search(line):
            return True

    return False


def find_broad_exception_without_log(
    repo_root: Path, files: Sequence[Path]
) -> list[str]:
    violations: list[str] = []
    for file_path in files:
        rel = file_path.relative_to(repo_root).as_posix()
        lines = _read_lines(file_path)
        for lineno, line in enumerate(lines, start=1):
            if not BROAD_EXCEPT_PATTERN.match(line):
                continue
            if _block_has_logger(lines, lineno - 1):
                continue
            violations.append(
                f"{rel}:{lineno}: broad exception block missing logger call"
            )
    return violations


def find_broad_exception_without_stack_log(
    repo_root: Path, files: Sequence[Path]
) -> list[str]:
    violations: list[str] = []
    for file_path in files:
        rel = file_path.relative_to(repo_root).as_posix()
        lines = _read_lines(file_path)
        for lineno, line in enumerate(lines, start=1):
            if not BROAD_EXCEPT_PATTERN.match(line):
                continue
            if _block_has_logger_exception(lines, lineno - 1):
                continue
            violations.append(
                f"{rel}:{lineno}: broad exception block missing logger.exception stack evidence"
            )
    return violations


def find_sensitive_logging_violations(
    repo_root: Path, files: Sequence[Path]
) -> list[str]:
    violations: list[str] = []
    for file_path in files:
        rel = file_path.relative_to(repo_root).as_posix()
        for lineno, line in enumerate(_read_lines(file_path), start=1):
            if not LOGGER_CALL_PATTERN.search(line):
                continue
            if SENSITIVE_INTERPOLATION_PATTERN.search(line):
                violations.append(
                    f"{rel}:{lineno}: sensitive identifier interpolated in logger f-string"
                )
            elif SENSITIVE_KV_PATTERN.search(line):
                violations.append(
                    f"{rel}:{lineno}: sensitive key-value passed into logger context"
                )
    return violations


def find_unstructured_key_logs(repo_root: Path) -> list[str]:
    violations: list[str] = []
    for rel_path in KEY_STRUCTURED_FILES:
        file_path = repo_root / rel_path
        if not file_path.is_file():
            violations.append(f"{rel_path}: missing structured logging file")
            continue
        for lineno, line in enumerate(_read_lines(file_path), start=1):
            if FSTRING_LOGGER_PATTERN.search(line):
                violations.append(
                    f"{rel_path}:{lineno}: key auth/provider path must not use f-string logger"
                )
    return violations


def find_missing_trace_contract(repo_root: Path) -> list[str]:
    violations: list[str] = []
    for rel_path, snippets in TRACE_CONTRACT_FILES.items():
        path = repo_root / rel_path
        if not path.is_file():
            violations.append(f"{rel_path} missing")
            continue
        content = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in content:
                violations.append(
                    f"{rel_path} missing trace contract snippet: {snippet}"
                )
    return violations


def _resolve_candidate_files(repo_root: Path, args: argparse.Namespace) -> list[Path]:
    if args.staged_only:
        proc = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"unable to read staged files: {proc.stderr.strip()}")
        staged_files = [
            item.strip() for item in proc.stdout.splitlines() if item.strip()
        ]
        paths = staged_files
    else:
        paths = args.paths

    if paths:
        candidates: list[Path] = []
        for rel in paths:
            rel_path = Path(rel)
            file_path = (repo_root / rel_path).resolve()
            try:
                file_path.relative_to(repo_root.resolve())
            except ValueError:
                continue
            if (
                file_path.is_file()
                and file_path.suffix == ".py"
                and not _is_skipped(file_path)
            ):
                candidates.append(file_path)
        return sorted(dict.fromkeys(candidates))

    return sorted(dict.fromkeys(_iter_python_files(repo_root, DEFAULT_SCAN_ROOTS)))


def _filter_files_by_list(
    repo_root: Path, files: Sequence[Path], allowed_paths: Sequence[str]
) -> list[Path]:
    allowed = {str((repo_root / item).resolve()) for item in allowed_paths}
    selected: list[Path] = []
    for file_path in files:
        resolved = str(file_path.resolve())
        if resolved in allowed:
            selected.append(file_path)
    return selected


def main() -> int:
    args = build_parser().parse_args()
    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else Path(__file__).resolve().parents[3]
    )

    try:
        scan_files = _resolve_candidate_files(repo_root, args)
    except RuntimeError as exc:
        print(f"FAIL [OBS-LOG-BOOT-001]: {exc}")
        return 2

    if not scan_files:
        print(
            "FAIL [OBS-LOG-BOOT-002]: no python files found in target scope; "
            "observability gate must fail closed."
        )
        return 1

    critical_files = _filter_files_by_list(repo_root, scan_files, CRITICAL_GUARD_FILES)
    exception_files = critical_files
    broad_exception_violations = find_broad_exception_without_log(
        repo_root, exception_files
    )
    broad_exception_stack_violations = find_broad_exception_without_stack_log(
        repo_root, exception_files
    )
    sensitive_log_violations = find_sensitive_logging_violations(
        repo_root, critical_files
    )
    key_unstructured_violations = find_unstructured_key_logs(repo_root)
    trace_contract_violations = find_missing_trace_contract(repo_root)

    failed = False

    if broad_exception_violations:
        failed = True
        print(
            "FAIL [OBS-LOG-001]: broad exception blocks in critical directories must log evidence."
        )
        for item in broad_exception_violations:
            print(f"- {item}")
        print()

    if sensitive_log_violations:
        failed = True
        print("FAIL [OBS-LOG-002]: sensitive identifiers must not be logged.")
        for item in sensitive_log_violations:
            print(f"- {item}")
        print()

    if broad_exception_stack_violations:
        failed = True
        print(
            "FAIL [OBS-LOG-005]: broad exception blocks in critical directories "
            "must log stack evidence with logger.exception."
        )
        for item in broad_exception_stack_violations:
            print(f"- {item}")
        print()

    if trace_contract_violations:
        failed = True
        print(
            "FAIL [OBS-LOG-003]: observability runtime and adapter bindings must preserve request/trace context contract."
        )
        for item in trace_contract_violations:
            print(f"- {item}")
        print()

    if key_unstructured_violations:
        failed = True
        print(
            "FAIL [OBS-LOG-004]: key auth/provider files require structured logger calls."
        )
        for item in key_unstructured_violations:
            print(f"- {item}")
        print()

    if failed:
        return 1

    print(
        "PASS [OBS-LOG-000]: observability log gate passed "
        "(exception evidence + secret-safe logging + shared trace contract)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
