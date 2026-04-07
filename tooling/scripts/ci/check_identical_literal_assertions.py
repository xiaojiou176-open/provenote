from __future__ import annotations

import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
FILE_PATTERN = re.compile(r".*\.(test|spec)\.(js|jsx|ts|tsx|mjs|cjs)$")

# Numeric/bool/null/undefined literals.
LITERAL_ASSERT_PATTERN = re.compile(
    r"expect\s*\(\s*(?P<lhs>true|false|null|undefined|[-+]?\d+(?:\.\d+)?)\s*\)\s*"
    r"\.\s*to(?:Be|Equal|StrictEqual)\s*\(\s*(?P<rhs>true|false|null|undefined|[-+]?\d+(?:\.\d+)?)\s*\)"
)

# String literals with matching quote type.
SINGLE_QUOTED_ASSERT_PATTERN = re.compile(
    r"expect\s*\(\s*'(?P<lhs>(?:\\.|[^'\\])*)'\s*\)\s*"
    r"\.\s*to(?:Be|Equal|StrictEqual)\s*\(\s*'(?P<rhs>(?:\\.|[^'\\])*)'\s*\)"
)
DOUBLE_QUOTED_ASSERT_PATTERN = re.compile(
    r'expect\s*\(\s*"(?P<lhs>(?:\\.|[^"\\])*)"\s*\)\s*'
    r'\.\s*to(?:Be|Equal|StrictEqual)\s*\(\s*"(?P<rhs>(?:\\.|[^"\\])*)"\s*\)'
)

# Tautological identifier/property assertions, e.g. expect(value).toBe(value)
IDENTICAL_IDENTIFIER_ASSERT_PATTERN = re.compile(
    r"expect\s*\(\s*(?P<lhs>[A-Za-z_$][\w$]*(?:\.[\w$]+)*)\s*\)\s*"
    r"\.\s*to(?:Be|Equal|StrictEqual)\s*\(\s*(?P<rhs>[A-Za-z_$][\w$]*(?:\.[\w$]+)*)\s*\)"
)

SKIP_PARTS = {
    ".git",
    ".next",
    ".runtime-cache",
    ".venv",
    "__pycache__",
    "coverage",
    "dist",
    "node_modules",
}


def _is_test_file(path: pathlib.Path) -> bool:
    return FILE_PATTERN.match(path.as_posix()) is not None


def iter_test_files() -> list[pathlib.Path]:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-files"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        tracked = []
        for rel in output.splitlines():
            rel_path = pathlib.Path(rel)
            if any(part in SKIP_PARTS for part in rel_path.parts):
                continue
            if _is_test_file(rel_path):
                full_path = ROOT / rel_path
                if full_path.exists():
                    tracked.append(full_path)
        if tracked:
            return tracked
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    files: list[pathlib.Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        rel_path = path.relative_to(ROOT)
        if _is_test_file(rel_path):
            files.append(path)
    return files


def line_without_inline_comment(line: str) -> str:
    return re.sub(r"//.*$", "", line)


def main() -> None:
    for path in iter_test_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            src = line_without_inline_comment(line)
            if "expect" not in src:
                continue

            literal_match = LITERAL_ASSERT_PATTERN.search(src)
            if literal_match and literal_match.group("lhs") == literal_match.group(
                "rhs"
            ):
                print(f"{path.as_posix()}:{lineno}:{line.strip()}")
                continue

            single_match = SINGLE_QUOTED_ASSERT_PATTERN.search(src)
            if single_match and single_match.group("lhs") == single_match.group("rhs"):
                print(f"{path.as_posix()}:{lineno}:{line.strip()}")
                continue

            double_match = DOUBLE_QUOTED_ASSERT_PATTERN.search(src)
            if double_match and double_match.group("lhs") == double_match.group("rhs"):
                print(f"{path.as_posix()}:{lineno}:{line.strip()}")
                continue

            identifier_match = IDENTICAL_IDENTIFIER_ASSERT_PATTERN.search(src)
            if identifier_match and identifier_match.group(
                "lhs"
            ) == identifier_match.group("rhs"):
                print(f"{path.as_posix()}:{lineno}:{line.strip()}")


if __name__ == "__main__":
    main()
