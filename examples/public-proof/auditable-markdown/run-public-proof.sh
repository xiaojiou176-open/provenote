#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
API_BASE="${OPEN_NOTEBOOK_API_BASE:-http://localhost:5055/api}"
PASSWORD="${OPEN_NOTEBOOK_PASSWORD:-}"
SAMPLE_PATH="${REPO_ROOT}/examples/public-proof/auditable-markdown/sample-source.txt"
OUTPUT_DIR="${REPO_ROOT}/.runtime-cache/public-proof"

if [[ -z "${PASSWORD}" ]]; then
  echo "OPEN_NOTEBOOK_PASSWORD is required." >&2
  exit 1
fi

SOURCE_ID=""

cleanup() {
  if [[ -n "${SOURCE_ID}" ]]; then
    curl -fsS \
      -X DELETE \
      -H "Authorization: Bearer ${PASSWORD}" \
      "${API_BASE}/sources/${SOURCE_ID}" >/dev/null || true
  fi
}

trap cleanup EXIT

PAYLOAD="$(
  PUBLIC_PROOF_SAMPLE_PATH="${SAMPLE_PATH}" python3 - <<'PY'
import json
import os
from pathlib import Path

sample_path = Path(os.environ["PUBLIC_PROOF_SAMPLE_PATH"])
payload = {
    "type": "text",
    "title": "Public Proof Sample",
    "content": sample_path.read_text(encoding="utf-8"),
    "embed": False,
    "async_processing": False,
}
print(json.dumps(payload))
PY
)"

SOURCE_ID="$(
  curl -fsS \
    -X POST \
    -H "Authorization: Bearer ${PASSWORD}" \
    -H "Content-Type: application/json" \
    -d "${PAYLOAD}" \
    "${API_BASE}/sources/json" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])'
)"

mkdir -p "${OUTPUT_DIR}"

bash "${REPO_ROOT}/tooling/scripts/runtime/run_uv_managed.sh" run python \
  "${REPO_ROOT}/tooling/scripts/run_auditable_markdown.py" \
  "${SOURCE_ID}" \
  --api-base "${API_BASE}" \
  --password "${PASSWORD}" \
  --output "${OUTPUT_DIR}"
