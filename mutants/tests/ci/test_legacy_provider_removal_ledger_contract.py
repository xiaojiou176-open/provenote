from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_legacy_provider_removal_ledger_exists() -> None:
    assert (REPO_ROOT / "config/runtime/legacy-provider-removal-ledger.json").exists()
    assert (
        REPO_ROOT / "tooling/scripts/ci/check_legacy_provider_removal_ledger.py"
    ).exists()


def test_legacy_provider_removal_ledger_dependency_entries_are_not_active_runtime_surfaces() -> (
    None
):
    payload = json.loads(
        (REPO_ROOT / "config/runtime/legacy-provider-removal-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    entries = payload["entries"]
    dependency_surfaces = {
        entry["surface"]: entry["removal_readiness"]
        for entry in entries
        if entry["layer"] == "dependency"
    }
    for surface in (
        "langchain-anthropic",
        "langchain-ollama",
        "langchain-groq",
        "langchain_mistralai",
    ):
        assert dependency_surfaces.get(surface) in {"candidate", "removed"}


def test_legacy_provider_removal_ledger_gate_passes() -> None:
    result = subprocess.run(
        ["python3", "tooling/scripts/ci/check_legacy_provider_removal_ledger.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS:" in result.stdout
