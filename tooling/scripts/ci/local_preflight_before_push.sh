#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"

MODE="fast"
RUN_HEAVY_LOCAL="${RUN_HEAVY_LOCAL:-0}"

usage() {
  cat <<'USAGE'
Usage: tooling/scripts/ci/local_preflight_before_push.sh [--mode full|fast]

Policy:
  - Default mode is fast for the lighter repo-owned pre-push rehearsal path.
  - Use `--mode full` when you explicitly want the stricter local push rehearsal.
  - Always run local unified gate first (fast/full).
  - If apps/web/runtime high-risk paths changed, run extra local smoke checks
    before pushing to remote CI.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[local-preflight] ERROR: unknown argument '$1'"
      usage
      exit 1
      ;;
  esac
done

if [[ "${MODE}" != "fast" && "${MODE}" != "full" ]]; then
  echo "[local-preflight] ERROR: --mode must be fast or full"
  exit 1
fi

if [[ "${OPEN_NOTEBOOK_CI_IN_CONTAINER:-0}" != "1" && "${OPEN_NOTEBOOK_CI_HOST_BYPASS:-0}" != "1" ]]; then
  CONTAINER_PROFILE="full"
  if [[ "${MODE}" == "fast" ]]; then
    CONTAINER_PROFILE="repo-fast"
  fi
  echo "[local-preflight] Re-executing inside repo CI container (set OPEN_NOTEBOOK_CI_HOST_BYPASS=1 to force host mode)."
  exec bash tooling/scripts/ci/run_in_consistent_container.sh --profile "${CONTAINER_PROFILE}" -- \
    env OPEN_NOTEBOOK_CI_IN_CONTAINER=1 OPEN_NOTEBOOK_PREPUSH_HOOK_CONTEXT="${OPEN_NOTEBOOK_PREPUSH_HOOK_CONTEXT:-}" \
      bash tooling/scripts/ci/local_preflight_before_push.sh --mode "${MODE}"
fi

OPEN_NOTEBOOK_PREPUSH_HOOK_CONTEXT="${OPEN_NOTEBOOK_PREPUSH_HOOK_CONTEXT:-0}"
export OPEN_NOTEBOOK_PREPUSH_HOOK_CONTEXT

collect_changed_files() {
  local upstream_ref=""
  local merge_base=""
  local fallback_ref=""

  if upstream_ref="$(git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null)"; then
    merge_base="$(git merge-base HEAD "${upstream_ref}" 2>/dev/null || true)"
    if [[ -n "${merge_base}" ]]; then
      git diff --name-only --diff-filter=ACMR "${merge_base}..HEAD"
      return
    fi
  fi

  for ref in origin/main origin/master main master; do
    if git rev-parse --verify --quiet "${ref}" >/dev/null 2>&1; then
      fallback_ref="${ref}"
      break
    fi
    if git rev-parse --verify --quiet "refs/remotes/${ref}" >/dev/null 2>&1; then
      fallback_ref="refs/remotes/${ref}"
      break
    fi
  done

  if [[ -n "${fallback_ref}" ]]; then
    merge_base="$(git merge-base HEAD "${fallback_ref}" 2>/dev/null || true)"
    if [[ -n "${merge_base}" ]]; then
      git diff --name-only --diff-filter=ACMR "${merge_base}..HEAD"
      return
    fi
  fi

  git diff-tree --no-commit-id --name-only -r HEAD --diff-filter=ACMR
}

echo "[local-preflight] Step 1/3: running local unified gate (${MODE})"
make guard-all GUARD_MODE="${MODE}"

NEED_FRONTEND_E2E=0
NEED_REAL_BACKEND_SMOKE=0

while IFS= read -r file; do
  [[ -n "${file}" ]] || continue
  case "${file}" in
    apps/web/**)
      NEED_FRONTEND_E2E=1
      ;;
  esac
  case "${file}" in
    api/**|packages/core/**|services/worker/**|tooling/scripts/ci/**|.github/workflows/test.yml|apps/web/e2e/real-backend-smoke.spec.ts|apps/web/src/app/\(dashboard\)/search/**|apps/web/src/app/\(dashboard\)/notebooks/**)
      NEED_REAL_BACKEND_SMOKE=1
      ;;
  esac
done < <(collect_changed_files)

if [[ "${MODE}" == "full" || "${RUN_HEAVY_LOCAL}" == "1" ]]; then
  if [[ "${NEED_FRONTEND_E2E}" -eq 1 ]]; then
    echo "[local-preflight] Step 2/3: apps/web changed, running chromium E2E smoke"
    make test-e2e-chromium
  else
    echo "[local-preflight] Step 2/3: apps/web unchanged, skip chromium E2E smoke"
  fi
else
  echo "[local-preflight] Step 2/3: fast mode skips local chromium E2E smoke (enforced in remote CI required-green gate)"
fi

if [[ "${MODE}" == "full" || "${RUN_HEAVY_LOCAL}" == "1" ]] && [[ "${NEED_REAL_BACKEND_SMOKE}" -eq 1 ]]; then
  echo "[local-preflight] Step 3/3: high-risk paths changed, running real backend smoke"
  make test-e2e-real-smoke
elif [[ "${MODE}" == "full" || "${RUN_HEAVY_LOCAL}" == "1" ]]; then
  echo "[local-preflight] Step 3/3: no high-risk backend/e2e path changed, skip real backend smoke"
else
  echo "[local-preflight] Step 3/3: fast mode skips local real-backend smoke (enforced in remote CI required-green gate)"
fi

echo "[local-preflight] PASS: local preflight completed, safe to push remote CI."
