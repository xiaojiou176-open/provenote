from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_provider_surface_truth_gate_script_exists() -> None:
    assert (REPO_ROOT / "tooling/scripts/ci/check_provider_surface_truth.py").exists()


def test_settings_surface_no_longer_recommends_non_gemini_default_runtime() -> None:
    text = (
        REPO_ROOT / "apps/web/src/lib/locales/en-US/sections/settings.ts"
    ).read_text(encoding="utf-8")
    assert "OpenAI or Anthropic recommended" not in text
    assert "Gemini recommended" not in text
    assert "Gemini-only runtime" in text
    assert "Google Gemini is the current runtime baseline" in text


def test_configuration_doc_declares_the_canonical_runtime_contract() -> None:
    text = (REPO_ROOT / "docs/configuration.md").read_text(encoding="utf-8")
    assert "Gemini-only runtime contract" in text
    assert "Runtime Allowlist (21)" in text
    assert "Blocked List (40)" in text


def test_provider_surface_truth_gate_passes_on_current_repo_state() -> None:
    result = subprocess.run(
        ["python3", "tooling/scripts/ci/check_provider_surface_truth.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS:" in result.stdout
