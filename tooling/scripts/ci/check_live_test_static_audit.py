#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    label: str
    pattern: str


REPO_ROOT = Path(__file__).resolve().parents[3]
WRITE_HINT_PATTERN = re.compile(
    r"\b(post|put|patch|delete|create|insert|update|remove|destroy)\b",
    flags=re.IGNORECASE | re.MULTILINE,
)
READ_ONLY_CLEANUP_MARKER = re.compile(
    r"live-cleanup:\s*read-only-no-op", flags=re.IGNORECASE | re.MULTILINE
)
REQUIRED_CLEANUP_MARKER = re.compile(
    r"live-cleanup:\s*required", flags=re.IGNORECASE | re.MULTILINE
)
IDEMPOTENCY_MARKER = re.compile(
    r"live-idempotency:", flags=re.IGNORECASE | re.MULTILINE
)

TARGET_RULES: dict[Path, list[Rule]] = {
    Path("tests/live/test_google_live_smoke.py"): [
        Rule("live switch gate", r"RUN_LIVE_TESTS"),
        Rule("real key env read", r"GEMINI_API_KEY"),
        Rule("env lookup implementation", r"os\.getenv\("),
        Rule("placeholder/fake key block", r"placeholder|dummy|fake|pytest\.fail"),
        Rule("heartbeat env config", r"LIVE_HEARTBEAT_SECONDS"),
        Rule("heartbeat log keyword", r"\[live-heartbeat\]"),
        Rule("teardown evidence prefix", r"\[live-teardown-evidence\]"),
        Rule("teardown evidence env", r"LIVE_TEARDOWN_EVIDENCE_FILE"),
        Rule("cleanup marker", r"live-cleanup:\s*read-only-no-op"),
        Rule("idempotency marker", r"live-idempotency:"),
    ],
    Path("apps/web/e2e-live/external-website.spec.ts"): [
        Rule("live switch gate", r"RUN_LIVE_TESTS"),
        Rule("explicit external-live enable switch", r"LIVE_EXTERNAL_WEB_ENABLED"),
        Rule("heartbeat env config", r"LIVE_HEARTBEAT_SECONDS"),
        Rule("heartbeat log keyword", r"\[live-heartbeat\]"),
        Rule("teardown evidence prefix", r"\[live-teardown-evidence\]"),
        Rule("teardown evidence env", r"LIVE_TEARDOWN_EVIDENCE_FILE"),
        Rule("https only guard", r"parsed\.protocol\)\.toBe\([\"']https:[\"']\)"),
        Rule("url credentials blocked", r"parsed\.username\)\.toBe\([\"'][\"']\)"),
        Rule("url password blocked", r"parsed\.password\)\.toBe\([\"'][\"']\)"),
        Rule("private/local host blocker", r"isPrivateOrLocalHost"),
        Rule("private/local host assert", r"toBe\(false\)"),
        Rule("cleanup marker", r"live-cleanup:\s*read-only-no-op"),
        Rule("idempotency marker", r"live-idempotency:"),
    ],
}
LIVE_FILE_GLOBS = ("tests/live/**/*.py", "apps/web/e2e-live/**/*.ts")
BASELINE_LIVE_RULES = (
    Rule("live switch gate", r"RUN_LIVE_TESTS"),
    Rule("heartbeat env config", r"LIVE_HEARTBEAT_SECONDS"),
    Rule("heartbeat log keyword", r"\[live-heartbeat\]"),
)


def _read_text(path: Path) -> str | None:
    full_path = REPO_ROOT / path
    if not full_path.exists():
        return None
    return full_path.read_text(encoding="utf-8")


def _audit_file(path: Path, rules: list[Rule]) -> list[str]:
    content = _read_text(path)
    if content is None:
        return [f"{path}: file not found"]

    errors: list[str] = []
    for rule in rules:
        if re.search(rule.pattern, content, flags=re.IGNORECASE | re.MULTILINE) is None:
            errors.append(f"{path}: missing {rule.label} (pattern: {rule.pattern})")

    has_write_hint = WRITE_HINT_PATTERN.search(content) is not None
    has_read_only_marker = READ_ONLY_CLEANUP_MARKER.search(content) is not None
    has_required_cleanup_marker = REQUIRED_CLEANUP_MARKER.search(content) is not None
    has_idempotency_marker = IDEMPOTENCY_MARKER.search(content) is not None

    if not has_idempotency_marker:
        errors.append(f"{path}: missing idempotency marker (live-idempotency: ...)")
    if has_write_hint and not has_required_cleanup_marker:
        errors.append(
            f"{path}: write-like operation detected; expected marker 'live-cleanup: required' and explicit teardown."
        )
    if not has_write_hint and not has_read_only_marker:
        errors.append(
            f"{path}: read-only live tests must declare 'live-cleanup: read-only-no-op'"
        )
    return errors


def _discover_live_files() -> list[Path]:
    discovered: set[Path] = set()
    for pattern in LIVE_FILE_GLOBS:
        for candidate in REPO_ROOT.glob(pattern):
            if candidate.is_file():
                discovered.add(candidate.relative_to(REPO_ROOT))
    for explicitly_audited in TARGET_RULES:
        discovered.discard(explicitly_audited)
    return sorted(discovered)


def main() -> int:
    issues: list[str] = []
    for rel_path in _discover_live_files():
        issues.extend(_audit_file(path=rel_path, rules=list(BASELINE_LIVE_RULES)))
    for rel_path, rules in TARGET_RULES.items():
        issues.extend(_audit_file(path=rel_path, rules=rules))

    if issues:
        print("[live-static-audit] FAILED")
        for item in issues:
            print(f"- {item}")
        return 1

    print("[live-static-audit] PASSED")
    print(
        "[live-static-audit] verified: RUN_LIVE_TESTS gate, real key env read, heartbeat, URL safety constraints,"
        " teardown evidence emission, and cleanup/idempotency policy markers."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
