#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"
# shellcheck source=/dev/null
source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"
RUNTIME_CACHE_DIR="$(resolve_open_notebook_repo_runtime_cache_dir "${ROOT_DIR}")"
MACHINE_CACHE_ROOT="$(resolve_open_notebook_machine_cache_root)"
REPO_CI_CACHE_ROOT="$(resolve_open_notebook_repo_ci_cache_root "${ROOT_DIR}")"
MACHINE_CI_NPM_CACHE_DIR="$(resolve_open_notebook_machine_ci_npm_cache_dir "${MACHINE_CACHE_ROOT}")"
REPO_MANAGED_UV_ENV="$(resolve_open_notebook_repo_managed_uv_environment "${ROOT_DIR}")"
MACHINE_UV_CACHE_DIR="$(resolve_open_notebook_machine_uv_cache_dir "${MACHINE_CACHE_ROOT}")"
PLAYWRIGHT_MACHINE_CACHE_DIR="$(resolve_open_notebook_machine_playwright_cache_dir "${MACHINE_CACHE_ROOT}")"
export OPEN_NOTEBOOK_MACHINE_CACHE_ROOT="${MACHINE_CACHE_ROOT}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-${MACHINE_UV_CACHE_DIR}}"

MODE="${1:-full}"
if [[ "${MODE}" != "fast" && "${MODE}" != "full" ]]; then
  echo "Usage: $(basename "$0") [fast|full]" >&2
  exit 1
fi

sanitize_runtime_env() {
  local blocked_vars=(
    OPENAI_API_KEY ANTHROPIC_API_KEY GROQ_API_KEY
    MISTRAL_API_KEY DEEPSEEK_API_KEY XAI_API_KEY OPENROUTER_API_KEY VOYAGE_API_KEY
    ELEVENLABS_API_KEY OLLAMA_API_BASE OLLAMA_BASE_URL VERTEX_PROJECT VERTEX_LOCATION
    GOOGLE_APPLICATION_CREDENTIALS AZURE_OPENAI_API_KEY AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_API_VERSION AZURE_OPENAI_ENDPOINT_LLM AZURE_OPENAI_ENDPOINT_EMBEDDING
    AZURE_OPENAI_ENDPOINT_STT AZURE_OPENAI_ENDPOINT_TTS OPENAI_COMPATIBLE_BASE_URL
    OPENAI_COMPATIBLE_API_KEY OPENAI_COMPATIBLE_BASE_URL_LLM OPENAI_COMPATIBLE_BASE_URL_EMBEDDING
    OPENAI_COMPATIBLE_BASE_URL_STT OPENAI_COMPATIBLE_BASE_URL_TTS
    API_BASE_URL
  )
  local key
  for key in "${blocked_vars[@]}"; do
    unset "${key}" || true
  done
}

restore_runtime_cache_layout() {
  ensure_open_notebook_machine_cache_layout "${MACHINE_CACHE_ROOT}"
  mkdir -p \
    .runtime-cache/build/egg-info \
    .runtime-cache/ci-host/bootstrap \
    .runtime-cache/ci-host/home-cache \
    .runtime-cache/ci-host/home-local \
    .runtime-cache/ci-host/tmp \
    .runtime-cache/locks \
    .runtime-cache/runs/current/logs/ci \
    .runtime-cache/runs/current/logs/local \
    .runtime-cache/local/pids \
    .runtime-cache/local/state \
    .runtime-cache/test/hypothesis \
    .runtime-cache/test/coverage/backend \
    .runtime-cache/test/coverage/apps/web \
    .runtime-cache/runs/current/evidence/playwright/report \
    .runtime-cache/runs/current/evidence/playwright/results \
    .runtime-cache/runs/current/reports/test-retry \
    .runtime-cache/runs/current/evidence
  mkdir -p "${UV_CACHE_DIR}"

  if [[ -n "${HOME:-}" ]]; then
    mkdir -p "${HOME}"
    if [[ -e "${HOME}/.cache" && ! -d "${HOME}/.cache" ]]; then
      rm -f "${HOME}/.cache"
    fi
    if [[ -e "${HOME}/.npm" && ! -d "${HOME}/.npm" ]]; then
      rm -f "${HOME}/.npm"
    fi
    mkdir -p "${HOME}/.cache"
    mkdir -p "${HOME}/.npm"
  fi

  if [[ -n "${TMPDIR:-}" ]]; then
    mkdir -p "${TMPDIR}"
  elif [[ -n "${HOME:-}" ]]; then
    mkdir -p "${HOME}/tmp"
  fi

  if [[ -n "${PRE_COMMIT_HOME:-}" ]]; then
    mkdir -p "${PRE_COMMIT_HOME}"
  fi

  if [[ -n "${NPM_CONFIG_CACHE:-}" ]]; then
    mkdir -p "${NPM_CONFIG_CACHE}"
  fi
}

if [[ "${OPEN_NOTEBOOK_SKIP_CACHE_WIPE_GATE:-0}" == "1" ]]; then
  echo "[cache-wipe-rebuild] skip requested via OPEN_NOTEBOOK_SKIP_CACHE_WIPE_GATE=1"
  exit 0
fi

echo "[cache-wipe-rebuild] deleting .runtime-cache before rebuild validation"
wipe_open_notebook_runtime_cache_contents "${RUNTIME_CACHE_DIR}"
restore_runtime_cache_layout

echo "[cache-wipe-rebuild] rerunning unified gate (${MODE}) with recursion disabled"
sanitize_runtime_env
if [[ "${OPEN_NOTEBOOK_CI_IN_CONTAINER:-0}" == "1" ]]; then
  export OPEN_NOTEBOOK_MACHINE_CACHE_ROOT="${MACHINE_CACHE_ROOT}"
  export HOME="${REPO_CI_CACHE_ROOT}/home-cache"
  export NPM_CONFIG_CACHE="${MACHINE_CI_NPM_CACHE_DIR}"
  export PRE_COMMIT_HOME="${HOME}/pre-commit"
  export TMPDIR="${REPO_CI_CACHE_ROOT}/tmp"
  UV_PROJECT_ENVIRONMENT="${REPO_MANAGED_UV_ENV}"
  export UV_PROJECT_ENVIRONMENT
  export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_MACHINE_CACHE_DIR}"
  mkdir -p "${HOME}" "${NPM_CONFIG_CACHE}" "${PRE_COMMIT_HOME}" "${TMPDIR}" "${PLAYWRIGHT_BROWSERS_PATH}"
  echo "[cache-wipe-rebuild] bootstrapping managed Python environment after cache wipe"
  bash tooling/scripts/runtime/run_uv_managed.sh sync --frozen --extra dev
  OPEN_NOTEBOOK_SKIP_CACHE_WIPE_GATE=1 bash tooling/scripts/ci/run_unified_test_gate.sh "${MODE}"
else
  if [[ -f "apps/web/package.json" ]]; then
    echo "[cache-wipe-rebuild] repairing apps/web host dependencies before recovery validation"
    (
      cd apps/web
      npm install --no-fund --no-audit
    )
  fi
  echo "[cache-wipe-rebuild] bootstrapping managed Python environment after cache wipe"
  bash tooling/scripts/runtime/run_uv_managed.sh sync --frozen --extra dev
  OPEN_NOTEBOOK_CI_HOST_BYPASS="${OPEN_NOTEBOOK_CI_HOST_BYPASS:-1}" \
    UV_OFFLINE="${UV_OFFLINE:-0}" \
    OPEN_NOTEBOOK_SKIP_CACHE_WIPE_GATE=1 \
    bash tooling/scripts/ci/run_unified_test_gate.sh "${MODE}"
fi

echo "[cache-wipe-rebuild] PASS: repo recovered after wiping .runtime-cache"
