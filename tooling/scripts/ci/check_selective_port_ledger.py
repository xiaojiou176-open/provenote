#!/usr/bin/env python3
"""Validate the selective-port-first upstream maintenance contract."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_UPSTREAM_URL = "https://github.com/lfnovo/open-notebook.git"
TEMP_UPSTREAM_NAMESPACE = "refs/open-notebook/upstream-cache"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ledger-path",
        type=Path,
        default=REPO_ROOT / "config/upstream/selective-port-ledger.json",
    )
    parser.add_argument(
        "--policy-path",
        type=Path,
        default=REPO_ROOT / "docs/development.md",
    )
    parser.add_argument(
        "--sop-path",
        type=Path,
        default=REPO_ROOT / "docs/development.md",
    )
    parser.add_argument(
        "--mapping-path",
        type=Path,
        default=REPO_ROOT / "config/upstream/podcasts-topology-mapping.json",
    )
    parser.add_argument(
        "--now-utc",
        help="Optional override for deterministic tests, format 2026-03-21T00:00:00Z.",
    )
    return parser.parse_args()


def parse_utc(value: str, field_name: str, failures: list[str]) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        failures.append(f"{field_name} must be an ISO-8601 UTC timestamp")
        return None
    if parsed.tzinfo is None:
        failures.append(f"{field_name} must include timezone information")
        return None
    return parsed.astimezone(timezone.utc)


def ensure_non_empty_string(
    value: object, field_name: str, failures: list[str]
) -> str | None:
    if not isinstance(value, str) or not value.strip():
        failures.append(f"{field_name} must be a non-empty string")
        return None
    return value


def validate_refresh_window(
    *,
    object_name: str,
    observed_at: datetime,
    refresh_required_after: datetime,
    max_snapshot_age_hours: int,
    now_utc: datetime,
    failures: list[str],
) -> None:
    expected_refresh = observed_at + timedelta(hours=max_snapshot_age_hours)
    if refresh_required_after != expected_refresh:
        failures.append(
            f"{object_name} refresh_required_after_utc must equal observed_at_utc + max_snapshot_age_hours"
        )
    if now_utc > refresh_required_after:
        failures.append(
            f"{object_name} stale snapshot: refresh_required_after_utc={refresh_required_after.isoformat().replace('+00:00', 'Z')}"
        )


def validate_freshness_policy(
    payload: dict[str, object], failures: list[str]
) -> int | None:
    freshness_policy = payload.get("freshness_policy")
    if not isinstance(freshness_policy, dict):
        failures.append("selective-port ledger missing freshness_policy block")
        return None

    max_snapshot_age_hours = freshness_policy.get("max_snapshot_age_hours")
    if not isinstance(max_snapshot_age_hours, int) or max_snapshot_age_hours <= 0:
        failures.append(
            "selective-port ledger freshness_policy.max_snapshot_age_hours must be a positive integer"
        )
        return None

    required_fields = freshness_policy.get("required_entry_fields")
    if not isinstance(required_fields, list) or not required_fields:
        failures.append(
            "selective-port ledger freshness_policy.required_entry_fields must be a non-empty list"
        )
    for field_name in (
        "refresh_cadence",
        "stale_snapshot_rule",
        "missing_metadata_rule",
    ):
        ensure_non_empty_string(
            freshness_policy.get(field_name),
            f"selective-port ledger freshness_policy.{field_name}",
            failures,
        )
    return max_snapshot_age_hours


def validate_entry_freshness(
    entry: dict[str, object],
    *,
    max_snapshot_age_hours: int,
    now_utc: datetime,
    failures: list[str],
) -> None:
    entry_id = entry.get("id", "<unknown>")
    observed_at_raw = ensure_non_empty_string(
        entry.get("observed_at_utc"),
        f"selective-port ledger entry {entry_id} observed_at_utc",
        failures,
    )
    refresh_after_raw = ensure_non_empty_string(
        entry.get("refresh_required_after_utc"),
        f"selective-port ledger entry {entry_id} refresh_required_after_utc",
        failures,
    )
    snapshot_scope = entry.get("snapshot_scope")
    if not isinstance(snapshot_scope, list) or not snapshot_scope:
        failures.append(
            f"selective-port ledger entry {entry_id} snapshot_scope must be a non-empty list"
        )
    ensure_non_empty_string(
        entry.get("current_truth_boundary"),
        f"selective-port ledger entry {entry_id} current_truth_boundary",
        failures,
    )
    if observed_at_raw is None or refresh_after_raw is None:
        return
    observed_at = parse_utc(
        observed_at_raw,
        f"selective-port ledger entry {entry_id} observed_at_utc",
        failures,
    )
    refresh_after = parse_utc(
        refresh_after_raw,
        f"selective-port ledger entry {entry_id} refresh_required_after_utc",
        failures,
    )
    if observed_at is None or refresh_after is None:
        return
    validate_refresh_window(
        object_name=f"selective-port ledger entry {entry_id}",
        observed_at=observed_at,
        refresh_required_after=refresh_after,
        max_snapshot_age_hours=max_snapshot_age_hours,
        now_utc=now_utc,
        failures=failures,
    )


def validate_mapping_freshness(
    mapping_payload: dict[str, object],
    *,
    now_utc: datetime,
    failures: list[str],
) -> None:
    freshness = mapping_payload.get("freshness")
    if not isinstance(freshness, dict):
        failures.append("podcasts topology mapping missing freshness block")
        return
    max_snapshot_age_hours = freshness.get("max_snapshot_age_hours")
    if not isinstance(max_snapshot_age_hours, int) or max_snapshot_age_hours <= 0:
        failures.append(
            "podcasts topology mapping freshness.max_snapshot_age_hours must be a positive integer"
        )
        return

    observed_at_raw = ensure_non_empty_string(
        freshness.get("observed_at_utc"),
        "podcasts topology mapping freshness.observed_at_utc",
        failures,
    )
    refresh_after_raw = ensure_non_empty_string(
        freshness.get("refresh_required_after_utc"),
        "podcasts topology mapping freshness.refresh_required_after_utc",
        failures,
    )
    snapshot_scope = freshness.get("snapshot_scope")
    if not isinstance(snapshot_scope, list) or not snapshot_scope:
        failures.append(
            "podcasts topology mapping freshness.snapshot_scope must be a non-empty list"
        )
    ensure_non_empty_string(
        freshness.get("current_truth_boundary"),
        "podcasts topology mapping freshness.current_truth_boundary",
        failures,
    )
    if observed_at_raw is None or refresh_after_raw is None:
        return
    observed_at = parse_utc(
        observed_at_raw, "podcasts topology mapping freshness.observed_at_utc", failures
    )
    refresh_after = parse_utc(
        refresh_after_raw,
        "podcasts topology mapping freshness.refresh_required_after_utc",
        failures,
    )
    if observed_at is None or refresh_after is None:
        return
    validate_refresh_window(
        object_name="podcasts topology mapping",
        observed_at=observed_at,
        refresh_required_after=refresh_after,
        max_snapshot_age_hours=max_snapshot_age_hours,
        now_utc=now_utc,
        failures=failures,
    )


def git_stdout(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def git_check(*args: str) -> bool:
    return (
        subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        ).returncode
        == 0
    )


def resolve_upstream_url() -> str:
    return (
        os.environ.get("OPEN_NOTEBOOK_UPSTREAM_URL")
        or os.environ.get("UPSTREAM_REPO_URL")
        or DEFAULT_UPSTREAM_URL
    )


def temp_upstream_ref(branch: str) -> str:
    return f"{TEMP_UPSTREAM_NAMESPACE}/{branch}"


def ensure_available_ref(
    ref_name: str,
    *,
    fetched_refs: set[str],
    failures: list[str],
) -> str | None:
    if not ref_name.startswith("upstream/"):
        remote_ref = f"refs/remotes/{ref_name}"
        if git_check("show-ref", "--verify", "--quiet", remote_ref):
            return ref_name
        failures.append(f"live_git_truth ref not found locally: {ref_name}")
        return None

    branch = ref_name.split("/", 1)[1]
    target_ref = temp_upstream_ref(branch)

    try:
        subprocess.run(
            [
                "git",
                "fetch",
                "--no-tags",
                resolve_upstream_url(),
                f"+refs/heads/{branch}:{target_ref}",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        failures.append(
            f"failed to fetch temporary upstream ref for {ref_name}: {detail or exc.returncode}"
        )
        return None

    fetched_refs.add(target_ref)
    return target_ref


def validate_live_git_truth(
    payload: dict[str, object],
    *,
    max_snapshot_age_hours: int | None,
    now_utc: datetime,
    fetched_refs: set[str],
    failures: list[str],
) -> None:
    live_git_truth = payload.get("live_git_truth")
    if not isinstance(live_git_truth, dict):
        failures.append("selective-port ledger missing live_git_truth block")
        return

    if max_snapshot_age_hours is not None:
        validate_entry_freshness(
            live_git_truth,
            max_snapshot_age_hours=max_snapshot_age_hours,
            now_utc=now_utc,
            failures=failures,
        )

    origin_ref = ensure_non_empty_string(
        live_git_truth.get("origin_ref"),
        "selective-port ledger live_git_truth.origin_ref",
        failures,
    )
    upstream_ref = ensure_non_empty_string(
        live_git_truth.get("upstream_ref"),
        "selective-port ledger live_git_truth.upstream_ref",
        failures,
    )
    if origin_ref is None or upstream_ref is None:
        return

    resolved_origin_ref = ensure_available_ref(
        origin_ref, fetched_refs=fetched_refs, failures=failures
    )
    resolved_upstream_ref = ensure_available_ref(
        upstream_ref, fetched_refs=fetched_refs, failures=failures
    )
    if resolved_origin_ref is None or resolved_upstream_ref is None:
        return

    counts_raw = git_stdout(
        "rev-list",
        "--left-right",
        "--count",
        f"{resolved_origin_ref}...{resolved_upstream_ref}",
    )
    try:
        origin_only_raw, upstream_only_raw = counts_raw.split()
        origin_only = int(origin_only_raw)
        upstream_only = int(upstream_only_raw)
    except ValueError:
        failures.append(
            f"could not parse live rev-list counts for {origin_ref}...{upstream_ref}: {counts_raw!r}"
        )
        return

    recorded_origin_only = live_git_truth.get("origin_only_commits")
    recorded_upstream_only = live_git_truth.get("upstream_only_commits")
    if recorded_origin_only != origin_only:
        failures.append(
            "live_git_truth.origin_only_commits does not match the current refs"
        )
    if recorded_upstream_only != upstream_only:
        failures.append(
            "live_git_truth.upstream_only_commits does not match the current refs"
        )

    has_merge_base = git_check("merge-base", resolved_origin_ref, resolved_upstream_ref)
    recorded_has_merge_base = live_git_truth.get("has_merge_base")
    if recorded_has_merge_base is not has_merge_base:
        failures.append("live_git_truth.has_merge_base does not match the current refs")

    recorded_roots = live_git_truth.get("root_commits")
    if not isinstance(recorded_roots, list) or len(recorded_roots) != 2:
        failures.append(
            "live_git_truth.root_commits must contain exactly two root commit identifiers"
        )
        return

    actual_roots = [
        git_stdout("rev-list", "--max-parents=0", resolved_origin_ref).splitlines()[0][
            :7
        ],
        git_stdout("rev-list", "--max-parents=0", resolved_upstream_ref).splitlines()[
            0
        ][:7],
    ]
    if recorded_roots != actual_roots:
        failures.append("live_git_truth.root_commits does not match the current refs")


def main() -> int:
    args = parse_args()
    failures: list[str] = []
    fetched_refs: set[str] = set()

    ledger_path = args.ledger_path
    policy_path = args.policy_path
    sop_path = args.sop_path
    mapping_path = args.mapping_path

    if not ledger_path.exists():
        failures.append(f"missing {ledger_path}")
    if not policy_path.exists():
        failures.append(f"missing {policy_path}")
    if not sop_path.exists():
        failures.append(f"missing {sop_path}")
    if not mapping_path.exists():
        failures.append(f"missing {mapping_path}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    mapping_payload = json.loads(mapping_path.read_text(encoding="utf-8"))
    now_utc = (
        parse_utc(args.now_utc, "--now-utc", failures)
        if args.now_utc
        else datetime.now(timezone.utc)
    )
    if args.now_utc and now_utc is None:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    if payload.get("policy_mode") != "selective-port-first":
        failures.append(
            "selective-port ledger must declare policy_mode=selective-port-first"
        )
    if payload.get("merge_rebase_default") is not False:
        failures.append("selective-port ledger must declare merge_rebase_default=false")
    strategies = payload.get("allowed_sync_strategies")
    if not isinstance(strategies, list) or "selective-port" not in strategies:
        failures.append("selective-port ledger must allow strategy 'selective-port'")
    max_snapshot_age_hours = validate_freshness_policy(payload, failures)
    try:
        validate_live_git_truth(
            payload,
            max_snapshot_age_hours=max_snapshot_age_hours,
            now_utc=now_utc if now_utc is not None else datetime.now(timezone.utc),
            fetched_refs=fetched_refs,
            failures=failures,
        )
    finally:
        for ref_name in fetched_refs:
            subprocess.run(
                ["git", "update-ref", "-d", ref_name],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        failures.append("selective-port ledger must contain at least one entry")
    else:
        for entry in entries:
            if not isinstance(entry, dict):
                failures.append("selective-port ledger entries must be objects")
                continue
            if not entry.get("id"):
                failures.append("selective-port ledger entry missing id")
            if not entry.get("recommended_strategy"):
                failures.append(
                    "selective-port ledger entry missing recommended_strategy"
                )
            if max_snapshot_age_hours is not None and now_utc is not None:
                validate_entry_freshness(
                    entry,
                    max_snapshot_age_hours=max_snapshot_age_hours,
                    now_utc=now_utc,
                    failures=failures,
                )
            if "clusters" in entry:
                clusters = entry["clusters"]
                if not isinstance(clusters, list) or not clusters:
                    failures.append(
                        f"selective-port ledger entry {entry.get('id', '<unknown>')} must provide a non-empty clusters list once clustered"
                    )
                else:
                    for cluster in clusters:
                        if not isinstance(cluster, dict):
                            failures.append(
                                "selective-port cluster entries must be objects"
                            )
                            continue
                        for field in (
                            "topic",
                            "commits",
                            "surface",
                            "recommended_strategy",
                            "reason",
                        ):
                            if not cluster.get(field):
                                failures.append(
                                    f"selective-port cluster missing field {field!r} in entry {entry.get('id', '<unknown>')}"
                                )

    policy_text = policy_path.read_text(encoding="utf-8")
    sop_text = sop_path.read_text(encoding="utf-8")
    validate_mapping_freshness(
        mapping_payload,
        now_utc=now_utc if now_utc is not None else datetime.now(timezone.utc),
        failures=failures,
    )
    if "selective-port-first" not in policy_text:
        failures.append(
            "upstream-selective-port-policy.md must state selective-port-first"
        )
    if "freshness" not in policy_text.lower():
        failures.append("upstream-selective-port-policy.md must define freshness rules")
    if "selective port" not in sop_text.lower():
        failures.append("upstream-sync-sop.md must mention selective port handling")
    if "observed_at_utc" not in sop_text:
        failures.append(
            "upstream-sync-sop.md must explain how observed_at_utc freshness is used"
        )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(
        "PASS: selective-port-first upstream maintenance contract and snapshot freshness are in place."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
