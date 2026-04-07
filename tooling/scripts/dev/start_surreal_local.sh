#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tooling/scripts/dev/common.sh"

init_local_runtime_dirs "${ROOT_DIR}"
PID_FILE="${PID_DIR}/surrealdb.pid"
LOG_FILE="${LOG_DIR}/surrealdb.log"

run_common_startup_checks "${ROOT_DIR}"

SURREAL_BIN="${SURREAL_BIN:-surreal}"
SURREAL_BIND="${SURREAL_BIND:-127.0.0.1:8000}"
SURREAL_USER="${SURREAL_USER:-root}"
SURREAL_PASSWORD="${SURREAL_PASSWORD:-root}"
SURREAL_DATA_PATH="${SURREAL_DATA_PATH:-${RUNTIME_DIR}/surrealdb/packages.core.db}"
SURREAL_LOG_LEVEL="${SURREAL_LOG_LEVEL:-info}"

check_port() {
  local host="$1"
  local port="$2"
  if command -v nc >/dev/null 2>&1; then
    nc -z "${host}" "${port}" >/dev/null 2>&1
  else
    (echo >"/dev/tcp/${host}/${port}") >/dev/null 2>&1
  fi
}

wait_for_port() {
  local host="$1"
  local port="$2"
  local max_retries="${3:-30}"
  local interval="${4:-1}"

  for _ in $(seq 1 "${max_retries}"); do
    if check_port "${host}" "${port}"; then
      return 0
    fi
    sleep "${interval}"
  done
  return 1
}

if safe_process_prepare_pid_file "${PID_FILE}"; then
  existing_state=0
  echo "SurrealDB is already running (pid=$(cat "${PID_FILE}"))."
  exit 0
else
  existing_state=$?
fi
if [[ "${existing_state}" -eq 2 ]]; then
  exit 1
fi

if ! command -v "${SURREAL_BIN}" >/dev/null 2>&1; then
  echo "ERROR: '${SURREAL_BIN}' not found. Install SurrealDB CLI first."
  exit 1
fi

mkdir -p "$(dirname "${SURREAL_DATA_PATH}")"

probe_host="${SURREAL_BIND%:*}"
probe_port="${SURREAL_BIND##*:}"
if [[ "${probe_host}" == "0.0.0.0" ]]; then
  probe_host="127.0.0.1"
fi

safe_process_require_port_free "${probe_port}" "SurrealDB"

echo "Starting SurrealDB at ${SURREAL_BIND} ..."
nohup "${SURREAL_BIN}" start \
  --log "${SURREAL_LOG_LEVEL}" \
  --user "${SURREAL_USER}" \
  --pass "${SURREAL_PASSWORD}" \
  --bind "${SURREAL_BIND}" \
  "rocksdb:${SURREAL_DATA_PATH}" \
  >"${LOG_FILE}" 2>&1 &

surreal_pid=$!
safe_process_write_record "${PID_FILE}" "${surreal_pid}" "surrealdb" "${SURREAL_BIN} start" "${ROOT_DIR}" "${probe_port}"

if wait_for_port "${probe_host}" "${probe_port}" 40 1; then
  echo "SurrealDB started (pid=${surreal_pid})"
  echo "Log: ${LOG_FILE}"
  exit 0
fi

echo "ERROR: SurrealDB failed to start."
tail -n 80 "${LOG_FILE}" || true
kill "${surreal_pid}" >/dev/null 2>&1 || true
safe_process_remove_record "${PID_FILE}"
exit 1
