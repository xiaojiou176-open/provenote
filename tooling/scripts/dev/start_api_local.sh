#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tooling/scripts/dev/common.sh"

init_local_runtime_dirs "${ROOT_DIR}"
PID_FILE="${PID_DIR}/services.api.pid"
LOG_FILE="${LOG_DIR}/services.api.log"

run_common_startup_checks "${ROOT_DIR}" "uv"

if safe_process_prepare_pid_file "${PID_FILE}"; then
  existing_state=0
  echo "API is already running (pid=$(cat "${PID_FILE}"))."
  exit 0
else
  existing_state=$?
fi
if [[ "${existing_state}" -eq 2 ]]; then
  exit 1
fi

api_host="${API_HOST:-127.0.0.1}"
api_port="${API_PORT:-5055}"
if [[ "${api_host}" == "0.0.0.0" ]]; then
  probe_host="127.0.0.1"
else
  probe_host="${api_host}"
fi
health_url="${API_HEALTH_URL:-http://${probe_host}:${api_port}/health}"

safe_process_require_port_free "${api_port}" "API"

echo "Starting API at ${api_host}:${api_port} ..."
cd "${ROOT_DIR}"
nohup bash tooling/scripts/runtime/run_uv_managed.sh run --env-file .env python tooling/bin/run_api.py >"${LOG_FILE}" 2>&1 &
api_pid=$!
safe_process_write_record "${PID_FILE}" "${api_pid}" "api" "tooling/bin/run_api.py" "${ROOT_DIR}" "${api_port}"

for _ in $(seq 1 45); do
  if curl -fsS "${health_url}" >/dev/null 2>&1; then
    echo "API started (pid=${api_pid})"
    echo "Health: ${health_url}"
    echo "Log: ${LOG_FILE}"
    exit 0
  fi
  sleep 1
done

echo "ERROR: API failed to become healthy."
tail -n 80 "${LOG_FILE}" || true
kill "${api_pid}" >/dev/null 2>&1 || true
safe_process_remove_record "${PID_FILE}"
exit 1
