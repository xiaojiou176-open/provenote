#!/usr/bin/env python3
"""Fail when the current GitHub repository has open code/secret scanning alerts."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=None,
        help="Optional owner/repo override. Defaults to origin remote slug.",
    )
    return parser


def _run_json(args: list[str], *, cwd: Path = REPO_ROOT) -> Any:
    result = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise RuntimeError(message)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("command returned non-JSON output") from exc


def _origin_repo_slug(repo_root: Path = REPO_ROOT) -> str:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git remote get-url origin failed")

    remote = result.stdout.strip()
    https_match = re.search(
        r"github\.com[:/](?P<slug>[^/\s]+/[^/\s]+?)(?:\.git)?$", remote
    )
    if https_match:
        return https_match.group("slug")
    raise RuntimeError(
        f"unable to derive GitHub repo slug from origin remote: {remote}"
    )


def _run_http_json(endpoint: str) -> Any:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("missing GH_TOKEN/GITHUB_TOKEN for GitHub API fallback")
    request = urllib.request.Request(
        f"https://api.github.com/{endpoint}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc)) from exc


def _load_endpoint_json(endpoint: str) -> Any:
    if shutil.which("gh"):
        try:
            return _run_json(["gh", "api", endpoint])
        except Exception as gh_exc:
            try:
                return _run_http_json(endpoint)
            except Exception as http_exc:
                raise RuntimeError(
                    f"{gh_exc}; HTTP fallback failed: {http_exc}"
                ) from http_exc
    return _run_http_json(endpoint)


def _repo_metadata(repo_slug: str) -> dict[str, Any]:
    payload = _load_endpoint_json(f"repos/{repo_slug}")
    if not isinstance(payload, dict):
        raise RuntimeError("repo metadata response was not a JSON object")
    return payload


def _repo_is_public(repo_slug: str) -> bool:
    payload = _repo_metadata(repo_slug)
    if "visibility" in payload:
        return payload["visibility"] == "public"
    if "private" in payload:
        return not bool(payload["private"])
    raise RuntimeError("repo metadata response was missing visibility/private")


def _count_alerts(repo_slug: str, alert_type: str) -> int:
    endpoint = f"repos/{repo_slug}/{alert_type}/alerts?state=open&per_page=100"
    try:
        payload = _load_endpoint_json(endpoint)
    except RuntimeError as exc:
        # GitHub documents this endpoint as unavailable for public repos.
        if (
            alert_type == "secret-scanning"
            and "404" in str(exc)
            and _repo_is_public(repo_slug)
        ):
            return 0
        metadata = _repo_metadata(repo_slug)
        security_and_analysis = metadata.get("security_and_analysis") or {}
        if (
            alert_type == "code-scanning"
            and "403" in str(exc)
            and metadata.get("visibility") == "public"
            and "advanced_security" not in security_and_analysis
        ):
            return 0
        raise
    if not isinstance(payload, list):
        raise RuntimeError(f"{alert_type} alerts response was not a JSON list")
    return len(payload)


def collect_failures(repo_slug: str) -> list[str]:
    failures: list[str] = []
    code_scanning_count = _count_alerts(repo_slug, "code-scanning")
    secret_scanning_count = _count_alerts(repo_slug, "secret-scanning")

    if code_scanning_count != 0:
        failures.append(
            f"{repo_slug}: GitHub code-scanning open alerts must be 0 (found {code_scanning_count})"
        )
    if secret_scanning_count != 0:
        failures.append(
            f"{repo_slug}: GitHub secret-scanning open alerts must be 0 (found {secret_scanning_count})"
        )
    return failures


def main() -> int:
    args = build_parser().parse_args()
    repo_slug = args.repo or _origin_repo_slug()
    try:
        failures = collect_failures(repo_slug)
    except Exception as exc:  # pragma: no cover - fail-closed CLI path
        print(f"FAIL: unable to verify GitHub security alerts for {repo_slug}: {exc}")
        return 1

    if failures:
        print(
            "FAIL: GitHub code-scanning and/or secret-scanning open alerts are non-zero; inspect the GitHub Security surfaces for details."
        )
        return 1

    print(
        f"PASS: GitHub code-scanning and secret-scanning open alerts are both 0 for {repo_slug}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
