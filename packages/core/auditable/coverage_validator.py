from __future__ import annotations

from collections import Counter

from packages.core.auditable.schemas import AuditableClaim, CoverageJSON, DedupEntry


def build_coverage_report(
    expected_pids: list[str],
    claims: list[AuditableClaim],
    dedup_entries: list[DedupEntry],
    unclassified_pids: list[str],
) -> CoverageJSON:
    claim_pids = [pid for claim in claims for pid in claim.source_pids]
    appendix_pids = [entry.pid for entry in dedup_entries]

    observed = set(claim_pids) | set(appendix_pids)
    expected = set(expected_pids)

    missing_pids = sorted(expected - observed)
    unknown_pids = sorted(set(claim_pids) - expected)

    claim_counter = Counter(claim_pids)
    duplicate_pids = sorted([pid for pid, count in claim_counter.items() if count > 1])

    covered_pids = len(expected) - len(missing_pids)
    coverage_rate = (covered_pids / len(expected)) if expected else 1.0

    return CoverageJSON(
        total_pids=len(expected),
        covered_pids=covered_pids,
        coverage_rate=coverage_rate,
        missing_pids=missing_pids,
        duplicate_pids=duplicate_pids,
        unknown_pids=unknown_pids,
        unclassified_pids=sorted(set(unclassified_pids)),
    )
