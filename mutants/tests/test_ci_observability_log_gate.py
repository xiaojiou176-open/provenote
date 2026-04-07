from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "tooling/scripts/ci/check_observability_log_gate.py"
)
SPEC = importlib.util.spec_from_file_location(
    "check_observability_log_gate", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_broad_exception_without_logger_is_blocked(tmp_path: Path) -> None:
    target = tmp_path / "services/api/foo.py"
    _write(
        target,
        "def run():\n"
        "    try:\n"
        "        work()\n"
        "    except Exception:\n"
        "        return None\n",
    )

    violations = GUARD.find_broad_exception_without_log(tmp_path, [target])

    assert violations == [
        "services/api/foo.py:4: broad exception block missing logger call"
    ]


def test_broad_exception_with_logger_is_allowed(tmp_path: Path) -> None:
    target = tmp_path / "packages/core/ai/foo.py"
    _write(
        target,
        "from packages.core.observability.logger import logger\n"
        "def run():\n"
        "    try:\n"
        "        work()\n"
        "    except Exception:\n"
        "        logger.error('failed')\n"
        "        return None\n",
    )

    violations = GUARD.find_broad_exception_without_log(tmp_path, [target])

    assert violations == []


def test_sensitive_interpolation_logging_is_blocked(tmp_path: Path) -> None:
    target = tmp_path / "services/api/secure.py"
    _write(
        target,
        'from packages.core.observability.logger import logger\nlogger.error(f"bad token={token}")\n',
    )

    violations = GUARD.find_sensitive_logging_violations(tmp_path, [target])

    assert violations == [
        "services/api/secure.py:2: sensitive identifier interpolated in logger f-string"
    ]


def test_key_files_reject_fstring_logger(tmp_path: Path) -> None:
    _write(
        tmp_path / "services/api/auth.py",
        'from packages.core.observability.logger import logger\nlogger.error(f"oops {err}")\n',
    )
    _write(
        tmp_path / "services/api/routers/providers.py",
        "from packages.core.observability.logger import logger\n",
    )
    _write(
        tmp_path / "packages/core/ai/connection_tester.py",
        "from packages.core.observability.logger import logger\n",
    )

    violations = GUARD.find_unstructured_key_logs(tmp_path)

    assert (
        "services/api/auth.py:2: key auth/provider path must not use f-string logger"
        in violations
    )


def test_trace_contract_missing_snippets_is_blocked(tmp_path: Path) -> None:
    _write(tmp_path / "services/api/main.py", "from fastapi import FastAPI\n")

    violations = GUARD.find_missing_trace_contract(tmp_path)

    assert violations
    assert any(
        item.startswith("services/api/main.py missing trace contract snippet:")
        for item in violations
    )


def test_default_scan_roots_follow_new_topology() -> None:
    assert GUARD.DEFAULT_SCAN_ROOTS == (
        "services/api",
        "services/worker",
        "packages/core",
        "tooling/scripts",
        "tests",
    )
