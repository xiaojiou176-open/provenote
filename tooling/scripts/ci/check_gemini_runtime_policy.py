#!/usr/bin/env python3
"""Guard Gemini-only runtime and default model strategy invariants."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

DISALLOWED_PROVIDER_PATTERN = re.compile(
    r"\bprovider\s*(?:==|=|:)\s*[\"'](openai|anthropic|groq|mistral|deepseek|xai|openrouter|ollama|azure|vertex|openai_compatible)[\"']",
    re.IGNORECASE,
)
DISALLOWED_ENV_READ_PATTERN = re.compile(
    r"(?:os\.getenv|os\.environ\.get)\(\s*[\"'](OPENAI_|ANTHROPIC_|GROQ_|MISTRAL_|DEEPSEEK_|XAI_|OPENROUTER_|OLLAMA_|AZURE_OPENAI_|OPENAI_COMPATIBLE_)",
    re.IGNORECASE,
)

RUNTIME_SCAN_ROOTS = (
    REPO_ROOT / "api",
    REPO_ROOT / "open_notebook",
)
RUNTIME_SCAN_EXCLUDES = {
    REPO_ROOT / "open_notebook" / "settings.py",
}

REQUIRED_SNIPPETS: dict[str, tuple[str, ...]] = {
    "packages/core/ai/model_strategy.py": (
        'GEMINI_MODEL_PRO_31 = "gemini-3.1-pro"',
        'GEMINI_MODEL_PRO_30 = "gemini-3.0-pro"',
        'GEMINI_MODEL_FLASH_30 = "gemini-3.0-flash"',
        'GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"',
    ),
    "services/api/routers/models.py": (
        "PRIMARY_LANGUAGE_MODEL = GEMINI_LANGUAGE_MODEL_PRIORITY[0]",
        "SECONDARY_LANGUAGE_MODEL = GEMINI_LANGUAGE_MODEL_PRIORITY[1]",
        "TERTIARY_LANGUAGE_MODEL = GEMINI_LANGUAGE_MODEL_PRIORITY[2]",
    ),
    "packages/core/automation/browser_actions.py": (
        "DEFAULT_BROWSER_AGENT_MODEL = GEMINI_COMPUTER_USE_MODEL",
    ),
    "packages/core/ai/connection_tester.py": (
        "DEFAULT_STARTUP_GEMINI_MODEL = GEMINI_MODEL_FLASH_25",
    ),
}


def _iter_runtime_files() -> list[Path]:
    files: list[Path] = []
    for root in RUNTIME_SCAN_ROOTS:
        if not root.exists():
            continue
        files.extend(
            path for path in root.rglob("*.py") if path not in RUNTIME_SCAN_EXCLUDES
        )
    return sorted(files)


def _check_runtime_violations() -> list[str]:
    violations: list[str] = []
    for file_path in _iter_runtime_files():
        rel = file_path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(
            file_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if DISALLOWED_PROVIDER_PATTERN.search(line):
                violations.append(
                    f"{rel}:{lineno}: disallowed provider runtime path -> {line.strip()}"
                )
            if DISALLOWED_ENV_READ_PATTERN.search(line):
                violations.append(
                    f"{rel}:{lineno}: disallowed legacy env read -> {line.strip()}"
                )
    return violations


def _check_required_snippets() -> list[str]:
    issues: list[str] = []
    for rel_path, snippets in REQUIRED_SNIPPETS.items():
        path = REPO_ROOT / rel_path
        if not path.exists():
            issues.append(f"{rel_path}: file missing")
            continue
        content = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in content:
                issues.append(f"{rel_path}: missing required snippet -> {snippet}")
    return issues


def main() -> int:
    violations = _check_runtime_violations()
    issues = _check_required_snippets()
    if violations or issues:
        print(
            "FAIL [GEMINI-RUNTIME-POLICY-001]: runtime/provider policy violations detected."
        )
        for item in violations:
            print(f"- {item}")
        for item in issues:
            print(f"- {item}")
        return 1

    print(
        "PASS [GEMINI-RUNTIME-POLICY-001]: Gemini-only runtime and model strategy defaults verified."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
