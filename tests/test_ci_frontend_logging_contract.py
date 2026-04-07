from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "tooling/scripts/ci/check_frontend_logging_contract.py"
)
SPEC = importlib.util.spec_from_file_location(
    "check_frontend_logging_contract", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_shared_runtime_file_blocks_raw_console_calls(tmp_path: Path) -> None:
    target = tmp_path / "apps/web/src/lib/config.ts"
    _write(target, 'export function load() { console.info("bad"); }\n')

    violations = GUARD.find_console_violations(tmp_path, [target])

    assert violations == [
        "apps/web/src/lib/config.ts:1: shared frontend runtime surfaces must use @/lib/log instead of raw console calls"
    ]


def test_logger_entrypoint_is_allowed_to_use_console(tmp_path: Path) -> None:
    target = tmp_path / "apps/web/src/lib/log.ts"
    _write(target, 'export const appLog = { info() { console.info("ok"); } };\n')

    violations = GUARD.find_console_violations(tmp_path, [target])

    assert violations == []


def test_default_scan_roots_target_new_shared_frontend_surfaces() -> None:
    assert GUARD.DEFAULT_SCAN_ROOTS == ("apps/web/src",)


def test_frontend_log_schema_sync_script_exists() -> None:
    script_path = (
        Path(__file__).resolve().parents[1]
        / "tooling/scripts/ci/check_frontend_log_schema_sync.mjs"
    )
    assert script_path.exists()
