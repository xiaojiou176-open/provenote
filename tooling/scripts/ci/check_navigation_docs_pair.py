#!/usr/bin/env python3
"""Guard navigation docs for coverage and context-engineering baseline."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

DEFAULT_REQUIRED_MODULES = (
    "apps/web",
    "services/api",
    "packages/core",
    "tests",
)

LAZY_LOAD_MARKERS = (
    "nearest-first rule",
    "Nearest-first rule",
    "read order is fixed",
    "Read order is fixed",
    "documentation navigation policy",
)

SEARCH_BEFORE_WRITE_CMD = (
    'rg -n "<keyword>" AGENTS.md CLAUDE.md README*.md '
    "docs config contracts tooling services packages apps tests ops evals mutants"
)

SEARCH_FILE_INDEX_CMD = "rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*.md'"

SEARCH_EVIDENCE_MARKERS = (
    "command + matched result",
    "matched result (path/line)",
    "evidence token example",
    "evidence token",
)

FAIL_HEADER = "[navigation-docs] FAIL: navigation docs pair coverage check failed."
REMEDIATION_HINT = (
    "[navigation-docs] Fix: add the missing docs pair, then restore the "
    "nearest-first route markers, search-before-write command, and search "
    "evidence wording."
)
PASS_TEMPLATE = (
    "[navigation-docs] PASS: root + {module_count} module(s) satisfy docs pair + "
    "context-policy checks (deep coverage enabled={deep_coverage_enabled})"
)
AUTHORITY_OUTPUT_STRINGS = (
    FAIL_HEADER,
    REMEDIATION_HINT,
    PASS_TEMPLATE,
)

DEEP_COVERAGE_SOURCE_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".json",
    ".md",
    ".yml",
    ".yaml",
    ".sh",
    ".toml",
}

DEEP_COVERAGE_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    ".next",
    ".nuxt",
    "dist",
    "build",
    "coverage",
    ".coverage",
    ".cache",
    "cache",
    ".runtime-cache",
    "tmp",
    "temp",
    "artifacts",
}


def _split_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _collect_modules(args: argparse.Namespace) -> list[str]:
    required_modules_raw = (
        args.required_modules
        if args.required_modules is not None
        else os.environ.get("NAV_DOCS_REQUIRED_MODULES", "")
    )
    if required_modules_raw:
        required_modules = _split_csv(required_modules_raw)
    else:
        required_modules = list(DEFAULT_REQUIRED_MODULES)

    ignored_modules = set(_split_csv(os.environ.get("NAV_DOCS_IGNORE_MODULES", "")))
    if args.ignore_modules:
        ignored_modules.update(_split_csv(args.ignore_modules))

    return [module for module in required_modules if module not in ignored_modules]


def _check_content_policy(file_path: Path, scope: str, errors: list[str]) -> None:
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"[navigation-docs] {scope} unreadable: {file_path} ({exc})")
        return

    if not any(marker in content for marker in LAZY_LOAD_MARKERS):
        errors.append(
            f"[navigation-docs] {scope} missing lazy-load route marker: {file_path}"
        )

    if SEARCH_BEFORE_WRITE_CMD not in content:
        errors.append(
            f"[navigation-docs] {scope} missing search-before-write command: {file_path}"
        )

    if SEARCH_FILE_INDEX_CMD not in content:
        errors.append(
            f"[navigation-docs] {scope} missing docs-index command: {file_path}"
        )

    if not any(marker in content for marker in SEARCH_EVIDENCE_MARKERS):
        errors.append(
            f"[navigation-docs] {scope} missing search evidence wording: {file_path}"
        )


def _is_excluded_path(path: Path) -> bool:
    return any(
        part.startswith(".") or part in DEEP_COVERAGE_IGNORED_DIRS
        for part in path.parts
    )


def _is_source_file(file_path: Path) -> bool:
    if file_path.name in {"Dockerfile", "Makefile"}:
        return True
    return file_path.suffix.lower() in DEEP_COVERAGE_SOURCE_SUFFIXES


def _has_docs_pair_on_ancestor(root: Path, directory: Path) -> bool:
    current = directory
    while True:
        if (current / "AGENTS.md").is_file() and (current / "CLAUDE.md").is_file():
            return True
        if current == root:
            return False
        parent = current.parent
        if parent == current:
            return False
        current = parent


def _check_deep_coverage(
    root: Path, module_path: Path, max_depth: int, errors: list[str]
) -> None:
    source_dirs: set[Path] = set()
    module_path_str = str(module_path)
    for current_root, dirnames, filenames in os.walk(
        module_path_str, topdown=True, followlinks=False
    ):
        current_dir = Path(current_root)
        rel_dir = current_dir.relative_to(module_path)
        rel_dir_parts = 0 if rel_dir == Path(".") else len(rel_dir.parts)

        # Prune ignored/hidden or out-of-scope directories early to avoid
        # expensive traversal into massive paths like node_modules.
        pruned_dirnames: list[str] = []
        for dirname in dirnames:
            rel_subdir = Path(dirname) if rel_dir == Path(".") else rel_dir / dirname
            if _is_excluded_path(rel_subdir):
                continue
            if len(rel_subdir.parts) > max_depth:
                continue
            pruned_dirnames.append(dirname)
        dirnames[:] = pruned_dirnames

        if rel_dir_parts > max_depth:
            continue

        for filename in filenames:
            rel_file = Path(filename) if rel_dir == Path(".") else rel_dir / filename
            if len(rel_file.parts) > max_depth:
                continue
            if _is_excluded_path(rel_file):
                continue
            file_path = current_dir / filename
            if _is_source_file(file_path):
                source_dirs.add(current_dir)

    for source_dir in sorted(source_dirs):
        if not _has_docs_pair_on_ancestor(root, source_dir):
            rel_source = source_dir.relative_to(root)
            errors.append(
                "[navigation-docs] deep coverage missing AGENTS.md+CLAUDE.md on ancestor "
                f"path for source dir: {rel_source}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate navigation docs pair coverage: AGENTS.md + CLAUDE.md must both exist "
            "for repo root and required first-level modules."
        )
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root path (default: current directory).",
    )
    parser.add_argument(
        "--required-modules",
        default=None,
        help=(
            "Comma-separated required first-level modules. "
            "Defaults to built-in policy list unless NAV_DOCS_REQUIRED_MODULES is set."
        ),
    )
    parser.add_argument(
        "--ignore-modules",
        default="",
        help=(
            "Comma-separated module ignore list. "
            "Merged with NAV_DOCS_IGNORE_MODULES env."
        ),
    )
    parser.add_argument(
        "--deep-max-depth",
        type=int,
        default=int(os.environ.get("NAV_DOCS_DEEP_MAX_DEPTH", "6")),
        help=(
            "Max depth (relative to each governed module) to scan for source directories "
            "when validating deep navigation coverage."
        ),
    )
    parser.add_argument(
        "--disable-deep-coverage",
        action="store_true",
        help="Disable deep source-directory coverage checks (not recommended).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    modules = _collect_modules(args)

    errors: list[str] = []

    root_agents = root / "AGENTS.md"
    root_claude = root / "CLAUDE.md"
    if not root_agents.is_file() or not root_claude.is_file():
        missing = []
        if not root_agents.is_file():
            missing.append("AGENTS.md")
        if not root_claude.is_file():
            missing.append("CLAUDE.md")
        errors.append(f"[navigation-docs] root missing: {', '.join(missing)}")
    else:
        _check_content_policy(root_agents, "root", errors)
        _check_content_policy(root_claude, "root", errors)

    for module in modules:
        module_path = root / module
        if not module_path.is_dir():
            errors.append(
                f"[navigation-docs] module path not found: {module} "
                "(update --required-modules or --ignore-modules if intentional)"
            )
            continue

        agents_file = module_path / "AGENTS.md"
        claude_file = module_path / "CLAUDE.md"
        missing = []
        if not agents_file.is_file():
            missing.append("AGENTS.md")
        if not claude_file.is_file():
            missing.append("CLAUDE.md")
        if missing:
            errors.append(f"[navigation-docs] {module} missing: {', '.join(missing)}")
            continue

        _check_content_policy(agents_file, module, errors)
        _check_content_policy(claude_file, module, errors)

        if not args.disable_deep_coverage:
            _check_deep_coverage(
                root=root,
                module_path=module_path,
                max_depth=max(args.deep_max_depth, 1),
                errors=errors,
            )

    if errors:
        print(FAIL_HEADER)
        for item in errors:
            print(f"  - {item}")
        print(REMEDIATION_HINT)
        return 1

    print(
        PASS_TEMPLATE.format(
            module_count=len(modules),
            deep_coverage_enabled=not args.disable_deep_coverage,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
