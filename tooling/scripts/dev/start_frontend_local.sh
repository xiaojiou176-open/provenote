#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tooling/scripts/dev/common.sh"

init_local_runtime_dirs "${ROOT_DIR}"
PID_FILE="${PID_DIR}/apps/web.pid"
LOG_FILE="${LOG_DIR}/apps/web.log"
FRONTEND_DIR="${ROOT_DIR}/apps/web"

run_common_startup_checks "${ROOT_DIR}" "npm"

if safe_process_prepare_pid_file "${PID_FILE}"; then
  existing_state=0
  echo "Frontend is already running (pid=$(cat "${PID_FILE}"))."
  exit 0
else
  existing_state=$?
fi
if [[ "${existing_state}" -eq 2 ]]; then
  exit 1
fi

API_PORT="${API_PORT:-5055}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
API_URL="${API_URL:-http://127.0.0.1:${API_PORT}}"

safe_process_require_port_free "${FRONTEND_PORT}" "Frontend"

if [[ ! -d "${FRONTEND_DIR}/node_modules" ]]; then
  echo "apps/web/node_modules not found. Installing dependencies..."
  (cd "${FRONTEND_DIR}" && npm ci)
fi

echo "Starting apps/web at http://${FRONTEND_HOST}:${FRONTEND_PORT} ..."
pushd "${FRONTEND_DIR}" >/dev/null
nohup env \
  API_URL="${API_URL}" \
  npm run dev -- --hostname "${FRONTEND_HOST}" --port "${FRONTEND_PORT}" \
  >"${LOG_FILE}" 2>&1 &
frontend_pid=$!
popd >/dev/null
safe_process_write_record "${PID_FILE}" "${frontend_pid}" "apps/web" "npm run dev -- --hostname ${FRONTEND_HOST} --port ${FRONTEND_PORT}" "${FRONTEND_DIR}" "${FRONTEND_PORT}"

for _ in $(seq 1 60); do
  if curl -fsS "http://${FRONTEND_HOST}:${FRONTEND_PORT}" >/dev/null 2>&1; then
    echo "Frontend started (pid=${frontend_pid})"
    echo "Log: ${LOG_FILE}"
    exit 0
  fi
  sleep 1
done

echo "ERROR: Frontend failed to become healthy."
tail -n 80 "${LOG_FILE}" || true
kill "${frontend_pid}" >/dev/null 2>&1 || true
safe_process_remove_record "${PID_FILE}"
exit 1
