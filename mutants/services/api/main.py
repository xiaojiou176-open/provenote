# Load environment variables
from dotenv import load_dotenv

load_dotenv()

import json
import os
import re
import sys
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from packages.core.ai.connection_tester import probe_startup_gemini_model
from packages.core.database.async_migrate import AsyncMigrationManager
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
from packages.core.observability import (
    artifact_group_ctx,
    configure_process_logging,
    logger,
    request_id_ctx,
    run_id_ctx,
    test_id_ctx,
    trace_id_ctx,
    user_id_ctx,
)
from packages.core.observability.context import PROCESS_RUN_ID
from packages.core.settings import list_legacy_provider_env_vars
from packages.core.utils.encryption import get_secret_from_env
from services.api.auth import PasswordAuthMiddleware
from services.api.routers import (
    auditable_runs,
    auth,
    chat,
    computer_use,
    config,
    context,
    credentials,
    embedding,
    embedding_rebuild,
    episode_profiles,
    insights,
    models,
    notebooks,
    notes,
    podcasts,
    providers,
    search,
    settings,
    source_chat,
    sources,
    speaker_profiles,
    transformations,
    ui_tests,
)
from services.api.routers import commands as commands_router

SERVICE_NAME = "notebooklab-api"
COMPONENT_NAME = "services.api.http"
DOMAIN_NAME = "http"
ALLOWED_LOG_LEVELS = {
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
}
DEFAULT_REQUEST_LOG_EXCLUDE_PATHS = frozenset(
    {"/health", "/docs", "/openapi.json", "/redoc"}
)
_SAFE_CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_SAFE_USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:@-]{1,128}$")


@dataclass(frozen=True)
class RuntimeGovernanceConfig:
    log_level: str
    serialize_logs: bool
    request_log_exclude_paths: frozenset[str]
    slow_request_threshold_ms: int


@dataclass(frozen=True)
class CorsConfig:
    allow_origins: tuple[str, ...]
    allow_credentials: bool


DEFAULT_DEV_CORS_ALLOW_ORIGINS: tuple[str, ...] = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _env_bool(name: str, *, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, *, default: int, minimum: int, maximum: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        parsed = int(raw_value.strip())
    except ValueError:
        return default
    return max(minimum, min(maximum, parsed))


def _is_production_env() -> bool:
    env_name = os.getenv("OPEN_NOTEBOOK_ENV", "development").strip().lower()
    return env_name in {"prod", "production"}


def _parse_cors_allow_origins(raw_value: str | None) -> tuple[str, ...]:
    if raw_value is None:
        return ()
    return tuple(
        dict.fromkeys(
            origin.strip() for origin in raw_value.split(",") if origin.strip()
        )
    )


def _load_cors_config() -> CorsConfig:
    allow_credentials = _env_bool("OPEN_NOTEBOOK_CORS_ALLOW_CREDENTIALS", default=True)
    raw_allow_origins = os.getenv("OPEN_NOTEBOOK_CORS_ALLOW_ORIGINS")
    allow_origins = _parse_cors_allow_origins(raw_allow_origins)

    if _is_production_env() and (raw_allow_origins is None or not allow_origins):
        raise RuntimeError(
            "OPEN_NOTEBOOK_CORS_ALLOW_ORIGINS must be explicitly configured in production."
        )
    if not allow_origins:
        allow_origins = DEFAULT_DEV_CORS_ALLOW_ORIGINS
    if allow_credentials and "*" in allow_origins:
        raise RuntimeError(
            "Invalid CORS configuration: wildcard origin '*' cannot be used when "
            "OPEN_NOTEBOOK_CORS_ALLOW_CREDENTIALS=true."
        )

    return CorsConfig(
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
    )


def _load_runtime_governance() -> RuntimeGovernanceConfig:
    requested_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = (
        requested_log_level if requested_log_level in ALLOWED_LOG_LEVELS else "INFO"
    )

    exclude_paths_raw = os.getenv(
        "REQUEST_LOG_EXCLUDE_PATHS", ",".join(DEFAULT_REQUEST_LOG_EXCLUDE_PATHS)
    )
    exclude_paths = frozenset(
        path.strip() for path in exclude_paths_raw.split(",") if path.strip()
    )

    return RuntimeGovernanceConfig(
        log_level=log_level,
        serialize_logs=_env_bool("LOG_JSON", default=False),
        request_log_exclude_paths=exclude_paths or DEFAULT_REQUEST_LOG_EXCLUDE_PATHS,
        slow_request_threshold_ms=_env_int(
            "REQUEST_LOG_SLOW_THRESHOLD_MS",
            default=2000,
            minimum=0,
            maximum=60000,
        ),
    )


RUNTIME_GOVERNANCE = _load_runtime_governance()
CORS_CONFIG = _load_cors_config()


def _inject_log_context(record: Any) -> None:
    if not isinstance(record, dict):
        return
    extra = record.get("extra")
    if not isinstance(extra, dict):
        return
    extra.setdefault("run_id", run_id_ctx.get())
    extra.setdefault("request_id", request_id_ctx.get())
    extra.setdefault("trace_id", trace_id_ctx.get())
    extra.setdefault("user_id", user_id_ctx.get())
    extra.setdefault("test_id", test_id_ctx.get())
    extra.setdefault("artifact_group", artifact_group_ctx.get())
    extra.setdefault("component", "services.api.http")
    extra.setdefault("service", "notebooklab-api")
    extra.setdefault("domain", "http")
    extra.setdefault("error_class", "-")
    extra.setdefault("error_stack", "-")
    extra.setdefault("redaction_version", "v1")
    extra.setdefault("event", record.get("message") or "-")
    if extra.get("run_id") in {None, "-"}:
        extra["run_id"] = run_id_ctx.get()
    if extra.get("request_id") in {None, "-"}:
        extra["request_id"] = request_id_ctx.get()
    if extra.get("trace_id") in {None, "-"}:
        extra["trace_id"] = trace_id_ctx.get()
    if extra.get("user_id") in {None, "-"}:
        extra["user_id"] = user_id_ctx.get()
    if extra.get("test_id") in {None, "-"}:
        extra["test_id"] = test_id_ctx.get()
    if extra.get("artifact_group") in {None, "-"}:
        extra["artifact_group"] = artifact_group_ctx.get()


def _sanitize_correlation_id(value: Any) -> str:
    if isinstance(value, str) and _SAFE_CORRELATION_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid.uuid4())


def _sanitize_user_id(value: Any) -> str:
    if not isinstance(value, str):
        return "-"
    normalized = value.strip()
    if not normalized:
        return "-"
    if _SAFE_USER_ID_PATTERN.fullmatch(normalized):
        return normalized
    return "-"


def _request_correlation_headers(request: Request) -> dict[str, str]:
    request_id = _sanitize_correlation_id(
        getattr(request.state, "request_id", None)
        or request.headers.get("x-request-id")
    )
    trace_id = _sanitize_correlation_id(
        getattr(request.state, "trace_id", None)
        or request.headers.get("x-trace-id")
        or request_id
    )
    request.state.request_id = request_id
    request.state.trace_id = trace_id
    return {"X-Request-ID": request_id, "X-Trace-ID": trace_id}


def _configure_logging() -> None:
    configure_process_logging(
        service=SERVICE_NAME,
        component=COMPONENT_NAME,
        domain=DOMAIN_NAME,
        level=RUNTIME_GOVERNANCE.log_level,
        serialize=RUNTIME_GOVERNANCE.serialize_logs,
    )


_configure_logging()

# Import commands to register them in the API process
try:
    logger.info("Commands imported in API process")
except Exception as e:
    logger.exception(
        "Failed to import commands in API process error_type={}",
        type(e).__name__,
    )


def assert_no_legacy_provider_env() -> None:
    """Fail startup when non-Google provider credentials are supplied via ENV."""
    legacy_env_vars = list_legacy_provider_env_vars()
    if not legacy_env_vars:
        return
    vars_list = ", ".join(legacy_env_vars)
    raise RuntimeError(
        "Non-Google provider environment variables are not allowed: "
        f"{vars_list}. "
        "Google ENV-first runtime is allowed via GEMINI_API_KEY/GEMINI_MODEL. "
        "Recommended GEMINI_MODEL strategy: gemini-3.1-pro | gemini-3.0-pro | gemini-3.0-flash. "
        "Keep all other providers in Settings -> API Keys only."
    )


async def assert_provider_policy_bootstrap() -> None:
    """
    Validate that provider policy has at least one configured provider per modality.

    Enforced only when OPEN_NOTEBOOK_ENFORCE_PROVIDER_POLICY=true.
    """
    if _env_bool("OPEN_NOTEBOOK_SKIP_MIGRATIONS", default=False):
        logger.info(
            "Skipping provider policy bootstrap due to OPEN_NOTEBOOK_SKIP_MIGRATIONS=true"
        )
        return

    from services.api.credentials_service import get_provider_status

    status = await get_provider_status()
    policy_effective = status.get("policy_effective", {})
    policy_blockers = status.get("policy_blockers", {})
    failed_modalities = [name for name, ok in policy_effective.items() if not ok]
    if not failed_modalities:
        return

    details = "; ".join(
        f"{modality}: {policy_blockers.get(modality) or 'not configured'}"
        for modality in failed_modalities
    )
    message = (
        "Provider policy is not effective for required modalities. "
        "Configure Google Gemini credentials and defaults in Settings -> API Keys. "
        f"Details: {details}"
    )
    if _env_bool("OPEN_NOTEBOOK_ENFORCE_PROVIDER_POLICY", default=False):
        raise RuntimeError(message)
    logger.warning(message)


async def assert_gemini_model_bootstrap_probe() -> None:
    """Run strict Gemini model probe and block startup on failure."""
    if _env_bool("OPEN_NOTEBOOK_SKIP_GEMINI_STARTUP_PROBE", default=False):
        logger.info(
            "Skipping Gemini startup probe due to OPEN_NOTEBOOK_SKIP_GEMINI_STARTUP_PROBE=true"
        )
        return

    probe_result = await probe_startup_gemini_model()
    if probe_result["model_probe_result"]["success"]:
        logger.info(
            "Gemini startup probe passed provider={} model={} key_source={}",
            probe_result["model_probe_result"]["provider"],
            probe_result["model_probe_result"]["model"],
            probe_result["model_probe_result"]["key_source"],
        )
        return

    payload = {
        "error": "gemini_model_probe_blocked",
        "model_probe_result": probe_result["model_probe_result"],
        "blocked_reason": probe_result["blocked_reason"],
        "remediation": probe_result["remediation"],
    }
    logger.error("Gemini startup probe failed payload={}", payload)
    raise RuntimeError(json.dumps(payload, ensure_ascii=False))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for the FastAPI application.
    Runs database migrations automatically on startup.
    """
    # Startup: Security checks
    logger.info("Starting API initialization...")
    logger.info(
        "Runtime governance log_level={} log_json={} slow_request_threshold_ms={} request_log_exclude_paths={}",
        RUNTIME_GOVERNANCE.log_level,
        RUNTIME_GOVERNANCE.serialize_logs,
        RUNTIME_GOVERNANCE.slow_request_threshold_ms,
        sorted(RUNTIME_GOVERNANCE.request_log_exclude_paths),
    )
    logger.info(
        "CORS config allow_credentials={} allow_origins={}",
        CORS_CONFIG.allow_credentials,
        list(CORS_CONFIG.allow_origins),
    )
    try:
        from packages.core.telemetry.phoenix import setup_phoenix_tracing

        setup_phoenix_tracing()
    except Exception as e:
        logger.exception(
            "Phoenix tracing bootstrap skipped error_type={}",
            type(e).__name__,
        )

    # Security check: Encryption key
    if not get_secret_from_env("OPEN_NOTEBOOK_ENCRYPTION_KEY"):
        logger.warning(
            "OPEN_NOTEBOOK_ENCRYPTION_KEY not set. "
            "API key encryption will fail until this is configured. "
            "Set OPEN_NOTEBOOK_ENCRYPTION_KEY to any secret string."
        )

    # Security check: enforce ENV policy (Google ENV-first allowed; legacy non-Google provider ENV vars blocked)
    assert_no_legacy_provider_env()
    await assert_gemini_model_bootstrap_probe()

    # Run database migrations unless explicitly skipped
    if _env_bool("OPEN_NOTEBOOK_SKIP_MIGRATIONS", default=False):
        logger.warning(
            "Skipping database migrations due to OPEN_NOTEBOOK_SKIP_MIGRATIONS=true"
        )
    else:
        try:
            migration_manager = AsyncMigrationManager()
            current_version = await migration_manager.get_current_version()
            logger.info("Current database version={}", current_version)

            if await migration_manager.needs_migration():
                logger.warning("Database migrations are pending. Running migrations...")
                await migration_manager.run_migration_up()
                new_version = await migration_manager.get_current_version()
                logger.success(
                    "Migrations completed successfully. Database is now at version={}",
                    new_version,
                )
            else:
                logger.info(
                    "Database is already at the latest version. No migrations needed."
                )
        except Exception as e:
            logger.exception(
                "CRITICAL: Database migration failed error_type={}",
                type(e).__name__,
            )
            # Fail fast - don't start the API with an outdated database schema
            raise RuntimeError(f"Failed to run database migrations: {str(e)}") from e

    await assert_provider_policy_bootstrap()

    logger.success("API initialization completed successfully")

    # Yield control to the application
    yield

    # Shutdown: cleanup if needed
    from packages.core.application.ui_test_service import ui_test_service

    try:
        await ui_test_service.shutdown()
    except Exception:
        logger.exception("UI test service shutdown failed")
    logger.info("API shutdown complete")


app = FastAPI(
    title="Notebooklab API",
    description="API for Notebooklab - Research Assistant",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = _sanitize_correlation_id(
        request.headers.get("x-request-id") or str(uuid.uuid4())
    )
    trace_id = _sanitize_correlation_id(request.headers.get("x-trace-id") or request_id)
    user_id = request.headers.get("x-user-id") or "-"
    user_id = _sanitize_user_id(user_id)
    request.state.request_id = request_id
    request.state.trace_id = trace_id
    request.state.user_id = user_id

    request_id_token = request_id_ctx.set(request_id)
    trace_id_token = trace_id_ctx.set(trace_id)
    user_id_token = user_id_ctx.set(user_id)
    start_time = time.monotonic()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.monotonic() - start_time) * 1000
        logger.exception(
            "Request failed method={} path={} duration_ms={:.2f}",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise
    else:
        duration_ms = (time.monotonic() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        if request.url.path not in RUNTIME_GOVERNANCE.request_log_exclude_paths:
            is_slow_request = (
                RUNTIME_GOVERNANCE.slow_request_threshold_ms > 0
                and duration_ms >= RUNTIME_GOVERNANCE.slow_request_threshold_ms
            )
            log_fn = logger.warning if is_slow_request else logger.info
            log_fn(
                "Request completed method={} path={} status_code={} duration_ms={:.2f}",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
        return response
    finally:
        user_id_ctx.reset(user_id_token)
        trace_id_ctx.reset(trace_id_token)
        request_id_ctx.reset(request_id_token)


# Add password authentication middleware first
# Exclude /api/auth/status and /api/config from authentication
app.add_middleware(
    PasswordAuthMiddleware,
    excluded_paths=[
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/auth/status",
        "/api/config",
    ],
)

# Add CORS middleware last (so it processes first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(CORS_CONFIG.allow_origins),
    allow_credentials=CORS_CONFIG.allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handler to ensure CORS headers are included in error responses
# This helps when errors occur before the CORS middleware can process them
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Custom exception handler that ensures CORS headers are included in error responses.
    This is particularly important for 413 (Payload Too Large) errors during file uploads.

    Note: If a reverse proxy (nginx, traefik) returns 413 before the request reaches
    FastAPI, this handler won't be called. In that case, configure your reverse proxy
    to add CORS headers to error responses.
    """
    cors_headers = _cors_headers(request)
    detail = exc.detail
    if exc.status_code >= 500:
        detail = "Internal server error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
        headers={
            **(exc.headers or {}),
            **cors_headers,
            **_request_correlation_headers(request),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception method={} path={} error_type={}",
        request.method,
        request.url.path,
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={**_cors_headers(request), **_request_correlation_headers(request)},
    )


def _cors_headers(request: Request) -> dict[str, str]:
    origin = request.headers.get("origin")
    if not origin:
        return {}
    allow_origins = CORS_CONFIG.allow_origins
    if "*" in allow_origins:
        allowed_origin = "*"
    elif origin in allow_origins:
        allowed_origin = origin
    else:
        return {}
    headers = {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
        "Vary": "Origin",
    }
    if CORS_CONFIG.allow_credentials:
        headers["Access-Control-Allow-Credentials"] = "true"
    return headers


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
        headers={**_cors_headers(request), **_request_correlation_headers(request)},
    )


@app.exception_handler(InvalidInputError)
async def invalid_input_error_handler(request: Request, exc: InvalidInputError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
        headers={**_cors_headers(request), **_request_correlation_headers(request)},
    )


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
        headers={**_cors_headers(request), **_request_correlation_headers(request)},
    )


@app.exception_handler(RateLimitError)
async def rate_limit_error_handler(request: Request, exc: RateLimitError):
    return JSONResponse(
        status_code=429,
        content={"detail": str(exc)},
        headers={**_cors_headers(request), **_request_correlation_headers(request)},
    )


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request: Request, exc: ConfigurationError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
        headers={**_cors_headers(request), **_request_correlation_headers(request)},
    )


@app.exception_handler(NetworkError)
async def network_error_handler(request: Request, exc: NetworkError):
    _ = exc
    return JSONResponse(
        status_code=502,
        content={"detail": "Upstream service request failed"},
        headers={**_cors_headers(request), **_request_correlation_headers(request)},
    )


@app.exception_handler(ExternalServiceError)
async def external_service_error_handler(request: Request, exc: ExternalServiceError):
    _ = exc
    return JSONResponse(
        status_code=502,
        content={"detail": "Upstream service request failed"},
        headers={**_cors_headers(request), **_request_correlation_headers(request)},
    )


@app.exception_handler(OpenNotebookError)
async def open_notebook_error_handler(request: Request, exc: OpenNotebookError):
    _ = exc
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={**_cors_headers(request), **_request_correlation_headers(request)},
    )


# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(notebooks.router, prefix="/api", tags=["notebooks"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(models.router, prefix="/api", tags=["models"])
app.include_router(transformations.router, prefix="/api", tags=["transformations"])
app.include_router(notes.router, prefix="/api", tags=["notes"])
app.include_router(embedding.router, prefix="/api", tags=["embedding"])
app.include_router(
    embedding_rebuild.router, prefix="/api/embeddings", tags=["embeddings"]
)
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(context.router, prefix="/api", tags=["context"])
app.include_router(sources.router, prefix="/api", tags=["sources"])
app.include_router(insights.router, prefix="/api", tags=["insights"])
app.include_router(providers.router, prefix="/api", tags=["providers"])
app.include_router(commands_router.router, prefix="/api", tags=["commands"])
app.include_router(podcasts.router, prefix="/api", tags=["podcasts"])
app.include_router(episode_profiles.router, prefix="/api", tags=["episode-profiles"])
app.include_router(speaker_profiles.router, prefix="/api", tags=["speaker-profiles"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(source_chat.router, prefix="/api", tags=["source-chat"])
app.include_router(credentials.router, prefix="/api", tags=["credentials"])
app.include_router(auditable_runs.router, prefix="/api", tags=["auditable-runs"])
app.include_router(ui_tests.router, prefix="/api", tags=["ui-tests"])
app.include_router(computer_use.router, prefix="/api", tags=["computer-use"])


@app.get("/")
async def root():
    return {"message": "Notebooklab API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
