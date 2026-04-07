#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT_DIR}/tooling/scripts/dev/common.sh"
init_local_runtime_dirs "${ROOT_DIR}"

if [[ "$#" -eq 0 ]]; then
  echo "[port-release] usage: tooling/scripts/ci/release_local_ports.sh <port> [port...]"
  exit 1
fi

for port in "$@"; do
  if ! safe_process_port_is_listening "${port}"; then
    echo "[port-release] port ${port}: free"
    continue
  fi

  echo "[port-release] port ${port}: attempting repo-owned release via recorded pid metadata"
  safe_process_release_recorded_port "${PID_DIR}" "${port}" 10 || true

  if safe_process_port_is_listening "${port}"; then
    echo "[port-release] ERROR: port ${port} is occupied by unowned or non-cooperative listener(s); refusing to stop them"
    while IFS= read -r line; do
      [[ -z "${line}" ]] && continue
      echo "[port-release]   ${line}"
    done < <(safe_process_port_listener_summary "${port}")
    exit 1
  fi

  echo "[port-release] port ${port}: released"
done
