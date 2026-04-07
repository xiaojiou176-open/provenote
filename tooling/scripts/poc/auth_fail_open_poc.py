#!/usr/bin/env python3
"""
PoC: detect fail-open behavior when OPEN_NOTEBOOK_PASSWORD is not configured.

Expected secure behavior (fixed): protected route returns non-200.
Vulnerable behavior (old): protected route returns 200 without Authorization.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.api.auth import PasswordAuthMiddleware


def _build_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(
        PasswordAuthMiddleware,
        excluded_paths=["/health"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/protected")
    async def protected() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(app)


def main() -> int:
    os.environ.pop("OPEN_NOTEBOOK_PASSWORD", None)
    os.environ.pop("OPEN_NOTEBOOK_PASSWORD_FILE", None)

    with _build_client() as client:
        response = client.get("/api/protected")

    print(f"PoC status_code={response.status_code} body={response.text}")
    if response.status_code == 200:
        print("VULNERABLE: fail-open detected (unauthenticated request was allowed).")
        return 1

    print("FIXED: fail-closed enforced (unauthenticated request was rejected).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
