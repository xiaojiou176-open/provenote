from __future__ import annotations

import json
import os
import re
import statistics
from typing import Literal

from pydantic import BaseModel, Field

from packages.core.ai.google_genai_adapter import generate_google_text
from packages.core.testing.artifact_pipeline import ArtifactManifest

try:
    from google.genai.errors import APIError as _GoogleGenAIApiError
except ImportError:  # pragma: no cover - optional dependency guard
    GOOGLE_GENAI_ERROR_TYPES: tuple[type[BaseException], ...] = ()
else:
    GOOGLE_GENAI_ERROR_TYPES = (_GoogleGenAIApiError,)
GEMINI_EVALUATOR_MAX_ATTEMPTS = 5
GEMINI_EVALUATOR_MIN_SUCCESSFUL_SAMPLES = 3


class FindingFailureReason(BaseModel):
    code: str
    message: str


class FindingEvidence(BaseModel):
    source: str
    relative_path: str
    sha256: str | None = None


class EvaluationFinding(BaseModel):
    severity: Literal["info", "warning", "critical"]
    title: str
    details: str
    artifact_paths: list[str] = Field(default_factory=list)
    evidence: list[FindingEvidence] = Field(default_factory=list)
    failure_reason: FindingFailureReason | None = None


class UIUXEvaluationResult(BaseModel):
    model_id: str
    strategy: Literal["gemini", "deterministic_fallback"]
    authoritative: bool = True
    score: float = Field(ge=0, le=100)
    verdict: Literal["pass", "needs_attention", "fail"]
    findings: list[EvaluationFinding] = Field(default_factory=list)
    fallback_reason: str | None = None
    ux_score: float | None = Field(default=None, ge=0, le=100)
    a11y_score: float | None = Field(default=None, ge=0, le=100)
    final_gate: Literal["PASS", "FAIL"] | None = None
    evidence_sources: dict[str, list[str]] = Field(default_factory=dict)
    generated_at: str | None = None
    git_sha: str | None = None
    github_run_id: str | None = None
    manifest_sha256: str | None = None
    artifact_hashes: dict[str, str] = Field(default_factory=dict)


def _determine_verdict(score: float) -> Literal["pass", "needs_attention", "fail"]:
    if score >= 80:
        return "pass"
    if score >= 50:
        return "needs_attention"
    return "fail"


def _determine_final_gate(
    ux_score: float, a11y_score: float
) -> Literal["PASS", "FAIL"]:
    return "PASS" if (ux_score >= 80 and a11y_score >= 80) else "FAIL"


def _normalize_verdict(
    value: object,
) -> Literal["pass", "needs_attention", "fail"] | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in {"pass", "passed", "success"}:
        return "pass"
    if normalized in {"needs_attention", "needs-attention", "warning", "warn"}:
        return "needs_attention"
    if normalized in {"fail", "failed", "error"}:
        return "fail"
    return None


def _normalize_strategy(
    value: object,
) -> Literal["gemini", "deterministic_fallback"] | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in {"gemini", "live", "model"}:
        return "gemini"
    if normalized in {"deterministic_fallback", "deterministic-fallback", "fallback"}:
        return "deterministic_fallback"
    return None


def _normalize_final_gate(value: object) -> Literal["PASS", "FAIL"] | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper()
    if normalized in {"PASS", "PASSED", "SUCCESS", "OK"}:
        return "PASS"
    if normalized in {"FAIL", "FAILED", "ERROR"}:
        return "FAIL"
    return None


def _extract_json_payload(response_text: str) -> dict:
    stripped = response_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    if fence_match:
        stripped = fence_match.group(1).strip()
    else:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            stripped = stripped[start : end + 1]
    return json.loads(stripped)


def _normalize_finding_severity(
    value: object,
) -> Literal["info", "warning", "critical"]:
    if not isinstance(value, str):
        return "warning"
    normalized = value.strip().lower()
    if normalized in {"critical", "blocker", "high", "severe"}:
        return "critical"
    if normalized in {"warning", "warn", "medium", "moderate"}:
        return "warning"
    if normalized in {"info", "informational", "low", "minor", "note"}:
        return "info"
    return "warning"


def _normalize_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _normalize_evidence_list(value: object) -> list[dict]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _coerce_score(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip().replace("%", "")
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _normalize_score_scale(payload: dict) -> None:
    keys = ("score", "ux_score", "a11y_score")
    values: list[float] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, (int, float)):
            values.append(float(value))
    if not values:
        return
    if any(value < 0 for value in values):
        return
    if any(value > 1 for value in values):
        return
    for key in keys:
        value = payload.get(key)
        if isinstance(value, (int, float)):
            payload[key] = float(value) * 100.0


def _normalize_finding_payload(payload: object) -> dict | None:
    if not isinstance(payload, dict):
        return None
    normalized = dict(payload)
    normalized["severity"] = _normalize_finding_severity(payload.get("severity"))
    normalized["title"] = str(payload.get("title") or "Untitled finding")
    normalized["details"] = str(payload.get("details") or "")
    normalized["artifact_paths"] = _normalize_string_list(payload.get("artifact_paths"))
    normalized["evidence"] = _normalize_evidence_list(payload.get("evidence"))
    if payload.get("failure_reason") is None:
        normalized["failure_reason"] = None
    return normalized


def _normalize_response_payload(payload: dict) -> dict:
    normalized = dict(payload)

    if strategy := _normalize_strategy(normalized.get("strategy")):
        normalized["strategy"] = strategy

    score = _coerce_score(normalized.get("score"))
    if score is not None:
        normalized["score"] = score

    ux_score = _coerce_score(normalized.get("ux_score"))
    if ux_score is not None:
        normalized["ux_score"] = ux_score
    elif score is not None:
        normalized["ux_score"] = score

    a11y_score = _coerce_score(normalized.get("a11y_score"))
    if a11y_score is not None:
        normalized["a11y_score"] = a11y_score
    elif score is not None:
        normalized["a11y_score"] = score

    _normalize_score_scale(normalized)

    verdict = _normalize_verdict(normalized.get("verdict"))
    if verdict is None and score is not None:
        verdict = _determine_verdict(score)
    if verdict is not None:
        normalized["verdict"] = verdict

    final_gate = _normalize_final_gate(normalized.get("final_gate"))
    ux_for_gate = _coerce_score(normalized.get("ux_score"))
    a11y_for_gate = _coerce_score(normalized.get("a11y_score"))
    if final_gate is None and ux_for_gate is not None and a11y_for_gate is not None:
        final_gate = _determine_final_gate(ux_for_gate, a11y_for_gate)
    if final_gate is not None:
        normalized["final_gate"] = final_gate

    findings = normalized.get("findings")
    if isinstance(findings, dict):
        candidate = _normalize_finding_payload(findings)
        normalized["findings"] = [candidate] if candidate is not None else []
    elif isinstance(findings, list):
        normalized["findings"] = [
            candidate
            for item in findings
            if (candidate := _normalize_finding_payload(item)) is not None
        ]

    return normalized


def _build_manifest_evidence(
    manifest: ArtifactManifest,
) -> tuple[list[FindingEvidence], dict[str, list[str]]]:
    evidence = [
        FindingEvidence(
            source=item.kind,
            relative_path=item.relative_path,
            sha256=item.sha256,
        )
        for item in manifest.files
    ]
    grouped: dict[str, list[str]] = {}
    for item in manifest.files:
        grouped.setdefault(item.kind, []).append(item.relative_path)
    return evidence, grouped


def _build_manifest_summary_finding(
    manifest: ArtifactManifest,
) -> EvaluationFinding | None:
    evidence, _ = _build_manifest_evidence(manifest)
    if not evidence:
        return None
    return EvaluationFinding(
        severity="info",
        title="Artifact bundle verified",
        details=(
            "Gemini completed evaluation against the collected UI test artifacts. "
            "This summary finding binds the trusted manifest evidence used for scoring."
        ),
        artifact_paths=[item.relative_path for item in evidence],
        evidence=evidence,
    )


def _bind_manifest_evidence_to_failure_findings(
    findings: list[EvaluationFinding],
    manifest: ArtifactManifest,
) -> list[EvaluationFinding]:
    manifest_evidence, _ = _build_manifest_evidence(manifest)
    if not manifest_evidence:
        return findings

    bound_findings: list[EvaluationFinding] = []
    manifest_paths = [item.relative_path for item in manifest_evidence]
    for finding in findings:
        if finding.artifact_paths or finding.evidence or finding.failure_reason is None:
            bound_findings.append(finding)
            continue
        bound_findings.append(
            finding.model_copy(
                update={
                    "artifact_paths": manifest_paths,
                    "evidence": manifest_evidence,
                }
            )
        )
    return bound_findings


def _infer_source_from_path(path: str) -> str:
    if "/" in path:
        return path.split("/", 1)[0]
    return "unknown"


def _normalize_result_schema(
    result: UIUXEvaluationResult,
) -> UIUXEvaluationResult:
    if result.strategy == "deterministic_fallback":
        result.authoritative = False
        result.final_gate = "FAIL"
        if result.score <= 0:
            result.verdict = "fail"
        elif result.verdict == "pass":
            result.verdict = "needs_attention"

    if result.ux_score is None:
        result.ux_score = result.score
    if result.a11y_score is None:
        result.a11y_score = result.score

    if result.final_gate is None:
        result.final_gate = _determine_final_gate(result.ux_score, result.a11y_score)

    if not result.evidence_sources:
        grouped: dict[str, list[str]] = {}
        for finding in result.findings:
            if finding.evidence:
                for item in finding.evidence:
                    grouped.setdefault(item.source, []).append(item.relative_path)
            else:
                for artifact_path in finding.artifact_paths:
                    source = _infer_source_from_path(artifact_path)
                    grouped.setdefault(source, []).append(artifact_path)
        result.evidence_sources = grouped
    return result


def _deterministic_fallback(
    manifest: ArtifactManifest, model_id: str, reason: str
) -> UIUXEvaluationResult:
    score = 0.0
    findings: list[EvaluationFinding] = []
    all_paths = [item.relative_path for item in manifest.files]
    all_evidence, evidence_sources = _build_manifest_evidence(manifest)

    has_html = any(path.endswith(".html") for path in all_paths)
    has_image = any(
        path.endswith(ext)
        for path in all_paths
        for ext in (".png", ".jpg", ".jpeg", ".webp")
    )
    has_trace = any(
        path.endswith(".zip") and "trace" in path.lower() for path in all_paths
    )
    has_result_json = any(path.endswith(".json") for path in all_paths)

    findings.append(
        EvaluationFinding(
            severity="warning",
            title="Deterministic fallback is non-authoritative",
            details=(
                "Gemini evaluation was unavailable, so this result only scores artifact "
                "completeness heuristically. It is degraded evidence and cannot satisfy "
                "the trusted blocking UIUX gate."
            ),
            artifact_paths=all_paths,
            evidence=all_evidence,
            failure_reason=FindingFailureReason(
                code="non_authoritative_fallback",
                message=reason,
            ),
        )
    )

    if manifest.total_files == 0:
        findings.append(
            EvaluationFinding(
                severity="critical",
                title="No UI artifacts found",
                details="Neither playwright-report nor test-results contains files.",
                artifact_paths=[],
                evidence=[],
                failure_reason=FindingFailureReason(
                    code="missing_artifacts",
                    message="No files were found in playwright-report or test-results.",
                ),
            )
        )
    if has_html:
        score += 30
    else:
        findings.append(
            EvaluationFinding(
                severity="warning",
                title="Missing HTML report",
                details="No HTML report file found under playwright-report.",
                artifact_paths=all_paths,
                evidence=all_evidence,
            )
        )
    if has_image:
        score += 25
    else:
        findings.append(
            EvaluationFinding(
                severity="warning",
                title="Missing screenshots",
                details="No screenshot-like image artifact was found.",
                artifact_paths=all_paths,
                evidence=all_evidence,
            )
        )
    if has_trace:
        score += 25
    else:
        findings.append(
            EvaluationFinding(
                severity="info",
                title="No trace archive detected",
                details="Trace archives improve replayability for UI regressions.",
                artifact_paths=all_paths,
                evidence=all_evidence,
            )
        )
    if has_result_json:
        score += 20
    else:
        findings.append(
            EvaluationFinding(
                severity="warning",
                title="Missing machine-readable test results",
                details="No JSON result artifact was found.",
                artifact_paths=all_paths,
                evidence=all_evidence,
            )
        )

    score = min(100.0, score)
    result = UIUXEvaluationResult(
        model_id=model_id,
        strategy="deterministic_fallback",
        authoritative=False,
        score=score,
        verdict="fail" if score <= 0 else "needs_attention",
        findings=_normalize_findings(findings),
        fallback_reason=reason,
        ux_score=score,
        a11y_score=score,
        final_gate="FAIL",
        evidence_sources=evidence_sources,
    )
    return _normalize_result_schema(result)


def _normalize_findings(findings: list[EvaluationFinding]) -> list[EvaluationFinding]:
    normalized: list[EvaluationFinding] = []
    for finding in findings:
        if finding.evidence and not finding.artifact_paths:
            artifact_paths = [item.relative_path for item in finding.evidence]
            finding = finding.model_copy(update={"artifact_paths": artifact_paths})
        elif finding.artifact_paths and not finding.evidence:
            finding = finding.model_copy(
                update={
                    "evidence": [
                        FindingEvidence(
                            source=_infer_source_from_path(path),
                            relative_path=path,
                            sha256=None,
                        )
                        for path in finding.artifact_paths
                    ]
                }
            )

        if finding.artifact_paths or finding.failure_reason is not None:
            normalized.append(finding)
            continue
        normalized.append(
            finding.model_copy(
                update={
                    "failure_reason": FindingFailureReason(
                        code="missing_artifact_paths",
                        message="artifact_paths is empty and no artifact evidence was attached.",
                    )
                }
            )
        )
    return normalized


def _resolve_google_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY")


async def _evaluate_with_gemini(
    manifest: ArtifactManifest,
    model_id: str,
) -> UIUXEvaluationResult:
    api_key = _resolve_google_api_key()
    if not api_key:
        raise RuntimeError("missing GEMINI_API_KEY")

    payload = manifest.model_dump(mode="json")
    prompt = (
        "You are a UI/UX test artifact evaluator. "
        "Return strict JSON with keys: model_id, strategy, score, ux_score, a11y_score, verdict, final_gate, findings, fallback_reason. "
        "findings is a list of objects with: severity, title, details, artifact_paths, evidence, failure_reason. "
        "evidence is optional and each item has: source, relative_path, sha256. "
        "failure_reason is optional but required when artifact_paths is empty. "
        "failure_reason must be an object with: code, message. "
        "Use strategy='gemini', fallback_reason=null, and final_gate in {PASS, FAIL}. "
        "Important rules: score, ux_score, and a11y_score must be percentage values in the 0-100 range, never 0-1 fractions. "
        "Only describe issues that are directly visible in the cited artifact_paths/evidence. "
        "Do not mention UI elements, charts, dialogs, or controls that are not clearly visible in the cited artifacts. "
        "Use FAIL only for clear, severe, evidence-backed accessibility or usability problems. "
        "If the artifact bundle is complete and the concerns are minor or uncertain, keep final_gate='PASS' and use warning/info findings instead of failing the gate. "
        "When the bundle contains HTML report + screenshots/traces from passing tests, default to PASS unless there is direct evidence of a major issue."
        f"\nArtifact manifest:\n{json.dumps(payload, ensure_ascii=False)}"
    )

    last_error: BaseException | None = None
    successful_results: list[UIUXEvaluationResult] = []
    for attempt in range(1, GEMINI_EVALUATOR_MAX_ATTEMPTS + 1):
        try:
            response_text = await generate_google_text(
                api_key=api_key,
                model_name=model_id,
                prompt=prompt,
            )

            parsed_payload = _normalize_response_payload(
                _extract_json_payload(response_text)
            )
            parsed = UIUXEvaluationResult.model_validate(parsed_payload)
            if parsed.strategy != "gemini":
                parsed.strategy = "gemini"
            if parsed.model_id != model_id:
                parsed.model_id = model_id
            parsed.fallback_reason = None
            parsed.findings = _normalize_findings(parsed.findings)
            parsed.findings = _bind_manifest_evidence_to_failure_findings(
                parsed.findings, manifest
            )
            if not parsed.findings:
                summary_finding = _build_manifest_summary_finding(manifest)
                if summary_finding is not None:
                    parsed.findings = [summary_finding]
            successful_results.append(_normalize_result_schema(parsed))
            pass_count = sum(
                1 for result in successful_results if result.final_gate == "PASS"
            )
            fail_count = sum(
                1 for result in successful_results if result.final_gate == "FAIL"
            )
            if len(successful_results) >= GEMINI_EVALUATOR_MIN_SUCCESSFUL_SAMPLES and (
                pass_count >= 2 or fail_count >= 2
            ):
                break
        except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
        except GOOGLE_GENAI_ERROR_TYPES as exc:
            last_error = exc

    if successful_results:
        if len(successful_results) == 1:
            return successful_results[0]

        median_score = statistics.median(result.score for result in successful_results)
        median_ux = statistics.median(
            result.ux_score if result.ux_score is not None else result.score
            for result in successful_results
        )
        median_a11y = statistics.median(
            result.a11y_score if result.a11y_score is not None else result.score
            for result in successful_results
        )
        representative = min(
            successful_results,
            key=lambda result: (
                abs(result.score - median_score)
                + abs((result.ux_score or result.score) - median_ux)
                + abs((result.a11y_score or result.score) - median_a11y)
            ),
        )
        pass_count = sum(
            1 for result in successful_results if result.final_gate == "PASS"
        )
        fail_count = sum(
            1 for result in successful_results if result.final_gate == "FAIL"
        )
        final_gate = "PASS" if pass_count >= fail_count else "FAIL"
        verdict_counts = {
            verdict: sum(
                1 for result in successful_results if result.verdict == verdict
            )
            for verdict in ("pass", "needs_attention", "fail")
        }
        verdict = max(
            verdict_counts,
            key=lambda item: (
                verdict_counts[item],
                item == _determine_verdict(median_score),
            ),
        )
        aggregated = representative.model_copy(
            update={
                "score": float(median_score),
                "ux_score": float(median_ux),
                "a11y_score": float(median_a11y),
                "final_gate": final_gate,
                "verdict": verdict,
            }
        )
        return _normalize_result_schema(aggregated)

    assert last_error is not None
    raise last_error


def evaluate_artifacts(
    manifest: ArtifactManifest | dict,
    model_id: str,
) -> UIUXEvaluationResult:
    normalized_manifest = (
        manifest
        if isinstance(manifest, ArtifactManifest)
        else ArtifactManifest.model_validate(manifest)
    )
    if normalized_manifest.total_files == 0:
        return _deterministic_fallback(
            normalized_manifest,
            model_id=model_id,
            reason="No files were found in playwright-report or test-results.",
        )
    try:
        import asyncio

        return asyncio.run(
            _evaluate_with_gemini(normalized_manifest, model_id=model_id)
        )
    except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as exc:
        return _deterministic_fallback(
            normalized_manifest,
            model_id=model_id,
            reason=str(exc),
        )
    except GOOGLE_GENAI_ERROR_TYPES as exc:
        # Quota and provider-side API errors should degrade to deterministic scoring
        # so CI does not fail when external LLM capacity is temporarily unavailable.
        return _deterministic_fallback(
            normalized_manifest,
            model_id=model_id,
            reason=str(exc),
        )
