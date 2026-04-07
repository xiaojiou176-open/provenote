from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from packages.core.observability.logger import logger
from packages.core.utils.encryption import get_secret_from_env


class PasswordAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check password authentication for all API requests.
    Always active with default password if OPEN_NOTEBOOK_PASSWORD is not set.
    Supports Docker secrets via OPEN_NOTEBOOK_PASSWORD_FILE.
    """

    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.password = get_secret_from_env("OPEN_NOTEBOOK_PASSWORD")
        self.excluded_paths = excluded_paths or [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Skip authentication for CORS preflight requests (OPTIONS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Fail closed when password is not configured.
        if not self.password:
            logger.warning(
                "Authentication rejected for path={} because OPEN_NOTEBOOK_PASSWORD is not configured",
                request.url.path,
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication is not configured"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            logger.warning(
                "Authentication rejected path={} reason=missing_authorization_header",
                request.url.path,
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Expected format: "Bearer {password}"
        try:
            scheme, credentials = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
        except ValueError:
            logger.warning(
                "Authentication rejected path={} reason=invalid_authorization_header_format",
                request.url.path,
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check password
        if credentials != self.password:
            logger.warning(
                "Authentication rejected path={} reason=invalid_password",
                request.url.path,
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid password"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Password is correct, proceed with the request
        response = await call_next(request)
        return response


# Optional: HTTPBearer security scheme for OpenAPI documentation
security = HTTPBearer(auto_error=False)


def check_api_password(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> bool:
    """
    Utility function to check API password.
    Can be used as a dependency in individual routes if needed.
    Supports Docker secrets via OPEN_NOTEBOOK_PASSWORD_FILE.
    Fails closed if OPEN_NOTEBOOK_PASSWORD is not configured.
    Raises 401 if credentials are missing or don't match the configured password.
    """
    password = get_secret_from_env("OPEN_NOTEBOOK_PASSWORD")

    # Fail closed when password is not configured.
    if not password:
        raise HTTPException(
            status_code=401,
            detail="Authentication is not configured",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # No credentials provided
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # HTTPBearer should already enforce scheme=Bearer; keep an explicit guard
    # to keep dependency behavior and middleware semantics consistent.
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization scheme, expected Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check password
    if credentials.credentials != password:
        raise HTTPException(
            status_code=401,
            detail="Invalid password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True
