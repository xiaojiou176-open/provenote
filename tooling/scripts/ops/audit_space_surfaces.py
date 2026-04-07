#!/usr/bin/env python3
"""Audit repo-local and repo-related disk space surfaces without mutating tracked state."""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

SECTIONS = (
    "Repo Internal",
    "Repo External",
    "Shared Layers: advisory only",
    "Historical Candidates / unresolved ownership",
)

DERIVED_SECTION = "Derived Candidates"
DEFAULT_STALE_BOOTSTRAP_MAX_AGE_DAYS = 14
DEFAULT_STALE_BOOTSTRAP_KEEP_GENERATIONS = 2
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


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def _resolve_matches(raw_path: str, path_kind: str) -> list[Path]:
    expanded = os.path.expandvars(os.path.expanduser(raw_path))
    if not os.path.isabs(expanded):
        expanded = str((REPO_ROOT / expanded).resolve())
    if path_kind == "glob":
        return sorted(Path(item) for item in glob.glob(expanded, recursive=True))
    path = Path(expanded)
    return [path]


def _path_is_repo_internal(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
        return True
    except FileNotFoundError:
        try:
            path.absolute().relative_to(REPO_ROOT.resolve())
            return True
        except ValueError:
            return False
    except ValueError:
        return False


def _du_bytes(path: Path) -> int:
    result = _run(["du", "-sk", str(path)])
    if result.returncode != 0 or not result.stdout.strip():
        return 0
    size_kb = int(result.stdout.split()[0])
    return size_kb * 1024


def _latest_mtime(paths: list[Path]) -> str | None:
    mtimes: list[float] = []
    for path in paths:
        try:
            mtimes.append(path.stat().st_mtime)
        except FileNotFoundError:
            continue
    if not mtimes:
        return None
    return dt.datetime.fromtimestamp(max(mtimes), tz=dt.timezone.utc).isoformat()


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


def _git_state_for_path(path: Path) -> str:
    if path.name == ".git" or ".git/" in path.as_posix():
        return "git_metadata"
    try:
        rel = path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except Exception:
        return "not_applicable"

    if not rel:
        return "not_applicable"
    if _run(["git", "check-ignore", "-q", "--", rel], cwd=REPO_ROOT).returncode == 0:
        return "ignored"
    if (
        _run(
            ["git", "ls-files", "--error-unmatch", "--", rel], cwd=REPO_ROOT
        ).returncode
        == 0
    ):
        return "tracked"
    descendants = _run(["git", "ls-files", "--", rel], cwd=REPO_ROOT)
    if descendants.returncode == 0 and descendants.stdout.strip():
        return "tracked_descendants"
    if path.exists():
        return "untracked"
    return "missing"


def _git_state(paths: list[Path], scope: str) -> str:
    if scope != "repo_internal":
        return "not_applicable"
    states = {
        _git_state_for_path(path) for path in paths if _path_is_repo_internal(path)
    }
    if not states:
        return "not_applicable"
    if len(states) == 1:
        return next(iter(states))
    return "mixed"


def _ownership_confirmed(value: str) -> bool:
    return value not in {"unknown", "historical_candidate"}


def _rebuildability_confirmed(value: str) -> bool:
    return value != "unknown"


def _clear_allowed(action: str) -> bool:
    return action in {"safe_clear", "cautious_clear"}


def _section_for_surface(surface: dict[str, Any]) -> str:
    if surface["retention_class"] == "shared_layer":
        return "Shared Layers: advisory only"
    if surface["ownership"] == "historical_candidate":
        return "Historical Candidates / unresolved ownership"
    if surface["scope"] == "repo_internal":
        return "Repo Internal"
    return "Repo External"


def _docker_attribution_status(surface: dict[str, Any], docker_available: bool) -> str:
    if not surface.get("requires_daemon_attribution"):
        return "n/a"
    if not docker_available:
        return "unresolved"
    if surface.get("attribution_verification") == "complete":
        return "resolved"
    return "reachable_but_unattributed"


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _distinct_section_bytes(report_surfaces: list[dict[str, Any]], section: str) -> int:
    candidates: list[tuple[Path, int]] = []
    for item in report_surfaces:
        if item["section"] != section:
            continue
        if item.get("path_kind", "path") == "glob":
            continue
        if not item.get("exists"):
            continue
        for raw_path in item.get("existing_matches", []):
            path = Path(raw_path)
            candidates.append((path, _du_bytes(path)))

    candidates.sort(key=lambda pair: (len(pair[0].parts), str(pair[0])))
    counted_roots: list[Path] = []
    total = 0
    for path, size_bytes in candidates:
        if any(_is_relative_to(path, ancestor) for ancestor in counted_roots):
            continue
        counted_roots.append(path)
        total += size_bytes
    return total


def _global_docker_attribution_status(
    report_surfaces: list[dict[str, Any]], docker_available: bool
) -> str:
    if not any(item.get("requires_daemon_attribution") for item in report_surfaces):
        return "n/a"
    if not docker_available:
        return "unresolved"
    if any(item["attribution_status"] == "resolved" for item in report_surfaces):
        return "resolved"
    return "reachable_but_unattributed"


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


def _classify_named_candidate(path: Path, confirmed_paths: set[Path]) -> str:
    try:
        resolved = path.resolve()
    except FileNotFoundError:
        resolved = path.absolute()
    if resolved in confirmed_paths:
        return "active-named-candidate"
    lowered = path.name.lower()
    if any(token in lowered for token in HISTORICAL_NAME_TOKENS):
        return "historical-candidate"
    return "unresolved-candidate"


def _build_derived_candidates(
    report_surfaces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    derived: list[dict[str, Any]] = []
    confirmed_paths: set[Path] = set()
    for item in report_surfaces:
        if not item.get("ownership_confirmed"):
            continue
        if item.get("path_kind", "path") == "glob":
            continue
        for raw_path in item.get("existing_matches", []):
            try:
                confirmed_paths.add(Path(raw_path).resolve())
            except FileNotFoundError:
                confirmed_paths.add(Path(raw_path).absolute())

    historical_surface = next(
        (
            item
            for item in report_surfaces
            if item.get("name") == "historical-provenote-cache-candidates"
        ),
        None,
    )
    if historical_surface is not None:
        for raw_path in historical_surface.get("existing_matches", []):
            path = Path(raw_path)
            candidate_status = _classify_named_candidate(path, confirmed_paths)
            derived.append(
                {
                    "name": f"named-candidate:{path.name}",
                    "path": str(path),
                    "size_bytes": _du_bytes(path),
                    "size_human": _human_size(_du_bytes(path)),
                    "candidate_status": candidate_status,
                    "cleanup_eligible": False,
                    "age_days": _age_days(path),
                    "last_modified": _mtime_iso(path),
                    "section": DERIVED_SECTION,
                    "source_surface": historical_surface["name"],
                    "notes": "Named cache candidate outside the canonical machine-cache root. Classified for reporting only until an explicit cleanup decision is made.",
                }
            )

    bootstrap_surface = next(
        (
            item
            for item in report_surfaces
            if item.get("name") == "machine-ci-host-bootstrap-frontend-cache-root"
        ),
        None,
    )
    if bootstrap_surface is not None and bootstrap_surface.get("existing_matches"):
        bootstrap_root = Path(bootstrap_surface["existing_matches"][0])
        current_hash = _current_frontend_lock_hash()
        snapshot_dirs = sorted(
            (
                path
                for path in bootstrap_root.iterdir()
                if path.is_dir() and path.name.startswith(".") is False
            ),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
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
                and age_days >= DEFAULT_STALE_BOOTSTRAP_MAX_AGE_DAYS
                and stale_rank > DEFAULT_STALE_BOOTSTRAP_KEEP_GENERATIONS
            )
            derived.append(
                {
                    "name": f"bootstrap-snapshot:{snapshot_dir.name}",
                    "path": str(snapshot_dir),
                    "size_bytes": _du_bytes(snapshot_dir),
                    "size_human": _human_size(_du_bytes(snapshot_dir)),
                    "candidate_status": (
                        "active-bootstrap-cache"
                        if is_active
                        else "stale-bootstrap-candidate"
                    ),
                    "cleanup_eligible": cleanup_eligible,
                    "age_days": age_days,
                    "last_modified": _mtime_iso(snapshot_dir),
                    "section": DERIVED_SECTION,
                    "source_surface": bootstrap_surface["name"],
                    "current_frontend_lock_hash": current_hash,
                    "lock_present": lock_dir.exists(),
                    "stale_generation_rank": None if is_active else stale_rank,
                    "notes": "Frontend bootstrap snapshot keyed by the consistent-container lock hash. Keep the active hash; only stale snapshots may become cleanup candidates.",
                }
            )

    derived.sort(
        key=lambda item: (
            0 if item["candidate_status"] == "active-bootstrap-cache" else 1,
            -item["size_bytes"],
            item["name"],
        )
    )
    return derived


def _render_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    lines = []
    lines.append(
        " | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers))
    )
    lines.append("-+-".join("-" * widths[idx] for idx in range(len(headers))))
    for row in rows:
        lines.append(
            " | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row))
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        default="config/runtime/space-surfaces.json",
        help="Path to space surfaces registry JSON",
    )
    parser.add_argument(
        "--format",
        choices=("human", "json"),
        default="human",
        help="Output format",
    )
    parser.add_argument(
        "--json-out",
        help="Optional path to write JSON report while still printing human output",
    )
    parser.add_argument(
        "--action-filter",
        help="Comma-separated default_action allowlist for reporting",
    )
    parser.add_argument(
        "--cleanup-owner",
        help="Only include surfaces whose cleanup_owner matches this value",
    )
    parser.add_argument(
        "--inventory-class",
        help="Only include surfaces whose inventory_class matches this value",
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

    action_filter = (
        {item.strip() for item in args.action_filter.split(",") if item.strip()}
        if args.action_filter
        else None
    )

    docker_info = _run(["docker", "info"])
    docker_available = docker_info.returncode == 0

    report_surfaces: list[dict[str, Any]] = []
    for item in surfaces:
        if not isinstance(item, dict):
            continue
        if args.cleanup_owner and item.get("cleanup_owner") != args.cleanup_owner:
            continue
        if args.inventory_class and item.get("inventory_class") != args.inventory_class:
            continue
        if action_filter and item.get("default_action") not in action_filter:
            continue

        path_kind = str(item.get("path_kind", "path")).strip() or "path"
        matches = _resolve_matches(str(item["path"]), path_kind)
        existing_matches = [path for path in matches if path.exists()]
        size_bytes = sum(_du_bytes(path) for path in existing_matches)
        git_state = _git_state(existing_matches or matches, str(item["scope"]))

        surface_report = dict(item)
        surface_report["resolved_matches"] = [str(path) for path in matches]
        surface_report["existing_matches"] = [str(path) for path in existing_matches]
        surface_report["size_bytes"] = size_bytes
        surface_report["size_human"] = _human_size(size_bytes)
        surface_report["exists"] = bool(existing_matches)
        surface_report["ownership_confirmed"] = _ownership_confirmed(
            str(item["ownership"])
        )
        surface_report["rebuildability_confirmed"] = _rebuildability_confirmed(
            str(item["rebuildability"])
        )
        surface_report["clear_allowed"] = _clear_allowed(str(item["default_action"]))
        surface_report["git_state"] = git_state
        surface_report["last_modified"] = _latest_mtime(existing_matches)
        surface_report["section"] = _section_for_surface(item)
        surface_report["attribution_status"] = _docker_attribution_status(
            item, docker_available
        )
        report_surfaces.append(surface_report)

    report_surfaces.sort(
        key=lambda item: (
            SECTIONS.index(item["section"]),
            -item["size_bytes"],
            item["name"],
        )
    )

    derived_candidates = _build_derived_candidates(report_surfaces)
    historical_candidate_bytes_reported = sum(
        item["size_bytes"]
        for item in derived_candidates
        if item["source_surface"] == "historical-provenote-cache-candidates"
    )

    summary: dict[str, Any] = {
        "repo_internal_bytes_distinct": _distinct_section_bytes(
            report_surfaces, "Repo Internal"
        ),
        "repo_external_bytes_distinct": _distinct_section_bytes(
            report_surfaces, "Repo External"
        ),
        "shared_layer_bytes_distinct": _distinct_section_bytes(
            report_surfaces, "Shared Layers: advisory only"
        ),
        "historical_candidate_bytes_distinct": _distinct_section_bytes(
            report_surfaces, "Historical Candidates / unresolved ownership"
        ),
        "counts_by_action": {},
        "docker_daemon_available": docker_available,
        "docker_attribution_status": _global_docker_attribution_status(
            report_surfaces, docker_available
        ),
        "distinct_summary_note": "Distinct summary excludes glob surfaces and avoids double-counting parent/child paths within the same section.",
        "strict_confirmed_bytes_distinct": 0,
        "historical_candidate_bytes_reported": historical_candidate_bytes_reported,
        "repo_related_with_historical_reported_bytes": 0,
    }
    for item in report_surfaces:
        summary["counts_by_action"].setdefault(item["default_action"], 0)
        summary["counts_by_action"][item["default_action"]] += 1
    summary["strict_confirmed_bytes_distinct"] = (
        summary["repo_internal_bytes_distinct"]
        + summary["repo_external_bytes_distinct"]
    )
    summary["repo_related_with_historical_reported_bytes"] = (
        summary["strict_confirmed_bytes_distinct"]
        + summary["historical_candidate_bytes_reported"]
    )

    payload: dict[str, Any] = {
        "generated_at": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "registry": str(registry_path),
        "summary": summary,
        "surfaces": report_surfaces,
        "derived_candidates": derived_candidates,
    }

    if args.json_out:
        json_target = Path(args.json_out)
        if str(json_target) == "-":
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            json_target.write_text(
                json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
            )

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    try:
        display_registry = registry_path.relative_to(REPO_ROOT)
    except ValueError:
        display_registry = registry_path

    print("# Space Surface Audit")
    print()
    print(f"Registry: {display_registry}")
    print(
        "Status columns: exists / ownership_confirmed / rebuildability_confirmed / clear_allowed"
    )
    print(f"Docker attribution: {summary['docker_attribution_status']}")
    print()
    print("Distinct Summary")
    print(
        "Glob surfaces are excluded from the distinct summary to avoid parent/child inflation."
    )
    print()
    summary_rows = [
        ["Repo Internal", _human_size(summary["repo_internal_bytes_distinct"])],
        ["Repo External", _human_size(summary["repo_external_bytes_distinct"])],
        [
            "Strict Confirmed Total",
            _human_size(summary["strict_confirmed_bytes_distinct"]),
        ],
        ["Shared Layers", _human_size(summary["shared_layer_bytes_distinct"])],
        [
            "Historical Candidates (distinct)",
            _human_size(summary["historical_candidate_bytes_distinct"]),
        ],
        [
            "Historical Candidates (reported)",
            _human_size(summary["historical_candidate_bytes_reported"]),
        ],
        [
            "Repo Related + Historical",
            _human_size(summary["repo_related_with_historical_reported_bytes"]),
        ],
    ]
    print(_render_table(["Section", "Observed Size"], summary_rows))
    print()
    print(
        "Historical candidate rows are also reported separately below so named cache candidates do not disappear behind the glob-excluded distinct-summary rule."
    )
    for section in SECTIONS:
        section_rows = [item for item in report_surfaces if item["section"] == section]
        if not section_rows:
            continue
        print()
        print(f"## {section}")
        rows = [
            [
                item["name"],
                item["size_human"],
                "yes" if item["exists"] else "no",
                "yes" if item["ownership_confirmed"] else "no",
                "yes" if item["rebuildability_confirmed"] else "no",
                "yes" if item["clear_allowed"] else "no",
                str(item["default_action"]),
                str(item.get("inventory_class", "")),
                str(item["git_state"]),
                str(item["attribution_status"]),
                str(item["path"]),
            ]
            for item in section_rows
        ]
        print(
            _render_table(
                [
                    "name",
                    "size",
                    "exists",
                    "ownership_confirmed",
                    "rebuildability_confirmed",
                    "clear_allowed",
                    "default_action",
                    "inventory_class",
                    "git_state",
                    "attribution",
                    "path",
                ],
                rows,
            )
        )
    if derived_candidates:
        print()
        print(f"## {DERIVED_SECTION}")
        rows = [
            [
                item["name"],
                item["size_human"],
                str(item["candidate_status"]),
                "yes" if item["cleanup_eligible"] else "no",
                str(item.get("age_days", "")),
                str(item.get("lock_present", "")),
                str(item["path"]),
            ]
            for item in derived_candidates
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
