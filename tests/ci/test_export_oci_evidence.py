from __future__ import annotations

import base64
import importlib.util
import urllib.error
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "tooling/scripts/ci/export_oci_evidence.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("export_oci_evidence", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("failed to load export_oci_evidence module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ghcr_token_request_headers_are_anonymous_without_credentials(
    monkeypatch,
) -> None:
    module = _load_module()
    monkeypatch.delenv("GHCR_USERNAME", raising=False)
    monkeypatch.delenv("GHCR_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_ACTOR", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    credentials = module._resolve_registry_credentials()
    headers = module._build_token_headers(credentials)

    assert headers == {"Accept": "application/json"}


def test_ghcr_token_request_headers_use_explicit_credentials(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setenv("GHCR_USERNAME", "octocat")
    monkeypatch.setenv("GHCR_TOKEN", "super-secret")
    monkeypatch.delenv("GITHUB_ACTOR", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    credentials = module._resolve_registry_credentials()
    headers = module._build_token_headers(credentials)

    assert headers["Accept"] == "application/json"
    assert headers["Authorization"].startswith("Basic ")
    payload = base64.b64decode(headers["Authorization"].removeprefix("Basic ")).decode(
        "utf-8"
    )
    assert payload == "octocat:super-secret"


def test_ghcr_token_request_headers_fall_back_to_github_env(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.delenv("GHCR_USERNAME", raising=False)
    monkeypatch.delenv("GHCR_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_ACTOR", "github-actions[bot]")
    monkeypatch.setenv("GITHUB_TOKEN", "workflow-token")

    credentials = module._resolve_registry_credentials()
    headers = module._build_token_headers(credentials)

    payload = base64.b64decode(headers["Authorization"].removeprefix("Basic ")).decode(
        "utf-8"
    )
    assert payload == "github-actions[bot]:workflow-token"


def test_retry_with_backoff_retries_retryable_registry_http_error(monkeypatch) -> None:
    module = _load_module()
    attempts = {"count": 0}

    def flaky_fetch():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise urllib.error.HTTPError(
                "https://ghcr.io/v2/example/manifests/test",
                404,
                "Not Found",
                hdrs=None,
                fp=None,
            )
        return {"ok": True}

    monkeypatch.setattr(module.time, "sleep", lambda _: None)

    result = module._retry_with_backoff(
        flaky_fetch, description="subject manifest test"
    )

    assert result == {"ok": True}
    assert attempts["count"] == 3


def test_retry_with_backoff_covers_longer_ghcr_visibility_delay(monkeypatch) -> None:
    module = _load_module()
    attempts = {"count": 0}

    def delayed_fetch():
        attempts["count"] += 1
        if attempts["count"] < 13:
            raise urllib.error.HTTPError(
                "https://ghcr.io/v2/example/manifests/test",
                404,
                "Not Found",
                hdrs=None,
                fp=None,
            )
        return {"ok": True}

    monkeypatch.setattr(module.time, "sleep", lambda _: None)

    result = module._retry_with_backoff(
        delayed_fetch,
        description="subject manifest test",
    )

    assert result == {"ok": True}
    assert attempts["count"] == 13


def test_retry_with_backoff_does_not_retry_non_retryable_http_error(
    monkeypatch,
) -> None:
    module = _load_module()
    monkeypatch.setattr(module.time, "sleep", lambda _: None)

    def forbidden_fetch():
        raise urllib.error.HTTPError(
            "https://ghcr.io/v2/example/manifests/test",
            401,
            "Unauthorized",
            hdrs=None,
            fp=None,
        )

    exc_info = pytest.raises(
        urllib.error.HTTPError,
        module._retry_with_backoff,
        forbidden_fetch,
        description="subject manifest test",
    )

    assert exc_info.value.code == 401
