from __future__ import annotations

from packages.core.auditable.schemas import (
    AuditableClaim,
    AuditableSection,
    CoverageJSON,
    DedupEntry,
    DedupJSON,
)


def _format_pid_refs(pids: list[str]) -> str:
    return "".join([f"[[{pid}]]" for pid in pids])


def render_markdown(
    *,
    title: str,
    sections: list[AuditableSection],
    claims: list[AuditableClaim],
    dedup_json: DedupJSON,
    coverage_json: CoverageJSON,
    dedup_entries: list[DedupEntry],
) -> str:
    lines: list[str] = [f"# {title}", ""]

    lines.extend(["## Rewritten Body (Evidence Linked)", ""])
    if sections:
        for section in sections:
            lines.append(f"### {section.title}")
            for bullet in section.bullets:
                refs = _format_pid_refs(section.source_pids)
                lines.append(f"- {bullet} {refs}".strip())
            lines.append("")
    else:
        lines.append("- No structured sections available")
        lines.append("")

    if claims:
        lines.append("### Claims")
        for claim in claims:
            refs = _format_pid_refs(claim.source_pids)
            lines.append(f"- {claim.text} {refs}".strip())
        lines.append("")

    lines.extend(["## Dedup Map", ""])
    lines.append("| Canonical PID | Merged PIDs | Evidence |")
    lines.append("|---|---|---|")

    for group in dedup_json.exact_groups:
        canonical = str(group.get("canonical_pid", ""))
        members = ", ".join([str(pid) for pid in group.get("member_pids", [])]) or "-"
        lines.append(f"| {canonical} | {members} | exact |")

    for group in dedup_json.near_groups:
        canonical = str(group.get("canonical_pid", ""))
        members = ", ".join([str(pid) for pid in group.get("member_pids", [])]) or "-"
        evidence = group.get("evidence", [])
        evidence_text = "; ".join(
            [
                f"{item.get('pid')}:{float(item.get('similarity', 0.0)):.4f}"
                for item in evidence
            ]
        )
        lines.append(f"| {canonical} | {members} | near ({evidence_text or '-'}) |")

    if not dedup_json.exact_groups and not dedup_json.near_groups:
        lines.append("| - | - | no dedup groups |")

    lines.append("")

    lines.extend(["## Coverage Report", ""])
    lines.append(f"- Total PIDs: {coverage_json.total_pids}")
    lines.append(f"- Coverage Rate: {coverage_json.coverage_rate:.4f}")
    lines.append(
        f"- Missing PIDs: {', '.join(coverage_json.missing_pids) if coverage_json.missing_pids else 'none'}"
    )
    lines.append(
        f"- Duplicate PIDs: {', '.join(coverage_json.duplicate_pids) if coverage_json.duplicate_pids else 'none'}"
    )
    lines.append(
        f"- Unknown PIDs: {', '.join(coverage_json.unknown_pids) if coverage_json.unknown_pids else 'none'}"
    )
    lines.append(
        f"- Unclassified PIDs: {', '.join(coverage_json.unclassified_pids) if coverage_json.unclassified_pids else 'none'}"
    )
    lines.append("")

    lines.extend(["## Lossless Source Appendix", ""])
    for entry in dedup_entries:
        lines.append(f"> [[{entry.pid}]] {entry.text}")

    lines.append("")
    return "\n".join(lines)
