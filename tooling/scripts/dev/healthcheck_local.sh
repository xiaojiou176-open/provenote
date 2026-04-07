#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT_DIR}/tooling/scripts/dev/common.sh"
init_local_runtime_dirs "${ROOT_DIR}"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "${ROOT_DIR}/.env"
  set +a
fi

API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-5055}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
SURREAL_URL="${SURREAL_URL:-ws://127.0.0.1:8000/rpc}"

if [[ "${API_HOST}" == "0.0.0.0" ]]; then
  API_HOST="127.0.0.1"
fi

surreal_host_port="$(printf '%s' "${SURREAL_URL}" | sed -E 's#^[a-z]+://##; s#/.*$##')"
surreal_host="${surreal_host_port%%:*}"
surreal_port="${surreal_host_port##*:}"
if [[ -z "${surreal_host}" || "${surreal_host}" == "${surreal_host_port}" ]]; then
  surreal_host="127.0.0.1"
  surreal_port="8000"
fi
if [[ "${surreal_host}" == "0.0.0.0" ]]; then
  surreal_host="127.0.0.1"
fi

check_port() {
  local host="$1"
  local port="$2"
  if command -v nc >/dev/null 2>&1; then
    nc -z "${host}" "${port}" >/dev/null 2>&1
  else
    (echo >"/dev/tcp/${host}/${port}") >/dev/null 2>&1
  fi
}

check_pid_record() {
  local pid_file="$1"
  safe_process_prepare_pid_file "${pid_file}" >/dev/null 2>&1
}

status=0

if check_port "${surreal_host}" "${surreal_port}" && check_pid_record "${PID_DIR}/surrealdb.pid"; then
  echo "[OK] SurrealDB  : ${surreal_host}:${surreal_port}"
else
  echo "[FAIL] SurrealDB: ${surreal_host}:${surreal_port}"
  status=1
fi

if curl -fsS "http://${API_HOST}:${API_PORT}/health" >/dev/null 2>&1 && check_pid_record "${PID_DIR}/services.api.pid"; then
  echo "[OK] API        : http://${API_HOST}:${API_PORT}/health"
else
  echo "[FAIL] API      : http://${API_HOST}:${API_PORT}/health"
  status=1
fi

if check_pid_record "${PID_DIR}/worker.pid"; then
  echo "[OK] Worker     : process alive"
else
  echo "[FAIL] Worker   : process not alive"
  status=1
fi

if curl -fsS "http://${FRONTEND_HOST}:${FRONTEND_PORT}" >/dev/null 2>&1 && check_pid_record "${PID_DIR}/apps/web.pid"; then
  echo "[OK] Frontend   : http://${FRONTEND_HOST}:${FRONTEND_PORT}"
else
  echo "[FAIL] Frontend : http://${FRONTEND_HOST}:${FRONTEND_PORT}"
  status=1
fi

exit "${status}"
