from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_provider_surface_truth_gate_exists() -> None:
    assert (REPO_ROOT / "tooling/scripts/ci/check_provider_surface_truth.py").exists()


def test_pyproject_no_longer_carries_legacy_provider_sdks() -> None:
    pyproject = _read("pyproject.toml")
    for token in (
        "langchain-anthropic",
        "langchain-ollama",
        "langchain-groq",
        "langchain_mistralai",
    ):
        assert token not in pyproject


def test_settings_locale_marks_legacy_provider_screens_as_reference_only() -> None:
    settings_locale = _read("apps/web/src/lib/locales/en-US/sections/settings.ts")
    assert "legacy provider screens remain migration/reference-only" in settings_locale


def test_provider_docs_keep_gemini_only_as_mainline_runtime() -> None:
    providers_config = _read("docs/configuration.md")

    assert "Gemini-only runtime contract" in providers_config
    assert "Runtime Allowlist (21)" in providers_config
    assert "Blocked List (40)" in providers_config
    assert "phase1_ssot_naming(canonical_only)" in providers_config


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
