import asyncio
import os
import time
import tomllib
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request

from packages.core.database.repository import repo_query
from packages.core.observability.logger import logger
from packages.core.utils.version_utils import (
    compare_versions,
    get_version_from_github_async,
)

router = APIRouter()

# In-memory cache for version check results
_version_cache: dict = {
    "latest_version": None,
    "has_update": False,
    "timestamp": 0,
    "check_failed": False,
}
_version_cache_lock = asyncio.Lock()

# Cache TTL in seconds (24 hours)
VERSION_CACHE_TTL = 24 * 60 * 60

# This fork does not declare an off-repo canonical release channel by default.
# When unset, /config stays repo-local and reports no remote update surface.
VERSION_CHECK_REPO_URL: str | None = None


def get_version() -> str:
    """Read version from pyproject.toml"""
    try:
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
            return pyproject.get("project", {}).get("version", "unknown")
    except Exception as e:
        logger.warning(f"Could not read version from pyproject.toml: {e}")
        return "unknown"


async def get_latest_version_cached(current_version: str) -> tuple[Optional[str], bool]:
    """
    Check for the latest version from an explicitly configured remote channel.

    Returns:
        tuple: (latest_version, has_update)
        - latest_version: str or None if check failed
        - has_update: bool indicating if update is available
    """
    global _version_cache

    async with _version_cache_lock:
        # Check if cache is still valid (within TTL)
        cache_age = time.time() - _version_cache["timestamp"]
        if _version_cache["timestamp"] > 0 and cache_age < VERSION_CACHE_TTL:
            logger.debug(f"Using cached version check result (age: {cache_age:.0f}s)")
            return _version_cache["latest_version"], _version_cache["has_update"]

        # Cache expired or not yet set
        if _version_cache["timestamp"] > 0:
            logger.info(f"Version cache expired (age: {cache_age:.0f}s), refreshing...")

        if not VERSION_CHECK_REPO_URL:
            logger.info("Remote version check disabled for repo-local public boundary")
            _version_cache["latest_version"] = None
            _version_cache["has_update"] = False
            _version_cache["timestamp"] = time.time()
            _version_cache["check_failed"] = False
            return None, False

        # Perform version check with strict error handling
        try:
            logger.info("Checking for latest version from configured remote channel...")

            # Fetch latest version from configured repository with 10-second timeout
            latest_version = await get_version_from_github_async(
                VERSION_CHECK_REPO_URL, "main"
            )

            logger.info(
                f"Latest remote version: {latest_version}, Current version: {current_version}"
            )

            # Compare versions
            has_update = compare_versions(current_version, latest_version) < 0

            # Cache the result
            _version_cache["latest_version"] = latest_version
            _version_cache["has_update"] = has_update
            _version_cache["timestamp"] = time.time()
            _version_cache["check_failed"] = False

            logger.info(f"Version check complete. Update available: {has_update}")

            return latest_version, has_update

        except Exception as e:
            logger.warning(f"Version check failed: {e}")

            # Cache the failure to avoid repeated attempts
            _version_cache["latest_version"] = None
            _version_cache["has_update"] = False
            _version_cache["timestamp"] = time.time()
            _version_cache["check_failed"] = True

            return None, False


async def check_database_health() -> dict:
    """
    Check if database is reachable using a lightweight query.

    Returns:
        dict with 'status' ("online" | "offline") and optional 'error'
    """
    try:
        # 2-second timeout for database health check
        result = await asyncio.wait_for(repo_query("RETURN 1"), timeout=2.0)
        if result:
            return {"status": "online"}
        return {"status": "offline", "error": "database_unavailable"}
    except asyncio.TimeoutError:
        logger.warning("Database health check timed out after 2 seconds")
        return {"status": "offline", "error": "health_check_timeout"}
    except Exception as e:
        logger.warning("Database health check failed error_type={}", type(e).__name__)
        return {"status": "offline", "error": "health_check_failed"}


@router.get("/config")
async def get_config(request: Request):
    """
    Get frontend configuration.

    Returns version information and health status.
    Note: The frontend determines the API URL via its own runtime-config endpoint,
    so this endpoint no longer returns apiUrl.

    Also checks for version updates from GitHub (with caching and error handling).
    """
    # Get current version
    current_version = get_version()

    # Check for updates (with caching and error handling)
    # This MUST NOT break the endpoint - wrapped in try-except as extra safety
    latest_version = None
    has_update = False

    try:
        latest_version, has_update = await get_latest_version_cached(current_version)
    except Exception as e:
        # Extra safety: ensure version check never breaks the config endpoint
        logger.error(
            "Unexpected error during version check error_type={}",
            type(e).__name__,
        )

    # Check database health
    db_health = await check_database_health()
    db_status = db_health["status"]

    if db_status == "offline":
        logger.warning(f"Database offline: {db_health.get('error', 'Unknown error')}")

    return {
        "version": current_version,
        "latestVersion": latest_version,
        "hasUpdate": has_update,
        "dbStatus": db_status,
    }
