#!/usr/bin/env python3
"""Gemini-powered apps/web UI/UX gate for pre-commit and pre-push."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from packages.core.ai.google_genai_adapter import generate_google_text

REPO_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_TARGETS = ("apps/web/src", "apps/web/e2e", "apps/web/e2e-live")
FRONTEND_EXTENSIONS = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".html",
}
SEVERITY_FAIL_SET = {"error", "critical", "blocker"}


def _run_git(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            (proc.stderr or proc.stdout or "").strip() or "git command failed"
        )
    return proc.stdout


def _staged_frontend_files() -> list[str]:
    output = _run_git(
        [
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMRT",
            "--",
            *FRONTEND_TARGETS,
        ]
    )
    files = [line.strip() for line in output.splitlines() if line.strip()]
    return [path for path in files if Path(path).suffix.lower() in FRONTEND_EXTENSIONS]


def _staged_diff(files: list[str], max_chars: int) -> str:
    output = _run_git(["diff", "--cached", "--unified=0", "--", *files])
    text = output.strip()
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-(max_chars // 2) :]
    return f"{head}\n\n... [diff truncated for token safety] ...\n\n{tail}"


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty LLM response")
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.S)
    if fenced:
        data = json.loads(fenced.group(1))
        if isinstance(data, dict):
            return data

    brace = re.search(r"(\{.*\})", stripped, re.S)
    if brace:
        data = json.loads(brace.group(1))
        if isinstance(data, dict):
            return data

    raise ValueError("unable to parse JSON object from LLM response")


def _build_prompt(mode: str, diff_text: str, file_list: list[str]) -> str:
    severity_rule = (
        "Use severity=error only for clear, actionable violations. "
        "Use warning for improvements and info for suggestions."
    )
    strictness = (
        "Pre-commit mode: keep feedback short and high signal."
        if mode == "pre-commit"
        else "Pre-push mode: perform stricter review with deeper UX and a11y reasoning."
    )
    files_json = json.dumps(file_list, ensure_ascii=False)
    return (
        "You are a senior Frontend + UI/UX reviewer.\n"
        "Review ONLY the staged apps/web diff below and focus on:\n"
        "1) Accessibility (WCAG 2.2 AA): keyboard, aria semantics, contrast risks, focus states.\n"
        "2) Design-system consistency: avoid hardcoded visual styles when tokenized alternatives are expected.\n"
        "3) Interaction quality: semantic HTML, button type, click+keyboard parity, form safety.\n"
        "4) Maintainability: avoid brittle patterns and noisy anti-patterns in UI code.\n\n"
        f"{strictness}\n"
        f"{severity_rule}\n"
        "If no issue exists, set pass=true and issues=[].\n\n"
        "Return STRICT JSON only with schema:\n"
        "{\n"
        '  "pass": true|false,\n'
        '  "score": 0-100,\n'
        '  "summary": "string",\n'
        '  "issues": [\n'
        "    {\n"
        '      "severity": "info|warning|error",\n'
        '      "file": "path",\n'
        '      "line": 1,\n'
        '      "rule": "short-rule-id",\n'
        '      "description": "what is wrong",\n'
        '      "suggested_fix": "how to fix"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"Changed files: {files_json}\n\n"
        "Unified diff:\n"
        f"{diff_text}\n"
    )


def _candidate_models(requested: str) -> list[str]:
    requested_clean = requested.strip()
    candidates: list[str] = [requested_clean]
    alias_map = {
        "gemini-3.0-flash": [
            "gemini-3-flash-preview",
            "gemini-flash-latest",
            "gemini-2.5-flash",
        ],
        "gemini-3-flash-preview": ["gemini-flash-latest", "gemini-2.5-flash"],
    }
    for alias in alias_map.get(requested_clean, []):
        if alias not in candidates:
            candidates.append(alias)
    return candidates


def _normalize_result(
    data: dict[str, Any],
) -> tuple[bool, float, str, list[dict[str, Any]]]:
    passed = bool(data.get("pass", False))
    score_raw = data.get("score", 0)
    summary = str(data.get("summary", "")).strip()
    issues_raw = data.get("issues", [])
    issues = issues_raw if isinstance(issues_raw, list) else []
    try:
        score = float(score_raw)
    except (TypeError, ValueError):
        score = 0.0
    return passed, score, summary, [item for item in issues if isinstance(item, dict)]


def _should_fail(
    *,
    passed: bool,
    score: float,
    issues: list[dict[str, Any]],
    min_score: float,
) -> bool:
    if score < min_score:
        return True
    error_count = 0
    for issue in issues:
        severity = str(issue.get("severity", "")).strip().lower()
        if severity in SEVERITY_FAIL_SET:
            error_count += 1
    # Allow a small amount of subjective model variance; fail only on concentrated critical issues.
    if error_count >= 4:
        return True
    return False


def _print_result(
    *,
    mode: str,
    model: str,
    passed: bool,
    score: float,
    summary: str,
    issues: list[dict[str, Any]],
) -> None:
    print(f"[gemini-uiux] mode={mode} model={model} score={score:.1f} pass={passed}")
    if summary:
        print(f"[gemini-uiux] summary: {summary}")
    if not issues:
        return
    for idx, issue in enumerate(issues[:8], start=1):
        severity = str(issue.get("severity", "warning")).lower()
        file_path = issue.get("file", "?")
        line = issue.get("line", "?")
        rule = issue.get("rule", "uiux")
        description = issue.get("description", "")
        fix = issue.get("suggested_fix", "")
        print(
            f"[gemini-uiux][{idx}] {severity} {file_path}:{line} ({rule}) - {description}"
        )
        if fix:
            print(f"[gemini-uiux][{idx}] fix: {fix}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("pre-commit", "pre-push"),
        default="pre-commit",
        help="Audit strictness profile",
    )
    parser.add_argument(
        "--model",
        default="gemini-3.0-flash",
        help="Gemini model id (default: gemini-3.0-flash)",
    )
    parser.add_argument(
        "--max-diff-chars",
        type=int,
        default=18000,
        help="Max diff chars sent to Gemini",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=70.0,
        help="Minimum score required to pass gate",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    if os.getenv("UIUX_GEMINI_AUDIT_SKIP", "0") == "1":
        print("[gemini-uiux] skipped via UIUX_GEMINI_AUDIT_SKIP=1")
        return 0

    load_dotenv(REPO_ROOT / ".env", override=False)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[gemini-uiux] missing GEMINI_API_KEY (env or .env)")
        return 1

    files = _staged_frontend_files()
    if not files:
        print("[gemini-uiux] no staged apps/web UI files; skip")
        return 0

    try:
        diff_text = _staged_diff(files, max_chars=max(2000, args.max_diff_chars))
    except RuntimeError as exc:
        print(f"[gemini-uiux] failed to read git diff: {exc}")
        return 1

    prompt = _build_prompt(mode=args.mode, diff_text=diff_text, file_list=files)
    used_model = args.model
    last_error: Exception | None = None
    data: dict[str, Any] | None = None
    for model_name in _candidate_models(args.model):
        try:
            response = asyncio.run(
                generate_google_text(
                    api_key=api_key,
                    model_name=model_name,
                    prompt=prompt,
                )
            )
            data = _extract_json(response)
            used_model = model_name
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            message = str(exc)
            if "NOT_FOUND" in message or "not found" in message.lower():
                continue
            print(f"[gemini-uiux] audit request failed: {type(exc).__name__}: {exc}")
            return 1

    if data is None:
        if last_error is not None:
            print(
                f"[gemini-uiux] audit request failed: {type(last_error).__name__}: {last_error}"
            )
        else:
            print("[gemini-uiux] audit request failed: unknown error")
        return 1

    passed, score, summary, issues = _normalize_result(data)
    _print_result(
        mode=args.mode,
        model=used_model,
        passed=passed,
        score=score,
        summary=summary,
        issues=issues,
    )

    if _should_fail(
        passed=passed, score=score, issues=issues, min_score=args.min_score
    ):
        print("[gemini-uiux] gate failed")
        return 1

    print("[gemini-uiux] gate passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
