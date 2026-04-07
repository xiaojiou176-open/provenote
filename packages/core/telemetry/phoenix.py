"""Optional Phoenix tracing bootstrap.

Tracing is disabled by default and only activated when:
OPEN_NOTEBOOK_PHOENIX_ENABLED=true
"""

from __future__ import annotations

from packages.core.observability.logger import logger
from packages.core.settings import get_settings

_TRUTHY = {"1", "true", "yes", "on"}


def _is_enabled() -> bool:
    raw = "true" if get_settings().open_notebook_phoenix_enabled else "false"
    return raw.strip().lower() in _TRUTHY


def setup_phoenix_tracing() -> bool:
    """Enable Phoenix tracing when explicitly requested via env vars."""
    if not _is_enabled():
        logger.debug(
            "Phoenix tracing disabled (OPEN_NOTEBOOK_PHOENIX_ENABLED is false)"
        )
        return False

    try:
        from phoenix.otel import register  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning(
            f"Phoenix tracing requested but phoenix package is unavailable: {exc}"
        )
        return False

    settings = get_settings()
    endpoint = settings.open_notebook_phoenix_collector_endpoint.strip()
    project_name = settings.open_notebook_phoenix_project_name.strip()

    headers: dict[str, str] = {}
    api_key = (settings.open_notebook_phoenix_api_key or "").strip()
    if api_key:
        headers["api_key"] = api_key

    kwargs: dict[str, object] = {"project_name": project_name}
    if endpoint:
        kwargs["endpoint"] = endpoint
    if headers:
        kwargs["headers"] = headers

    try:
        register(**kwargs)
        logger.info(
            f"Phoenix tracing enabled (project={project_name}, endpoint={endpoint})"
        )
        return True
    except Exception as exc:  # pragma: no cover - defensive for optional runtime
        logger.warning(f"Failed to initialize Phoenix tracing: {exc}")
        return False
