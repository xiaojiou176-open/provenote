"""Notebooklab package bootstrap."""

from __future__ import annotations

import sys
import types

from langchain_core.caches import BaseCache


def _ensure_langgraph_cache_compat() -> None:
    """Patch langgraph 1.0 packaging drift where graph.state still imports langgraph.cache.base."""

    if "langgraph.cache.base" in sys.modules:
        return

    cache_pkg = types.ModuleType("langgraph.cache")
    cache_pkg.__path__ = []  # type: ignore[attr-defined]

    base_mod = types.ModuleType("langgraph.cache.base")
    setattr(base_mod, "BaseCache", BaseCache)

    sys.modules.setdefault("langgraph.cache", cache_pkg)
    sys.modules["langgraph.cache.base"] = base_mod


_ensure_langgraph_cache_compat()
