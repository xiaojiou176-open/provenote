from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from packages.core.testing.artifact_pipeline import build_artifact_manifest
from packages.core.testing.uiux_gemini_evaluator import evaluate_artifacts

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "tooling/scripts/ci/run_uiux_gemini_gate.py"
)
SPEC = importlib.util.spec_from_file_location("run_uiux_gemini_gate", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _manifest_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _trusted_manifest_payload(
    root_dir: Path,
    *,
    git_sha: str,
    run_id: str,
    artifact_hashes: dict[str, str],
    generated_at: str,
) -> dict[str, object]:
    return {
        "generated_at": generated_at,
        "root_dir": str(root_dir),
        "git_sha": git_sha,
        "github_run_id": run_id,
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


def _trusted_evaluator_payload(
    *,
    git_sha: str,
    run_id: str,
    artifact_hashes: dict[str, str],
    manifest_sha256: str,
    generated_at: str,
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "strategy": "gemini",
        "authoritative": True,
        "model_id": "gemini-3.1-pro",
        "ux_score": 85,
        "a11y_score": 88,
        "final_gate": "PASS",
        "findings": [
            {
                "severity": "info",
                "title": "artifact coverage",
                "details": "required artifact evidence attached",
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
        "generated_at": generated_at,
        "git_sha": git_sha,
        "github_run_id": run_id,
        "manifest_sha256": manifest_sha256,
        "artifact_hashes": artifact_hashes,
    }
    payload.update(overrides)
    return payload


def _run_gate(argv: list[str]) -> int:
    cleared_env: dict[str, str | None] = {
        "GITHUB_SHA": os.environ.pop("GITHUB_SHA", None),
        "GITHUB_RUN_ID": os.environ.pop("GITHUB_RUN_ID", None),
    }
    old_argv = sys.argv
    sys.argv = argv
    try:
        return GATE.main()
    finally:
        sys.argv = old_argv
        for key, value in cleared_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _write_trusted_inputs(
    tmp_path: Path,
    *,
    git_sha: str = "abc123",
    run_id: str = "run-001",
    manifest_overrides: dict[str, object] | None = None,
    evaluator_overrides: dict[str, object] | None = None,
) -> tuple[Path, Path, Path, Path]:
    report_dir, results_dir = _seed_artifacts(tmp_path)
    artifact_hashes = GATE._compute_artifact_hashes(report_dir, results_dir)
    manifest = tmp_path / "manifest.json"
    evaluator = tmp_path / "evaluator.json"

    manifest_payload = _trusted_manifest_payload(
        tmp_path,
        git_sha=git_sha,
        run_id=run_id,
        artifact_hashes=artifact_hashes,
        generated_at=_iso_now(),
    )
    if manifest_overrides:
        manifest_payload.update(manifest_overrides)
    _write_json(manifest, manifest_payload)

    evaluator_payload = _trusted_evaluator_payload(
        git_sha=git_sha,
        run_id=run_id,
        artifact_hashes=artifact_hashes,
        manifest_sha256=_manifest_sha256(manifest),
        generated_at=_iso_now(),
    )
    if evaluator_overrides:
        evaluator_payload.update(evaluator_overrides)
    _write_json(evaluator, evaluator_payload)
    return manifest, evaluator, report_dir, results_dir


def test_uiux_gate_passes_with_expected_metrics(tmp_path: Path, capsys) -> None:
    manifest, evaluator, report_dir, results_dir = _write_trusted_inputs(tmp_path)

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
            "--expected-git-sha",
            "abc123",
            "--expected-run-id",
            "run-001",
        ]
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "PASS [UIUX-GATE-001]" in out


def test_uiux_gate_fails_when_threshold_or_gate_not_met(tmp_path: Path, capsys) -> None:
    manifest, evaluator, report_dir, results_dir = _write_trusted_inputs(
        tmp_path,
        evaluator_overrides={"ux_score": 79, "a11y_score": 81, "final_gate": "FAIL"},
    )

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
        ]
    )

    out = capsys.readouterr().out
    assert code == 1
    assert "FAIL [UIUX-GATE-001]" in out
    assert "ux score 79.00 < 80.00" in out
    assert "final_gate is FAIL (expected PASS)" in out


def test_uiux_gate_supports_nested_alias_fields(tmp_path: Path, capsys) -> None:
    manifest, evaluator, report_dir, results_dir = _write_trusted_inputs(
        tmp_path,
        evaluator_overrides={
            "metrics": {"ux": "80.5", "a11y": "82%"},
            "summary": {"final_gate": "pass"},
            "ux_score": None,
            "a11y_score": None,
            "final_gate": None,
        },
    )

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
        ]
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "PASS [UIUX-GATE-001]" in out


def test_uiux_gate_accepts_score_and_verdict_aliases(tmp_path: Path, capsys) -> None:
    manifest, evaluator, report_dir, results_dir = _write_trusted_inputs(
        tmp_path,
        evaluator_overrides={
            "score": 84,
            "verdict": "pass",
            "ux_score": None,
            "a11y_score": None,
            "final_gate": None,
        },
    )

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
        ]
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "PASS [UIUX-GATE-001]" in out


def test_uiux_gate_rejects_untrusted_inputs_with_trust_001(
    tmp_path: Path, capsys
) -> None:
    manifest, evaluator, report_dir, results_dir = _write_trusted_inputs(
        tmp_path,
        manifest_overrides={"github_run_id": ""},
    )

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
        ]
    )

    out = capsys.readouterr().out
    assert code == 2
    assert "FAIL [UIUX-GATE-TRUST-001]" in out


def test_uiux_gate_rejects_git_sha_mismatch(tmp_path: Path, capsys) -> None:
    manifest, evaluator, report_dir, results_dir = _write_trusted_inputs(tmp_path)

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
            "--expected-git-sha",
            "deadbeef",
            "--expected-run-id",
            "run-001",
        ]
    )

    out = capsys.readouterr().out
    assert code == 2
    assert "FAIL [UIUX-GATE-TRUST-001]" in out
    assert "does not match expected" in out


def test_uiux_gate_fails_when_required_data_missing(tmp_path: Path, capsys) -> None:
    manifest, evaluator, report_dir, results_dir = _write_trusted_inputs(
        tmp_path,
        evaluator_overrides={
            "ux_score": None,
            "a11y_score": None,
            "final_gate": None,
            "scores": {"ux": 90},
        },
    )

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
        ]
    )

    out = capsys.readouterr().out
    assert code == 2
    assert "FAIL [UIUX-GATE-DATA-002]" in out


def test_uiux_gate_fails_when_findings_are_missing(tmp_path: Path, capsys) -> None:
    manifest, evaluator, report_dir, results_dir = _write_trusted_inputs(
        tmp_path, evaluator_overrides={"findings": []}
    )

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
        ]
    )

    out = capsys.readouterr().out
    assert code == 2
    assert "FAIL [UIUX-GATE-DATA-003]" in out
    assert "evaluator.findings must be a non-empty list" in out


def test_uiux_gate_fails_when_findings_reference_unknown_artifacts(
    tmp_path: Path, capsys
) -> None:
    manifest, evaluator, report_dir, results_dir = _write_trusted_inputs(
        tmp_path,
        evaluator_overrides={
            "findings": [
                {
                    "severity": "warning",
                    "title": "unknown reference",
                    "details": "path should be bound to manifest",
                    "artifact_paths": ["test-results/unknown.json"],
                }
            ],
            "evidence_sources": {"test-results": ["test-results/unknown.json"]},
        },
    )

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
        ]
    )

    out = capsys.readouterr().out
    assert code == 2
    assert "FAIL [UIUX-GATE-DATA-003]" in out
    assert "references unknown artifact path" in out


def test_uiux_gate_rejects_stale_manifest(tmp_path: Path, capsys) -> None:
    stale = (datetime.now(UTC) - timedelta(hours=5)).isoformat().replace("+00:00", "Z")
    manifest, evaluator, report_dir, results_dir = _write_trusted_inputs(
        tmp_path, manifest_overrides={"generated_at": stale}
    )
    _write_json(
        evaluator,
        _trusted_evaluator_payload(
            git_sha="abc123",
            run_id="run-001",
            artifact_hashes=GATE._compute_artifact_hashes(report_dir, results_dir),
            manifest_sha256=_manifest_sha256(manifest),
            generated_at=_iso_now(),
        ),
    )

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
            "--max-input-age-minutes",
            "60",
        ]
    )

    out = capsys.readouterr().out
    assert code == 2
    assert "FAIL [UIUX-GATE-TRUST-001]" in out
    assert "manifest is stale" in out


def test_uiux_gate_deterministic_fallback_blocked_by_default(
    tmp_path: Path, capsys
) -> None:
    manifest, evaluator, report_dir, results_dir = _write_trusted_inputs(
        tmp_path,
        evaluator_overrides={
            "strategy": "deterministic_fallback",
            "fallback_reason": "offline",
        },
    )

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
        ]
    )

    out = capsys.readouterr().out
    assert code == 2
    assert "FAIL [UIUX-GATE-TRUST-001]" in out
    assert "deterministic_fallback is not allowed" in out


def test_uiux_gate_allow_deterministic_fallback_path(tmp_path: Path, capsys) -> None:
    manifest, evaluator, report_dir, results_dir = _write_trusted_inputs(
        tmp_path,
        evaluator_overrides={
            "strategy": "deterministic_fallback",
            "authoritative": False,
            "final_gate": "FAIL",
            "fallback_reason": "offline",
        },
    )

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
            "--allow-deterministic-fallback",
        ]
    )

    out = capsys.readouterr().out
    assert code == 1
    assert "DEGRADED [UIUX-GATE-002]" in out
    assert "non-authoritative" in out


def test_uiux_gate_auto_generate_is_blocked_by_default(tmp_path: Path, capsys) -> None:
    report_dir = tmp_path / "apps/web" / "playwright-report"
    results_dir = tmp_path / "apps/web" / "test-results"
    report_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    (report_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    (results_dir / "trace.zip").write_text("zip", encoding="utf-8")
    (results_dir / "screenshot.png").write_text("png", encoding="utf-8")
    (results_dir / "results.json").write_text("{}", encoding="utf-8")

    manifest = tmp_path / "artifacts" / "uiux-gemini" / "manifest.json"
    evaluator = tmp_path / "artifacts" / "uiux-gemini" / "evaluator.json"

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--auto-generate",
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
        ]
    )

    out = capsys.readouterr().out
    assert code == 2
    assert "FAIL [UIUX-GATE-TRUST-000]" in out
    assert not manifest.exists()
    assert not evaluator.exists()


def test_uiux_gate_allow_legacy_auto_generate_path(tmp_path: Path, capsys) -> None:
    report_dir = tmp_path / "apps/web" / "playwright-report"
    results_dir = tmp_path / "apps/web" / "test-results"
    report_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    (report_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    (results_dir / "trace.zip").write_text("zip", encoding="utf-8")
    (results_dir / "screenshot.png").write_text("png", encoding="utf-8")
    (results_dir / "results.json").write_text("{}", encoding="utf-8")

    manifest = tmp_path / "artifacts" / "uiux-gemini" / "manifest.json"
    evaluator = tmp_path / "artifacts" / "uiux-gemini" / "evaluator.json"

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--auto-generate",
            "--allow-legacy-auto-generate",
            "--allow-deterministic-fallback",
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
        ]
    )

    out = capsys.readouterr().out
    assert code == 1
    assert "DEGRADED [UIUX-GATE-002]" in out
    assert manifest.exists()
    assert evaluator.exists()


def test_uiux_gate_rejects_legacy_auto_generate_without_fallback_opt_in(
    tmp_path: Path, capsys
) -> None:
    report_dir = tmp_path / "apps/web" / "playwright-report"
    results_dir = tmp_path / "apps/web" / "test-results"
    report_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    (report_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    (results_dir / "trace.zip").write_text("zip", encoding="utf-8")
    (results_dir / "screenshot.png").write_text("png", encoding="utf-8")
    (results_dir / "results.json").write_text("{}", encoding="utf-8")

    manifest = tmp_path / "artifacts" / "uiux-gemini" / "manifest.json"
    evaluator = tmp_path / "artifacts" / "uiux-gemini" / "evaluator.json"

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest),
            "--evaluator",
            str(evaluator),
            "--auto-generate",
            "--allow-legacy-auto-generate",
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
        ]
    )

    out = capsys.readouterr().out
    assert code == 2
    assert "--allow-legacy-auto-generate requires --allow-deterministic-fallback" in out


def test_uiux_gate_end_to_end_accepts_evaluate_artifacts_output(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    report_dir, results_dir = _seed_artifacts(tmp_path)
    frontend_root = tmp_path / "apps/web"
    manifest_path = tmp_path / "manifest.json"
    evaluator_path = tmp_path / "evaluator.json"

    manifest_obj = build_artifact_manifest(frontend_root)
    artifact_hashes = GATE._compute_artifact_hashes(report_dir, results_dir)

    manifest_payload = manifest_obj.model_dump(mode="json")
    manifest_payload.update(
        {
            "strategy": "artifact_manifest_v2",
            "generated_at": _iso_now(),
            "git_sha": "abc123",
            "github_run_id": "run-001",
            "artifact_hashes": artifact_hashes,
        }
    )
    _write_json(manifest_path, manifest_payload)

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")

    async def _fake_generate_google_text(
        *, api_key: str, model_name: str, prompt: str
    ) -> str:
        del api_key, prompt
        return json.dumps(
            {
                "model_id": model_name,
                "strategy": "gemini",
                "score": 91,
                "verdict": "pass",
                "findings": [
                    {
                        "severity": "info",
                        "title": "artifact coverage",
                        "details": "all required evidence present",
                        "artifact_paths": ["playwright-report/index.html"],
                    }
                ],
                "fallback_reason": None,
            }
        )

    monkeypatch.setattr(
        "packages.core.testing.uiux_gemini_evaluator.generate_google_text",
        _fake_generate_google_text,
    )

    evaluator_result = evaluate_artifacts(manifest_obj, model_id="gemini-3.1-pro")
    evaluator_payload = evaluator_result.model_dump(mode="json")
    evaluator_payload.update(
        {
            "generated_at": _iso_now(),
            "git_sha": "abc123",
            "github_run_id": "run-001",
            "manifest_sha256": _manifest_sha256(manifest_path),
            "artifact_hashes": artifact_hashes,
        }
    )
    _write_json(evaluator_path, evaluator_payload)

    code = _run_gate(
        [
            "run_uiux_gemini_gate.py",
            "--manifest",
            str(manifest_path),
            "--evaluator",
            str(evaluator_path),
            "--playwright-report-dir",
            str(report_dir),
            "--playwright-results-dir",
            str(results_dir),
            "--expected-git-sha",
            "abc123",
            "--expected-run-id",
            "run-001",
        ]
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "PASS [UIUX-GATE-001]" in out
