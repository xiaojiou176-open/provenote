from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_frontend_logger_keeps_redaction_version() -> None:
    log_text = (REPO_ROOT / "apps/web/src/lib/log.ts").read_text(encoding="utf-8")
    assert 'redaction_version: "v1"' in log_text


def test_frontend_logger_does_not_hardcode_secret_env_names() -> None:
    log_text = (REPO_ROOT / "apps/web/src/lib/log.ts").read_text(encoding="utf-8")
    for token in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        assert token not in log_text
