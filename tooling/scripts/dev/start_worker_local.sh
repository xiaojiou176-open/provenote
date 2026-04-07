#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tooling/scripts/dev/common.sh"

init_local_runtime_dirs "${ROOT_DIR}"
PID_FILE="${PID_DIR}/worker.pid"
LOG_FILE="${LOG_DIR}/worker.log"

run_common_startup_checks "${ROOT_DIR}" "uv"

if safe_process_prepare_pid_file "${PID_FILE}"; then
  existing_state=0
  echo "Worker is already running (pid=$(cat "${PID_FILE}"))."
  exit 0
else
  existing_state=$?
fi
if [[ "${existing_state}" -eq 2 ]]; then
  exit 1
fi

cd "${ROOT_DIR}"
echo "Starting worker ..."
nohup bash tooling/scripts/runtime/run_uv_managed.sh run --env-file .env surreal-commands-worker --import-modules services.worker >"${LOG_FILE}" 2>&1 &
worker_pid=$!
safe_process_write_record "${PID_FILE}" "${worker_pid}" "worker" "surreal-commands-worker --import-modules services.worker" "${ROOT_DIR}"

sleep 2
if kill -0 "${worker_pid}" >/dev/null 2>&1; then
  echo "Worker started (pid=${worker_pid})"
  echo "Log: ${LOG_FILE}"
  exit 0
fi

echo "ERROR: Worker failed to start."
tail -n 80 "${LOG_FILE}" || true
safe_process_remove_record "${PID_FILE}"
exit 1
