#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
MODE="${1:-all}"

run_lint() {
  echo "[consistent-env] lint checks"
  cd "${ROOT_DIR}"
  bash tooling/scripts/runtime/run_uv_managed.sh run ruff check .
  bash tooling/scripts/runtime/run_uv_managed.sh run python -m mypy .
  (cd apps/web && npm run lint)
}

run_test() {
  echo "[consistent-env] non-live test gate"
  cd "${ROOT_DIR}"
  make quality-fast
}

run_live() {
  if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    echo "ERROR: set GEMINI_API_KEY before running live checks"
    exit 1
  fi

  echo "[consistent-env] live checks"
  cd "${ROOT_DIR}"
  make quality-live
}

case "${MODE}" in
  lint)
    run_lint
    ;;
  test)
    run_test
    ;;
  live)
    run_live
    ;;
  all)
    run_lint
    run_test
    run_live
    ;;
  *)
    echo "Usage: bash tooling/scripts/dev/run_consistent_env_gate.sh [lint|test|live|all]"
    exit 2
    ;;
esac
