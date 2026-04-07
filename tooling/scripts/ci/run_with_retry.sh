#!/usr/bin/env bash
set -euo pipefail

MAX_RETRIES="${RETRY_MAX_RETRIES:-2}"
LABEL="${RETRY_LABEL:-command}"
RETRY_CLASSIFICATION="${RETRY_CLASSIFICATION:-network_env_vs_logic}"
RETRY_ON_LOGIC_FAIL="${RETRY_ON_LOGIC_FAIL:-0}"

usage() {
  cat <<USAGE
Usage: $(basename "$0") [--label name] [--max-retries N] [--classification network_env_vs_logic] [--retry-on-logic-fail 0|1] -- <command> [args...]
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --label)
      LABEL="$2"
      shift 2
      ;;
    --max-retries)
      MAX_RETRIES="$2"
      shift 2
      ;;
    --classification)
      RETRY_CLASSIFICATION="$2"
      shift 2
      ;;
    --retry-on-logic-fail)
      RETRY_ON_LOGIC_FAIL="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[retry-gate][$LABEL] ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ $# -eq 0 ]]; then
  echo "[retry-gate][$LABEL] ERROR: missing command after --" >&2
  usage >&2
  exit 2
fi

if ! [[ "$MAX_RETRIES" =~ ^[0-9]+$ ]]; then
  echo "[retry-gate][$LABEL] ERROR: --max-retries must be a non-negative integer" >&2
  exit 2
fi
if (( MAX_RETRIES > 2 )); then
  echo "[retry-gate][$LABEL] ERROR: --max-retries must be <= 2 (policy: at most 2 retries)" >&2
  exit 2
fi

if [[ "$RETRY_CLASSIFICATION" != "network_env_vs_logic" ]]; then
  echo "[retry-gate][$LABEL] ERROR: unsupported classification mode: $RETRY_CLASSIFICATION" >&2
  exit 2
fi

if [[ "$RETRY_ON_LOGIC_FAIL" != "0" && "$RETRY_ON_LOGIC_FAIL" != "1" ]]; then
  echo "[retry-gate][$LABEL] ERROR: --retry-on-logic-fail must be 0 or 1" >&2
  exit 2
fi

TOTAL_ATTEMPTS="$((MAX_RETRIES + 1))"
ATTEMPT=1
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"
LOG_DIR="$(resolve_open_notebook_runtime_reports_dir "${ROOT_DIR}" "test-retry")"
mkdir -p "$LOG_DIR"

classify_failure() {
  local log_file="$1"
  local matched_line=""

  # network errors: transient connection/network/external service instability
  local network_regex='(ECONNRESET|ECONNREFUSED|EAI_AGAIN|ENOTFOUND|ETIMEDOUT|TimeoutError|timed out|network timeout|socket hang up|ERR_NETWORK|net::ERR_|502 Bad Gateway|503 Service Unavailable|429 Too Many Requests)'
  # environment errors: local runtime/config/dependency setup mismatch
  local environment_regex='(Target page, context or browser has been closed|browser has disconnected|Executable doesn'\''t exist|Failed to launch|webServer.*failed|Address already in use|EADDRINUSE|is already used, make sure that nothing is running on the port/url|no space left on device|ENOSPC|RUN_LIVE_TESTS|LIVE_EXTERNAL_WEB_ENABLED|GEMINI_API_KEY|Failed to extract archive|I/O operation failed during extraction|failed to query metadata of file|os error 2|No such file or directory)'

  if command -v rg >/dev/null 2>&1; then
    matched_line="$(rg -i -n -m 1 --no-heading --color never "$network_regex" "$log_file" || true)"
    if [[ -n "$matched_line" ]]; then
      echo "network_or_environment|network_or_external_dependency|${matched_line}"
      return 0
    fi
    matched_line="$(rg -i -n -m 1 --no-heading --color never "$environment_regex" "$log_file" || true)"
    if [[ -n "$matched_line" ]]; then
      echo "network_or_environment|environment_or_runtime_setup|${matched_line}"
      return 0
    fi
  else
    matched_line="$(grep -In -m 1 "$network_regex" "$log_file" || true)"
    if [[ -n "$matched_line" ]]; then
      echo "network_or_environment|network_or_external_dependency|${matched_line}"
      return 0
    fi
    matched_line="$(grep -In -m 1 "$environment_regex" "$log_file" || true)"
    if [[ -n "$matched_line" ]]; then
      echo "network_or_environment|environment_or_runtime_setup|${matched_line}"
      return 0
    fi
  fi

  echo "logic_or_test_regression|logic_or_test_regression|no-network-or-environment-signature-detected"
  return 0
}

while (( ATTEMPT <= TOTAL_ATTEMPTS )); do
  ATTEMPT_LOG="${LOG_DIR}/${LABEL}.attempt-${ATTEMPT}.log"
  echo "[retry-gate][$LABEL] START attempt ${ATTEMPT}/${TOTAL_ATTEMPTS}"

  set +e
  "$@" 2>&1 | tee "$ATTEMPT_LOG"
  STATUS=${PIPESTATUS[0]}
  set -e

  if [[ $STATUS -eq 0 ]]; then
    echo "[retry-gate][$LABEL] SUCCESS attempt ${ATTEMPT}/${TOTAL_ATTEMPTS}"
    exit 0
  fi

  CLASSIFICATION_RAW="$(classify_failure "$ATTEMPT_LOG")"
  IFS='|' read -r CLASSIFICATION DETAIL_CLASSIFICATION EVIDENCE <<< "$CLASSIFICATION_RAW"
  RETRYABLE=1
  if [[ "$CLASSIFICATION" == "logic_or_test_regression" && "$RETRY_ON_LOGIC_FAIL" != "1" ]]; then
    RETRYABLE=0
  fi

  echo "[retry-gate][$LABEL] FAIL attempt ${ATTEMPT}/${TOTAL_ATTEMPTS} exit=${STATUS}"
  echo "[retry-gate][$LABEL] classification=${CLASSIFICATION} detail=${DETAIL_CLASSIFICATION} retryable=${RETRYABLE} log=${ATTEMPT_LOG}"
  echo "[retry-gate][$LABEL] evidence=${EVIDENCE}"

  if (( ATTEMPT >= TOTAL_ATTEMPTS )); then
    echo "[retry-gate][$LABEL] RETRY_EXHAUSTED attempts=${TOTAL_ATTEMPTS}"
    exit "$STATUS"
  fi

  if [[ "$RETRYABLE" -eq 0 ]]; then
    echo "[retry-gate][$LABEL] STOP_EARLY non-retryable failure classification=${CLASSIFICATION}"
    exit "$STATUS"
  fi

  ATTEMPT="$((ATTEMPT + 1))"
done

echo "[retry-gate][$LABEL] ERROR: unexpected retry loop termination"
exit 1
