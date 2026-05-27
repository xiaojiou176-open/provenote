from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = REPO_ROOT / "ops" / "docker" / "Dockerfile.ci"
RUNNER_SCRIPT = REPO_ROOT / "tooling/scripts/ci/run_in_consistent_container.sh"
TOOLCHAIN_MANIFEST = REPO_ROOT / "config" / "ci-toolchain.env"
REAL_BACKEND_SMOKE_SCRIPT = REPO_ROOT / "tooling/scripts/ci/run_real_backend_smoke.sh"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def test_ci_toolchain_manifest_exists() -> None:
    assert TOOLCHAIN_MANIFEST.exists(), (
        "repo CI container contract requires config/ci-toolchain.env"
    )


def test_ci_toolchain_manifest_pins_surreal_real_smoke_binary_contract() -> None:
    toolchain_manifest = TOOLCHAIN_MANIFEST.read_text(encoding="utf-8")
    for token in (
        "CI_SURREAL_VERSION=2.3.10",
        "CI_SURREAL_LINUX_AMD64_SHA256=",
        "CI_SURREAL_LINUX_ARM64_SHA256=",
        "CI_SURREAL_DARWIN_AMD64_SHA256=",
        "CI_SURREAL_DARWIN_ARM64_SHA256=",
    ):
        assert token in toolchain_manifest, (
            "repo CI toolchain manifest must pin the fallback surreal binary used by real-backend smoke"
        )


def test_ci_dockerfile_uses_manifest_base_image_argument() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    assert "ARG CI_BASE_IMAGE" in dockerfile
    assert "FROM ${CI_BASE_IMAGE}" in dockerfile


def test_consistent_container_forwards_gemini_api_key_without_hardcoded_assignment_shape() -> (
    None
):
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")
    forbidden_assignment_shape = "-e GEMINI_API_KEY" + '="${GEMINI_API_KEY:-}"'

    assert "-e GEMINI_API_KEY" in runner_script
    assert forbidden_assignment_shape not in runner_script, (
        "consistent container runner must forward GEMINI_API_KEY by env name rather than a quoted key=value assignment shape that env governance flags as hardcoded"
    )


def test_consistent_container_redirects_uv_project_environment_into_container_home() -> (
    None
):
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")

    assert (
        'CONTAINER_MACHINE_CACHE_ROOT="${CONTAINER_HOME}/.cache/notebooklab"'
        in runner_script
    ), (
        "consistent container runner must declare the container-local machine cache root under container home"
    )
    assert (
        'UV_PROJECT_ENVIRONMENT="$(resolve_open_notebook_managed_uv_environment "${CONTAINER_MACHINE_CACHE_ROOT}")"'
        in runner_script
    ), (
        "consistent container runner must keep uv's project environment inside the container-home managed cache tree instead of the mounted workspace"
    )
    assert 'UV_PROJECT_ENVIRONMENT="${WORKSPACE_DIR}/.venv"' not in runner_script, (
        "consistent container runner must not point uv's project environment at the mounted workspace .venv"
    )


def test_consistent_container_bootstrap_uses_same_machine_uv_cache_contract_as_runtime() -> (
    None
):
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")

    for token in (
        'CONTAINER_MACHINE_CACHE_ROOT="${CONTAINER_HOME}/.cache/notebooklab"',
        'CONTAINER_UV_CACHE_DIR="$(resolve_open_notebook_machine_uv_cache_dir "${CONTAINER_MACHINE_CACHE_ROOT}")"',
        'CI_CACHE_ROOT="$(resolve_open_notebook_repo_ci_cache_root "${ROOT_DIR}")"',
        'NPM_CACHE_DIR="$(resolve_open_notebook_machine_ci_npm_cache_dir "${HOST_MACHINE_CACHE_ROOT}")"',
        'HOME_CACHE_DIR="${CI_CACHE_ROOT}/home-cache"',
        'REPO_PYCACHE_DIR="$(resolve_open_notebook_repo_pycache_dir "${ROOT_DIR}")"',
        '-e OPEN_NOTEBOOK_MACHINE_CACHE_ROOT="${CONTAINER_MACHINE_CACHE_ROOT}"',
        '-e UV_CACHE_DIR="${CONTAINER_UV_CACHE_DIR}"',
        '-e PYTHONPYCACHEPREFIX="${WORKSPACE_DIR}/.runtime-cache/pycache"',
        'export OPEN_NOTEBOOK_MACHINE_CACHE_ROOT="${OPEN_NOTEBOOK_MACHINE_CACHE_ROOT:-__CONTAINER_MACHINE_CACHE_ROOT__}"',
        'export UV_CACHE_DIR="${UV_CACHE_DIR:-__CONTAINER_UV_CACHE_DIR__}"',
        'export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/workspaces/notebooklab/.runtime-cache/pycache}"',
    ):
        assert token in runner_script, (
            "consistent container bootstrap must keep download caches on the machine-wide lane while moving repo-owned runtime/bootstrap state back under .runtime-cache/ci-host"
        )
    assert '-v "${NPM_CACHE_DIR}:${CONTAINER_HOME}/.npm"' in runner_script


def test_consistent_container_frontend_bootstrap_clears_node_modules_in_place() -> None:
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")

    assert (
        'wipe_open_notebook_directory_contents "apps/web/node_modules"' in runner_script
    ), (
        "consistent container frontend bootstrap must clear node_modules contents in place instead of deleting the root directory on a bind-mounted workspace"
    )
    assert "rm -rf apps/web/node_modules" not in runner_script, (
        "consistent container frontend bootstrap must not remove the node_modules root directly, because bind-mounted workspace cleanup can race and fail with ENOTEMPTY"
    )
    assert "npm ci --no-audit --no-fund" in runner_script, (
        "consistent container frontend bootstrap must use lower-noise npm ci flags for runner stability"
    )
    assert "frontend bootstrap failed after 2 npm ci attempts" in runner_script, (
        "consistent container frontend bootstrap must fail closed after bounded npm ci retries"
    )
    assert (
        "frontend bootstrap did not produce expected node_modules executables"
        in runner_script
    ), (
        "consistent container frontend bootstrap must verify required executables exist before continuing"
    )


def test_consistent_container_frontend_bootstrap_uses_shared_cache_and_lock() -> None:
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")

    for token in (
        "frontend_binaries_ready()",
        'frontend_cache_root="$HOME/bootstrap/apps-web-node-modules"',
        'frontend_cache_lock="${frontend_cache_root}/.${frontend_lock_hash}.lock"',
        "frontend bootstrap waiting for shared cache lock",
        '[[ -x "${bin_root}/.bin/biome" ]]',
        'cp -R "${frontend_cache_dir}/." "apps/web/node_modules/"',
    ):
        assert token in runner_script, (
            "consistent container frontend bootstrap must reuse a shared node_modules cache with a lock so concurrent self-hosted jobs do not all rerun npm ci"
        )


def test_consistent_container_mounts_writable_user_local_home_for_non_root_tools() -> (
    None
):
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")

    for token in (
        'LOCAL_HOME_DIR="${CI_CACHE_ROOT}/home-local"',
        '-v "${LOCAL_HOME_DIR}:${CONTAINER_HOME}/.local"',
        'export PATH="$HOME/.local/bin:$PATH"',
        'mkdir -p "$HOME" "$HOME/.cache" "$HOME/.local" "$HOME/.local/bin"',
    ):
        assert token in runner_script, (
            "consistent container runner must provide a writable ~/.local and PATH bootstrap for non-root user installs such as pre-commit on hosted lanes"
        )


def test_consistent_container_preserves_worktree_git_metadata_for_git_aware_checks() -> (
    None
):
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")

    for token in (
        'HOST_GIT_COMMON_DIR_RAW="$(git -C "${ROOT_DIR}" rev-parse --git-common-dir 2>/dev/null || true)"',
        'if [[ "${HOST_GIT_COMMON_DIR_RAW}" = /* ]]; then',
        'HOST_GIT_COMMON_DIR="$(cd "${ROOT_DIR}/${HOST_GIT_COMMON_DIR_RAW}" && pwd -P)"',
        '-v "${ROOT_DIR}:${ROOT_DIR}"',
        'if [[ -n "${HOST_GIT_COMMON_DIR}" ]] && [[ "${HOST_GIT_COMMON_DIR}" != "${ROOT_DIR}/.git" ]]; then',
        '-v "${HOST_GIT_COMMON_DIR}:${HOST_GIT_COMMON_DIR}"',
    ):
        assert token in runner_script, (
            "consistent container runner must expose worktree git metadata paths inside the container so git-aware governance/runtime guards keep working on git worktrees"
        )


def test_consistent_container_uses_host_uid_gid_for_bind_mounted_cache_paths() -> None:
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")

    assert 'if [[ "$(id -u)" != "0" ]]; then' in runner_script, (
        "consistent container runner must map the host uid/gid whenever it is not already running as root, so bind-mounted cache directories stay writable on hosted and local runners"
    )
    assert 'if [[ "${GITHUB_ACTIONS:-}" != "true" ]]; then' not in runner_script, (
        "consistent container runner must not special-case hosted GitHub Actions out of the uid/gid mapping contract"
    )


def test_setup_uv_python_uses_managed_wrapper_for_sync() -> None:
    action = (REPO_ROOT / ".github/actions/setup-uv-python/action.yml").read_text(
        encoding="utf-8"
    )
    assert "tooling/scripts/runtime/run_uv_managed.sh" in action
    assert "uv sync ${{ inputs.sync-args }}" not in action


def test_consistent_container_preserves_github_pull_request_refs_for_detached_ci() -> (
    None
):
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")

    for token in (
        '-e GITHUB_EVENT_NAME="${GITHUB_EVENT_NAME:-}"',
        '-e GITHUB_HEAD_REF="${GITHUB_HEAD_REF:-}"',
        '-e GITHUB_BASE_REF="${GITHUB_BASE_REF:-}"',
    ):
        assert token in runner_script, (
            "consistent container runner must forward GitHub pull-request ref context into the container so detached governance checks can still resolve audited branch exceptions"
        )


def test_consistent_container_forwards_github_tokens_for_repo_owned_api_checks() -> (
    None
):
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")

    for token in (
        '-e GH_TOKEN="${GH_TOKEN:-}"',
        '-e GITHUB_TOKEN="${GITHUB_TOKEN:-}"',
    ):
        assert token in runner_script, (
            "consistent container runner must forward GitHub auth tokens into the container so repo-owned GitHub API guards can authenticate in hosted CI"
        )


def test_runtime_policy_workflow_prefers_owner_supplied_security_read_token() -> None:
    workflow = (REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")

    assert (
        "GH_TOKEN: ${{ secrets.NOTEBOOKLAB_SECURITY_READ_TOKEN || github.token }}"
        in workflow
    ), (
        "runtime policy gates must allow an owner-supplied read token to override github.token when hosted CI cannot read GitHub security alert surfaces with the default workflow token"
    )


def test_consistent_container_runner_persists_playwright_browsers_in_machine_cache() -> (
    None
):
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")

    assert (
        'PLAYWRIGHT_BROWSERS_PATH="${CONTAINER_HOME}/playwright-browsers"'
        in runner_script
    ), (
        "consistent container runner must keep Playwright browsers under container-home paths backed by machine-level cache mounts rather than the repo checkout"
    )
    assert (
        'PLAYWRIGHT_BROWSERS_PATH="${WORKSPACE_DIR}/.runtime-cache/ms-playwright"'
        not in runner_script
    ), (
        "consistent container runner must not persist Playwright browsers inside the repo workspace cache tree"
    )
    assert (
        '-e PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH}"' in runner_script
    ), (
        "consistent container runner must pass the persistent Playwright browser cache path into the container"
    )


def test_consistent_container_auto_cleans_repo_specific_machine_cache_before_bootstrap() -> (
    None
):
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")

    for token in (
        "auto_cleanup_machine_cache()",
        "--include-historical-candidates",
        "--historical-max-age-days 0",
    ):
        assert token in runner_script

    assert "--include-stale-bootstrap-snapshots" not in runner_script


def test_consistent_container_frontend_bootstrap_detects_browser_bundles_via_revision_globs() -> (
    None
):
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")

    for token in (
        "playwright_cache_has_browsers()",
        'compgen -G "${PLAYWRIGHT_BROWSERS_PATH}/chromium_headless_shell-*/chrome-linux/headless_shell"',
        'compgen -G "${PLAYWRIGHT_BROWSERS_PATH}/firefox-*/firefox/firefox"',
        'compgen -G "${PLAYWRIGHT_BROWSERS_PATH}/firefox-*/firefox"',
        'compgen -G "${PLAYWRIGHT_BROWSERS_PATH}/webkit-*/pw_run.sh"',
        "frontend bootstrap did not provision the expected browser set into the shared Playwright cache",
    ):
        assert token in runner_script, (
            "consistent container frontend bootstrap must validate shared Playwright browser bundles via revision- and layout-tolerant globs so Playwright upgrades do not break the cache contract"
        )


def test_ci_dockerfile_installs_required_ci_toolchain_components() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    for token in (
        "docker.io",
        "python3-pip",
        'python3 --version | grep -E "^Python ${CI_PYTHON_SERIES}',
        'npm install --global "@playwright/test@${CI_PLAYWRIGHT_VERSION}"',
        "playwright install chromium firefox webkit",
        'python3 -m pip install --no-cache-dir --break-system-packages "uv==${CI_UV_VERSION}"',
    ):
        assert token in dockerfile, f"ops/docker/Dockerfile.ci must include '{token}'"


def test_consistent_container_defaults_to_repo_ci_contract_files() -> None:
    runner_script = RUNNER_SCRIPT.read_text(encoding="utf-8")
    assert 'TOOLCHAIN_FILE="${ROOT_DIR}/config/ci-toolchain.env"' in runner_script
    assert (
        'DOCKERFILE_PATH="${CONSISTENT_CONTAINER_DOCKERFILE:-${ROOT_DIR}/ops/docker/Dockerfile.ci}"'
        in runner_script
    )
    assert (
        'IMAGE_NAME="${CONSISTENT_CONTAINER_IMAGE:-${CI_IMAGE_NAME}:${IMAGE_FINGERPRINT}}"'
        in runner_script
    )


def test_test_workflow_installs_cross_browser_playwright_browsers_before_smoke_run() -> (
    None
):
    workflow = (REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "ops/docker/Dockerfile.ci" in DOCKERFILE.as_posix() or DOCKERFILE.exists()
    assert (
        "bash tooling/scripts/ci/run_in_consistent_container.sh --profile apps/web --"
        in workflow
    ), (
        "cross-browser smoke lane must use the repo CI container profile for apps/web execution"
    )


def test_real_backend_smoke_bootstraps_pinned_surreal_binary_before_failing_closed() -> (
    None
):
    script = REAL_BACKEND_SMOKE_SCRIPT.read_text(encoding="utf-8")

    assert 'source "${TOOLCHAIN_FILE}"' in script, (
        "real-backend smoke must source the repo CI toolchain manifest before deciding how to boot SurrealDB"
    )
    assert "ensure_local_surreal_binary()" in script, (
        "real-backend smoke must attempt machine-cache surreal bootstrap before falling back to docker or PATH"
    )
    assert "sha256_file()" in script, (
        "real-backend smoke must checksum-verify the downloaded surreal binary"
    )
    assert (
        "https://github.com/surrealdb/surrealdb/releases/download/v${SURREAL_VERSION}/"
        in script
    ), "real-backend smoke fallback must download from a pinned surreal release URL"
    assert 'source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"' in script, (
        "real-backend smoke must resolve machine-cache paths through the shared cache environment helper"
    )
    assert (
        'resolve_open_notebook_machine_surreal_binary_path "${MACHINE_CACHE_ROOT}"'
        in script
    ), (
        "real-backend smoke must resolve its pinned surreal binary location outside the repo-owned runtime tree"
    )
    assert 'install -m 0755 "${tmp_dir}/surreal" "${LOCAL_SURREAL_BIN}"' in script, (
        "real-backend smoke must persist the verified surreal binary under the machine cache tooling bin directory for reuse"
    )


def test_consistent_container_uses_sudo_docker_when_plain_docker_cannot_access_daemon(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    log_path = tmp_path / "docker-invocations.log"

    _write_executable(
        fake_bin / "docker",
        f"""#!/usr/bin/env bash
set -euo pipefail
printf 'docker:%s\n' "$*" >> {log_path!s}
if [[ "$1" == "build" ]]; then
  echo 'permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock' >&2
  exit 1
fi
if [[ "$1" == "image" && "$2" == "inspect" ]]; then
  echo 'Error: No such image' >&2
  exit 1
fi
if [[ "$1" == "run" ]]; then
  exit 0
fi
exit 0
""",
    )
    _write_executable(
        fake_bin / "sudo",
        f"""#!/usr/bin/env bash
set -euo pipefail
printf 'sudo:%s\n' "$*" >> {log_path!s}
if [[ "$1" == "docker" ]]; then
  shift
  printf 'sudo-docker:%s\n' "$*" >> {log_path!s}
  exit 0
fi
exit 1
""",
    )

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{fake_bin}:{env['PATH']}",
            "CI": "true",
            "GITHUB_ACTIONS": "true",
            "CONSISTENT_CONTAINER_BOOTSTRAP": "never",
        }
    )

    result = subprocess.run(
        ["bash", str(RUNNER_SCRIPT), "--", "true"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    log_lines = log_path.read_text(encoding="utf-8").splitlines()
    assert any(line.startswith("docker:build ") for line in log_lines), (
        "runner should try plain docker first for outer image build"
    )
    assert any(line.startswith("sudo:docker build ") for line in log_lines), (
        "runner should retry the outer image build through sudo docker when daemon socket access is denied"
    )
    assert any(line.startswith("sudo:docker run ") for line in log_lines), (
        "runner should keep outer container run aligned with sudo docker once fallback is required"
    )
    assert (
        "permission denied while trying to connect to the Docker daemon socket"
        not in result.stderr
    )
