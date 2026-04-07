#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"
RUNTIME_CACHE_DIR="$(resolve_open_notebook_repo_runtime_cache_dir "${ROOT_DIR}")"
MACHINE_CACHE_ROOT="$(resolve_open_notebook_machine_cache_root)"
UV_PROJECT_ENVIRONMENT="$(resolve_open_notebook_repo_managed_uv_environment "${ROOT_DIR}")"
MACHINE_UV_CACHE_DIR="$(resolve_open_notebook_machine_uv_cache_dir "${MACHINE_CACHE_ROOT}")"
REPO_PYCACHE_DIR="$(resolve_open_notebook_repo_pycache_dir "${ROOT_DIR}")"
export OPEN_NOTEBOOK_MACHINE_CACHE_ROOT="${MACHINE_CACHE_ROOT}"
export UV_PROJECT_ENVIRONMENT
export UV_CACHE_DIR="${UV_CACHE_DIR:-${MACHINE_UV_CACHE_DIR}}"
export SETUPTOOLS_EGG_BASE="${RUNTIME_CACHE_DIR}/build/egg-info"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${REPO_PYCACHE_DIR}}"

usage() {
  cat <<'EOF'
Usage:
  bash tooling/scripts/runtime/run_uv_managed.sh sync [<uv sync args...>]
  bash tooling/scripts/runtime/run_uv_managed.sh run [<uv run args...>]

Examples:
  bash tooling/scripts/runtime/run_uv_managed.sh sync --frozen --extra dev
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_root_cleanliness.py --mode authoritative
EOF
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 1
fi

command="$1"
shift

ensure_open_notebook_machine_cache_layout "${MACHINE_CACHE_ROOT}"
mkdir -p "${RUNTIME_CACHE_DIR}/build/egg-info"
mkdir -p "${UV_CACHE_DIR}"
mkdir -p "${PYTHONPYCACHEPREFIX}"
cd "${ROOT_DIR}"

auto_cleanup_machine_cache() {
  if [[ "${PROVENOTE_MACHINE_CACHE_AUTO_CLEAN:-1}" == "0" ]]; then
    return 0
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "[run_uv_managed] skip machine-cache auto-clean: python3 not available" >&2
    return 0
  fi

  if ! python3 tooling/scripts/ops/cleanup_machine_cache.py \
    --mode apply \
    --include-historical-candidates \
    --historical-max-age-days 0 >/dev/null; then
    echo "[run_uv_managed] warn: machine-cache auto-clean failed; continuing" >&2
  fi
}

auto_cleanup_machine_cache

cleanup_legacy_root_outputs() {
  local egg_info_dir
  for egg_info_dir in \
    "${ROOT_DIR}/open_notebook.egg-info" \
    "${ROOT_DIR}/provenote.egg-info" \
    "${ROOT_DIR}/auditable_markdown_workbench.egg-info"; do
    find "${egg_info_dir}" -depth -delete 2>/dev/null || true
    rmdir "${egg_info_dir}" 2>/dev/null || true
  done
}

ensure_python_command_shim() {
  if command -v python >/dev/null 2>&1; then
    return 0
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    return 0
  fi

  local shim_dir="${RUNTIME_CACHE_DIR}/shim-bin"
  local python_shim="${shim_dir}/python"
  mkdir -p "${shim_dir}"
  if [[ ! -e "${python_shim}" ]]; then
    ln -s "$(command -v python3)" "${python_shim}" 2>/dev/null || true
  fi
  export PATH="${shim_dir}:${PATH}"
}

managed_env_probe_failed() {
  if [[ ! -x "${UV_PROJECT_ENVIRONMENT}/bin/python" ]]; then
    return 0
  fi

  if ! "${UV_PROJECT_ENVIRONMENT}/bin/python" - <<'PY' >/dev/null 2>&1
import pydantic.fields
import typing_extensions
PY
  then
    return 0
  fi

  return 1
}

if managed_env_probe_failed; then
  echo "[run_uv_managed] managed env probe failed, rebuilding ${UV_PROJECT_ENVIRONMENT}" >&2
  if ! wipe_open_notebook_directory_contents "${UV_PROJECT_ENVIRONMENT}"; then
    echo "[run_uv_managed] ERROR: failed to clear managed env contents at ${UV_PROJECT_ENVIRONMENT}" >&2
    exit 1
  fi
fi

ensure_python_command_shim

case "${command}" in
  sync)
    uv sync "$@"
    cleanup_legacy_root_outputs
    ;;
  run)
    uv run "$@"
    cleanup_legacy_root_outputs
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "Unknown command: ${command}" >&2
    usage >&2
    exit 1
    ;;
esac
