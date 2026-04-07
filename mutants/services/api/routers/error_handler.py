from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar, cast

from fastapi import HTTPException

from packages.core.exceptions import InvalidInputError, NotFoundError
from packages.core.observability.logger import logger

RouteHandler = TypeVar("RouteHandler", bound=Callable[..., Awaitable[Any]])


def _format_template(template: str, kwargs: dict[str, Any]) -> str:
    try:
        return template.format(**kwargs)
    except Exception:
        return template


def with_router_error_handling(
    *,
    log_template: str,
    detail_template: str,
    include_exception_detail: bool = True,
    exception_status_map: dict[type[Exception], int] | None = None,
) -> Callable[[RouteHandler], RouteHandler]:
    status_map: dict[type[Exception], int] = {
        NotFoundError: 404,
        InvalidInputError: 400,
    }
    if exception_status_map:
        status_map.update(exception_status_map)

    def decorator(func: RouteHandler) -> RouteHandler:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as exc:
                for error_type, status_code in status_map.items():
                    if isinstance(exc, error_type):
                        raise HTTPException(
                            status_code=status_code, detail=str(exc)
                        ) from exc

                log_message = _format_template(log_template, kwargs)
                logger.error(f"{log_message}: {exc}")

                detail_message = _format_template(detail_template, kwargs)
                detail = (
                    f"{detail_message}: {exc}"
                    if include_exception_detail
                    else detail_message
                )
                raise HTTPException(status_code=500, detail=detail) from exc

        return cast(RouteHandler, wrapper)

    return decorator
