from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "tooling/scripts/ci/check_github_security_alerts.py"
SPEC = importlib.util.spec_from_file_location(
    "check_github_security_alerts", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def test_github_security_alerts_guard_exists() -> None:
    assert SCRIPT_PATH.exists()


def test_origin_repo_slug_parses_https_remote(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/example/provenote.git"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    assert GUARD._origin_repo_slug(tmp_path) == "example/provenote"


def test_collect_failures_passes_when_both_alert_surfaces_are_zero(monkeypatch) -> None:
    monkeypatch.setattr(GUARD, "_count_alerts", lambda *_args, **_kwargs: 0)
    assert GUARD.collect_failures("example/provenote") == []


def test_collect_failures_flags_nonzero_alerts(monkeypatch) -> None:
    counts = {"code-scanning": 2, "secret-scanning": 1}

    def fake_count(repo_slug: str, alert_type: str) -> int:
        assert repo_slug == "example/provenote"
        return counts[alert_type]

    monkeypatch.setattr(GUARD, "_count_alerts", fake_count)
    failures = GUARD.collect_failures("example/provenote")

    assert any("code-scanning open alerts must be 0" in item for item in failures)
    assert any("secret-scanning open alerts must be 0" in item for item in failures)


def test_run_json_parses_gh_api_payload(monkeypatch) -> None:
    def fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            args=["gh", "api"],
            returncode=0,
            stdout=json.dumps([]),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert (
        GUARD._run_json(["gh", "api", "repos/example/provenote/code-scanning/alerts"])
        == []
    )


def test_run_json_raises_runtime_error_when_output_is_not_json(monkeypatch) -> None:
    def fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            args=["gh", "api"],
            returncode=0,
            stdout="not-json",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="non-JSON"):
        GUARD._run_json(["gh", "api", "repos/example/provenote/code-scanning/alerts"])


def test_github_security_alerts_guard_main_passes_with_clean_counts(
    monkeypatch,
) -> None:
    monkeypatch.setattr(GUARD, "collect_failures", lambda _repo_slug: [])
    monkeypatch.setattr(GUARD, "_origin_repo_slug", lambda: "example/provenote")
    monkeypatch.setattr(sys, "argv", ["check_github_security_alerts.py"])

    assert GUARD.main() == 0


def test_count_alerts_uses_tokened_http_fallback_when_gh_is_missing(
    monkeypatch,
) -> None:
    monkeypatch.setattr(GUARD.shutil, "which", lambda _name: None)
    monkeypatch.setenv("GH_TOKEN", "workflow-token")

    class _FakeResponse:
        def __enter__(self) -> io.StringIO:
            return io.StringIO("[]")

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    captured: dict[str, str] = {}

    def fake_urlopen(request, timeout: int = 30):
        captured["url"] = request.full_url
        captured["accept"] = request.get_header("Accept")
        captured["auth"] = request.get_header("Authorization")
        captured["version"] = request.get_header("X-github-api-version")
        assert timeout == 30
        return _FakeResponse()

    monkeypatch.setattr(GUARD.urllib.request, "urlopen", fake_urlopen)

    assert GUARD._count_alerts("example/provenote", "code-scanning") == 0
    assert captured["url"].endswith(
        "/repos/example/provenote/code-scanning/alerts?state=open&per_page=100"
    )
    assert captured["accept"] == "application/vnd.github+json"
    assert captured["auth"] == "Bearer workflow-token"
    assert captured["version"] == "2022-11-28"


def test_count_alerts_falls_back_to_tokened_http_when_gh_api_fails(
    monkeypatch,
) -> None:
    monkeypatch.setattr(GUARD.shutil, "which", lambda _name: "/usr/bin/gh")
    monkeypatch.setenv("GH_TOKEN", "workflow-token")

    def fake_run_json(_args):
        raise RuntimeError("gh api rate limited")

    class _FakeResponse:
        def __enter__(self) -> io.StringIO:
            return io.StringIO("[]")

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    captured: dict[str, str] = {}

    def fake_urlopen(request, timeout: int = 30):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        assert timeout == 30
        return _FakeResponse()

    monkeypatch.setattr(GUARD, "_run_json", fake_run_json)
    monkeypatch.setattr(GUARD.urllib.request, "urlopen", fake_urlopen)

    assert GUARD._count_alerts("example/provenote", "secret-scanning") == 0
    assert captured["url"].endswith(
        "/repos/example/provenote/secret-scanning/alerts?state=open&per_page=100"
    )
    assert captured["auth"] == "Bearer workflow-token"


def test_count_alerts_treats_secret_scanning_404_as_zero_for_public_repo(
    monkeypatch,
) -> None:
    def fake_load_endpoint_json(endpoint: str):
        if endpoint == "repos/example/provenote":
            return {"visibility": "public"}
        raise RuntimeError("HTTP Error 404: Not Found")

    monkeypatch.setattr(GUARD, "_load_endpoint_json", fake_load_endpoint_json)

    assert GUARD._count_alerts("example/provenote", "secret-scanning") == 0


def test_count_alerts_treats_code_scanning_403_as_zero_for_public_repo_without_ghas(
    monkeypatch,
) -> None:
    def fake_load_endpoint_json(endpoint: str):
        if endpoint == "repos/example/provenote":
            return {"visibility": "public", "security_and_analysis": {}}
        raise RuntimeError("HTTP Error 403: Forbidden")

    monkeypatch.setattr(GUARD, "_load_endpoint_json", fake_load_endpoint_json)

    assert GUARD._count_alerts("example/provenote", "code-scanning") == 0
