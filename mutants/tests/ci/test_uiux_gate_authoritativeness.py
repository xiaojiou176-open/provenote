from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "tooling/scripts/ci/run_uiux_gemini_gate.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_uiux_gemini_gate_authority", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    report_dir = tmp_path / "apps/web" / "playwright-report"
    results_dir = tmp_path / "apps/web" / "test-results"
    report_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    (report_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    (results_dir / "trace.zip").write_text("zip", encoding="utf-8")
    (results_dir / "screenshot.png").write_text("png", encoding="utf-8")
    (results_dir / "results.json").write_text("{}", encoding="utf-8")
    return report_dir, results_dir


def test_deterministic_fallback_can_never_claim_authoritative_pass(
    tmp_path: Path,
) -> None:
    report_dir, results_dir = _seed_artifacts(tmp_path)
    artifact_hashes = GATE._compute_artifact_hashes(report_dir, results_dir)
    manifest = {
        "generated_at": _iso_now(),
        "root_dir": str(tmp_path),
        "git_sha": "abc123",
        "github_run_id": "run-001",
        "strategy": "artifact_manifest_v2",
        "artifact_hashes": artifact_hashes,
        "files": [
            {
                "kind": "playwright-report",
                "relative_path": "playwright-report/index.html",
                "size_bytes": 13,
                "sha256": "a" * 64,
            }
        ],
        "total_files": 1,
        "kind_counts": {"playwright-report": 1},
    }
    evaluator = {
        "strategy": "deterministic_fallback",
        "authoritative": False,
        "model_id": "gemini-3.1-pro",
        "ux_score": 100,
        "a11y_score": 100,
        "final_gate": "PASS",
        "fallback_reason": "offline",
        "findings": [
            {
                "severity": "warning",
                "title": "fallback",
                "details": "fallback used",
                "artifact_paths": ["playwright-report/index.html"],
                "evidence": [
                    {
                        "source": "playwright-report",
                        "relative_path": "playwright-report/index.html",
                        "sha256": "a" * 64,
                    }
                ],
            }
        ],
        "evidence_sources": {
            "playwright-report": ["playwright-report/index.html"],
        },
        "generated_at": _iso_now(),
        "git_sha": "abc123",
        "github_run_id": "run-001",
        "manifest_sha256": "0" * 64,
        "artifact_hashes": artifact_hashes,
    }

    failures = GATE._validate_evaluator_trust(
        evaluator,
        expected_git_sha="abc123",
        expected_run_id="run-001",
        max_input_age_minutes=180,
        allow_deterministic_fallback=True,
        expected_manifest_sha256="0" * 64,
        expected_artifact_hashes=artifact_hashes,
    )

    assert any("must never report PASS final_gate" in item for item in failures)


def test_uiux_workflow_never_opts_into_deterministic_fallback_pass() -> None:
    workflow = (
        Path(__file__).resolve().parents[2] / ".github/workflows/uiux-gemini-gate.yml"
    ).read_text(encoding="utf-8")

    assert "--allow-deterministic-fallback" not in workflow
    assert "--allow-legacy-auto-generate" not in workflow
    assert "trusted-path only" in workflow
