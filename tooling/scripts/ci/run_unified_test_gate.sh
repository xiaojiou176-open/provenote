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

MODE="${1:-fast}"
if [[ "$MODE" != "fast" && "$MODE" != "full" ]]; then
  echo "Usage: $(basename "$0") [fast|full]" >&2
  exit 1
fi

if [[ "${OPEN_NOTEBOOK_CI_IN_CONTAINER:-0}" != "1" && "${OPEN_NOTEBOOK_CI_HOST_BYPASS:-0}" != "1" ]]; then
  echo "[unified-test] Re-executing inside repo CI container (set OPEN_NOTEBOOK_CI_HOST_BYPASS=1 to force host mode)."
  exec bash tooling/scripts/ci/run_in_consistent_container.sh --profile full -- \
    env OPEN_NOTEBOOK_CI_IN_CONTAINER=1 OPEN_NOTEBOOK_EXTERNAL_PR_FAST_GATE="${OPEN_NOTEBOOK_EXTERNAL_PR_FAST_GATE:-}" \
      bash tooling/scripts/ci/run_unified_test_gate.sh "${MODE}"
fi

LONG_TESTS_PARALLEL="${LONG_TESTS_PARALLEL:-1}"
HEARTBEAT_INTERVAL_SECONDS="${HEARTBEAT_INTERVAL_SECONDS:-30}"
E2E_MAX_RETRIES="${E2E_MAX_RETRIES:-2}"
E2E_CHROMIUM_WORKERS="${E2E_CHROMIUM_WORKERS:-1}"
MUTATION_MAX_CHILDREN="${MUTATION_MAX_CHILDREN:-1}"
MUTATION_MIN_SCORE="${MUTATION_MIN_SCORE:-84}"
MUTATION_MAX_NO_TESTS="${MUTATION_MAX_NO_TESTS:-0}"
MUTATION_MAX_SURVIVED_REGRESSION="${MUTATION_MAX_SURVIVED_REGRESSION:-0}"
MUTATION_MAX_SCORE_REGRESSION="${MUTATION_MAX_SCORE_REGRESSION:-0}"
BACKEND_COVERAGE_SCOPE="${BACKEND_COVERAGE_SCOPE:-phase1}"
RUN_PERFORMANCE_BENCHMARKS="${RUN_PERFORMANCE_BENCHMARKS:-0}"
UV_OFFLINE="${UV_OFFLINE:-1}"
HYPOTHESIS_STORAGE_DIRECTORY="${HYPOTHESIS_STORAGE_DIRECTORY:-.runtime-cache/test/hypothesis}"
RUN_START_TS="$(date +%s)"
export UV_OFFLINE
export HYPOTHESIS_STORAGE_DIRECTORY

log() {
  local now
  now="$(date '+%Y-%m-%d %H:%M:%S')"
  echo "[unified-test][$now] $*"
}

announce_stage() {
  local stage_index="$1"
  local stage_total="$2"
  local stage_name="$3"
  local stage_pct
  stage_pct="$(( stage_index * 100 / stage_total ))"
  log "STAGE_PROGRESS: ${stage_index}/${stage_total} (${stage_pct}%) -> ${stage_name}"
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log "ERROR: required command not found: $cmd"
    exit 127
  fi
}

run_step() {
  local label="$1"
  shift

  local step_start step_end step_elapsed status
  step_start="$(date +%s)"
  log "START: $label"

  set +e
  "$@"
  status=$?
  set -e

  step_end="$(date +%s)"
  step_elapsed="$((step_end - step_start))"

  if [[ $status -ne 0 ]]; then
    log "FAILED: $label (exit=$status, elapsed=${step_elapsed}s)"
    exit "$status"
  fi
  log "DONE: $label (elapsed=${step_elapsed}s)"
}

run_long_with_heartbeat() {
  local label="$1"
  local command_str="$2"
  run_step "$label" bash tooling/scripts/ci/with_heartbeat.sh --label "$label" --interval "$HEARTBEAT_INTERVAL_SECONDS" -- \
    bash -lc "$command_str"
}

find_open_port_in_range() {
  local start="$1"
  local end="$2"
  local excluded="${3:-}"
  local port

  for ((port=start; port<=end; port+=1)); do
    if [[ -n "$excluded" && "$port" == "$excluded" ]]; then
      continue
    fi
    if command -v lsof >/dev/null 2>&1; then
      if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        continue
      fi
    elif command -v ss >/dev/null 2>&1; then
      if ss -ltn "( sport = :$port )" 2>/dev/null | tail -n +2 | grep -q .; then
        continue
      fi
    elif command -v netstat >/dev/null 2>&1; then
      if netstat -an 2>/dev/null | grep -E -q "[\\.:]${port}[[:space:]].*LISTEN"; then
        continue
      fi
    fi

    if PORT_RANGE_START="$port" PORT_RANGE_END="$port" PORT_RANGE_EXCLUDED="$excluded" node <<'NODE'
const net = require("node:net");

const start = Number(process.env.PORT_RANGE_START || "0");
const end = Number(process.env.PORT_RANGE_END || "0");
const excluded = Number(process.env.PORT_RANGE_EXCLUDED || "0");

if (!Number.isInteger(start) || !Number.isInteger(end) || start <= 0 || end < start) {
  process.exit(2);
}

const canBind = (port) =>
  new Promise((resolve) => {
    if (port === excluded) {
      resolve(false);
      return;
    }
    const server = net.createServer();
    server.unref();
    server.once("error", () => resolve(false));
    server.listen(port, "127.0.0.1", () => {
      server.close(() => resolve(true));
    });
  });

(async () => {
  for (let port = start; port <= end; port += 1) {
    if (await canBind(port)) {
      process.stdout.write(String(port));
      return;
    }
  }
  process.exit(1);
})();
NODE
    then
      return 0
    fi
  done
  return 1
}

run_parallel_pair() {
  local label_a="$1"
  local cmd_a="$2"
  local label_b="$3"
  local cmd_b="$4"
  local group_start_ts group_elapsed

  group_start_ts="$(date +%s)"
  log "Parallel start: ${label_a} + ${label_b}"

  bash -lc "$cmd_a" &
  local pid_a=$!
  bash -lc "$cmd_b" &
  local pid_b=$!

  set +e
  wait "$pid_a"
  local status_a=$?
  wait "$pid_b"
  local status_b=$?
  set -e
  group_elapsed="$(( $(date +%s) - group_start_ts ))"

  if [[ $status_a -ne 0 || $status_b -ne 0 ]]; then
    log "Parallel group failed: ${label_a}=${status_a}, ${label_b}=${status_b}, elapsed=${group_elapsed}s"
    exit 1
  fi

  log "Parallel done: ${label_a} + ${label_b} (elapsed=${group_elapsed}s)"
}

log "Bootstrapping: mode=${MODE}, long_tests_parallel=${LONG_TESTS_PARALLEL}, heartbeat_interval=${HEARTBEAT_INTERVAL_SECONDS}s, e2e_max_retries=${E2E_MAX_RETRIES}"
require_cmd bash
require_cmd uv
require_cmd npm

case "$BACKEND_COVERAGE_SCOPE" in
  phase0)
    BACKEND_COV_ARGS_STR="--cov=services.api.main --cov=packages.core.application.models --cov=services.api.routers.auditable_runs --cov=packages.core.auditable"
    ;;
  phase1)
    BACKEND_COV_ARGS_STR="--cov=services.api --cov=services.worker --cov=packages.core.ai --cov=packages.core.graphs --cov=packages.core.database --cov=packages.core.utils --cov=packages.core.auditable"
    ;;
  *)
    log "ERROR: unsupported BACKEND_COVERAGE_SCOPE='${BACKEND_COVERAGE_SCOPE}' (allowed: phase0|phase1)"
    exit 1
    ;;
esac
log "Coverage scope: backend=${BACKEND_COVERAGE_SCOPE}"
log "Coverage args: ${BACKEND_COV_ARGS_STR}"
if [[ "${RUN_PERFORMANCE_BENCHMARKS}" == "1" ]]; then
  PYTHON_CORE_IGNORE_PERF_ARGS=""
  log "Core python tests include performance benchmarks (RUN_PERFORMANCE_BENCHMARKS=1)"
else
  PYTHON_CORE_IGNORE_PERF_ARGS="--ignore=tests/performance"
  log "Core python tests skip performance benchmarks (set RUN_PERFORMANCE_BENCHMARKS=1 to include)"
fi

announce_stage 1 4 "commit gates (short checks first)"
run_step "test-smells-guard" bash tooling/scripts/ci/check_test_smells.sh
run_step "commit-authorship-range-guard" bash tooling/scripts/ci/check_commit_authorship_range.sh
run_step "lint-gate(runtime-scope)" bash tooling/scripts/ci/pre_commit_lint.sh --mode runtime
run_step "legacy-root-runtime-noise-cleanup" bash -lc 'find .pytest_cache .hypothesis .benchmarks .coverage .coverage.* -depth -delete 2>/dev/null || true'
run_step "root-cleanliness-guard" python3 tooling/scripts/ci/check_root_cleanliness.py --mode authoritative
run_step "sensitive-surface-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_sensitive_surface_guard.py
run_step "github-security-alerts-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_github_security_alerts.py
run_step "entrypoint-contract-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_entrypoint_contract.py
run_step "output-path-policy-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_output_path_policy.py
run_step "frontend-logging-contract-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_logging_contract.py
run_step "frontend-log-schema-sync" node tooling/scripts/ci/check_frontend_log_schema_sync.mjs
run_parallel_pair \
  "observability-log-gate" \
  "bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_observability_log_gate.py" \
  "env-governance-guard" \
  "bash tooling/scripts/ci/check_env_governance.sh"
run_parallel_pair \
  "log-contract-guard" \
  "bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_log_contract.py" \
  "log-sink-integrity-guard" \
  "bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_log_sink_integrity.py"
run_step "runtime-surfaces-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_runtime_surfaces.py
run_step "space-surfaces-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_space_surfaces.py
run_step "layer-boundaries-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_layer_boundaries.py
run_step "frontend-layer-boundaries-guard" node tooling/scripts/ci/check_frontend_layer_boundaries.mjs
run_parallel_pair \
  "secret-leak-guard" \
  "bash tooling/scripts/ci/check_secret_leaks.sh" \
  "sensitive-surface-guard" \
  "bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_sensitive_surface_guard.py"
run_parallel_pair \
  "navigation-docs-pair-guard" \
  "bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py"
run_step "openapi-contract-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_openapi_contract_drift.py
run_step "frontend-api-contract-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_api_contract_drift.py
run_parallel_pair \
  "env-contract-drift-guard" \
  "bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_env_contract_drift.py" \
  "docs-render-freshness-guard" \
  "bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_render_freshness.py"
run_step "path-truth-drift-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_path_truth_drift.py
run_step "snapshot-freshness-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_snapshot_freshness.py
run_step "open-source-surface-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_open_source_surface.py
run_step "public-identity-surface-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_public_identity_surface.py
run_step "provider-surface-truth-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_provider_surface_truth.py
run_step "selective-port-ledger-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_selective_port_ledger.py
run_step "legacy-provider-removal-ledger-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_legacy_provider_removal_ledger.py
run_step "legacy-provider-runtime-imports-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_legacy_provider_runtime_imports.py
run_step "podcasts-topology-mapping-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_podcasts_topology_mapping.py
run_parallel_pair \
  "docs-change-guard(pre-push-mode)" \
  "bash tooling/scripts/ci/check_docs_change_guard.sh --mode pre-push" \
  "workflow-policy-guard" \
  "bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_workflow_policy.py"
run_step "external-surfaces-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_external_surfaces.py
run_step "implicit-external-surface-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_no_implicit_external_surface.py
run_step "floating-external-input-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_no_floating_external_inputs.py
run_step "upstream-compatibility-matrix-guard" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_upstream_compatibility_matrix_sync.py

if [[ "$MODE" == "full" && "${OPEN_NOTEBOOK_SKIP_CACHE_WIPE_GATE:-0}" != "1" ]]; then
  run_step "cache-wipe-rebuild-guard" bash tooling/scripts/ci/check_cache_wipe_rebuild.sh fast
fi

if [[ "$MODE" == "fast" ]]; then
  announce_stage 2 4 "fast smoke in parallel"
  run_parallel_pair \
    "python-smoke" \
    "OPEN_NOTEBOOK_SKIP_MIGRATIONS=true bash tooling/scripts/runtime/run_uv_managed.sh run python -m pytest tests/test_ci_google_genai_usage.py tests/test_ci_file_length_guard.py tests/ci/test_gate_of_gates.py tests/test_uiux_gemini_evaluator.py tests/test_ci_uiux_gate.py tests/ci/test_artifact_evidence_contract.py -v" \
    "apps/web-smoke" \
    "cd apps/web && npm run test -- src/lib/config.test.ts src/lib/api/client.test.ts"

  announce_stage 4 4 "fast mode done (stage 3 skipped by design)"
  log "PASSED (mode=fast, total_elapsed=$(( $(date +%s) - RUN_START_TS ))s)"
  exit 0
fi

announce_stage 2 4 "core tests in parallel"
rm -f .coverage .coverage.* .runtime-cache/test/coverage/backend/coverage.xml .runtime-cache/test/coverage/apps/web/lcov.info
mkdir -p .runtime-cache/test/coverage/backend .runtime-cache/test/coverage/apps/web
run_parallel_pair \
  "python-core" \
  "OPEN_NOTEBOOK_SKIP_MIGRATIONS=true bash tooling/scripts/runtime/run_uv_managed.sh run python -m pytest tests/ -v -m 'not property and not live' ${PYTHON_CORE_IGNORE_PERF_ARGS} ${BACKEND_COV_ARGS_STR} --cov-branch --cov-fail-under=0 --cov-report=term-missing --cov-report=xml:.runtime-cache/test/coverage/backend/coverage.xml" \
  "apps/web-core" \
  "cd apps/web && FRONTEND_COVERAGE_SCOPE=${FRONTEND_COVERAGE_SCOPE:-phase0} npm run test:coverage"
run_step "coverage-thresholds(95/95)" \
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_coverage_thresholds.py --backend-xml .runtime-cache/test/coverage/backend/coverage.xml --frontend-lcov .runtime-cache/test/coverage/apps/web/lcov.info --backend-scope "${BACKEND_COVERAGE_SCOPE}"
run_step "apps/web-action-matrix" \
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_action_matrix.py

announce_stage 3 4 "long tests with heartbeat"
if [[ "${LONG_TESTS_PARALLEL}" == "1" ]]; then
  run_parallel_pair \
    "property-tests" \
    "bash tooling/scripts/ci/with_heartbeat.sh --label property-tests --interval ${HEARTBEAT_INTERVAL_SECONDS} -- bash -lc 'OPEN_NOTEBOOK_SKIP_MIGRATIONS=true bash tooling/scripts/runtime/run_uv_managed.sh run python -m pytest tests/property/ -v -m property'" \
    "mutation-tests" \
    "bash tooling/scripts/ci/with_heartbeat.sh --label mutation-tests --interval ${HEARTBEAT_INTERVAL_SECONDS} -- bash -lc 'bash tooling/scripts/ci/run_with_retry.sh --label mutation-tests --max-retries 1 --retry-on-logic-fail 1 -- bash -lc \"MUTATION_PROFILE=${MUTATION_PROFILE:-core} MUTATION_MAX_CHILDREN=${MUTATION_MAX_CHILDREN} MUTATION_MIN_SCORE=${MUTATION_MIN_SCORE} MUTATION_MAX_NO_TESTS=${MUTATION_MAX_NO_TESTS} MUTATION_MAX_SURVIVED_REGRESSION=${MUTATION_MAX_SURVIVED_REGRESSION} MUTATION_MAX_SCORE_REGRESSION=${MUTATION_MAX_SCORE_REGRESSION} bash tooling/scripts/ci/run_mutation_profile.sh\"'"
else
  run_long_with_heartbeat "property-tests" "OPEN_NOTEBOOK_SKIP_MIGRATIONS=true bash tooling/scripts/runtime/run_uv_managed.sh run python -m pytest tests/property/ -v -m property"
  run_long_with_heartbeat "mutation-tests" "bash tooling/scripts/ci/run_with_retry.sh --label mutation-tests --max-retries 1 --retry-on-logic-fail 1 -- bash -lc 'MUTATION_PROFILE=${MUTATION_PROFILE:-core} MUTATION_MAX_CHILDREN=${MUTATION_MAX_CHILDREN} MUTATION_MIN_SCORE=${MUTATION_MIN_SCORE} MUTATION_MAX_NO_TESTS=${MUTATION_MAX_NO_TESTS} MUTATION_MAX_SURVIVED_REGRESSION=${MUTATION_MAX_SURVIVED_REGRESSION} MUTATION_MAX_SCORE_REGRESSION=${MUTATION_MAX_SCORE_REGRESSION} bash tooling/scripts/ci/run_mutation_profile.sh'"
fi
PLAYWRIGHT_PORT_RANGE_START="${PLAYWRIGHT_PORT_RANGE_START:-3100}"
PLAYWRIGHT_PORT_RANGE_END="${PLAYWRIGHT_PORT_RANGE_END:-3499}"
PLAYWRIGHT_API_PORT_RANGE_START="${PLAYWRIGHT_API_PORT_RANGE_START:-5055}"
PLAYWRIGHT_API_PORT_RANGE_END="${PLAYWRIGHT_API_PORT_RANGE_END:-5455}"
E2E_PLAYWRIGHT_PORT="$(find_open_port_in_range "${PLAYWRIGHT_PORT_RANGE_START}" "${PLAYWRIGHT_PORT_RANGE_END}")" || {
  log "ERROR: failed to find open apps/web Playwright port in range ${PLAYWRIGHT_PORT_RANGE_START}-${PLAYWRIGHT_PORT_RANGE_END}"
  exit 1
}
E2E_PLAYWRIGHT_API_PORT="$(find_open_port_in_range "${PLAYWRIGHT_API_PORT_RANGE_START}" "${PLAYWRIGHT_API_PORT_RANGE_END}" "${E2E_PLAYWRIGHT_PORT}")" || {
  log "ERROR: failed to find open API Playwright port in range ${PLAYWRIGHT_API_PORT_RANGE_START}-${PLAYWRIGHT_API_PORT_RANGE_END}"
  exit 1
}
log "Selected isolated Playwright ports: apps/web=${E2E_PLAYWRIGHT_PORT}, api=${E2E_PLAYWRIGHT_API_PORT}"
run_long_with_heartbeat "e2e-chromium" "PLAYWRIGHT_PORT=${E2E_PLAYWRIGHT_PORT} PLAYWRIGHT_API_PORT=${E2E_PLAYWRIGHT_API_PORT} PLAYWRIGHT_REUSE_EXISTING_SERVER=0 bash tooling/scripts/ci/run_with_retry.sh --label e2e-chromium --max-retries ${E2E_MAX_RETRIES} -- bash -lc 'cd apps/web && npm run test:e2e:install && npm run test:e2e -- --project=chromium --workers=${E2E_CHROMIUM_WORKERS}'"

announce_stage 4 4 "housekeeping"
run_step "post-test-housekeeping" bash tooling/scripts/ci/post_test_housekeeping.sh --cleanup-only

log "PASSED (mode=full, total_elapsed=$(( $(date +%s) - RUN_START_TS ))s)"
