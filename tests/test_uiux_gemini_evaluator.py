from __future__ import annotations

import json
from pathlib import Path

from packages.core.testing.artifact_pipeline import build_artifact_manifest
from packages.core.testing.uiux_gemini_evaluator import (
    _resolve_google_api_key,
    evaluate_artifacts,
)


def _write_file(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_evaluate_artifacts_uses_deterministic_fallback_when_gemini_unavailable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_file(tmp_path / "playwright-report/index.html", b"<html/>")
    _write_file(tmp_path / "test-results/run/trace.zip", b"trace")
    _write_file(tmp_path / "test-results/run/screenshot.png", b"png")
    _write_file(tmp_path / "test-results/results.json", b"{}")
    manifest = build_artifact_manifest(tmp_path)

    monkeypatch.setattr(
        "packages.core.testing.uiux_gemini_evaluator._evaluate_with_gemini",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("offline")),
    )

    result = evaluate_artifacts(manifest, model_id="gemini-2.5-pro")
    assert result.strategy == "deterministic_fallback"
    assert result.authoritative is False
    assert result.model_id == "gemini-2.5-pro"
    assert result.verdict == "needs_attention"
    assert result.score == 100
    assert result.ux_score == 100
    assert result.a11y_score == 100
    assert result.final_gate == "FAIL"
    assert result.fallback_reason == "offline"
    assert set(result.evidence_sources) == {"playwright-report", "test-results"}
    assert result.findings[0].title == "Deterministic fallback is non-authoritative"
    failure_reason = result.findings[0].failure_reason
    assert (
        failure_reason is not None
        and failure_reason.code == "non_authoritative_fallback"
    )


def test_evaluate_artifacts_reports_missing_artifacts(tmp_path) -> None:
    manifest = build_artifact_manifest(tmp_path / "missing-artifacts-root")

    result = evaluate_artifacts(manifest, model_id="gemini-2.5-pro")
    assert result.strategy == "deterministic_fallback"
    assert result.authoritative is False
    assert result.score == 0
    assert result.final_gate == "FAIL"
    assert result.verdict == "fail"
    assert any(finding.severity == "critical" for finding in result.findings)


def test_evaluate_artifacts_prefers_gemini_api_key_from_env(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_file(tmp_path / "playwright-report/index.html", b"<html/>")
    _write_file(tmp_path / "test-results/run/trace.zip", b"trace")
    _write_file(tmp_path / "test-results/run/screenshot.png", b"png")
    _write_file(tmp_path / "test-results/results.json", b"{}")
    manifest = build_artifact_manifest(tmp_path)

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "legacy-google-key")
    captured: dict[str, str] = {}

    async def _fake_generate_google_text(
        *, api_key: str, model_name: str, prompt: str
    ) -> str:
        captured["api_key"] = api_key
        captured["model_name"] = model_name
        captured["prompt"] = prompt
        return json.dumps(
            {
                "model_id": model_name,
                "strategy": "gemini",
                "score": 88,
                "verdict": "pass",
                "findings": [
                    {
                        "severity": "info",
                        "title": "ok",
                        "details": "ok",
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

    result = evaluate_artifacts(manifest, model_id="gemini-2.5-pro")
    assert result.strategy == "gemini"
    assert captured["api_key"] == "gemini-key"
    assert result.ux_score == 88
    assert result.a11y_score == 88
    assert result.final_gate == "PASS"
    assert (
        result.findings[0].evidence[0].relative_path == "playwright-report/index.html"
    )


def test_evaluate_artifacts_env_resolution_rejects_legacy_google_api_key_alias(
    monkeypatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "legacy-google-key")

    assert _resolve_google_api_key() is None


def test_evaluate_artifacts_supports_evidence_only_findings(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_file(tmp_path / "playwright-report/index.html", b"<html/>")
    manifest = build_artifact_manifest(tmp_path)

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")

    async def _fake_generate_google_text(
        *, api_key: str, model_name: str, prompt: str
    ) -> str:
        del api_key, prompt
        return json.dumps(
            {
                "model_id": model_name,
                "strategy": "gemini",
                "score": 90,
                "verdict": "pass",
                "findings": [
                    {
                        "severity": "info",
                        "title": "ok",
                        "details": "ok",
                        "evidence": [
                            {
                                "source": "playwright-report",
                                "relative_path": "playwright-report/index.html",
                                "sha256": "a" * 64,
                            }
                        ],
                    }
                ],
                "fallback_reason": None,
            }
        )

    monkeypatch.setattr(
        "packages.core.testing.uiux_gemini_evaluator.generate_google_text",
        _fake_generate_google_text,
    )

    result = evaluate_artifacts(manifest, model_id="gemini-2.5-pro")
    assert result.strategy == "gemini"
    assert result.final_gate == "PASS"
    assert result.findings[0].artifact_paths == ["playwright-report/index.html"]
    assert result.evidence_sources["playwright-report"] == [
        "playwright-report/index.html"
    ]


def test_evaluate_artifacts_normalizes_relaxed_gemini_payloads(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_file(tmp_path / "playwright-report/index.html", b"<html/>")
    _write_file(tmp_path / "test-results/results.json", b"{}")
    manifest = build_artifact_manifest(tmp_path)

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")

    async def _fake_generate_google_text(
        *, api_key: str, model_name: str, prompt: str
    ) -> str:
        del api_key, prompt
        return (
            "```json\n"
            + json.dumps(
                {
                    "model_id": "gemini-pro-evaluator-v1",
                    "strategy": "Gemini",
                    "score": "0",
                    "ux_score": "0",
                    "a11y_score": "0",
                    "verdict": "Critical test execution failure. No valid artifacts were generated.",
                    "final_gate": "FAIL",
                    "findings": [
                        {
                            "severity": "BLOCKER",
                            "title": "bad artifacts",
                            "details": "artifacts are invalid",
                            "artifact_paths": "playwright-report/index.html",
                            "evidence": None,
                        }
                    ],
                    "fallback_reason": None,
                }
            )
            + "\n```"
        )

    monkeypatch.setattr(
        "packages.core.testing.uiux_gemini_evaluator.generate_google_text",
        _fake_generate_google_text,
    )

    result = evaluate_artifacts(manifest, model_id="gemini-2.5-pro")

    assert result.strategy == "gemini"
    assert result.fallback_reason is None
    assert result.verdict == "fail"
    assert result.final_gate == "FAIL"
    assert result.findings[0].severity == "critical"
    assert result.findings[0].artifact_paths == ["playwright-report/index.html"]
    assert (
        result.findings[0].evidence[0].relative_path == "playwright-report/index.html"
    )


def test_evaluate_artifacts_derives_gate_tokens_from_scores(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_file(tmp_path / "playwright-report/index.html", b"<html/>")
    manifest = build_artifact_manifest(tmp_path)

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")

    async def _fake_generate_google_text(
        *, api_key: str, model_name: str, prompt: str
    ) -> str:
        del api_key, prompt
        return json.dumps(
            {
                "model_id": model_name,
                "strategy": "live",
                "score": "85%",
                "verdict": "Looks good overall",
                "final_gate": "ready",
                "findings": [
                    {
                        "severity": "low",
                        "title": "ok",
                        "details": "ok",
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

    result = evaluate_artifacts(manifest, model_id="gemini-2.5-pro")

    assert result.strategy == "gemini"
    assert result.verdict == "pass"
    assert result.ux_score == 85
    assert result.a11y_score == 85
    assert result.final_gate == "PASS"
    assert result.findings[0].severity == "info"


def test_evaluate_artifacts_binds_manifest_evidence_for_failure_only_findings(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_file(tmp_path / "playwright-report/index.html", b"<html/>")
    _write_file(tmp_path / "test-results/results.json", b"{}")
    manifest = build_artifact_manifest(tmp_path)

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")

    async def _fake_generate_google_text(
        *, api_key: str, model_name: str, prompt: str
    ) -> str:
        del api_key, model_name, prompt
        return json.dumps(
            {
                "model_id": "gemini-2.5-pro",
                "strategy": "gemini",
                "score": 0,
                "verdict": "fail",
                "findings": [
                    {
                        "severity": "critical",
                        "title": "insufficient artifacts",
                        "details": "not enough coverage",
                        "artifact_paths": [],
                        "evidence": [],
                        "failure_reason": {
                            "code": "INSUFFICIENT_ARTIFACTS",
                            "message": "attach manifest evidence",
                        },
                    }
                ],
                "fallback_reason": None,
                "ux_score": 0,
                "a11y_score": 0,
                "final_gate": "FAIL",
            }
        )

    monkeypatch.setattr(
        "packages.core.testing.uiux_gemini_evaluator.generate_google_text",
        _fake_generate_google_text,
    )

    result = evaluate_artifacts(manifest, model_id="gemini-2.5-pro")

    assert result.strategy == "gemini"
    assert result.findings[0].artifact_paths == [
        "playwright-report/index.html",
        "test-results/results.json",
    ]
    assert [item.relative_path for item in result.findings[0].evidence] == [
        "playwright-report/index.html",
        "test-results/results.json",
    ]
    assert result.evidence_sources == {
        "playwright-report": ["playwright-report/index.html"],
        "test-results": ["test-results/results.json"],
    }


def test_evaluate_artifacts_injects_summary_finding_when_gemini_returns_none(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_file(tmp_path / "playwright-report/index.html", b"<html/>")
    manifest = build_artifact_manifest(tmp_path)

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")

    async def _fake_generate_google_text(
        *, api_key: str, model_name: str, prompt: str
    ) -> str:
        del api_key, model_name, prompt
        return json.dumps(
            {
                "model_id": "gemini-2.5-pro",
                "strategy": "gemini",
                "score": 100,
                "verdict": "pass",
                "findings": [],
                "fallback_reason": None,
                "ux_score": 100,
                "a11y_score": 100,
                "final_gate": "PASS",
            }
        )

    monkeypatch.setattr(
        "packages.core.testing.uiux_gemini_evaluator.generate_google_text",
        _fake_generate_google_text,
    )

    result = evaluate_artifacts(manifest, model_id="gemini-2.5-pro")

    assert result.strategy == "gemini"
    assert len(result.findings) == 1
    assert result.findings[0].title == "Artifact bundle verified"
    assert result.findings[0].artifact_paths == ["playwright-report/index.html"]
    assert result.evidence_sources == {
        "playwright-report": ["playwright-report/index.html"]
    }


def test_evaluate_artifacts_scales_fractional_scores_to_percentages(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_file(tmp_path / "playwright-report/index.html", b"<html/>")
    manifest = build_artifact_manifest(tmp_path)

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")

    async def _fake_generate_google_text(
        *, api_key: str, model_name: str, prompt: str
    ) -> str:
        del api_key, model_name, prompt
        return json.dumps(
            {
                "model_id": "gemini-2.5-pro",
                "strategy": "gemini",
                "score": 0.9,
                "ux_score": 0.95,
                "a11y_score": 0.85,
                "verdict": "pass",
                "final_gate": "PASS",
                "findings": [
                    {
                        "severity": "info",
                        "title": "ok",
                        "details": "ok",
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

    result = evaluate_artifacts(manifest, model_id="gemini-2.5-pro")

    assert result.score == 90
    assert result.ux_score == 95
    assert result.a11y_score == 85
    assert result.final_gate == "PASS"


def test_evaluate_artifacts_retries_transient_parse_failures(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_file(tmp_path / "playwright-report/index.html", b"<html/>")
    manifest = build_artifact_manifest(tmp_path)

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    calls = {"count": 0}

    async def _fake_generate_google_text(
        *, api_key: str, model_name: str, prompt: str
    ) -> str:
        del api_key, model_name, prompt
        calls["count"] += 1
        if calls["count"] == 1:
            return '{"model_id": "gemini-2.5-pro", "strategy": "gemini",'
        return json.dumps(
            {
                "model_id": "gemini-2.5-pro",
                "strategy": "gemini",
                "score": 92,
                "ux_score": 93,
                "a11y_score": 94,
                "verdict": "pass",
                "final_gate": "PASS",
                "findings": [
                    {
                        "severity": "info",
                        "title": "ok",
                        "details": "ok",
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

    result = evaluate_artifacts(manifest, model_id="gemini-2.5-pro")

    assert calls["count"] == 4
    assert result.strategy == "gemini"
    assert result.final_gate == "PASS"


def test_evaluate_artifacts_aggregates_multiple_successful_samples(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _write_file(tmp_path / "playwright-report/index.html", b"<html/>")
    manifest = build_artifact_manifest(tmp_path)

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    responses = iter(
        [
            {
                "model_id": "gemini-2.5-pro",
                "strategy": "gemini",
                "score": 92,
                "ux_score": 94,
                "a11y_score": 90,
                "verdict": "pass",
                "final_gate": "PASS",
                "findings": [
                    {
                        "severity": "warning",
                        "title": "minor issue",
                        "details": "minor",
                        "artifact_paths": ["playwright-report/index.html"],
                    }
                ],
                "fallback_reason": None,
            },
            {
                "model_id": "gemini-2.5-pro",
                "strategy": "gemini",
                "score": 61,
                "ux_score": 55,
                "a11y_score": 70,
                "verdict": "fail",
                "final_gate": "FAIL",
                "findings": [
                    {
                        "severity": "warning",
                        "title": "outlier issue",
                        "details": "outlier",
                        "artifact_paths": ["playwright-report/index.html"],
                    }
                ],
                "fallback_reason": None,
            },
            {
                "model_id": "gemini-2.5-pro",
                "strategy": "gemini",
                "score": 95,
                "ux_score": 96,
                "a11y_score": 94,
                "verdict": "pass",
                "final_gate": "PASS",
                "findings": [
                    {
                        "severity": "info",
                        "title": "good overall",
                        "details": "good",
                        "artifact_paths": ["playwright-report/index.html"],
                    }
                ],
                "fallback_reason": None,
            },
        ]
    )

    async def _fake_generate_google_text(
        *, api_key: str, model_name: str, prompt: str
    ) -> str:
        del api_key, model_name, prompt
        return json.dumps(next(responses))

    monkeypatch.setattr(
        "packages.core.testing.uiux_gemini_evaluator.generate_google_text",
        _fake_generate_google_text,
    )

    result = evaluate_artifacts(manifest, model_id="gemini-2.5-pro")

    assert result.strategy == "gemini"
    assert result.final_gate == "PASS"
    assert result.verdict == "pass"
    assert result.ux_score == 94
    assert result.a11y_score == 90
