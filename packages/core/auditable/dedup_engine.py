from __future__ import annotations

import math
from collections import Counter, defaultdict

from packages.core.auditable.schemas import DedupEntry, DedupJSON, SourceParagraph


def _to_features(text: str) -> Counter[str]:
    normalized = text.lower()
    if len(normalized) < 3:
        return Counter([normalized] if normalized else [])
    return Counter(normalized[i : i + 3] for i in range(len(normalized) - 2))


def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0

    common_keys = set(left) & set(right)
    dot = sum(left[key] * right[key] for key in common_keys)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def build_dedup_entries(
    source_paragraphs: list[SourceParagraph], near_threshold: float
) -> tuple[list[DedupEntry], DedupJSON]:
    if not source_paragraphs:
        return [], DedupJSON(exact_groups=[], near_groups=[], group_count=0)

    dedup_entries: list[DedupEntry] = []
    exact_index: dict[str, str] = {}
    core_candidates: list[tuple[str, Counter[str]]] = []

    exact_groups_map: dict[str, list[str]] = defaultdict(list)
    near_groups_map: dict[str, list[dict[str, float | str]]] = defaultdict(list)

    for paragraph in source_paragraphs:
        canonical_hash = paragraph.canonical_hash

        if canonical_hash in exact_index:
            leader_pid = exact_index[canonical_hash]
            dedup_entries.append(
                DedupEntry(
                    pid=paragraph.pid,
                    text=paragraph.raw_text,
                    status="duplicate_exact",
                    duplicate_of=leader_pid,
                )
            )
            exact_groups_map[leader_pid].append(paragraph.pid)
            continue

        near_leader: str | None = None
        near_similarity: float | None = None
        paragraph_features = _to_features(paragraph.canonical_text)
        for leader_pid, leader_features in core_candidates:
            similarity = _cosine_similarity(paragraph_features, leader_features)
            if similarity >= near_threshold:
                near_leader = leader_pid
                near_similarity = similarity
                break

        if near_leader:
            dedup_entries.append(
                DedupEntry(
                    pid=paragraph.pid,
                    text=paragraph.raw_text,
                    status="duplicate_near",
                    duplicate_of=near_leader,
                    similarity=near_similarity,
                )
            )
            near_groups_map[near_leader].append(
                {"pid": paragraph.pid, "similarity": float(near_similarity or 0.0)}
            )
            continue

        exact_index[canonical_hash] = paragraph.pid
        core_candidates.append((paragraph.pid, paragraph_features))
        dedup_entries.append(
            DedupEntry(pid=paragraph.pid, text=paragraph.raw_text, status="core")
        )
        exact_groups_map.setdefault(paragraph.pid, [])
        near_groups_map.setdefault(paragraph.pid, [])

    exact_groups = [
        {"canonical_pid": canonical_pid, "member_pids": member_pids}
        for canonical_pid, member_pids in exact_groups_map.items()
        if member_pids
    ]

    near_groups = [
        {
            "canonical_pid": canonical_pid,
            "member_pids": [m["pid"] for m in members],
            "evidence": members,
        }
        for canonical_pid, members in near_groups_map.items()
        if members
    ]

    dedup_json = DedupJSON(
        exact_groups=exact_groups,
        near_groups=near_groups,
        group_count=len(exact_groups) + len(near_groups),
    )
    return dedup_entries, dedup_json
