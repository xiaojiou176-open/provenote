#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

echo "[python-test-smells] Scanning Python tests for anti-false-green smells"

python3 - <<'PY'
from __future__ import annotations

import ast
import os
import sys
from dataclasses import dataclass
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    ".next",
    "dist",
    "build",
    "coverage",
    ".runtime-cache",
    "__pycache__",
    "mutants",
}


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    line: int
    col: int
    message: str


def is_test_file(path: Path) -> bool:
    name = path.name
    if not name.endswith(".py"):
        return False
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    return "tests" in path.parts


def collect_test_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            candidate = Path(dirpath) / filename
            if is_test_file(candidate):
                files.append(candidate)
    return sorted(files)


def is_assert_call(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Attribute):
        if func.attr.startswith("assert") or func.attr == "fail":
            return True
        if (
            func.attr == "raises"
            and isinstance(func.value, ast.Name)
            and func.value.id == "pytest"
        ):
            return True
    if isinstance(func, ast.Name):
        if func.id.startswith("assert") or func.id in {"fail", "raises"}:
            return True
    return False


def is_len_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len"


def compare_is_weak_len(compare: ast.Compare) -> bool:
    if len(compare.ops) != 1 or len(compare.comparators) != 1:
        return False
    op = compare.ops[0]
    left = compare.left
    right = compare.comparators[0]
    if isinstance(right, ast.Constant) and isinstance(right.value, (int, float)):
        if isinstance(op, ast.GtE) and is_len_call(left) and right.value <= 0:
            return True
        if isinstance(op, ast.Gt) and is_len_call(left) and right.value <= -1:
            return True
    if isinstance(left, ast.Constant) and isinstance(left.value, (int, float)):
        if isinstance(op, ast.LtE) and is_len_call(right) and left.value <= 0:
            return True
        if isinstance(op, ast.Lt) and is_len_call(right) and left.value <= -1:
            return True
    return False


def assert_is_noop(assert_node: ast.Assert) -> bool:
    test = assert_node.test
    return isinstance(test, ast.Constant) and test.value is True


def assert_is_weak(assert_node: ast.Assert) -> bool:
    test = assert_node.test
    if isinstance(test, ast.Compare):
        if len(test.ops) == 1 and isinstance(test.ops[0], ast.IsNot):
            comp = test.comparators[0] if test.comparators else None
            if isinstance(comp, ast.Constant) and comp.value is None:
                return True
        if compare_is_weak_len(test):
            return True
    return False


def call_is_noop(call: ast.Call) -> bool:
    if not isinstance(call.func, ast.Attribute):
        return False
    if call.func.attr == "assertTrue" and call.args:
        first = call.args[0]
        return isinstance(first, ast.Constant) and first.value is True
    return False


def call_is_weak(call: ast.Call) -> bool:
    if not isinstance(call.func, ast.Attribute):
        return False
    method = call.func.attr
    if method == "assertIsNotNone":
        return True
    if method == "assertGreaterEqual" and len(call.args) >= 2:
        return is_len_call(call.args[0]) and isinstance(call.args[1], ast.Constant) and call.args[1].value <= 0
    if method == "assertGreater" and len(call.args) >= 2:
        return is_len_call(call.args[0]) and isinstance(call.args[1], ast.Constant) and call.args[1].value <= -1
    return False


def iter_test_blocks(tree: ast.AST) -> list[ast.AST]:
    blocks: list[ast.AST] = []
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            blocks.append(node)
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test_"):
                    blocks.append(child)
    return blocks


class ConditionalAssertionVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.if_depth = 0
        self.except_depth = 0
        self.lines: set[int] = set()
        self.matches: list[tuple[int, int]] = []

    def _record(self, node: ast.AST) -> None:
        line = getattr(node, "lineno", 0)
        col = getattr(node, "col_offset", 0)
        if line and line not in self.lines:
            self.lines.add(line)
            self.matches.append((line, col))

    def visit_If(self, node: ast.If) -> None:
        self.if_depth += 1
        for child in node.body:
            self.visit(child)
        for child in node.orelse:
            self.visit(child)
        self.if_depth -= 1

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.except_depth += 1
        for child in node.body:
            self.visit(child)
        self.except_depth -= 1

    def visit_Assert(self, node: ast.Assert) -> None:
        if self.if_depth > 0 or self.except_depth > 0:
            self._record(node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if (self.if_depth > 0 or self.except_depth > 0) and is_assert_call(node):
            self._record(node)
        self.generic_visit(node)


def analyze_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    rel = str(path.relative_to(Path.cwd()))
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=rel)
    except (UnicodeDecodeError, SyntaxError) as exc:
        line = getattr(exc, "lineno", 1) or 1
        col = getattr(exc, "offset", 1) or 1
        findings.append(
            Finding(
                kind="parse-error",
                path=rel,
                line=line,
                col=col,
                message=f"Unable to parse test file: {exc}",
            )
        )
        return findings

    test_blocks = iter_test_blocks(tree)
    for block in test_blocks:
        has_assertion = False
        for node in ast.walk(block):
            if isinstance(node, ast.Assert):
                has_assertion = True
                break
            if isinstance(node, ast.Call) and is_assert_call(node):
                has_assertion = True
                break
        if not has_assertion:
            findings.append(
                Finding(
                    kind="no-assertion-test",
                    path=rel,
                    line=getattr(block, "lineno", 1),
                    col=getattr(block, "col_offset", 0),
                    message="Test block has no detectable assertion",
                )
            )

    conditional_visitor = ConditionalAssertionVisitor()
    conditional_visitor.visit(tree)
    for line, col in conditional_visitor.matches:
        findings.append(
            Finding(
                kind="conditional-assertion",
                path=rel,
                line=line,
                col=col,
                message="Assertion inside if/except branch can hide false-green behavior",
            )
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) and assert_is_noop(node):
            findings.append(
                Finding(
                    kind="constant-true-assertion",
                    path=rel,
                    line=node.lineno,
                    col=node.col_offset,
                    message="Constant-true assert detected (assert True)",
                )
            )
        if isinstance(node, ast.Call) and call_is_noop(node):
            findings.append(
                Finding(
                    kind="constant-true-assertion",
                    path=rel,
                    line=node.lineno,
                    col=node.col_offset,
                    message="Constant-true unittest assertion detected (self.assertTrue(True))",
                )
            )
        if isinstance(node, ast.Assert) and assert_is_weak(node):
            findings.append(
                Finding(
                    kind="weak-assertion",
                    path=rel,
                    line=node.lineno,
                    col=node.col_offset,
                    message="Weak assertion detected (e.g. is not None / len(x) >= 0)",
                )
            )
        if isinstance(node, ast.Call) and call_is_weak(node):
            findings.append(
                Finding(
                    kind="weak-assertion",
                    path=rel,
                    line=node.lineno,
                    col=node.col_offset,
                    message="Weak unittest assertion detected (assertIsNotNone / len-based threshold)",
                )
            )

    return findings


def main() -> int:
    root = Path.cwd()
    test_files = collect_test_files(root)
    if not test_files:
        print("[python-test-smells] No Python test files found; skipping")
        return 0

    all_findings: list[Finding] = []
    for path in test_files:
        all_findings.extend(analyze_file(path))

    if all_findings:
        for finding in sorted(all_findings, key=lambda x: (x.path, x.line, x.col, x.kind)):
            print(
                f"[python-test-smells] ERROR [{finding.kind}] "
                f"{finding.path}:{finding.line}:{finding.col + 1} {finding.message}"
            )
        print(f"[python-test-smells] FAILED ({len(all_findings)} finding(s))")
        return 1

    print("[python-test-smells] PASSED")
    return 0


raise SystemExit(main())
PY
