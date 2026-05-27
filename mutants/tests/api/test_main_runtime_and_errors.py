from __future__ import annotations

import json
import re
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request

from packages.core.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ExternalServiceError,
    InvalidInputError,
    NetworkError,
    NotFoundError,
    OpenNotebookError,
    RateLimitError,
)
from services.api import main as api_main


def _response_json(response: JSONResponse) -> dict[str, Any]:
    return json.loads(response.body.decode("utf-8"))


_SAFE_CORRELATION_HEADER_VALUE_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def _make_request(
    path: str = "/api/test",
    origin: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if origin is not None:
        headers.append((b"origin", origin.encode("utf-8")))
    if extra_headers:
        headers.extend(
            (name.lower().encode("utf-8"), value.encode("utf-8"))
            for name, value in extra_headers.items()
        )
    scope: dict[str, Any] = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


def _set_request_correlation(
    request: Request, *, request_id: str = "req-123", trace_id: str = "trace-123"
) -> None:
    request.state.request_id = request_id
    request.state.trace_id = trace_id


def test_env_int_invalid_value_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REQUEST_LOG_SLOW_THRESHOLD_MS", "not-an-int")

    value = api_main._env_int(
        "REQUEST_LOG_SLOW_THRESHOLD_MS",
        default=2000,
        minimum=0,
        maximum=60000,
    )

    assert value == 2000


def test_parse_cors_allow_origins_none_returns_empty_tuple() -> None:
    assert api_main._parse_cors_allow_origins(None) == ()


def test_inject_log_context_ignores_invalid_record_shapes() -> None:
    api_main._inject_log_context([])

    invalid_extra_record = {"extra": []}
    api_main._inject_log_context(invalid_extra_record)

    valid_record = {"extra": {}}
    api_main._inject_log_context(valid_record)

    assert invalid_extra_record == {"extra": []}
    assert valid_record["extra"]["run_id"] == api_main.PROCESS_RUN_ID
    assert valid_record["extra"]["request_id"] == "-"
    assert valid_record["extra"]["trace_id"] == "-"
    assert valid_record["extra"]["user_id"] == "-"
    assert valid_record["extra"]["component"] == "services.api.http"
    assert valid_record["extra"]["service"] == "notebooklab-api"
    assert valid_record["extra"]["domain"] == "http"
    assert valid_record["extra"]["redaction_version"] == "v1"


def test_inject_log_context_replaces_default_placeholders_with_context_values() -> None:
    run_token = api_main.run_id_ctx.set("run-live")
    request_token = api_main.request_id_ctx.set("req-live")
    trace_token = api_main.trace_id_ctx.set("trace-live")
    user_token = api_main.user_id_ctx.set("user-live")
    test_token = api_main.test_id_ctx.set("test-live")
    artifact_token = api_main.artifact_group_ctx.set("artifact-live")
    try:
        record = {
            "extra": {
                "run_id": "-",
                "request_id": "-",
                "trace_id": "-",
                "user_id": "-",
                "test_id": "-",
                "artifact_group": "-",
            }
        }

        api_main._inject_log_context(record)

        assert record["extra"]["run_id"] == "run-live"
        assert record["extra"]["request_id"] == "req-live"
        assert record["extra"]["trace_id"] == "trace-live"
        assert record["extra"]["user_id"] == "user-live"
        assert record["extra"]["test_id"] == "test-live"
        assert record["extra"]["artifact_group"] == "artifact-live"
    finally:
        api_main.artifact_group_ctx.reset(artifact_token)
        api_main.test_id_ctx.reset(test_token)
        api_main.user_id_ctx.reset(user_token)
        api_main.trace_id_ctx.reset(trace_token)
        api_main.request_id_ctx.reset(request_token)
        api_main.run_id_ctx.reset(run_token)


def test_request_correlation_headers_replaces_crlf_and_oversized_values() -> None:
    request = _make_request()
    malicious_request_id = "req-123\r\nx-injected: true"
    oversized_trace_id = "t" * 129
    _set_request_correlation(
        request,
        request_id=malicious_request_id,
        trace_id=oversized_trace_id,
    )

    headers = api_main._request_correlation_headers(request)

    assert headers["X-Request-ID"] != malicious_request_id
    assert headers["X-Trace-ID"] != oversized_trace_id
    assert _SAFE_CORRELATION_HEADER_VALUE_RE.fullmatch(headers["X-Request-ID"])
    assert _SAFE_CORRELATION_HEADER_VALUE_RE.fullmatch(headers["X-Trace-ID"])
    assert "\r" not in headers["X-Request-ID"]
    assert "\n" not in headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_request_context_middleware_reraises_and_resets_context() -> None:
    request = _make_request("/api/fail")

    async def _raise(_: Request) -> JSONResponse:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await api_main.request_context_middleware(request, _raise)

    assert api_main.request_id_ctx.get() == "-"
    assert api_main.trace_id_ctx.get() == "-"
    assert api_main.user_id_ctx.get() == "-"
    assert api_main.run_id_ctx.get() == api_main.PROCESS_RUN_ID


@pytest.mark.asyncio
async def test_request_context_middleware_skips_request_log_for_excluded_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_main,
        "RUNTIME_GOVERNANCE",
        api_main.RuntimeGovernanceConfig(
            log_level="INFO",
            serialize_logs=False,
            request_log_exclude_paths=frozenset({"/health"}),
            slow_request_threshold_ms=1,
        ),
    )

    request = _make_request("/health")

    async def _ok(_: Request) -> JSONResponse:
        return JSONResponse(status_code=200, content={"ok": True})

    response = await api_main.request_context_middleware(request, _ok)

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] not in {"", "-"}
    assert response.headers["X-Trace-ID"] not in {"", "-"}


@pytest.mark.asyncio
async def test_request_context_middleware_sanitizes_incoming_correlation_headers() -> (
    None
):
    malicious_request_id = "req-123\r\nx-forged: yes"
    oversized_trace_id = "trace" * 30
    request = _make_request(
        "/api/safe",
        extra_headers={
            "x-request-id": malicious_request_id,
            "x-trace-id": oversized_trace_id,
        },
    )

    async def _ok(_: Request) -> JSONResponse:
        return JSONResponse(status_code=200, content={"ok": True})

    response = await api_main.request_context_middleware(request, _ok)

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != malicious_request_id
    assert response.headers["X-Trace-ID"] != oversized_trace_id
    assert _SAFE_CORRELATION_HEADER_VALUE_RE.fullmatch(response.headers["X-Request-ID"])
    assert _SAFE_CORRELATION_HEADER_VALUE_RE.fullmatch(response.headers["X-Trace-ID"])
    assert "\r" not in response.headers["X-Request-ID"]
    assert "\n" not in response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_request_context_middleware_sanitizes_untrusted_user_id_header() -> None:
    request = _make_request(
        "/api/safe",
        extra_headers={"x-user-id": "alice\r\nforged-log-line: 1"},
    )

    async def _echo_user(req: Request) -> JSONResponse:
        return JSONResponse(status_code=200, content={"user_id": req.state.user_id})

    response = await api_main.request_context_middleware(request, _echo_user)

    assert response.status_code == 200
    assert _response_json(response)["user_id"] == "-"


@pytest.mark.asyncio
async def test_custom_http_exception_handler_masks_5xx_detail_and_keeps_cors_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_main,
        "CORS_CONFIG",
        api_main.CorsConfig(
            allow_origins=("https://app.example.com",),
            allow_credentials=True,
        ),
    )
    request = _make_request(origin="https://app.example.com")
    _set_request_correlation(request)

    response = await api_main.custom_http_exception_handler(
        request,
        HTTPException(status_code=500, detail="raw detail", headers={"x-error": "1"}),
    )

    assert response.status_code == 500
    assert response.headers["x-error"] == "1"
    assert response.headers["Access-Control-Allow-Origin"] == "https://app.example.com"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    assert response.headers["X-Request-ID"] == "req-123"
    assert response.headers["X-Trace-ID"] == "trace-123"
    assert _response_json(response) == {"detail": "Internal server error"}


def test_unhandled_exception_handler_is_registered() -> None:
    assert (
        api_main.app.exception_handlers[Exception]
        is api_main.unhandled_exception_handler
    )


@pytest.mark.asyncio
async def test_unhandled_exception_handler_keeps_json_cors_and_correlation_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_main,
        "CORS_CONFIG",
        api_main.CorsConfig(
            allow_origins=("https://app.example.com",),
            allow_credentials=True,
        ),
    )
    request = _make_request(origin="https://app.example.com")
    _set_request_correlation(request)

    response = await api_main.unhandled_exception_handler(request, RuntimeError("boom"))

    assert response.status_code == 500
    assert response.headers["Access-Control-Allow-Origin"] == "https://app.example.com"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    assert response.headers["X-Request-ID"] == "req-123"
    assert response.headers["X-Trace-ID"] == "trace-123"
    assert _response_json(response) == {"detail": "Internal server error"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("handler", "exc", "status", "detail"),
    [
        (api_main.not_found_error_handler, NotFoundError("missing"), 404, "missing"),
        (
            api_main.invalid_input_error_handler,
            InvalidInputError("bad input"),
            400,
            "bad input",
        ),
        (
            api_main.authentication_error_handler,
            AuthenticationError("no auth"),
            401,
            "no auth",
        ),
        (
            api_main.rate_limit_error_handler,
            RateLimitError("too many"),
            429,
            "too many",
        ),
        (
            api_main.configuration_error_handler,
            ConfigurationError("bad config"),
            422,
            "bad config",
        ),
        (
            api_main.network_error_handler,
            NetworkError("upstream timeout"),
            502,
            "Upstream service request failed",
        ),
        (
            api_main.external_service_error_handler,
            ExternalServiceError("provider failed"),
            502,
            "Upstream service request failed",
        ),
        (
            api_main.open_notebook_error_handler,
            OpenNotebookError("internal"),
            500,
            "Internal server error",
        ),
    ],
)
async def test_domain_exception_handlers_return_expected_contract(
    monkeypatch: pytest.MonkeyPatch,
    handler,
    exc,
    status: int,
    detail: str,
) -> None:
    monkeypatch.setattr(
        api_main,
        "CORS_CONFIG",
        api_main.CorsConfig(
            allow_origins=("https://app.example.com",),
            allow_credentials=True,
        ),
    )
    request = _make_request(origin="https://app.example.com")
    _set_request_correlation(request)

    response = await handler(request, exc)

    assert response.status_code == status
    assert response.headers["Access-Control-Allow-Origin"] == "https://app.example.com"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    assert response.headers["X-Request-ID"] == "req-123"
    assert response.headers["X-Trace-ID"] == "trace-123"
    assert _response_json(response) == {"detail": detail}
