from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_supervisor_log_path_guard_is_nested_under_log_contract() -> None:
    log_contract = (REPO_ROOT / "tooling/scripts/ci/check_log_contract.py").read_text(
        encoding="utf-8"
    )
    assert "check_supervisor_log_path.py" in log_contract


def test_supervisor_log_path_guard_passes_for_current_repo_state() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tooling/scripts/ci/check_supervisor_log_path.py"),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout or result.stderr


def test_single_container_compose_contract_pins_quickstart_ports_and_project_name() -> (
    None
):
    compose_text = (REPO_ROOT / "ops/compose/docker-compose.yml").read_text(
        encoding="utf-8"
    )

    assert "name: notebooklab" in compose_text
    assert '"8000:8000"' not in compose_text
    assert '- "8502:8502"  # Web UI' in compose_text
    assert '- "5055:5055"  # REST API' in compose_text
    assert "- API_URL=http://localhost:5055" in compose_text
    assert "- INTERNAL_API_URL=http://127.0.0.1:5055" in compose_text
    assert "- NEXT_PUBLIC_API_URL=http://localhost:5055" in compose_text
    assert (
        "- OPEN_NOTEBOOK_CORS_ALLOW_ORIGINS=http://localhost:8502,http://127.0.0.1:8502"
        in compose_text
    )
    assert "- GEMINI_MODEL=gemini-2.5-flash" in compose_text


def test_supervisor_configs_use_safe_program_names() -> None:
    for rel_path in (
        "ops/supervisor/supervisord.single.conf",
        "ops/supervisor/supervisord.conf",
    ):
        content = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        program_names = re.findall(
            r"^\[program:([^\]]+)\]$", content, flags=re.MULTILINE
        )
        assert program_names, f"expected supervisor program sections in {rel_path}"
        assert all("/" not in name and ":" not in name for name in program_names), (
            f"supervisor program names must avoid '/' and ':': {rel_path} -> {program_names}"
        )


def test_single_container_worker_uses_repo_worker_module_path() -> None:
    single_text = (REPO_ROOT / "ops/supervisor/supervisord.single.conf").read_text(
        encoding="utf-8"
    )
    assert "--import-modules services.worker" in single_text
    assert "--import-modules commands" not in single_text


def test_supervisor_web_process_uses_start_server_entrypoint() -> None:
    for rel_path in (
        "ops/supervisor/supervisord.single.conf",
        "ops/supervisor/supervisord.conf",
    ):
        content = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert "node start-server.js" in content
        assert "node server.js" not in content
