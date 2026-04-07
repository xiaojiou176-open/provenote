#!/usr/bin/env bash
set -euo pipefail

INTERVAL="${HEARTBEAT_INTERVAL:-30}"
LABEL="${HEARTBEAT_LABEL:-long-test}"
HEARTBEAT_SEQ=0

usage() {
  cat <<USAGE
Usage: $(basename "$0") [--interval seconds] [--label name] -- <command> [args...]
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --label)
      LABEL="$2"
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
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ $# -eq 0 ]]; then
  echo "Missing command after --" >&2
  usage >&2
  exit 1
fi

if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]] || [[ "$INTERVAL" -lt 1 ]]; then
  echo "[heartbeat][$LABEL] ERROR invalid interval: ${INTERVAL} (must be integer >= 1)" >&2
  exit 2
fi

"$@" &
CMD_PID=$!
START_TS="$(date +%s)"
echo "[heartbeat][$LABEL] START pid=${CMD_PID} interval=${INTERVAL}s"

while kill -0 "$CMD_PID" 2>/dev/null; do
  NOW_TS="$(date +%s)"
  ELAPSED="$((NOW_TS - START_TS))"
  HEARTBEAT_SEQ="$((HEARTBEAT_SEQ + 1))"
  echo "[heartbeat][$LABEL] tick=${HEARTBEAT_SEQ} elapsed=${ELAPSED}s next_tick_in=${INTERVAL}s"
  sleep "$INTERVAL"
done

set +e
wait "$CMD_PID"
STATUS=$?
set -e
if [[ $STATUS -ne 0 ]]; then
  TOTAL_ELAPSED="$(( $(date +%s) - START_TS ))"
  echo "[heartbeat][$LABEL] FAILED exit=${STATUS} elapsed=${TOTAL_ELAPSED}s ticks=${HEARTBEAT_SEQ}"
  exit "$STATUS"
fi

TOTAL_ELAPSED="$(( $(date +%s) - START_TS ))"
echo "[heartbeat][$LABEL] COMPLETED elapsed=${TOTAL_ELAPSED}s ticks=${HEARTBEAT_SEQ}"
