"""
Pytest configuration file.

This file ensures that the project root is in the Python path,
allowing tests to import from the api and open_notebook modules.
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure password auth has a deterministic non-empty test password BEFORE any imports.
DEFAULT_TEST_PASSWORD = "open-notebook-test-password"
if not os.environ.get("OPEN_NOTEBOOK_PASSWORD"):
    os.environ["OPEN_NOTEBOOK_PASSWORD"] = DEFAULT_TEST_PASSWORD
os.environ.setdefault("OPEN_NOTEBOOK_SKIP_GEMINI_STARTUP_PROBE", "1")

# Load environment variables from .env file
# This must be done BEFORE any imports that depend on environment variables
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
dotenv_test_path = project_root / ".env.test"

# Add the project root to the Python path before local imports
sys.path.insert(0, str(project_root))

from packages.core.settings import LEGACY_PROVIDER_ENV_BLOCKLIST
from services.api.session_locks import reset_session_locks


def _clear_legacy_provider_env_vars() -> None:
    """Ensure tests never inherit non-Google provider credentials from local dotenv files."""
    for env_var in LEGACY_PROVIDER_ENV_BLOCKLIST:
        os.environ.pop(env_var, None)


# Tests should not silently inherit developer/local root .env.
# Load .env.test first. If missing, safely skip dotenv loading by default.
if dotenv_test_path.exists():
    load_dotenv(dotenv_test_path)
    print(f"Loaded test environment variables from {dotenv_test_path}")
else:
    print("Info: .env.test not found, skipped loading root .env by default.")

# Clear legacy provider env vars after dotenv load to avoid test pollution.
_clear_legacy_provider_env_vars()


@pytest.fixture(autouse=True)
def isolate_legacy_provider_env(monkeypatch: pytest.MonkeyPatch):
    """Isolate each test from legacy provider env leakage."""
    for env_var in LEGACY_PROVIDER_ENV_BLOCKLIST:
        monkeypatch.delenv(env_var, raising=False)


@pytest.fixture(autouse=True)
def reset_session_lock_registry():
    """Prevent lock state leakage between chat/source_chat tests."""
    reset_session_locks()
    yield
    reset_session_locks()


@pytest.fixture
def api_client():
    """Shared authenticated API client fixture for router tests."""
    auth_header_value = f"Bearer {os.environ['OPEN_NOTEBOOK_PASSWORD']}"
    with patch("services.api.main.AsyncMigrationManager") as mock_migration_manager:
        manager = mock_migration_manager.return_value
        manager.get_current_version = AsyncMock(return_value=16)
        manager.needs_migration = AsyncMock(return_value=False)
        from services.api.main import app

        with TestClient(app) as test_client:
            test_client.headers.update({"Authorization": auth_header_value})
            yield test_client


@pytest.fixture
def api_client_no_auth():
    """Shared API client without Authorization header for negative auth cases."""
    with patch("services.api.main.AsyncMigrationManager") as mock_migration_manager:
        manager = mock_migration_manager.return_value
        manager.get_current_version = AsyncMock(return_value=16)
        manager.needs_migration = AsyncMock(return_value=False)
        from services.api.main import app

        with TestClient(app) as test_client:
            yield test_client
