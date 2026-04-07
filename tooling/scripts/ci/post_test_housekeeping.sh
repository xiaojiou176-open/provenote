#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"
# shellcheck source=/dev/null
source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"
MACHINE_CACHE_ROOT="$(resolve_open_notebook_machine_cache_root)"
UV_PROJECT_ENVIRONMENT="$(resolve_open_notebook_repo_managed_uv_environment "${ROOT_DIR}")"
export UV_PROJECT_ENVIRONMENT
export SETUPTOOLS_EGG_BASE="${ROOT_DIR}/.runtime-cache/build/egg-info"
ensure_open_notebook_machine_cache_layout "${MACHINE_CACHE_ROOT}"
mkdir -p "${ROOT_DIR}/.runtime-cache/build/egg-info"

MAX_AGE_DAYS="${HOUSEKEEPING_MAX_AGE_DAYS:-7}"
RUNTIME_CACHE_MAX_MB="${HOUSEKEEPING_RUNTIME_CACHE_MAX_MB:-2048}"
LOGS_MAX_MB="${HOUSEKEEPING_LOGS_MAX_MB:-512}"
TARGET_USAGE_PERCENT="${HOUSEKEEPING_TARGET_USAGE_PERCENT:-80}"

DRY_RUN_CLEANUP=false
SKIP_DOCS_DRIFT=false
SKIP_UPSTREAM_CHECK=false
SKIP_FETCH=false
CLEANUP_ONLY=false
STRICT_UPSTREAM_CHECK="${HOUSEKEEPING_STRICT_UPSTREAM_CHECK:-false}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --cleanup-only            Only run runtime cleanup (cron/systemd friendly).
  --dry-run-cleanup         Run cleanup script in dry-run mode.
  --skip-docs-drift         Skip docs drift check.
  --skip-upstream-check     Skip upstream drift checks.
  --skip-fetch              Skip git fetch and run drift check with --no-fetch.
  --strict-upstream-check   Fail housekeeping when upstream drift check fails.
  --max-age-days N          Cleanup retention days (default: ${MAX_AGE_DAYS}).
  --runtime-cache-max-mb N  Runtime cache cap in MB (default: ${RUNTIME_CACHE_MAX_MB}).
  --logs-max-mb N           Logs cap in MB (default: ${LOGS_MAX_MB}).
  --target-usage-percent N  Cleanup target percent after trim (default: ${TARGET_USAGE_PERCENT}).
  -h, --help                Show this help message.
EOF
}

require_value() {
  local option="$1"
  local value="${2:-}"
  if [[ -z "$value" || "$value" == --* ]]; then
    echo "Missing value for ${option}" >&2
    exit 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cleanup-only)
      CLEANUP_ONLY=true
      shift
      ;;
    --dry-run-cleanup)
      DRY_RUN_CLEANUP=true
      shift
      ;;
    --skip-docs-drift)
      SKIP_DOCS_DRIFT=true
      shift
      ;;
    --skip-upstream-check)
      SKIP_UPSTREAM_CHECK=true
      shift
      ;;
    --skip-fetch)
      SKIP_FETCH=true
      shift
      ;;
    --strict-upstream-check)
      STRICT_UPSTREAM_CHECK=true
      shift
      ;;
    --max-age-days)
      require_value "$1" "${2:-}"
      MAX_AGE_DAYS="$2"
      shift 2
      ;;
    --runtime-cache-max-mb)
      require_value "$1" "${2:-}"
      RUNTIME_CACHE_MAX_MB="$2"
      shift 2
      ;;
    --logs-max-mb)
      require_value "$1" "${2:-}"
      LOGS_MAX_MB="$2"
      shift 2
      ;;
    --target-usage-percent)
      require_value "$1" "${2:-}"
      TARGET_USAGE_PERCENT="$2"
      shift 2
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

if [[ "$CLEANUP_ONLY" == true ]]; then
  SKIP_DOCS_DRIFT=true
  SKIP_UPSTREAM_CHECK=true
fi

if [[ "$DRY_RUN_CLEANUP" == true ]]; then
  echo "[housekeeping] cleanup execution inventory (repo-internal safe/cautious surfaces)"
  bash tooling/scripts/ops/audit_space_surfaces.sh \
    --cleanup-owner cleanup_runtime_cache.sh \
    --action-filter safe_clear,cautious_clear
fi

echo "[housekeeping] cleanup runtime cache"
cleanup_cmd=(
  bash tooling/scripts/ops/cleanup_runtime_cache.sh
  --max-age-days "$MAX_AGE_DAYS"
  --runtime-cache-max-mb "$RUNTIME_CACHE_MAX_MB"
  --logs-max-mb "$LOGS_MAX_MB"
  --target-usage-percent "$TARGET_USAGE_PERCENT"
)
if [[ "$DRY_RUN_CLEANUP" == true ]]; then
  cleanup_cmd+=(--dry-run)
fi
"${cleanup_cmd[@]}"

if [[ "$SKIP_DOCS_DRIFT" == false ]]; then
  echo "[housekeeping] check docs drift"
  if command -v uv >/dev/null 2>&1; then
    bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_env_contract_drift.py
    bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_render_freshness.py
  else
    echo "[housekeeping] uv not found, fallback to python3"
    python3 tooling/scripts/ci/check_env_contract_drift.py
    python3 tooling/scripts/ci/check_docs_render_freshness.py
  fi
fi

if [[ "$SKIP_UPSTREAM_CHECK" == false ]]; then
  echo "[housekeeping] check upstream drift"
  drift_cmd=(bash tooling/scripts/ci/check_upstream_drift.sh --branch main)
  if [[ "$SKIP_FETCH" == true ]]; then
    drift_cmd+=(--no-fetch)
  fi
  if [[ "$STRICT_UPSTREAM_CHECK" == true ]]; then
    drift_cmd+=(--strict-divergence)
  else
    drift_cmd+=(--no-strict-divergence)
  fi
  if [[ "$STRICT_UPSTREAM_CHECK" == true ]]; then
    "${drift_cmd[@]}"
  else
    if ! "${drift_cmd[@]}"; then
      echo "[housekeeping] warning: upstream drift check reported advisory drift for the current product-line branch; continuing because strict upstream housekeeping is disabled."
    fi
  fi
fi
