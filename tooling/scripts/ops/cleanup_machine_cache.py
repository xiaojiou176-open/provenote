#!/usr/bin/env python3
"""Audit or selectively clear repo-specific machine cache surfaces."""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
LOCK_STALE_SECONDS = 3600
HISTORICAL_NAME_TOKENS = (
    "archive",
    "audit",
    "backup",
    "final",
    "history",
    "rewrite",
    "snapshot",
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _human_size(size_bytes: int) -> str:
    suffixes = ("B", "KiB", "MiB", "GiB", "TiB")
    value = float(size_bytes)
    for suffix in suffixes:
        if value < 1024.0 or suffix == suffixes[-1]:
            if suffix == "B":
                return f"{int(value)} {suffix}"
            return f"{value:.1f} {suffix}"
        value /= 1024.0
    return f"{size_bytes} B"


def _resolve_matches(raw_path: str, path_kind: str) -> list[Path]:
    expanded = os.path.expandvars(os.path.expanduser(raw_path))
    if not os.path.isabs(expanded):
        expanded = str((REPO_ROOT / expanded).resolve())
    if path_kind == "glob":
        return sorted(Path(item) for item in glob.glob(expanded, recursive=True))
    return [Path(expanded)]


def _du_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    import subprocess

    result = subprocess.run(
        ["du", "-sk", str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return 0
    return int(result.stdout.split()[0]) * 1024


def _last_used_epoch(path: Path) -> float | None:
    try:
        stats = path.stat()
    except FileNotFoundError:
        return None
    return max(stats.st_atime, stats.st_mtime)


def _mtime_iso(path: Path) -> str | None:
    try:
        return dt.datetime.fromtimestamp(
            path.stat().st_mtime, tz=dt.timezone.utc
        ).isoformat()
    except FileNotFoundError:
        return None


def _age_days(path: Path) -> int | None:
    try:
        mtime = path.stat().st_mtime
    except FileNotFoundError:
        return None
    delta = dt.datetime.now(tz=dt.timezone.utc) - dt.datetime.fromtimestamp(
        mtime, tz=dt.timezone.utc
    )
    return max(0, int(delta.total_seconds() // 86400))


def _age_days_from_epoch(epoch_seconds: float | None) -> int | None:
    if epoch_seconds is None:
        return None
    delta = dt.datetime.now(tz=dt.timezone.utc) - dt.datetime.fromtimestamp(
        epoch_seconds, tz=dt.timezone.utc
    )
    return max(0, int(delta.total_seconds() // 86400))


def _sha256_hash_for_paths(paths: list[Path]) -> str | None:
    digest = hashlib.sha256()
    for path in paths:
        if not path.exists():
            return None
        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        digest.update(f"{file_hash}  {relative_path}\n".encode("utf-8"))
    return digest.hexdigest()


def _current_frontend_lock_hash() -> str | None:
    return _sha256_hash_for_paths(
        [
            REPO_ROOT / "apps/web/package-lock.json",
            REPO_ROOT / "apps/web/package.json",
            REPO_ROOT / "tooling/scripts/ci/run_in_consistent_container.sh",
        ]
    )


def _candidate_status_for_named_cache(path: Path) -> str:
    lowered = path.name.lower()
    if any(token in lowered for token in HISTORICAL_NAME_TOKENS):
        return "historical-candidate"
    return "unresolved-candidate"


def _machine_cache_root(indexed: dict[str, dict[str, Any]]) -> Path:
    for surface_name in (
        "machine-uv-cache",
        "machine-playwright-cache",
        "machine-ci-host",
    ):
        surface = indexed.get(surface_name)
        if surface is None:
            continue
        matches = _resolve_matches(
            str(surface["path"]), str(surface.get("path_kind", "path"))
        )
        if not matches:
            continue
        path = matches[0]
        if surface_name == "machine-ci-host":
            return path.parent
        if surface_name == "machine-playwright-cache":
            return path.parents[1]
        return path.parents[1]
    return Path.home() / ".cache" / "provenote"


def _surface_rows(indexed: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in indexed.values():
        if item.get("scope") != "repo_external":
            continue
        if item.get("ownership") != "exclusive":
            continue
        if item.get("default_action") not in {"safe_clear", "cautious_clear"}:
            continue
        if item.get("inventory_class") != "repo_managed_candidate":
            continue
        if str(item.get("path_kind", "path")) == "glob":
            continue
        for path in _resolve_matches(
            str(item["path"]), str(item.get("path_kind", "path"))
        ):
            if not path.exists():
                continue
            size_bytes = _du_bytes(path)
            rows.append(
                {
                    "name": str(item["name"]),
                    "kind": "registered-surface",
                    "path": str(path),
                    "size_bytes": size_bytes,
                    "size_human": _human_size(size_bytes),
                    "default_action": str(item["default_action"]),
                    "cleanup_eligible": False,
                    "cleanup_reasons": [],
                    "ttl_days": item.get("ttl_days"),
                    "max_bytes": item.get("max_bytes"),
                    "last_modified": _mtime_iso(path),
                    "age_days": _age_days(path),
                    "notes": str(item.get("notes", "")),
                }
            )
    rows.sort(key=lambda item: (-item["size_bytes"], item["name"]))
    return rows


def _surface_entry_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    if path.is_file():
        last_used_epoch = _last_used_epoch(path)
        size_bytes = _du_bytes(path)
        return [
            {
                "path": str(path),
                "size_bytes": size_bytes,
                "size_human": _human_size(size_bytes),
                "age_days": _age_days_from_epoch(last_used_epoch),
                "last_used_epoch": last_used_epoch,
                "selected_reasons": [],
            }
        ]

    entries: list[dict[str, Any]] = []
    for child in path.iterdir():
        last_used_epoch = _last_used_epoch(child)
        size_bytes = _du_bytes(child)
        entries.append(
            {
                "path": str(child),
                "size_bytes": size_bytes,
                "size_human": _human_size(size_bytes),
                "age_days": _age_days_from_epoch(last_used_epoch),
                "last_used_epoch": last_used_epoch,
                "selected_reasons": [],
            }
        )
    entries.sort(
        key=lambda item: (
            float("inf")
            if item["last_used_epoch"] is None
            else item["last_used_epoch"],
            item["path"],
        )
    )
    return entries


def _select_entry(row: dict[str, Any], entry: dict[str, Any], reason: str) -> None:
    selected = row.setdefault("_selected_entries", {})
    selected_entry = selected.get(entry["path"])
    if selected_entry is None:
        selected_entry = {**entry, "selected_reasons": []}
        selected[entry["path"]] = selected_entry
    if reason not in selected_entry["selected_reasons"]:
        selected_entry["selected_reasons"].append(reason)


def _select_registered_surface_rows(
    rows: list[dict[str, Any]], root_cap_bytes: int | None
) -> list[dict[str, Any]]:
    for row in rows:
        ttl_days = row.get("ttl_days")
        max_bytes = row.get("max_bytes")
        entries = _surface_entry_rows(Path(row["path"]))
        row["_entries"] = entries

        if isinstance(ttl_days, int) and ttl_days >= 0:
            for entry in entries:
                age_days = entry.get("age_days")
                if age_days is not None and age_days >= ttl_days:
                    _select_entry(row, entry, "ttl-expired")

        if isinstance(max_bytes, int) and max_bytes >= 0:
            retained_bytes = sum(
                int(entry["size_bytes"])
                for entry in entries
                if entry["path"] not in row.get("_selected_entries", {})
            )
            for entry in entries:
                if retained_bytes <= max_bytes:
                    break
                if entry["path"] in row.get("_selected_entries", {}):
                    continue
                _select_entry(row, entry, "surface-cap-exceeded")
                retained_bytes -= int(entry["size_bytes"])

        selected_entries = list(row.get("_selected_entries", {}).values())
        row["selected_entries"] = selected_entries
        row["cleanup_reasons"] = sorted(
            {
                reason
                for entry in selected_entries
                for reason in entry.get("selected_reasons", [])
            }
        )
        row["cleanup_eligible"] = bool(selected_entries)

    if root_cap_bytes is None or root_cap_bytes <= 0:
        for row in rows:
            row.pop("_entries", None)
            row.pop("_selected_entries", None)
        return rows

    total_bytes = 0
    for row in rows:
        total_bytes += sum(
            int(entry["size_bytes"])
            for entry in row.get("_entries", [])
            if entry["path"] not in row.get("_selected_entries", {})
        )
    if total_bytes <= root_cap_bytes:
        for row in rows:
            row.pop("_entries", None)
            row.pop("_selected_entries", None)
        return rows

    projected_bytes = total_bytes
    candidate_entries: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for row in rows:
        selected_paths = set(row.get("_selected_entries", {}).keys())
        for entry in row.get("_entries", []):
            if entry["path"] in selected_paths:
                continue
            candidate_entries.append((row, entry))

    candidate_entries.sort(
        key=lambda item: (
            float("inf")
            if item[1]["last_used_epoch"] is None
            else item[1]["last_used_epoch"],
            item[1]["size_bytes"],
            item[1]["path"],
        )
    )

    for row, entry in candidate_entries:
        if projected_bytes <= root_cap_bytes:
            break
        _select_entry(row, entry, "root-cap-exceeded")
        projected_bytes -= int(entry["size_bytes"])

    for row in rows:
        selected_entries = list(row.get("_selected_entries", {}).values())
        row["selected_entries"] = selected_entries
        row["cleanup_reasons"] = sorted(
            {
                reason
                for entry in selected_entries
                for reason in entry.get("selected_reasons", [])
            }
        )
        row["cleanup_eligible"] = bool(selected_entries)
        row.pop("_entries", None)
        row.pop("_selected_entries", None)

    return rows


def _historical_candidate_rows(
    indexed: dict[str, dict[str, Any]], historical_max_age_days: int
) -> list[dict[str, Any]]:
    surface = indexed.get("historical-provenote-cache-candidates")
    if surface is None:
        return []
    rows: list[dict[str, Any]] = []
    for path in _resolve_matches(
        str(surface["path"]), str(surface.get("path_kind", "glob"))
    ):
        if not path.exists():
            continue
        status = _candidate_status_for_named_cache(path)
        age_days = _age_days(path)
        size_bytes = _du_bytes(path)
        rows.append(
            {
                "name": f"named-candidate:{path.name}",
                "kind": "historical-candidate",
                "path": str(path),
                "size_bytes": size_bytes,
                "size_human": _human_size(size_bytes),
                "candidate_status": status,
                "cleanup_eligible": status == "historical-candidate"
                and age_days is not None
                and age_days >= historical_max_age_days,
                "last_modified": _mtime_iso(path),
                "age_days": age_days,
                "notes": "Named cache candidate outside the canonical machine-cache root. Explicit opt-in is required before cleanup.",
            }
        )
    rows.sort(key=lambda item: (-item["size_bytes"], item["name"]))
    return rows


def _bootstrap_snapshot_rows(
    indexed: dict[str, dict[str, Any]],
    bootstrap_stale_max_age_days: int,
    bootstrap_keep_generations: int,
) -> list[dict[str, Any]]:
    surface = indexed.get("machine-ci-host-bootstrap-frontend-cache-root")
    if surface is None:
        return []
    matches = _resolve_matches(
        str(surface["path"]), str(surface.get("path_kind", "path"))
    )
    if not matches:
        return []
    root = matches[0]
    if not root.exists() or not root.is_dir():
        return []

    current_hash = _current_frontend_lock_hash()
    snapshot_dirs = sorted(
        (
            candidate
            for candidate in root.iterdir()
            if candidate.is_dir() and candidate.name.startswith(".") is False
        ),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )

    rows: list[dict[str, Any]] = []
    stale_rank = 0
    for snapshot_dir in snapshot_dirs:
        is_active = current_hash is not None and snapshot_dir.name == current_hash
        if not is_active:
            stale_rank += 1
        lock_dir = snapshot_dir.parent / f".{snapshot_dir.name}.lock"
        age_days = _age_days(snapshot_dir)
        cleanup_eligible = (
            is_active is False
            and lock_dir.exists() is False
            and age_days is not None
            and age_days >= bootstrap_stale_max_age_days
            and stale_rank > bootstrap_keep_generations
        )
        size_bytes = _du_bytes(snapshot_dir)
        rows.append(
            {
                "name": f"bootstrap-snapshot:{snapshot_dir.name}",
                "kind": "bootstrap-snapshot",
                "path": str(snapshot_dir),
                "size_bytes": size_bytes,
                "size_human": _human_size(size_bytes),
                "candidate_status": (
                    "active-bootstrap-cache"
                    if is_active
                    else "stale-bootstrap-candidate"
                ),
                "cleanup_eligible": cleanup_eligible,
                "last_modified": _mtime_iso(snapshot_dir),
                "age_days": age_days,
                "current_frontend_lock_hash": current_hash,
                "lock_present": lock_dir.exists(),
                "stale_generation_rank": None if is_active else stale_rank,
                "notes": "Keep the active lock hash. Only stale snapshots may become cleanup candidates, and only after age/generation/lock checks pass.",
            }
        )
    rows.sort(
        key=lambda item: (
            0 if item["candidate_status"] == "active-bootstrap-cache" else 1,
            -item["size_bytes"],
            item["name"],
        )
    )
    return rows


def _render_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    lines = [
        " | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers)),
        "-+-".join("-" * widths[idx] for idx in range(len(headers))),
    ]
    for row in rows:
        lines.append(
            " | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row))
        )
    return "\n".join(lines)


def _wipe_directory_contents(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def _remove_tree(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
        return
    if path.exists():
        path.unlink()


@contextmanager
def _lock_machine_cache(machine_cache_root: Path, mode: str):
    if mode != "apply":
        yield
        return
    lock_dir = machine_cache_root / "cleanup_machine_cache.lock"
    lock_dir.parent.mkdir(parents=True, exist_ok=True)
    if lock_dir.exists():
        age_seconds = (
            dt.datetime.now(tz=dt.timezone.utc)
            - dt.datetime.fromtimestamp(lock_dir.stat().st_mtime, tz=dt.timezone.utc)
        ).total_seconds()
        if age_seconds > LOCK_STALE_SECONDS:
            shutil.rmtree(lock_dir, ignore_errors=True)
    try:
        lock_dir.mkdir()
    except FileExistsError as exc:
        raise SystemExit(
            f"skip: another machine-cache cleanup process is active ({lock_dir})"
        ) from exc
    try:
        yield
    finally:
        shutil.rmtree(lock_dir, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        default="config/runtime/space-surfaces.json",
        help="Path to space surfaces registry JSON",
    )
    parser.add_argument(
        "--mode",
        choices=("audit-only", "dry-run", "apply"),
        default="audit-only",
        help="Whether to only audit, print deletions, or apply them",
    )
    parser.add_argument(
        "--format",
        choices=("human", "json"),
        default="human",
        help="Output format",
    )
    parser.add_argument(
        "--include-historical-candidates",
        action="store_true",
        help="Allow historical named cache candidates to become cleanup candidates when their age threshold is met",
    )
    parser.add_argument(
        "--include-stale-bootstrap-snapshots",
        action="store_true",
        help="Allow stale bootstrap node_modules snapshots to become cleanup candidates when their age/generation thresholds are met",
    )
    parser.add_argument(
        "--historical-max-age-days",
        type=int,
        default=30,
        help="Minimum age for historical named cache candidates before they can become cleanup candidates (default: 30)",
    )
    parser.add_argument(
        "--bootstrap-stale-max-age-days",
        type=int,
        default=14,
        help="Minimum age for stale bootstrap snapshots before they can become cleanup candidates (default: 14)",
    )
    parser.add_argument(
        "--bootstrap-keep-generations",
        type=int,
        default=2,
        help="Number of newest stale bootstrap generations to keep even when age thresholds are met (default: 2)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    registry_path = (REPO_ROOT / args.registry).resolve()
    registry = _load_json(registry_path)
    surfaces = registry.get("surfaces", [])
    if not isinstance(surfaces, list) or not surfaces:
        print(
            "FAIL: space surfaces registry must declare a non-empty surfaces list",
            file=sys.stderr,
        )
        return 1

    indexed = {
        str(item["name"]): item
        for item in surfaces
        if isinstance(item, dict) and str(item.get("name", "")).strip()
    }
    machine_cache_policy = registry.get("machine_cache_policy", {})
    if not isinstance(machine_cache_policy, dict):
        machine_cache_policy = {}

    machine_cache_root = _machine_cache_root(indexed)
    root_cap_bytes = machine_cache_policy.get("clearable_root_cap_bytes")
    if not isinstance(root_cap_bytes, int):
        root_cap_bytes = None
    surface_rows = _select_registered_surface_rows(
        _surface_rows(indexed), root_cap_bytes
    )
    historical_max_age_days = args.historical_max_age_days
    if isinstance(machine_cache_policy.get("historical_max_age_days"), int):
        historical_max_age_days = int(machine_cache_policy["historical_max_age_days"])
    historical_rows = _historical_candidate_rows(indexed, historical_max_age_days)
    bootstrap_stale_max_age_days = args.bootstrap_stale_max_age_days
    if isinstance(machine_cache_policy.get("bootstrap_stale_max_age_days"), int):
        bootstrap_stale_max_age_days = int(
            machine_cache_policy["bootstrap_stale_max_age_days"]
        )
    bootstrap_keep_generations = args.bootstrap_keep_generations
    if isinstance(machine_cache_policy.get("bootstrap_keep_generations"), int):
        bootstrap_keep_generations = int(
            machine_cache_policy["bootstrap_keep_generations"]
        )
    bootstrap_rows = _bootstrap_snapshot_rows(
        indexed,
        bootstrap_stale_max_age_days,
        bootstrap_keep_generations,
    )

    planned_actions: list[dict[str, Any]] = []
    for row in surface_rows:
        planned_actions.append(
            {
                **row,
                "action_type": "prune-entries",
                "selected": args.mode in {"dry-run", "apply"}
                and row["cleanup_eligible"],
            }
        )
    for row in historical_rows:
        planned_actions.append(
            {
                **row,
                "action_type": "remove-tree",
                "selected": args.include_historical_candidates
                and args.mode in {"dry-run", "apply"}
                and row["cleanup_eligible"],
            }
        )
    for row in bootstrap_rows:
        planned_actions.append(
            {
                **row,
                "action_type": "remove-tree",
                "selected": args.include_stale_bootstrap_snapshots
                and args.mode in {"dry-run", "apply"}
                and row["cleanup_eligible"],
            }
        )

    applied_actions: list[dict[str, Any]] = []
    with _lock_machine_cache(machine_cache_root, args.mode):
        if args.mode == "apply":
            for row in planned_actions:
                if not row["selected"]:
                    continue
                target = Path(row["path"])
                if row["action_type"] == "prune-entries":
                    for entry in row.get("selected_entries", []):
                        entry_path = Path(entry["path"])
                        _remove_tree(entry_path)
                        applied_actions.append(
                            {
                                "name": row["name"],
                                "path": entry["path"],
                                "action_type": row["action_type"],
                                "size_bytes_before": entry["size_bytes"],
                                "selected_reasons": entry.get("selected_reasons", []),
                            }
                        )
                else:
                    _remove_tree(target)
                    applied_actions.append(
                        {
                            "name": row["name"],
                            "path": row["path"],
                            "action_type": row["action_type"],
                            "size_bytes_before": row["size_bytes"],
                        }
                    )

    payload = {
        "generated_at": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "registry": str(registry_path),
        "mode": args.mode,
        "machine_cache_root": str(machine_cache_root),
        "summary": {
            "registered_clearable_external_bytes": sum(
                item["size_bytes"] for item in surface_rows
            ),
            "clearable_root_cap_bytes": root_cap_bytes,
            "historical_candidate_bytes": sum(
                item["size_bytes"] for item in historical_rows
            ),
            "bootstrap_snapshot_bytes": sum(
                item["size_bytes"] for item in bootstrap_rows
            ),
            "selected_action_count": sum(
                1 for item in planned_actions if item["selected"]
            ),
            "applied_action_count": len(applied_actions),
        },
        "registered_clearable_surfaces": surface_rows,
        "historical_candidates": historical_rows,
        "bootstrap_snapshots": bootstrap_rows,
        "planned_actions": planned_actions,
        "applied_actions": applied_actions,
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print("# Machine Cache Cleanup")
    print()
    print(f"Mode: {args.mode}")
    print(f"Machine cache root: {machine_cache_root}")
    print()
    print(
        "This lane only manages repo-specific machine-cache surfaces. Shared layers such as ~/.npm, system Playwright, and Docker Desktop stay advisory-only."
    )
    print()

    if surface_rows:
        print("## Registered Clearable External Surfaces")
        rows = [
            [
                item["name"],
                item["size_human"],
                item["default_action"],
                ",".join(item.get("cleanup_reasons", [])) or "none",
                str(item["path"]),
            ]
            for item in surface_rows
        ]
        print(
            _render_table(
                ["name", "size", "default_action", "cleanup_reasons", "path"], rows
            )
        )
        print()

    if historical_rows:
        print("## Historical Named Candidates")
        rows = [
            [
                item["name"],
                item["size_human"],
                str(item["candidate_status"]),
                "yes" if item["cleanup_eligible"] else "no",
                str(item.get("age_days", "")),
                str(item["path"]),
            ]
            for item in historical_rows
        ]
        print(
            _render_table(
                ["name", "size", "status", "cleanup_eligible", "age_days", "path"],
                rows,
            )
        )
        print()

    if bootstrap_rows:
        print("## Bootstrap Snapshots")
        rows = [
            [
                item["name"],
                item["size_human"],
                str(item["candidate_status"]),
                "yes" if item["cleanup_eligible"] else "no",
                str(item.get("age_days", "")),
                "yes" if item.get("lock_present") else "no",
                str(item["path"]),
            ]
            for item in bootstrap_rows
        ]
        print(
            _render_table(
                [
                    "name",
                    "size",
                    "status",
                    "cleanup_eligible",
                    "age_days",
                    "lock_present",
                    "path",
                ],
                rows,
            )
        )
        print()

    print("## Planned Actions")
    if not any(item["selected"] for item in planned_actions):
        print("No cleanup actions selected for this run.")
    else:
        rows = [
            [
                item["name"],
                item["action_type"],
                item["size_human"],
                str(item["path"]),
            ]
            for item in planned_actions
            if item["selected"]
        ]
        print(_render_table(["name", "action", "size", "path"], rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
