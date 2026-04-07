#!/usr/bin/env python3
"""Guard the Gemini-only runtime narrative on current-facing provider surfaces."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    "docs/configuration.md": (
        "Gemini-only runtime contract",
        "Runtime Allowlist (21)",
        "Blocked List (40)",
        "phase1_ssot_naming(canonical_only)",
    ),
    "apps/web/src/lib/locales/en-US/sections/settings.ts": (
        "Gemini-only runtime",
        "Google Gemini is the current runtime baseline",
        "migration/reference-only",
    ),
    "packages/core/settings.py": (
        "does not imply that the active runtime contract is multi-provider",
    ),
}

FORBIDDEN_TOKENS: dict[str, tuple[str, ...]] = {
    "apps/web/src/lib/locales/en-US/sections/settings.ts": (
        "OpenAI or Anthropic recommended",
        "Gemini recommended",
    ),
}


def main() -> int:
    failures: list[str] = []

    for rel_path, tokens in REQUIRED_TOKENS.items():
        path = REPO_ROOT / rel_path
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                failures.append(f"{rel_path} must include token: {token!r}")

    for rel_path, tokens in FORBIDDEN_TOKENS.items():
        path = REPO_ROOT / rel_path
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token in text:
                failures.append(f"{rel_path} must not include token: {token!r}")

    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    legacy_sdk_tokens = (
        "langchain-anthropic",
        "langchain-ollama",
        "langchain-groq",
        "langchain_mistralai",
    )
    if any(token in pyproject_text for token in legacy_sdk_tokens):
        for token in (
            "migration/reference-only provider surfaces",
            "primary Gemini-only runtime path",
        ):
            if token not in pyproject_text:
                failures.append(f"pyproject.toml must include token: {token!r}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: provider surface truth matches the Gemini-only runtime baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
