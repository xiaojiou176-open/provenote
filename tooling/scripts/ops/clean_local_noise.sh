#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"

DRY_RUN="${1:-}"

find_args=(
  .
  -path './.git' -prune -o
  -path './apps/web/node_modules' -prune -o
  -name '.DS_Store'
  -print
)

if [[ "${DRY_RUN}" == "--dry-run" ]]; then
  find "${find_args[@]}"
  exit 0
fi

while IFS= read -r path; do
  [[ -n "${path}" ]] || continue
  rm -f "${path}"
  printf 'REMOVED %s\n' "${path}"
done < <(find "${find_args[@]}")
