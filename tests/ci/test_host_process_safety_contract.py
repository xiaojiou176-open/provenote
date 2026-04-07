from __future__ import annotations

import re
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_SCRIPT = REPO_ROOT / "tooling/scripts/ci/check_host_process_safety.py"
COMMON_SH = REPO_ROOT / "tooling/scripts/dev/common.sh"
RELEASE_PORTS_SH = REPO_ROOT / "tooling/scripts/ci/release_local_ports.sh"
START_SCRIPTS = (
    REPO_ROOT / "tooling/scripts/dev/start_api_local.sh",
    REPO_ROOT / "tooling/scripts/dev/start_frontend_local.sh",
    REPO_ROOT / "tooling/scripts/dev/start_surreal_local.sh",
    REPO_ROOT / "tooling/scripts/dev/start_worker_local.sh",
)


def _run_gate(*paths: Path) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(GATE_SCRIPT)]
    if paths:
        cmd.extend(["--paths", *[str(path) for path in paths]])
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_port(port: int, *, timeout_seconds: float = 5.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise AssertionError(f"Timed out waiting for port {port} to accept connections")


def test_host_process_safety_guard_passes_for_current_repo_state() -> None:
    result = _run_gate()
    assert result.returncode == 0, result.stdout + result.stderr


def test_host_process_safety_allows_signal_probe_js(tmp_path: Path) -> None:
    file_path = tmp_path / "probe.mjs"
    file_path.write_text(
        "function isAlive(pid) {\n  process.kill(pid, 0);\n}\n",
        encoding="utf-8",
    )

    result = _run_gate(file_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_host_process_safety_blocks_dangerous_process_kill_in_js(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "danger.mjs"
    file_path.write_text(
        "export function stop(pid) {\n  process.kill(pid, 'SIGTERM');\n}\n",
        encoding="utf-8",
    )

    result = _run_gate(file_path)
    assert result.returncode != 0
    assert "direct Node process.kill is forbidden" in (result.stdout + result.stderr)


def test_release_local_ports_refuses_unowned_listener(tmp_path: Path) -> None:
    port = _find_free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)],
        cwd=tmp_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_port(port)
        result = subprocess.run(
            ["bash", str(RELEASE_PORTS_SH), str(port)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode != 0
        assert "refusing to stop them" in (result.stdout + result.stderr)
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_release_local_ports_can_stop_repo_owned_recorded_listener(
    tmp_path: Path,
) -> None:
    port = _find_free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)],
        cwd=tmp_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    pid_file = (
        REPO_ROOT / ".runtime-cache/local/pids" / f"host-process-safety-{port}.pid"
    )
    try:
        _wait_for_port(port)
        register = subprocess.run(
            [
                "bash",
                "-lc",
                "\n".join(
                    [
                        f'source "{COMMON_SH}"',
                        f'init_local_runtime_dirs "{REPO_ROOT}"',
                        (
                            f'safe_process_write_record "{pid_file}" "{proc.pid}" '
                            f'"test-http-server" "http.server {port}" "{tmp_path}" "{port}"'
                        ),
                    ]
                ),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert register.returncode == 0, register.stdout + register.stderr

        result = subprocess.run(
            ["bash", str(RELEASE_PORTS_SH), str(port)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        proc.wait(timeout=5)
        assert not pid_file.exists()
        assert not pid_file.with_suffix(".pid.meta").exists()
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
        pid_file.unlink(missing_ok=True)
        pid_file.with_suffix(".pid.meta").unlink(missing_ok=True)


def test_unsafe_pid_prepare_status_is_only_preserved_inside_else_branch(
    tmp_path: Path,
) -> None:
    port = _find_free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)],
        cwd=tmp_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    pid_file = tmp_path / "unsafe-status.pid"
    meta_file = pid_file.with_suffix(".pid.meta")
    try:
        _wait_for_port(port)
        register = subprocess.run(
            [
                "bash",
                "-lc",
                "\n".join(
                    [
                        f'source "{COMMON_SH}"',
                        (
                            f'safe_process_write_record "{pid_file}" "{proc.pid}" '
                            f'"test-http-server" "http.server {port}" "{tmp_path}" "{port}"'
                        ),
                    ]
                ),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert register.returncode == 0, register.stdout + register.stderr

        with meta_file.open("a", encoding="utf-8") as handle:
            handle.write("SAFE_PROCESS_COMMAND_PATTERN='definitely-not-this-command'\n")

        bad_pattern = subprocess.run(
            [
                "bash",
                "-lc",
                "\n".join(
                    [
                        f'source "{COMMON_SH}"',
                        f'if safe_process_prepare_pid_file "{pid_file}"; then',
                        "  :",
                        "fi",
                        "existing_state=$?",
                        'printf "observed=%s error=%s\\n" "$existing_state" "$SAFE_PROCESS_RECORD_ERROR"',
                    ]
                ),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert bad_pattern.returncode == 0, bad_pattern.stdout + bad_pattern.stderr
        assert "observed=0 error=command_mismatch" in (
            bad_pattern.stdout + bad_pattern.stderr
        )

        good_pattern = subprocess.run(
            [
                "bash",
                "-lc",
                "\n".join(
                    [
                        f'source "{COMMON_SH}"',
                        f'if safe_process_prepare_pid_file "{pid_file}"; then',
                        "  :",
                        "else",
                        "  existing_state=$?",
                        "fi",
                        'printf "observed=%s error=%s\\n" "$existing_state" "$SAFE_PROCESS_RECORD_ERROR"',
                    ]
                ),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert good_pattern.returncode == 0, good_pattern.stdout + good_pattern.stderr
        assert "observed=2 error=command_mismatch" in (
            good_pattern.stdout + good_pattern.stderr
        )
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
        pid_file.unlink(missing_ok=True)
        meta_file.unlink(missing_ok=True)


def test_start_scripts_capture_unsafe_pid_prepare_status_inside_else_branch() -> None:
    pattern = re.compile(
        r'if safe_process_prepare_pid_file "\$\{PID_FILE\}"; then\n'
        r".*?\n"
        r"else\n"
        r"  existing_state=\$\?\n"
        r"fi\n"
        r'if \[\[ "\$\{existing_state\}" -eq 2 \]\]; then',
        re.DOTALL,
    )

    for script_path in START_SCRIPTS:
        script_text = script_path.read_text(encoding="utf-8")
        assert pattern.search(script_text), (
            f"{script_path.name} must capture safe_process_prepare_pid_file status "
            "inside the if/else compound so unsafe pid records stay fail-closed"
        )
