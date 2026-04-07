#!/usr/bin/env python3
"""Generate a traceable release proof report (JSON + Markdown)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import cast


@dataclass(frozen=True)
class GateRecord:
    name: str
    status: str
    source: str
    sha_match: bool


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    status: str
    evidence_kind: str = "opaque"
    source_role: str = "direct_artifact"
    limitation: str = ""


@dataclass(frozen=True)
class ImageDigestRecord:
    label: str
    digest: str
    status: str


def _parse_bool(raw: str) -> bool:
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"invalid bool value: {raw}")


def _parse_gate_record(raw: str) -> GateRecord:
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) not in {3, 4} or not all(parts):
        raise ValueError(
            "invalid gate format, expected 'name|status|source' or "
            "'name|status|source|sha_match': "
            f"{raw}"
        )
    sha_match = _parse_bool(parts[3]) if len(parts) == 4 else False
    return GateRecord(
        name=parts[0], status=parts[1], source=parts[2], sha_match=sha_match
    )


def _to_record(base_dir: Path, raw_path: str) -> ArtifactRecord:
    candidate = Path(raw_path)
    resolved = candidate if candidate.is_absolute() else (base_dir / candidate)
    status = "present" if resolved.exists() else "missing"
    evidence_kind = "opaque"
    source_role = "direct_artifact"
    limitation = ""

    if resolved.exists() and resolved.suffix == ".json":
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, dict):
            if "SPDX" in payload:
                evidence_kind = "sbom_spdx"
                source_role = "raw_oci_export"
            elif "SLSA" in payload:
                evidence_kind = "attestation_slsa"
                source_role = "raw_oci_export"
            else:
                raw_kind = payload.get("evidence_kind")
                raw_role = payload.get("source_role")
                raw_limitation = payload.get("limitation")
                if isinstance(raw_kind, str) and raw_kind.strip():
                    evidence_kind = raw_kind.strip()
                if isinstance(raw_role, str) and raw_role.strip():
                    source_role = raw_role.strip()
                if isinstance(raw_limitation, str) and raw_limitation.strip():
                    limitation = raw_limitation.strip()

    return ArtifactRecord(
        path=raw_path,
        status=status,
        evidence_kind=evidence_kind,
        source_role=source_role,
        limitation=limitation,
    )


def _parse_digest_record(raw: str) -> ImageDigestRecord:
    parts = [part.strip() for part in raw.split("|", 1)]
    if len(parts) != 2 or not parts[0]:
        raise ValueError(
            f"invalid image digest format, expected 'label|sha256:...': {raw}"
        )
    digest = parts[1]
    status = "present" if digest else "missing"
    return ImageDigestRecord(label=parts[0], digest=digest, status=status)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commit-sha",
        default=os.getenv("GITHUB_SHA", "unknown"),
        help="Release commit SHA (default: env GITHUB_SHA or 'unknown').",
    )
    parser.add_argument(
        "--required-gate",
        action="append",
        default=[],
        help=(
            "Required gate entry in format: name|status|source "
            "or name|status|source|sha_match"
        ),
    )
    parser.add_argument(
        "--required-gate-validation",
        choices=("strict", "warn", "off"),
        default="strict",
        help=(
            "Required gate status validation mode. "
            "strict=non-zero on non-success gates, warn=report only, off=skip checks."
        ),
    )
    parser.add_argument(
        "--coverage-artifact",
        action="append",
        default=[],
        help="Coverage artifact path (repeatable).",
    )
    parser.add_argument(
        "--e2e-uiux-artifact",
        action="append",
        default=[],
        help="E2E/UIUX artifact path (repeatable).",
    )
    parser.add_argument(
        "--sbom-artifact",
        action="append",
        default=[],
        help="SBOM evidence artifact path (repeatable).",
    )
    parser.add_argument(
        "--attestation-artifact",
        action="append",
        default=[],
        help="Attestation/provenance evidence artifact path (repeatable).",
    )
    parser.add_argument(
        "--image-digest",
        action="append",
        default=[],
        help="Image digest entry in format label|sha256:...",
    )
    parser.add_argument(
        "--mutation-tier",
        default="unknown",
        help="Mutation configuration tier/profile, e.g. core/extended.",
    )
    parser.add_argument(
        "--mutation-config-path",
        default="",
        help="Mutation config path for traceability (optional).",
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Base directory used to resolve artifact paths.",
    )
    parser.add_argument(
        "--output-dir",
        default=".runtime-cache/runs/current/evidence/release-proof",
        help="Directory to write release proof files.",
    )
    return parser


def _render_markdown(data: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Release Proof Report")
    lines.append("")
    lines.append(f"- Commit SHA: `{data['commit_sha']}`")
    lines.append(f"- Generated At (UTC): `{data['generated_at_utc']}`")
    lines.append("")
    lines.append("## Required Gates")
    lines.append("")
    validation = cast(dict[str, object], data["required_gate_validation"])
    lines.append(
        f"- Validation Mode: `{validation['mode']}` | Result: `{validation['result']}`"
    )
    lines.append("")
    lines.append("| Gate | Status | Source | SHA Match |")
    lines.append("| --- | --- | --- | --- |")
    gates = cast(list[dict[str, object]], data["required_gates"])
    if gates:
        for gate in gates:
            assert isinstance(gate, dict)
            status = str(gate["status"]).lower()
            marker = "✅" if status == "success" else "❌"
            sha_match = "true" if gate["sha_match"] else "false"
            lines.append(
                f"| `{gate['name']}` | `{marker} {gate['status']}` | "
                f"`{gate['source']}` | `{sha_match}` |"
            )
    else:
        lines.append("| `missing` | `missing` | `missing` | `false` |")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append("| Category | Path | Status | Source Role | Evidence Kind |")
    lines.append("| --- | --- | --- | --- | --- |")
    coverage_artifacts = cast(list[dict[str, object]], data["coverage_artifacts"])
    for item in coverage_artifacts:
        assert isinstance(item, dict)
        lines.append(
            f"| coverage | `{item['path']}` | `{item['status']}` | `{item['source_role']}` | `{item['evidence_kind']}` |"
        )
    e2e_uiux_artifacts = cast(list[dict[str, object]], data["e2e_uiux_artifacts"])
    for item in e2e_uiux_artifacts:
        assert isinstance(item, dict)
        lines.append(
            f"| e2e/uiux | `{item['path']}` | `{item['status']}` | `{item['source_role']}` | `{item['evidence_kind']}` |"
        )
    sbom_artifacts = cast(list[dict[str, object]], data["sbom_artifacts"])
    for item in sbom_artifacts:
        assert isinstance(item, dict)
        lines.append(
            f"| sbom | `{item['path']}` | `{item['status']}` | `{item['source_role']}` | `{item['evidence_kind']}` |"
        )
    attestation_artifacts = cast(list[dict[str, object]], data["attestation_artifacts"])
    for item in attestation_artifacts:
        assert isinstance(item, dict)
        lines.append(
            f"| attestation | `{item['path']}` | `{item['status']}` | `{item['source_role']}` | `{item['evidence_kind']}` |"
        )
    mutation = data["mutation"]
    assert isinstance(mutation, dict)
    lines.append(
        "| mutation | "
        f"`{mutation['config_path'] or '(not provided)'}` | `{mutation['config_status']}` | `direct_artifact` | `mutation_config` |"
    )
    lines.append("")
    auxiliary_artifacts = [
        item
        for item in [*sbom_artifacts, *attestation_artifacts]
        if isinstance(item, dict) and item.get("source_role") == "auxiliary_summary"
    ]
    if auxiliary_artifacts:
        lines.append("## Evidence Limits")
        lines.append("")
        lines.append(
            "- Some release-proof inputs are digest-linked auxiliary summaries derived from build metadata because the current workflow does not export raw OCI SBOM/attestation files directly."
        )
        for item in auxiliary_artifacts:
            assert isinstance(item, dict)
            limitation = str(item.get("limitation") or "").strip()
            if limitation:
                lines.append(f"  - `{item['path']}`: {limitation}")
        lines.append("")
    lines.append("## Image Digests")
    lines.append("")
    lines.append("| Image | Digest | Status |")
    lines.append("| --- | --- | --- |")
    image_digests = cast(list[dict[str, object]], data["image_digests"])
    if image_digests:
        for item in image_digests:
            assert isinstance(item, dict)
            lines.append(
                f"| `{item['label']}` | `{item['digest'] or '(missing)'}` | `{item['status']}` |"
            )
    else:
        lines.append("| `(none)` | `(none)` | `missing` |")
    lines.append("")
    lines.append("## Mutation Configuration")
    lines.append("")
    lines.append(f"- Tier/Profile: `{mutation['tier']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        gates = [_parse_gate_record(raw) for raw in args.required_gate]
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    failing_gate_names = [
        gate.name for gate in gates if gate.status.strip().lower() != "success"
    ]
    validation_result = "PASS"
    if failing_gate_names:
        validation_result = "FAIL"
    if args.required_gate_validation == "off":
        validation_result = "SKIPPED"

    coverage_records = [_to_record(base_dir, path) for path in args.coverage_artifact]
    e2e_uiux_records = [_to_record(base_dir, path) for path in args.e2e_uiux_artifact]
    sbom_records = [_to_record(base_dir, path) for path in args.sbom_artifact]
    attestation_records = [
        _to_record(base_dir, path) for path in args.attestation_artifact
    ]
    try:
        image_digest_records = [_parse_digest_record(raw) for raw in args.image_digest]
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    mutation_path = args.mutation_config_path.strip()
    mutation_status = "missing"
    if mutation_path:
        mutation_status = _to_record(base_dir, mutation_path).status

    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    report = {
        "commit_sha": args.commit_sha,
        "generated_at_utc": now_utc,
        "required_gates": [asdict(item) for item in gates],
        "required_gate_validation": {
            "mode": args.required_gate_validation,
            "result": validation_result,
            "failing_gate_names": failing_gate_names,
        },
        "coverage_artifacts": [asdict(item) for item in coverage_records],
        "e2e_uiux_artifacts": [asdict(item) for item in e2e_uiux_records],
        "sbom_artifacts": [asdict(item) for item in sbom_records],
        "attestation_artifacts": [asdict(item) for item in attestation_records],
        "image_digests": [asdict(item) for item in image_digest_records],
        "mutation": {
            "tier": args.mutation_tier,
            "config_path": mutation_path,
            "config_status": mutation_status,
        },
    }

    json_path = output_dir / "release-proof.json"
    md_path = output_dir / "release-proof.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    print(f"Release proof JSON: {json_path}")
    print(f"Release proof Markdown: {md_path}")
    if args.required_gate_validation in {"strict", "warn"} and failing_gate_names:
        print(
            "Required gate validation failed: non-success gates: "
            f"{', '.join(failing_gate_names)}",
            file=sys.stderr,
        )
        if args.required_gate_validation == "strict":
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
