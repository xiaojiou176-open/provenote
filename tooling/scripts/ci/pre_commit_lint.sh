#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"
# shellcheck source=/dev/null
source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"
MACHINE_CACHE_ROOT="$(resolve_open_notebook_machine_cache_root)"
UV_PROJECT_ENVIRONMENT="$(resolve_open_notebook_repo_managed_uv_environment "${ROOT_DIR}")"
export UV_PROJECT_ENVIRONMENT
export SETUPTOOLS_EGG_BASE="${ROOT_DIR}/.runtime-cache/build/egg-info"
ensure_open_notebook_machine_cache_layout "${MACHINE_CACHE_ROOT}"
mkdir -p "${ROOT_DIR}/.runtime-cache/build/egg-info"

MODE="staged"
if [[ "${1:-}" == "--mode" ]]; then
  MODE="${2:-}"
  shift 2 || true
fi
if [[ "$MODE" != "staged" && "$MODE" != "runtime" ]]; then
  echo "[pre-commit-lint] Usage: $(basename "$0") [--mode staged|runtime] [files...]" >&2
  exit 2
fi

declare -a PY_FILES=()
declare -a RUFF_FILES=()
declare -a FRONTEND_FILES=()
declare -a MYPY_FILES=()
declare -a FRONTEND_LINT_FILES=()
declare -a CANDIDATE_FILES=()

is_mypy_excluded() {
  local path="$1"
  [[ "$path" == tests/* || "$path" == mutants/* ]]
}

is_ruff_excluded() {
  local path="$1"
  [[ "$path" == mutants/* ]]
}

run_runtime_gate() {
  local -a runtime_paths=()
  local -a python_candidates=("services/api" "services/worker" "packages/core" "packages/prompts" "tooling/scripts")
  local candidate=""

  if [[ -x "${UV_PROJECT_ENVIRONMENT}/bin/python" ]]; then
    if ! "${UV_PROJECT_ENVIRONMENT}/bin/python" -c "import typing_extensions, mypy" >/dev/null 2>&1; then
      echo "[pre-commit-lint] Runtime scope: managed env probe failed, rebuilding ${UV_PROJECT_ENVIRONMENT}"
      if ! wipe_open_notebook_directory_contents "${UV_PROJECT_ENVIRONMENT}"; then
        echo "[pre-commit-lint] Runtime scope: failed to clear managed env contents at ${UV_PROJECT_ENVIRONMENT}" >&2
        exit 1
      fi
    fi
  fi

  echo "[pre-commit-lint] Runtime scope: sync managed Python env"
  bash tooling/scripts/runtime/run_uv_managed.sh sync --frozen --extra dev

  for candidate in "${python_candidates[@]}"; do
    if [[ -d "${candidate}" ]] && find "${candidate}" -type f -name '*.py' -print -quit | grep -q .; then
      runtime_paths+=("${candidate}")
    fi
  done

  if [[ ${#runtime_paths[@]} -gt 0 ]]; then
    echo "[pre-commit-lint] Runtime scope: ruff on ${runtime_paths[*]}"
    bash tooling/scripts/runtime/run_uv_managed.sh run ruff check "${runtime_paths[@]}"
    echo "[pre-commit-lint] Runtime scope: mypy on ${runtime_paths[*]}"
    bash tooling/scripts/runtime/run_uv_managed.sh run --extra dev python -m mypy "${runtime_paths[@]}"
  fi
  echo "[pre-commit-lint] Runtime scope: observability logging gate"
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_observability_log_gate.py
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_sensitive_surface_guard.py
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_entrypoint_contract.py
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_space_surfaces.py
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_host_process_safety.py
  node tooling/scripts/ci/check_frontend_log_schema_sync.mjs
  node tooling/scripts/ci/check_frontend_layer_boundaries.mjs
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_api_contract_drift.py
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_upstream_compatibility_matrix_sync.py

  if [[ -f "apps/web/package.json" ]]; then
    echo "[pre-commit-lint] Runtime scope: apps/web lint (biome)"
    (
      cd apps/web
      npm run lint
    )
    echo "[pre-commit-lint] Runtime scope: apps/web shared logging contract"
    bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_logging_contract.py
    node tooling/scripts/ci/check_frontend_log_schema_sync.mjs
    node tooling/scripts/ci/check_frontend_layer_boundaries.mjs
  fi
}

for path in "$@"; do
  [[ -z "$path" ]] && continue
  CANDIDATE_FILES+=("$path")
  if [[ "$path" == *.py ]]; then
    PY_FILES+=("$path")
    if ! is_ruff_excluded "$path"; then
      RUFF_FILES+=("$path")
    fi
    if ! is_mypy_excluded "$path"; then
      MYPY_FILES+=("$path")
    fi
  fi
  if [[ "$path" == apps/web/* ]]; then
    FRONTEND_FILES+=("$path")
  fi
done

if [[ "$MODE" == "runtime" ]]; then
  run_runtime_gate
  echo "[pre-commit-lint] PASSED"
  exit 0
fi

if [[ ${#CANDIDATE_FILES[@]} -eq 0 ]]; then
  while IFS= read -r staged_path; do
    [[ -z "$staged_path" ]] && continue
    CANDIDATE_FILES+=("$staged_path")
    if [[ "$staged_path" == *.py ]]; then
      PY_FILES+=("$staged_path")
      if ! is_ruff_excluded "$staged_path"; then
        RUFF_FILES+=("$staged_path")
      fi
      if ! is_mypy_excluded "$staged_path"; then
        MYPY_FILES+=("$staged_path")
      fi
    fi
    if [[ "$staged_path" == apps/web/* ]]; then
      FRONTEND_FILES+=("$staged_path")
    fi
  done < <(git diff --cached --name-only --diff-filter=ACMRTUXB)
fi

if [[ ${#CANDIDATE_FILES[@]} -eq 0 ]]; then
  echo "[pre-commit-lint] No staged files, skip."
  echo "[pre-commit-lint] PASSED"
  exit 0
fi

echo "[pre-commit-lint] Running host-process safety gate on ${#CANDIDATE_FILES[@]} staged file(s)"
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_host_process_safety.py --paths "${CANDIDATE_FILES[@]}"

echo "[pre-commit-lint] Running sensitive surface guard on ${#CANDIDATE_FILES[@]} staged file(s)"
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_sensitive_surface_guard.py --paths "${CANDIDATE_FILES[@]}"

if [[ ${#RUFF_FILES[@]} -gt 0 ]]; then
  echo "[pre-commit-lint] Running Python lint gate (ruff) on ${#RUFF_FILES[@]} staged file(s)"
  bash tooling/scripts/runtime/run_uv_managed.sh run ruff check "${RUFF_FILES[@]}"
fi

if [[ ${#MYPY_FILES[@]} -gt 0 ]]; then
  echo "[pre-commit-lint] Running Python type gate (mypy) on ${#MYPY_FILES[@]} staged runtime file(s)"
  bash tooling/scripts/runtime/run_uv_managed.sh run --extra dev python -m mypy "${MYPY_FILES[@]}"
else
  if [[ ${#PY_FILES[@]} -gt 0 ]]; then
    echo "[pre-commit-lint] Skipping mypy for staged test/mutation-only Python files (tests/**, mutants/**)"
  fi
fi

if [[ ${#PY_FILES[@]} -gt 0 ]]; then
  echo "[pre-commit-lint] Running observability logging gate on staged Python files"
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_observability_log_gate.py --paths "${PY_FILES[@]}"
fi

if [[ ${#FRONTEND_FILES[@]} -gt 0 && -f "apps/web/package.json" ]]; then
  for path in "${FRONTEND_FILES[@]}"; do
    rel_path="${path#apps/web/}"
    [[ "$rel_path" == "$path" ]] && continue
    case "$rel_path" in
      src/*|e2e/*|e2e-live/*)
        case "$rel_path" in
          *.js|*.jsx|*.ts|*.tsx|*.mjs|*.cjs)
            FRONTEND_LINT_FILES+=("$rel_path")
            ;;
        esac
        ;;
    esac
  done

  if [[ ${#FRONTEND_LINT_FILES[@]} -gt 0 ]]; then
    echo "[pre-commit-lint] Running apps/web lint gate (biome) on ${#FRONTEND_LINT_FILES[@]} staged apps/web file(s)"
    (
      cd apps/web
      npx @biomejs/biome check "${FRONTEND_LINT_FILES[@]}"
    )
  else
    echo "[pre-commit-lint] No lintable apps/web staged files under apps/web/src|e2e|e2e-live, skip apps/web eslint gate."
  fi

  echo "[pre-commit-lint] Running apps/web shared logging contract on staged apps/web file(s)"
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_logging_contract.py --paths "${FRONTEND_FILES[@]}"
fi

echo "[pre-commit-lint] PASSED"
