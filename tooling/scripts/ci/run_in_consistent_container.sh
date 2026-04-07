#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"
HOST_MACHINE_CACHE_ROOT="$(resolve_open_notebook_machine_cache_root)"
TOOLCHAIN_FILE="${ROOT_DIR}/config/ci-toolchain.env"
DOCKERFILE_PATH="${CONSISTENT_CONTAINER_DOCKERFILE:-${ROOT_DIR}/ops/docker/Dockerfile.ci}"
WORKSPACE_DIR="/workspaces/provenote"
CONTAINER_HOME="/tmp/provenote-home"
CONTAINER_MACHINE_CACHE_ROOT="${CONTAINER_HOME}/.cache/provenote"
UV_PROJECT_ENVIRONMENT="$(resolve_open_notebook_managed_uv_environment "${CONTAINER_MACHINE_CACHE_ROOT}")"
CONTAINER_UV_CACHE_DIR="$(resolve_open_notebook_machine_uv_cache_dir "${CONTAINER_MACHINE_CACHE_ROOT}")"
PLAYWRIGHT_BROWSERS_PATH="${CONTAINER_HOME}/playwright-browsers"
BOOTSTRAP_MODE="${CONSISTENT_CONTAINER_BOOTSTRAP:-auto}"
BOOTSTRAP_PROFILE="${CONSISTENT_CONTAINER_PROFILE:-full}"
CI_CACHE_ROOT="$(resolve_open_notebook_repo_ci_cache_root "${ROOT_DIR}")"
NPM_CACHE_DIR="$(resolve_open_notebook_machine_ci_npm_cache_dir "${HOST_MACHINE_CACHE_ROOT}")"
TMP_CACHE_DIR="${CI_CACHE_ROOT}/tmp"
HOME_CACHE_DIR="${CI_CACHE_ROOT}/home-cache"
LOCAL_HOME_DIR="${CI_CACHE_ROOT}/home-local"
BOOTSTRAP_CACHE_DIR="${CI_CACHE_ROOT}/bootstrap"
PLAYWRIGHT_CACHE_DIR="$(resolve_open_notebook_machine_playwright_cache_dir "${HOST_MACHINE_CACHE_ROOT}")"
REPO_PYCACHE_DIR="$(resolve_open_notebook_repo_pycache_dir "${ROOT_DIR}")"
DOCKER_SOCKET_PATH="/var/run/docker.sock"
HOST_GIT_COMMON_DIR_RAW="$(git -C "${ROOT_DIR}" rev-parse --git-common-dir 2>/dev/null || true)"
HOST_GIT_COMMON_DIR=""

if [[ -n "${HOST_GIT_COMMON_DIR_RAW}" ]]; then
  if [[ "${HOST_GIT_COMMON_DIR_RAW}" = /* ]]; then
    HOST_GIT_COMMON_DIR="${HOST_GIT_COMMON_DIR_RAW}"
  else
    HOST_GIT_COMMON_DIR="$(cd "${ROOT_DIR}/${HOST_GIT_COMMON_DIR_RAW}" && pwd -P)"
  fi
fi

if [[ ! -f "${TOOLCHAIN_FILE}" ]]; then
  echo "Missing CI toolchain manifest: ${TOOLCHAIN_FILE}" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "${TOOLCHAIN_FILE}"

hash_files() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$@" | shasum -a 256 | awk '{print $1}'
    return 0
  fi
  sha256sum "$@" | sha256sum | awk '{print $1}'
}

IMAGE_FINGERPRINT="$(hash_files "${TOOLCHAIN_FILE}" "${DOCKERFILE_PATH}" | cut -c1-16)"
IMAGE_NAME="${CONSISTENT_CONTAINER_IMAGE:-${CI_IMAGE_NAME}:${IMAGE_FINGERPRINT}}"

usage() {
  cat <<'EOF'
Usage: bash tooling/scripts/ci/run_in_consistent_container.sh [--bootstrap auto|always|never] [--profile minimal|python|apps/web-static|apps/web|repo-fast|full] -- <command>
EOF
}

if [[ $# -eq 0 ]]; then
  usage >&2
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bootstrap)
      BOOTSTRAP_MODE="$2"
      shift 2
      ;;
    --profile)
      BOOTSTRAP_PROFILE="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ $# -eq 0 ]]; then
  echo "Missing command after --" >&2
  usage >&2
  exit 1
fi

case "${BOOTSTRAP_MODE}" in
  auto|always|never) ;;
  *)
    echo "Invalid bootstrap mode: ${BOOTSTRAP_MODE}" >&2
    exit 1
    ;;
esac

case "${BOOTSTRAP_PROFILE}" in
  minimal|python|apps/web-static|apps/web|repo-fast|full) ;;
  *)
    echo "Invalid bootstrap profile: ${BOOTSTRAP_PROFILE}" >&2
    exit 1
    ;;
esac

ensure_open_notebook_machine_cache_layout "${HOST_MACHINE_CACHE_ROOT}"
mkdir -p "${CI_CACHE_ROOT}" "${NPM_CACHE_DIR}" "${TMP_CACHE_DIR}" "${HOME_CACHE_DIR}" "${LOCAL_HOME_DIR}" "${BOOTSTRAP_CACHE_DIR}" "${PLAYWRIGHT_CACHE_DIR}" "${ROOT_DIR}/.runtime-cache/build/egg-info"
mkdir -p "${REPO_PYCACHE_DIR}"

auto_cleanup_machine_cache() {
  if [[ "${PROVENOTE_MACHINE_CACHE_AUTO_CLEAN:-1}" == "0" ]]; then
    return 0
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    return 0
  fi
  if ! python3 "${ROOT_DIR}/tooling/scripts/ops/cleanup_machine_cache.py" \
    --mode apply \
    --include-historical-candidates \
    --historical-max-age-days 0 >/dev/null; then
    echo "[consistent-container] warn: machine-cache auto-clean failed; continuing" >&2
  fi
}

auto_cleanup_machine_cache

if [[ "${DOCKER_HOST:-}" == unix://* ]]; then
  DOCKER_SOCKET_PATH="${DOCKER_HOST#unix://}"
fi

DOCKER_BIN=(docker)

run_docker() {
  "${DOCKER_BIN[@]}" "$@"
}

run_docker_with_permission_fallback() {
  local output
  local status=0

  set +e
  output="$(run_docker "$@" 2>&1)"
  status=$?
  set -e

  if [[ ${status} -eq 0 ]]; then
    printf '%s\n' "${output}"
    return 0
  fi

  if [[ "${output}" == *"permission denied while trying to connect to the Docker daemon socket"* ]] && command -v sudo >/dev/null 2>&1; then
    DOCKER_BIN=(sudo docker)
    run_docker "$@"
    return 0
  fi

  printf '%s\n' "${output}" >&2
  return ${status}
}

ensure_image_built() {
  if run_docker_with_permission_fallback image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
    return 0
  fi

  echo "Building repo CI container image: ${IMAGE_NAME}"
  run_docker_with_permission_fallback build \
    --build-arg "CI_BASE_IMAGE=${CI_BASE_IMAGE}" \
    --build-arg "CI_PYTHON_SERIES=${CI_PYTHON_SERIES}" \
    --build-arg "CI_NODE_VERSION=${CI_NODE_VERSION}" \
    --build-arg "CI_NODE_DIST=${CI_NODE_DIST}" \
    --build-arg "CI_NODE_SHA256=${CI_NODE_SHA256}" \
    --build-arg "CI_UV_VERSION=${CI_UV_VERSION}" \
    --build-arg "CI_PLAYWRIGHT_VERSION=${CI_PLAYWRIGHT_VERSION}" \
    -f "${DOCKERFILE_PATH}" \
    -t "${IMAGE_NAME}" \
    "${ROOT_DIR}"
}

DOCKER_ARGS=(
  run
  --rm
  -t
  --init
  --ipc=host
  -v "${ROOT_DIR}:${WORKSPACE_DIR}"
  -v "${ROOT_DIR}:${ROOT_DIR}"
  -v "${NPM_CACHE_DIR}:${CONTAINER_HOME}/.npm"
  -v "${HOME_CACHE_DIR}:${CONTAINER_HOME}/.cache"
  -v "${LOCAL_HOME_DIR}:${CONTAINER_HOME}/.local"
  -v "${TMP_CACHE_DIR}:${CONTAINER_HOME}/tmp"
  -v "${BOOTSTRAP_CACHE_DIR}:${CONTAINER_HOME}/bootstrap"
  -v "${PLAYWRIGHT_CACHE_DIR}:${PLAYWRIGHT_BROWSERS_PATH}"
  -w "${WORKSPACE_DIR}"
  -e HOME="${CONTAINER_HOME}"
  -e OPEN_NOTEBOOK_MACHINE_CACHE_ROOT="${CONTAINER_MACHINE_CACHE_ROOT}"
  -e UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT}"
  -e UV_CACHE_DIR="${CONTAINER_UV_CACHE_DIR}"
  -e PYTHONPYCACHEPREFIX="${WORKSPACE_DIR}/.runtime-cache/pycache"
  -e SETUPTOOLS_EGG_BASE="${WORKSPACE_DIR}/.runtime-cache/build/egg-info"
  -e NPM_CONFIG_CACHE="${CONTAINER_HOME}/.npm"
  -e PRE_COMMIT_HOME="${CONTAINER_HOME}/.cache/pre-commit"
  -e SKIP="${SKIP:-}"
  -e TMPDIR="${CONTAINER_HOME}/tmp"
  -e DOCKER_HOST="unix:///var/run/docker.sock"
  -e PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH}"
  -e CI="${CI:-}"
  -e GITHUB_ACTIONS="${GITHUB_ACTIONS:-}"
  -e GITHUB_EVENT_NAME="${GITHUB_EVENT_NAME:-}"
  -e GITHUB_HEAD_REF="${GITHUB_HEAD_REF:-}"
  -e GITHUB_BASE_REF="${GITHUB_BASE_REF:-}"
  -e GITHUB_WORKSPACE="${GITHUB_WORKSPACE:-}"
  -e GITHUB_RUN_ID="${GITHUB_RUN_ID:-}"
  -e GITHUB_RUN_ATTEMPT="${GITHUB_RUN_ATTEMPT:-}"
  -e GITHUB_SHA="${GITHUB_SHA:-}"
  -e GITHUB_REF="${GITHUB_REF:-}"
  -e GITHUB_REF_NAME="${GITHUB_REF_NAME:-}"
  -e GITHUB_HEAD_REF="${GITHUB_HEAD_REF:-}"
  -e GITHUB_BASE_REF="${GITHUB_BASE_REF:-}"
  -e GITHUB_EVENT_NAME="${GITHUB_EVENT_NAME:-}"
  -e GITHUB_EVENT_BEFORE="${GITHUB_EVENT_BEFORE:-}"
  -e GH_TOKEN="${GH_TOKEN:-}"
  -e GITHUB_TOKEN="${GITHUB_TOKEN:-}"
  -e RUNNER_WORKSPACE="${RUNNER_WORKSPACE:-}"
  -e PLAYWRIGHT_PORT="${PLAYWRIGHT_PORT:-}"
  -e PLAYWRIGHT_API_PORT="${PLAYWRIGHT_API_PORT:-}"
  -e PLAYWRIGHT_TRACE_MODE="${PLAYWRIGHT_TRACE_MODE:-}"
  -e PLAYWRIGHT_SCREENSHOT_MODE="${PLAYWRIGHT_SCREENSHOT_MODE:-}"
  -e PLAYWRIGHT_VIDEO_MODE="${PLAYWRIGHT_VIDEO_MODE:-}"
  -e PLAYWRIGHT_DISABLE_VISUAL_BASELINES="${PLAYWRIGHT_DISABLE_VISUAL_BASELINES:-}"
  -e PLAYWRIGHT_DISABLE_COLOR_CONTRAST_CHECK="${PLAYWRIGHT_DISABLE_COLOR_CONTRAST_CHECK:-}"
  -e FRONTEND_COVERAGE_SCOPE="${FRONTEND_COVERAGE_SCOPE:-}"
  -e RUN_LIVE_TESTS="${RUN_LIVE_TESTS:-}"
  -e LIVE_EXTERNAL_WEB_ENABLED="${LIVE_EXTERNAL_WEB_ENABLED:-}"
  -e LIVE_EXTERNAL_SITE_URL="${LIVE_EXTERNAL_SITE_URL:-}"
  -e LIVE_HEARTBEAT_SECONDS="${LIVE_HEARTBEAT_SECONDS:-}"
  -e LIVE_GEMINI_SMOKE_MODEL="${LIVE_GEMINI_SMOKE_MODEL:-}"
  -e LIVE_TEARDOWN_EVIDENCE_FILE="${LIVE_TEARDOWN_EVIDENCE_FILE:-}"
  -e OPEN_NOTEBOOK_SKIP_MIGRATIONS="${OPEN_NOTEBOOK_SKIP_MIGRATIONS:-}"
  -e LONG_TESTS_PARALLEL="${LONG_TESTS_PARALLEL:-}"
  -e HEARTBEAT_INTERVAL_SECONDS="${HEARTBEAT_INTERVAL_SECONDS:-}"
  -e E2E_MAX_RETRIES="${E2E_MAX_RETRIES:-}"
  -e E2E_CHROMIUM_WORKERS="${E2E_CHROMIUM_WORKERS:-}"
  -e MUTATION_MAX_CHILDREN="${MUTATION_MAX_CHILDREN:-}"
  -e MUTATION_MIN_SCORE="${MUTATION_MIN_SCORE:-}"
  -e MUTATION_MAX_NO_TESTS="${MUTATION_MAX_NO_TESTS:-}"
  -e MUTATION_MAX_SURVIVED_REGRESSION="${MUTATION_MAX_SURVIVED_REGRESSION:-}"
  -e MUTATION_MAX_SCORE_REGRESSION="${MUTATION_MAX_SCORE_REGRESSION:-}"
  -e BACKEND_COVERAGE_SCOPE="${BACKEND_COVERAGE_SCOPE:-}"
  -e RUN_PERFORMANCE_BENCHMARKS="${RUN_PERFORMANCE_BENCHMARKS:-}"
  -e PERF_BENCHMARK_ALLOW_ENV_SKIP="${PERF_BENCHMARK_ALLOW_ENV_SKIP:-}"
  -e SURREAL_URL="${SURREAL_URL:-}"
  -e SURREAL_EXTERNAL_URL="${SURREAL_EXTERNAL_URL:-}"
  -e SURREAL_USER="${SURREAL_USER:-}"
  -e SURREAL_PASSWORD="${SURREAL_PASSWORD:-}"
  -e SURREAL_NAMESPACE="${SURREAL_NAMESPACE:-}"
  -e SURREAL_DATABASE="${SURREAL_DATABASE:-}"
  -e OPEN_NOTEBOOK_PASSWORD="${OPEN_NOTEBOOK_PASSWORD:-}"
  -e OPEN_NOTEBOOK_ENCRYPTION_KEY="${OPEN_NOTEBOOK_ENCRYPTION_KEY:-}"
  -e GEMINI_API_KEY
  --add-host host.docker.internal:host-gateway
)

if [[ -S "${DOCKER_SOCKET_PATH}" ]]; then
  DOCKER_ARGS+=(-v "${DOCKER_SOCKET_PATH}:/var/run/docker.sock")
fi

if [[ -n "${HOST_GIT_COMMON_DIR}" ]] && [[ "${HOST_GIT_COMMON_DIR}" != "${ROOT_DIR}/.git" ]]; then
  DOCKER_ARGS+=(-v "${HOST_GIT_COMMON_DIR}:${HOST_GIT_COMMON_DIR}")
fi

if [[ "$(id -u)" != "0" ]]; then
  DOCKER_ARGS+=(--user "$(id -u):$(id -g)")
fi

if [[ -n "${CONSISTENT_CONTAINER_DOCKER_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  EXTRA_DOCKER_ARGS=( ${CONSISTENT_CONTAINER_DOCKER_ARGS} )
  DOCKER_ARGS+=("${EXTRA_DOCKER_ARGS[@]}")
fi

if [[ -n "${CONSISTENT_CONTAINER_PLATFORM:-}" ]]; then
  DOCKER_ARGS+=(--platform "${CONSISTENT_CONTAINER_PLATFORM}")
fi

ensure_image_built

read -r -d '' BOOTSTRAP_PREAMBLE <<'EOF' || true
export OPEN_NOTEBOOK_MACHINE_CACHE_ROOT="${OPEN_NOTEBOOK_MACHINE_CACHE_ROOT:-__CONTAINER_MACHINE_CACHE_ROOT__}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-__CONTAINER_UV_CACHE_DIR__}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/workspaces/provenote/.runtime-cache/pycache}"
export PATH="$HOME/.local/bin:$PATH"
source tooling/scripts/runtime/cache_env.sh
mkdir -p "$HOME" "$HOME/.cache" "$HOME/.local" "$HOME/.local/bin" "$HOME/.npm" "$TMPDIR" "$PLAYWRIGHT_BROWSERS_PATH" "$HOME/bootstrap" "$OPEN_NOTEBOOK_MACHINE_CACHE_ROOT" "$UV_CACHE_DIR" "$PYTHONPYCACHEPREFIX" .runtime-cache/build/egg-info
python_lock_hash="$(sha256sum uv.lock pyproject.toml tooling/scripts/ci/run_in_consistent_container.sh | sha256sum | awk '{print $1}')"
python_lock_file="$HOME/bootstrap/python.lock.sha256"
frontend_lock_hash="$(sha256sum apps/web/package-lock.json apps/web/package.json tooling/scripts/ci/run_in_consistent_container.sh | sha256sum | awk '{print $1}')"
frontend_lock_file="apps/web/node_modules/.package-lock.sha256"
case "__BOOTSTRAP_MODE__" in
  always)
    force_bootstrap=1
    ;;
  never)
    force_bootstrap=0
    skip_bootstrap=1
    ;;
  *)
    force_bootstrap=0
    ;;
esac
skip_bootstrap="${skip_bootstrap:-0}"
bootstrap_python() {
  if [[ "${skip_bootstrap}" == "1" ]]; then
    return 0
  fi
  if [[ -d "$UV_PROJECT_ENVIRONMENT" ]]; then
    if [[ ! -x "$UV_PROJECT_ENVIRONMENT/bin/python" ]] || ! "$UV_PROJECT_ENVIRONMENT/bin/python" - <<'PY' >/dev/null 2>&1
import pydantic.fields
import typing_extensions
PY
    then
      wipe_open_notebook_directory_contents "$UV_PROJECT_ENVIRONMENT"
    fi
  fi
  if [[ "${force_bootstrap}" == "1" ]] || [[ ! -x "$UV_PROJECT_ENVIRONMENT/bin/python" ]] || [[ ! -f "${python_lock_file}" ]] || [[ "$(cat "${python_lock_file}")" != "${python_lock_hash}" ]]; then
    uv sync --frozen --extra dev
    printf '%s' "${python_lock_hash}" > "${python_lock_file}"
  fi
}
bootstrap_frontend() {
  local install_browsers="${1:-1}"
  local attempt
  local browsers_ready=1
  local install_ok=0
  local node_modules_ready=1
  local frontend_cache_root="$HOME/bootstrap/apps-web-node-modules"
  local frontend_cache_dir="${frontend_cache_root}/${frontend_lock_hash}"
  local frontend_cache_lock="${frontend_cache_root}/.${frontend_lock_hash}.lock"
  local stale_lock_minutes="${FRONTEND_CACHE_LOCK_STALE_MINUTES:-15}"
  local lock_acquired=0
  if [[ "${skip_bootstrap}" == "1" ]]; then
    return 0
  fi
  mkdir -p "${frontend_cache_root}"

  frontend_binaries_ready() {
    local bin_root="$1"
    [[ -x "${bin_root}/.bin/vitest" ]] && [[ -x "${bin_root}/.bin/playwright" ]] && [[ -x "${bin_root}/.bin/biome" ]]
  }

  frontend_cache_has_binaries() {
    frontend_binaries_ready "${frontend_cache_dir}"
  }

  playwright_cache_has_browsers() {
    local chromium_ready=1
    local firefox_ready=1
    local webkit_ready=1

    if compgen -G "${PLAYWRIGHT_BROWSERS_PATH}/chromium_headless_shell-*" >/dev/null; then
      chromium_ready=0
    elif compgen -G "${PLAYWRIGHT_BROWSERS_PATH}/chromium_headless_shell-*/chrome-linux/headless_shell" >/dev/null; then
      chromium_ready=0
    fi

    if compgen -G "${PLAYWRIGHT_BROWSERS_PATH}/firefox-*" >/dev/null; then
      firefox_ready=0
    elif compgen -G "${PLAYWRIGHT_BROWSERS_PATH}/firefox-*/firefox/firefox" >/dev/null; then
      firefox_ready=0
    elif compgen -G "${PLAYWRIGHT_BROWSERS_PATH}/firefox-*/firefox" >/dev/null; then
      firefox_ready=0
    fi

    if compgen -G "${PLAYWRIGHT_BROWSERS_PATH}/webkit-*" >/dev/null; then
      webkit_ready=0
    elif compgen -G "${PLAYWRIGHT_BROWSERS_PATH}/webkit-*/pw_run.sh" >/dev/null; then
      webkit_ready=0
    fi

    [[ "${chromium_ready}" == "0" && "${firefox_ready}" == "0" && "${webkit_ready}" == "0" ]]
  }

  acquire_frontend_cache_lock() {
    while ! mkdir "${frontend_cache_lock}" 2>/dev/null; do
      if find "${frontend_cache_lock}" -maxdepth 0 -mmin "+${stale_lock_minutes}" >/dev/null 2>&1; then
        echo "frontend bootstrap clearing stale shared cache lock ${frontend_cache_lock}"
        rm -rf "${frontend_cache_lock}"
        continue
      fi
      echo "frontend bootstrap waiting for shared cache lock ${frontend_cache_lock}"
      sleep 2
    done
    lock_acquired=1
  }

  release_frontend_cache_lock() {
    if [[ "${lock_acquired}" == "1" ]]; then
      rmdir "${frontend_cache_lock}" 2>/dev/null || true
      lock_acquired=0
    fi
  }
  if ! frontend_binaries_ready "apps/web/node_modules"; then
    node_modules_ready=0
  fi
  if ! playwright_cache_has_browsers; then
    browsers_ready=0
  fi
  if [[ "${force_bootstrap}" == "1" ]] || [[ "${node_modules_ready}" == "0" ]] || [[ ! -f "${frontend_lock_file}" ]] || [[ "$(cat "${frontend_lock_file}")" != "${frontend_lock_hash}" ]]; then
    acquire_frontend_cache_lock
    if [[ "${force_bootstrap}" != "1" ]] && frontend_cache_has_binaries; then
      wipe_open_notebook_directory_contents "apps/web/node_modules"
      mkdir -p "apps/web/node_modules"
      cp -R "${frontend_cache_dir}/." "apps/web/node_modules/"
      install_ok=1
    else
      for attempt in 1 2; do
        wipe_open_notebook_directory_contents "apps/web/node_modules"
        if (
          cd apps/web
          npm ci --no-audit --no-fund
        ); then
          install_ok=1
          break
        fi
        echo "frontend bootstrap attempt ${attempt} failed; retrying npm ci"
        sleep 5
      done
    fi
    if [[ "${install_ok}" != "1" ]]; then
      release_frontend_cache_lock
      echo "frontend bootstrap failed after 2 npm ci attempts" >&2
      exit 1
    fi
    if ! frontend_binaries_ready "apps/web/node_modules"; then
      release_frontend_cache_lock
      echo "frontend bootstrap did not produce expected node_modules executables" >&2
      exit 1
    fi
    if [[ "${force_bootstrap}" == "1" ]] || [[ ! -d "${frontend_cache_dir}" ]] || ! frontend_cache_has_binaries; then
      rm -rf "${frontend_cache_dir}"
      mkdir -p "${frontend_cache_dir}"
      cp -R "apps/web/node_modules/." "${frontend_cache_dir}/"
    fi
    mkdir -p apps/web/node_modules
    printf '%s' "${frontend_lock_hash}" > "${frontend_lock_file}"
    release_frontend_cache_lock
    browsers_ready=0
  fi
  if [[ "${install_browsers}" != "1" ]]; then
    return 0
  fi
  if [[ "${browsers_ready}" == "0" ]]; then
    (
      cd apps/web
      npx playwright install chromium firefox webkit
    )
    if ! playwright_cache_has_browsers; then
      echo "frontend bootstrap did not provision the expected browser set into the shared Playwright cache" >&2
      exit 1
    fi
  fi
}
case "__BOOTSTRAP_PROFILE__" in
  minimal)
    ;;
  python)
    bootstrap_python
    ;;
  apps/web-static)
    bootstrap_frontend 0
    ;;
  apps/web)
    bootstrap_frontend 1
    ;;
  repo-fast)
    bootstrap_python
    bootstrap_frontend 0
    ;;
  full)
    bootstrap_python
    bootstrap_frontend 1
    ;;
esac
EOF

BOOTSTRAP_COMMAND="${BOOTSTRAP_PREAMBLE//__BOOTSTRAP_MODE__/${BOOTSTRAP_MODE}}"
BOOTSTRAP_COMMAND="${BOOTSTRAP_COMMAND//__BOOTSTRAP_PROFILE__/${BOOTSTRAP_PROFILE}}"
BOOTSTRAP_COMMAND="${BOOTSTRAP_COMMAND//__CONTAINER_MACHINE_CACHE_ROOT__/${CONTAINER_MACHINE_CACHE_ROOT}}"
BOOTSTRAP_COMMAND="${BOOTSTRAP_COMMAND//__CONTAINER_UV_CACHE_DIR__/${CONTAINER_UV_CACHE_DIR}}"

printf -v QUOTED_COMMAND '%q ' "$@"
INNER_COMMAND="${BOOTSTRAP_COMMAND} && ${QUOTED_COMMAND% }"

run_docker "${DOCKER_ARGS[@]}" "${IMAGE_NAME}" bash -lc "${INNER_COMMAND}"
