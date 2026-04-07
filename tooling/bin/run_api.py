"""
Startup script for Provenote API server.
"""

import sys
from pathlib import Path

import uvicorn

from packages.core.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

if __name__ == "__main__":
    settings = get_settings()
    host = settings.api_host
    port = settings.api_port
    reload = settings.api_reload

    print(f"Starting Provenote API server on {host}:{port}")
    print(f"Reload mode: {reload}")

    uvicorn.run(
        "services.api.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[str(REPO_ROOT)] if reload else None,
    )
