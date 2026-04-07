#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT_DIR}/tooling/scripts/dev/common.sh"
init_local_runtime_dirs "${ROOT_DIR}"

pid_file_for_service() {
  local service="$1"
  case "${service}" in
    apps/web|web|frontend)
      printf '%s/apps/web.pid' "${PID_DIR}"
      ;;
    worker)
      printf '%s/worker.pid' "${PID_DIR}"
      ;;
    api|services.api)
      printf '%s/services.api.pid' "${PID_DIR}"
      ;;
    surrealdb|db|database)
      printf '%s/surrealdb.pid' "${PID_DIR}"
      ;;
    *)
      return 1
      ;;
  esac
}

stop_selected_services() {
  local status=0
  local service pid_file label

  if [[ "$#" -eq 0 ]]; then
    set -- "apps/web" "worker" "api" "surrealdb"
  fi

  for service in "$@"; do
    if ! pid_file="$(pid_file_for_service "${service}")"; then
      echo "Unknown service name: ${service}" >&2
      status=1
      continue
    fi
    case "${service}" in
      apps/web|web|frontend)
        label="apps/web"
        ;;
      api|services.api)
        label="api"
        ;;
      surrealdb|db|database)
        label="surrealdb"
        ;;
      *)
        label="${service}"
        ;;
    esac
    if [[ ! -f "${pid_file}" ]]; then
      echo "${label}: no pid file"
      continue
    fi
    safe_process_stop_recorded "${pid_file}" "${label}" 10 || status=1
  done

  return "${status}"
}

stop_selected_services "$@"

echo "Local services stop sequence completed."
