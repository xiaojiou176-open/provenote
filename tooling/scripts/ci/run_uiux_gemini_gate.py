#!/usr/bin/env python3
"""UI/UX Gemini quality gate for CI pipelines."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

AUTO_GENERATOR_ID = "uiux-gate-auto-generator"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
SOURCE_KEY_RE = re.compile(r"^[a-zA-Z0-9_\\-]+$")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default=".runtime-cache/runs/current/evidence/uiux-gemini/manifest.json",
        help="Path to manifest JSON",
    )
    parser.add_argument(
        "--evaluator",
        default=".runtime-cache/runs/current/evidence/uiux-gemini/evaluator.json",
        help="Path to evaluator JSON result",
    )
    parser.add_argument(
        "--ux-threshold",
        type=float,
        default=80.0,
        help="Minimum acceptable UX score",
    )
    parser.add_argument(
        "--a11y-threshold",
        type=float,
        default=80.0,
        help="Minimum acceptable accessibility score",
    )
    parser.add_argument(
        "--auto-generate",
        action="store_true",
        help="Legacy mode: auto-generate manifest/evaluator files from Playwright artifacts",
    )
    parser.add_argument(
        "--allow-legacy-auto-generate",
        action="store_true",
        help="Explicitly allow legacy auto-generated evaluator to be used for scoring",
    )
    parser.add_argument(
        "--playwright-report-dir",
        default=".runtime-cache/runs/current/evidence/playwright/report",
        help="Playwright HTML report directory for auto-generation",
    )
    parser.add_argument(
        "--playwright-results-dir",
        default=".runtime-cache/runs/current/evidence/playwright/results",
        help="Playwright test-results directory for auto-generation",
    )
    parser.add_argument(
        "--expected-git-sha",
        default=os.getenv("GITHUB_SHA", ""),
        help="Expected git SHA for trusted artifacts (defaults to GITHUB_SHA env)",
    )
    parser.add_argument(
        "--expected-run-id",
        default=os.getenv("GITHUB_RUN_ID", ""),
        help="Expected workflow run id for trusted artifacts (defaults to GITHUB_RUN_ID env)",
    )
    parser.add_argument(
        "--max-input-age-minutes",
        type=int,
        default=180,
        help="Maximum allowed age for manifest/evaluator generated_at timestamps",
    )
    parser.add_argument(
        "--allow-deterministic-fallback",
        action="store_true",
        help=(
            "Allow deterministic fallback payloads to be inspected in degraded mode. "
            "This never upgrades fallback into an authoritative PASS."
        ),
    )
    parser.add_argument(
        "--extra-evidence-dir",
        action="append",
        default=[],
        metavar="SOURCE=PATH",
        help=(
            "Additional evidence source to bind in artifact_hashes trust contract. "
            "Example: screenshots=.runtime-cache/runs/current/evidence/playwright/results/screenshots"
        ),
    )
    return parser


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_by_path(data: Any, path: str) -> Any:
    current: Any = data
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _first_present(data: Any, candidates: list[str]) -> Any:
    for candidate in candidates:
        value = _extract_by_path(data, candidate)
        if value is not None:
            return value
    return None


def _to_score(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip().replace("%", "")
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _normalize_gate(value: Any) -> str | None:
    if value is None:
        return None
    normalized = (
        value.strip().upper() if isinstance(value, str) else str(value).strip().upper()
    )
    if normalized in {"PASS", "SUCCESS", "OK"}:
        return "PASS"
    if normalized in {"FAIL", "FAILED", "ERROR", "NEEDS_ATTENTION"}:
        return "FAIL"
    return normalized


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    return None


def _extract_strategy_and_authoritative(
    evaluator: Any,
) -> tuple[str | None, bool | None]:
    strategy_raw = _first_present(
        evaluator,
        [
            "strategy",
            "result.strategy",
            "summary.strategy",
        ],
    )
    strategy = None
    if isinstance(strategy_raw, str):
        strategy = strategy_raw.strip().lower()
    authoritative = _to_bool(
        _first_present(
            evaluator,
            [
                "authoritative",
                "result.authoritative",
                "summary.authoritative",
            ],
        )
    )
    return strategy, authoritative


def _parse_extra_evidence_dirs(entries: list[str]) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for raw_entry in entries:
        if "=" not in raw_entry:
            raise ValueError(
                f"Invalid --extra-evidence-dir value {raw_entry!r}; expected SOURCE=PATH."
            )
        source, raw_path = raw_entry.split("=", 1)
        source = source.strip()
        raw_path = raw_path.strip()
        if not source or not raw_path:
            raise ValueError(
                f"Invalid --extra-evidence-dir value {raw_entry!r}; SOURCE and PATH are required."
            )
        if not SOURCE_KEY_RE.fullmatch(source):
            raise ValueError(
                f"Invalid evidence source key {source!r}; use only letters, digits, '_' or '-'."
            )
        mapping[source] = Path(raw_path)
    return mapping


def _collect_files(dir_path: Path) -> list[Path]:
    if not dir_path.exists():
        return []
    return sorted([p for p in dir_path.rglob("*") if p.is_file()])


def _auto_generate_inputs(
    manifest_path: Path,
    evaluator_path: Path,
    report_dir: Path,
    results_dir: Path,
) -> None:
    report_files = _collect_files(report_dir)
    result_files = _collect_files(results_dir)
    files = report_files + result_files

    manifest = {
        "generated_by": AUTO_GENERATOR_ID,
        "report_dir": report_dir.as_posix(),
        "results_dir": results_dir.as_posix(),
        "total_files": len(files),
        "kind_counts": {
            "playwright-report": len(report_files),
            "test-results": len(result_files),
        },
        "files": [p.as_posix() for p in files],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    has_html = any(p.suffix.lower() == ".html" for p in report_files)
    has_image = any(
        p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} for p in files
    )
    has_trace = any(
        "trace" in p.name.lower() and p.suffix.lower() == ".zip" for p in files
    )
    has_json = any(p.suffix.lower() == ".json" for p in files)

    ux_score = 0.0
    a11y_score = 0.0
    if has_html:
        ux_score += 35
        a11y_score += 20
    if has_image:
        ux_score += 25
        a11y_score += 20
    if has_trace:
        ux_score += 20
        a11y_score += 20
    if has_json:
        ux_score += 20
        a11y_score += 20

    ux_score = round(min(100.0, ux_score), 2)
    a11y_score = round(min(100.0, a11y_score), 2)
    final_gate = "PASS" if (ux_score >= 80 and a11y_score >= 80) else "FAIL"
    evaluator = {
        "generator": AUTO_GENERATOR_ID,
        "strategy": "deterministic_fallback",
        "authoritative": False,
        "verdict": "needs_attention",
        "ux_score": ux_score,
        "a11y_score": a11y_score,
        "final_gate": "FAIL",
        "fallback_reason": "legacy auto-generated deterministic fallback",
    }
    evaluator_path.parent.mkdir(parents=True, exist_ok=True)
    evaluator_path.write_text(json.dumps(evaluator, indent=2), encoding="utf-8")


def _extract_scores_and_gate(
    evaluator: Any,
) -> tuple[float | None, float | None, str | None]:
    ux_raw = _first_present(
        evaluator,
        [
            "ux",
            "ux_score",
            "scores.ux",
            "scores.ux_score",
            "metrics.ux",
            "metrics.ux_score",
            "result.ux",
            "result.ux_score",
            "summary.ux",
            "summary.ux_score",
            "score",
            "result.score",
            "summary.score",
        ],
    )
    a11y_raw = _first_present(
        evaluator,
        [
            "a11y",
            "a11y_score",
            "scores.a11y",
            "scores.a11y_score",
            "metrics.a11y",
            "metrics.a11y_score",
            "result.a11y",
            "result.a11y_score",
            "summary.a11y",
            "summary.a11y_score",
            "score",
            "result.score",
            "summary.score",
        ],
    )
    gate_raw = _first_present(
        evaluator,
        [
            "final_gate",
            "gate",
            "status",
            "verdict",
            "result.final_gate",
            "summary.final_gate",
            "result.verdict",
            "summary.verdict",
        ],
    )
    return _to_score(ux_raw), _to_score(a11y_raw), _normalize_gate(gate_raw)


def _is_hex_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value.strip().lower()))


def _parse_utc_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8192)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _compute_bundle_hash_for_dir(dir_path: Path) -> str:
    digest = hashlib.sha256()
    if not dir_path.exists():
        digest.update(b"missing")
        return digest.hexdigest()

    files = sorted([item for item in dir_path.rglob("*") if item.is_file()])
    for item in files:
        rel = item.relative_to(dir_path).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\n")
        digest.update(_sha256_file(item).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _compute_artifact_hashes(
    report_dir: Path,
    results_dir: Path,
    *,
    extra_sources: dict[str, Path] | None = None,
) -> dict[str, str]:
    source_hashes: dict[str, str] = {
        "playwright_report": _compute_bundle_hash_for_dir(report_dir),
        "test_results": _compute_bundle_hash_for_dir(results_dir),
    }
    if extra_sources:
        for key, path in extra_sources.items():
            source_hashes[key] = _compute_bundle_hash_for_dir(path)
    return source_hashes


def _validate_manifest_trust(
    manifest: Any,
    *,
    expected_git_sha: str,
    expected_run_id: str,
    max_input_age_minutes: int,
    expected_artifact_hashes: dict[str, str],
) -> list[str]:
    failures: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be a JSON object"]

    if manifest.get("generated_by") == AUTO_GENERATOR_ID:
        failures.append("manifest is auto-generated and not trusted for blocking gate")

    required_top_level = (
        "generated_at",
        "root_dir",
        "git_sha",
        "github_run_id",
        "strategy",
        "artifact_hashes",
        "files",
        "total_files",
        "kind_counts",
    )
    for key in required_top_level:
        if key not in manifest:
            failures.append(f"manifest missing required field: {key}")

    files = manifest.get("files")
    if not isinstance(files, list):
        failures.append("manifest.files must be a list")
        return failures
    if len(files) == 0:
        failures.append("manifest.files is empty")
        return failures

    for index, item in enumerate(files):
        if not isinstance(item, dict):
            failures.append(f"manifest.files[{index}] must be an object")
            continue
        for required in ("kind", "relative_path", "size_bytes", "sha256"):
            if required not in item:
                failures.append(
                    f"manifest.files[{index}] missing required field: {required}"
                )
        if "sha256" in item and not _is_hex_sha256(item.get("sha256")):
            failures.append(
                f"manifest.files[{index}].sha256 must be a 64-char hex string"
            )

    total_files = manifest.get("total_files")
    if isinstance(total_files, int) and total_files != len(files):
        failures.append(
            f"manifest.total_files ({total_files}) does not match files length ({len(files)})"
        )

    generated_at = _parse_utc_timestamp(manifest.get("generated_at"))
    if generated_at is None:
        failures.append("manifest.generated_at must be an ISO-8601 timestamp")
    else:
        age_minutes = (datetime.now(UTC) - generated_at).total_seconds() / 60.0
        if age_minutes < -2:
            failures.append("manifest.generated_at is in the future")
        elif age_minutes > max_input_age_minutes:
            failures.append(
                f"manifest is stale ({age_minutes:.1f}m old > {max_input_age_minutes}m)"
            )

    strategy = manifest.get("strategy")
    if strategy != "artifact_manifest_v2":
        failures.append("manifest.strategy must be 'artifact_manifest_v2'")

    git_sha = manifest.get("git_sha")
    if not isinstance(git_sha, str) or not git_sha.strip():
        failures.append("manifest.git_sha must be a non-empty string")
    elif expected_git_sha and git_sha != expected_git_sha:
        failures.append(
            f"manifest.git_sha {git_sha!r} does not match expected {expected_git_sha!r}"
        )

    run_id = manifest.get("github_run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        failures.append("manifest.github_run_id must be a non-empty string")
    elif expected_run_id and run_id != expected_run_id:
        failures.append(
            f"manifest.github_run_id {run_id!r} does not match expected {expected_run_id!r}"
        )

    artifact_hashes = manifest.get("artifact_hashes")
    if not isinstance(artifact_hashes, dict):
        failures.append("manifest.artifact_hashes must be an object")
    else:
        for key, value in artifact_hashes.items():
            if not _is_hex_sha256(value):
                failures.append(
                    f"manifest.artifact_hashes.{key} must be a 64-char hex string"
                )
        for key in expected_artifact_hashes:
            value = artifact_hashes.get(key)
            if not _is_hex_sha256(value):
                failures.append(
                    f"manifest.artifact_hashes.{key} must be a 64-char hex string"
                )
        for key, expected_hash in expected_artifact_hashes.items():
            actual = artifact_hashes.get(key)
            if isinstance(actual, str) and actual != expected_hash:
                failures.append(
                    f"manifest.artifact_hashes.{key} mismatch (manifest={actual}, runtime={expected_hash})"
                )
    return failures


def _validate_evaluator_trust(
    evaluator: Any,
    *,
    expected_git_sha: str,
    expected_run_id: str,
    max_input_age_minutes: int,
    allow_deterministic_fallback: bool,
    expected_manifest_sha256: str,
    expected_artifact_hashes: dict[str, str],
) -> list[str]:
    failures: list[str] = []
    if not isinstance(evaluator, dict):
        return ["evaluator must be a JSON object"]

    if evaluator.get("generator") == AUTO_GENERATOR_ID:
        failures.append("evaluator is auto-generated and not trusted for blocking gate")

    strategy, authoritative = _extract_strategy_and_authoritative(evaluator)
    if authoritative is None:
        failures.append("evaluator.authoritative must be a boolean")
    if strategy == "deterministic_fallback":
        if authoritative is not False:
            failures.append(
                "evaluator.authoritative must be false when strategy=deterministic_fallback"
            )
        if not allow_deterministic_fallback:
            failures.append(
                "evaluator.strategy deterministic_fallback is not allowed in blocking mode"
            )
    elif strategy != "gemini":
        failures.append(
            "evaluator.strategy must be 'gemini' (or deterministic_fallback with explicit opt-in)"
        )
    elif authoritative is not True:
        failures.append(
            "evaluator.authoritative must be true for trusted gemini results"
        )

    fallback_reason = _first_present(
        evaluator,
        [
            "fallback_reason",
            "result.fallback_reason",
            "summary.fallback_reason",
        ],
    )
    if (
        strategy == "gemini"
        and fallback_reason is not None
        and str(fallback_reason).strip() not in {"", "null", "None"}
    ):
        failures.append(
            "evaluator fallback_reason must be empty/null for trusted evaluator"
        )
    if strategy == "deterministic_fallback" and (
        fallback_reason is None or str(fallback_reason).strip() in {"", "null", "None"}
    ):
        failures.append(
            "evaluator fallback_reason must be present for deterministic_fallback results"
        )

    final_gate = _normalize_gate(
        _first_present(
            evaluator,
            [
                "final_gate",
                "result.final_gate",
                "summary.final_gate",
                "gate",
                "status",
                "verdict",
            ],
        )
    )
    if strategy == "deterministic_fallback" and final_gate == "PASS":
        failures.append(
            "deterministic_fallback must never report PASS final_gate; fallback is degraded/non-authoritative"
        )

    if (
        _first_present(evaluator, ["model_id", "result.model_id", "summary.model_id"])
        is None
    ):
        failures.append("evaluator missing model_id")

    generated_at = _parse_utc_timestamp(evaluator.get("generated_at"))
    if generated_at is None:
        failures.append("evaluator.generated_at must be an ISO-8601 timestamp")
    else:
        age_minutes = (datetime.now(UTC) - generated_at).total_seconds() / 60.0
        if age_minutes < -2:
            failures.append("evaluator.generated_at is in the future")
        elif age_minutes > max_input_age_minutes:
            failures.append(
                f"evaluator is stale ({age_minutes:.1f}m old > {max_input_age_minutes}m)"
            )

    git_sha = evaluator.get("git_sha")
    if not isinstance(git_sha, str) or not git_sha.strip():
        failures.append("evaluator.git_sha must be a non-empty string")
    elif expected_git_sha and git_sha != expected_git_sha:
        failures.append(
            f"evaluator.git_sha {git_sha!r} does not match expected {expected_git_sha!r}"
        )

    run_id = evaluator.get("github_run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        failures.append("evaluator.github_run_id must be a non-empty string")
    elif expected_run_id and run_id != expected_run_id:
        failures.append(
            f"evaluator.github_run_id {run_id!r} does not match expected {expected_run_id!r}"
        )

    manifest_sha256 = evaluator.get("manifest_sha256")
    if not _is_hex_sha256(manifest_sha256):
        failures.append("evaluator.manifest_sha256 must be a 64-char hex string")
    elif manifest_sha256 != expected_manifest_sha256:
        failures.append(
            f"evaluator.manifest_sha256 mismatch (evaluator={manifest_sha256}, runtime={expected_manifest_sha256})"
        )

    artifact_hashes = evaluator.get("artifact_hashes")
    if not isinstance(artifact_hashes, dict):
        failures.append("evaluator.artifact_hashes must be an object")
    else:
        for key, actual in artifact_hashes.items():
            if not _is_hex_sha256(actual):
                failures.append(
                    f"evaluator.artifact_hashes.{key} must be a 64-char hex string"
                )
        for key, expected_hash in expected_artifact_hashes.items():
            actual = artifact_hashes.get(key)
            if not _is_hex_sha256(actual):
                failures.append(
                    f"evaluator.artifact_hashes.{key} must be a 64-char hex string"
                )
                continue
            if actual != expected_hash:
                failures.append(
                    f"evaluator.artifact_hashes.{key} mismatch (evaluator={actual}, runtime={expected_hash})"
                )
    return failures


def _manifest_relative_paths(manifest: Any) -> set[str]:
    files = manifest.get("files")
    if not isinstance(files, list):
        return set()
    paths: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            continue
        path = item.get("relative_path")
        if isinstance(path, str) and path.strip():
            paths.add(path.strip())
    return paths


def _validate_findings_evidence_contract(manifest: Any, evaluator: Any) -> list[str]:
    failures: list[str] = []
    manifest_paths = _manifest_relative_paths(manifest)

    findings_raw = _first_present(
        evaluator,
        ["findings", "result.findings", "summary.findings"],
    )
    if not isinstance(findings_raw, list) or not findings_raw:
        return ["evaluator.findings must be a non-empty list"]

    allowed_severity = {"info", "warning", "critical"}
    for index, finding in enumerate(findings_raw):
        if not isinstance(finding, dict):
            failures.append(f"evaluator.findings[{index}] must be an object")
            continue

        severity = finding.get("severity")
        if severity not in allowed_severity:
            failures.append(
                f"evaluator.findings[{index}].severity must be one of {sorted(allowed_severity)}"
            )
        for required in ("title", "details"):
            value = finding.get(required)
            if not isinstance(value, str) or not value.strip():
                failures.append(
                    f"evaluator.findings[{index}].{required} must be a non-empty string"
                )

        has_evidence_binding = False
        artifact_paths = finding.get("artifact_paths", [])
        if artifact_paths is None:
            artifact_paths = []
        if not isinstance(artifact_paths, list):
            failures.append(
                f"evaluator.findings[{index}].artifact_paths must be a list when present"
            )
            artifact_paths = []
        for artifact_idx, path in enumerate(artifact_paths):
            if not isinstance(path, str) or not path.strip():
                failures.append(
                    f"evaluator.findings[{index}].artifact_paths[{artifact_idx}] must be a non-empty string"
                )
                continue
            normalized_path = path.strip()
            if normalized_path in manifest_paths:
                has_evidence_binding = True
            else:
                failures.append(
                    f"evaluator.findings[{index}] references unknown artifact path: {normalized_path!r}"
                )

        evidence_items = finding.get("evidence", [])
        if evidence_items is None:
            evidence_items = []
        if not isinstance(evidence_items, list):
            failures.append(
                f"evaluator.findings[{index}].evidence must be a list when present"
            )
            evidence_items = []
        for evidence_idx, evidence in enumerate(evidence_items):
            if not isinstance(evidence, dict):
                failures.append(
                    f"evaluator.findings[{index}].evidence[{evidence_idx}] must be an object"
                )
                continue
            source = evidence.get("source")
            if not isinstance(source, str) or not SOURCE_KEY_RE.fullmatch(source):
                failures.append(
                    f"evaluator.findings[{index}].evidence[{evidence_idx}].source is invalid"
                )
            rel_path = evidence.get("relative_path")
            if not isinstance(rel_path, str) or not rel_path.strip():
                failures.append(
                    f"evaluator.findings[{index}].evidence[{evidence_idx}].relative_path must be a non-empty string"
                )
            else:
                normalized_rel_path = rel_path.strip()
                if normalized_rel_path in manifest_paths:
                    has_evidence_binding = True
                else:
                    failures.append(
                        f"evaluator.findings[{index}] evidence references unknown artifact path: {normalized_rel_path!r}"
                    )
            sha256 = evidence.get("sha256")
            if sha256 is not None and not _is_hex_sha256(sha256):
                failures.append(
                    f"evaluator.findings[{index}].evidence[{evidence_idx}].sha256 must be a 64-char hex string when provided"
                )

        if not has_evidence_binding:
            failure_reason = finding.get("failure_reason")
            if not isinstance(failure_reason, dict):
                failures.append(
                    f"evaluator.findings[{index}] must include artifact evidence or a failure_reason object"
                )
                continue
            code = failure_reason.get("code")
            message = failure_reason.get("message")
            if not isinstance(code, str) or not code.strip():
                failures.append(
                    f"evaluator.findings[{index}].failure_reason.code must be a non-empty string"
                )
            if not isinstance(message, str) or not message.strip():
                failures.append(
                    f"evaluator.findings[{index}].failure_reason.message must be a non-empty string"
                )

    evidence_sources = evaluator.get("evidence_sources")
    if not isinstance(evidence_sources, dict) or not evidence_sources:
        failures.append("evaluator.evidence_sources must be a non-empty object")
        return failures
    for source, paths in evidence_sources.items():
        if not isinstance(source, str) or not SOURCE_KEY_RE.fullmatch(source):
            failures.append("evaluator.evidence_sources contains an invalid source key")
        if not isinstance(paths, list) or not paths:
            failures.append(
                f"evaluator.evidence_sources.{source} must be a non-empty list"
            )
            continue
        for path_idx, path in enumerate(paths):
            if not isinstance(path, str) or not path.strip():
                failures.append(
                    f"evaluator.evidence_sources.{source}[{path_idx}] must be a non-empty string"
                )
                continue
            if path.strip() not in manifest_paths:
                failures.append(
                    f"evaluator.evidence_sources.{source}[{path_idx}] references unknown artifact path: {path!r}"
                )
    return failures


def main() -> int:
    args = build_arg_parser().parse_args()
    manifest_path = Path(args.manifest)
    evaluator_path = Path(args.evaluator)
    try:
        extra_evidence_dirs = _parse_extra_evidence_dirs(args.extra_evidence_dir)
    except ValueError as exc:
        print(f"FAIL [UIUX-GATE-ARGS-001]: {exc}")
        return 2

    if args.auto_generate:
        if not args.allow_legacy_auto_generate:
            print(
                "FAIL [UIUX-GATE-TRUST-000]: legacy --auto-generate is blocked by default."
            )
            print(
                "Provide a real evaluator output instead, or explicitly opt in with --allow-legacy-auto-generate."
            )
            return 2
        if not args.allow_deterministic_fallback:
            print(
                "FAIL [UIUX-GATE-TRUST-000]: --allow-legacy-auto-generate requires --allow-deterministic-fallback."
            )
            print("Blocking mode forbids deterministic fallback from passing the gate.")
            return 2
        if not manifest_path.exists() or not evaluator_path.exists():
            _auto_generate_inputs(
                manifest_path=manifest_path,
                evaluator_path=evaluator_path,
                report_dir=Path(args.playwright_report_dir),
                results_dir=Path(args.playwright_results_dir),
            )

    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = _load_json(manifest_path)
        evaluator = _load_json(evaluator_path)
    except FileNotFoundError as exc:
        print(f"FAIL [UIUX-GATE-BOOT-001]: required input file missing: {exc.filename}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"FAIL [UIUX-GATE-BOOT-002]: invalid JSON input: {exc}")
        return 2

    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    runtime_artifact_hashes = _compute_artifact_hashes(
        Path(args.playwright_report_dir),
        Path(args.playwright_results_dir),
        extra_sources=extra_evidence_dirs,
    )
    manifest_failures = _validate_manifest_trust(
        manifest,
        expected_git_sha=args.expected_git_sha,
        expected_run_id=args.expected_run_id,
        max_input_age_minutes=args.max_input_age_minutes,
        expected_artifact_hashes=runtime_artifact_hashes,
    )
    evaluator_failures = _validate_evaluator_trust(
        evaluator,
        expected_git_sha=args.expected_git_sha,
        expected_run_id=args.expected_run_id,
        max_input_age_minutes=args.max_input_age_minutes,
        allow_deterministic_fallback=args.allow_deterministic_fallback,
        expected_manifest_sha256=manifest_sha256,
        expected_artifact_hashes=runtime_artifact_hashes,
    )
    trust_failures = manifest_failures + evaluator_failures
    if trust_failures and not args.allow_legacy_auto_generate:
        print("FAIL [UIUX-GATE-TRUST-001]: evaluator/manifest is not trusted.")
        for item in trust_failures:
            print(f"- {item}")
        return 2

    ux_score, a11y_score, final_gate = _extract_scores_and_gate(evaluator)
    if ux_score is None or a11y_score is None or final_gate is None:
        print(
            "FAIL [UIUX-GATE-DATA-002]: evaluator is missing ux/a11y/final_gate fields."
        )
        print(
            "Expected keys include: ux_score, a11y_score, final_gate or score/verdict (or compatible nested aliases)."
        )
        return 2

    findings_contract_failures = _validate_findings_evidence_contract(
        manifest, evaluator
    )
    if findings_contract_failures and not args.allow_legacy_auto_generate:
        print(
            "FAIL [UIUX-GATE-DATA-003]: evaluator findings/evidence contract is invalid."
        )
        for item in findings_contract_failures:
            print(f"- {item}")
        return 2

    failures: list[str] = []
    if ux_score < args.ux_threshold:
        failures.append(f"ux score {ux_score:.2f} < {args.ux_threshold:.2f}")
    if a11y_score < args.a11y_threshold:
        failures.append(f"a11y score {a11y_score:.2f} < {args.a11y_threshold:.2f}")
    if final_gate != "PASS":
        failures.append(f"final_gate is {final_gate} (expected PASS)")

    print("UIUX Gemini Gate Input:")
    print(f"- manifest: {manifest_path.as_posix()}")
    print(f"- evaluator: {evaluator_path.as_posix()}")
    print("UIUX Gemini Gate Metrics:")
    print(f"- ux_score: {ux_score:.2f}")
    print(f"- a11y_score: {a11y_score:.2f}")
    print(f"- final_gate: {final_gate}")

    strategy, authoritative = _extract_strategy_and_authoritative(evaluator)
    if strategy == "deterministic_fallback":
        print(
            "DEGRADED [UIUX-GATE-002]: deterministic fallback is non-authoritative and cannot satisfy the trusted CI gate."
        )
        print(f"- authoritative: {authoritative}")
        return 1

    if failures:
        print("FAIL [UIUX-GATE-001]: quality gate not met.")
        for item in failures:
            print(f"- {item}")
        return 1

    print("PASS [UIUX-GATE-001]: ux>=80, a11y>=80, final_gate=PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
