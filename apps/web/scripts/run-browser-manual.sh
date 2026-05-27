#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOT_DIR="$(cd "${APP_DIR}/../.." && pwd)"

# shellcheck source=/dev/null
source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"

usage() {
  cat <<'EOF'
Usage: bash ./scripts/run-browser-manual.sh [start-or-attach|migrate|status] [--dry-run] [--start-url URL]

Env:
- NOTEBOOKLAB_BROWSER_MODE=real_chrome_profile|managed_playwright
- NOTEBOOKLAB_BROWSER_URL=http://127.0.0.1:3100
- NOTEBOOKLAB_CHROME_USER_DATA_DIR=~/.cache/notebooklab/browser/chrome-user-data
- NOTEBOOKLAB_CHROME_PROFILE_NAME=notebooklab
- NOTEBOOKLAB_CHROME_PROFILE_KEY=Profile 1
- NOTEBOOKLAB_SOURCE_CHROME_USER_DATA_DIR=~/Library/Application Support/Google/Chrome
- NOTEBOOKLAB_SOURCE_CHROME_PROFILE_KEY=Profile 25
- NOTEBOOKLAB_CHROME_CDP_PORT=9342
- NOTEBOOKLAB_BROWSER_IDENTITY_LABEL=notebooklab
- NOTEBOOKLAB_BROWSER_IDENTITY_ACCENT=#2563eb
- NOTEBOOKLAB_MANAGED_PLAYWRIGHT_PROFILE_DIR=.runtime-cache/browser/manual-playwright-profile
EOF
}

DRY_RUN=0
SUBCOMMAND="start-or-attach"

if [[ $# -gt 0 ]] && [[ "$1" != -* ]]; then
  case "$1" in
    start-or-attach|migrate|status)
      SUBCOMMAND="$1"
      shift
      ;;
  esac
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --start-url)
      export NOTEBOOKLAB_BROWSER_URL="$2"
      shift 2
      ;;
    --start-url=*)
      export NOTEBOOKLAB_BROWSER_URL="${1#*=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

MACHINE_CACHE_ROOT="$(resolve_open_notebook_machine_cache_root)"
mkdir -p "${ROOT_DIR}/.runtime-cache/browser"
ensure_open_notebook_machine_cache_layout "${MACHINE_CACHE_ROOT}"

export NOTEBOOKLAB_CHROME_USER_DATA_DIR="${NOTEBOOKLAB_CHROME_USER_DATA_DIR:-$(resolve_open_notebook_chrome_user_data_dir "${MACHINE_CACHE_ROOT}")}"
export NOTEBOOKLAB_BROWSER_INSTANCE_STATE_FILE="${NOTEBOOKLAB_BROWSER_INSTANCE_STATE_FILE:-$(resolve_open_notebook_browser_instance_state_file "${ROOT_DIR}")}"
export NOTEBOOKLAB_MANAGED_PLAYWRIGHT_PROFILE_DIR="${NOTEBOOKLAB_MANAGED_PLAYWRIGHT_PROFILE_DIR:-${ROOT_DIR}/.runtime-cache/browser/manual-playwright-profile}"

node_args=("${SCRIPT_DIR}/real-chrome-profile.mjs" "${SUBCOMMAND}")
if [[ "${DRY_RUN}" == "1" ]]; then
  node_args+=(--dry-run)
fi

node "${node_args[@]}"
