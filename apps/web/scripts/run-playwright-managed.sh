#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOT_DIR="$(cd "${APP_DIR}/../.." && pwd)"

# shellcheck source=/dev/null
source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"

MACHINE_CACHE_ROOT="$(resolve_open_notebook_machine_cache_root)"
if [[ -z "${PLAYWRIGHT_BROWSERS_PATH:-}" ]]; then
  PLAYWRIGHT_BROWSERS_PATH="$(resolve_open_notebook_machine_playwright_cache_dir "${MACHINE_CACHE_ROOT}")"
fi

auto_cleanup_machine_cache() {
  if [[ "${NOTEBOOKLAB_MACHINE_CACHE_AUTO_CLEAN:-1}" == "0" ]]; then
    return 0
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    return 0
  fi

  if ! python3 "${ROOT_DIR}/tooling/scripts/ops/cleanup_machine_cache.py" \
    --mode apply \
    --include-historical-candidates \
    --historical-max-age-days 0 >/dev/null; then
    echo "[run-playwright-managed] warn: machine-cache auto-clean failed; continuing" >&2
  fi
}

auto_cleanup_machine_cache
ensure_open_notebook_machine_cache_layout "${MACHINE_CACHE_ROOT}"
mkdir -p "${PLAYWRIGHT_BROWSERS_PATH}"

export PLAYWRIGHT_BROWSERS_PATH

cd "${APP_DIR}"
exec npx playwright "$@"
