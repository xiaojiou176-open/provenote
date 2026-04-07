#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RUNTIME_DIR="${ROOT_DIR}/.runtime-cache/local"
LOG_ROOT="${ROOT_DIR}/.runtime-cache/evals"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ARTIFACT_DIR="${LOG_ROOT}/${TIMESTAMP}"

# shellcheck source=/dev/null
source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"
MACHINE_CACHE_ROOT="$(resolve_open_notebook_machine_cache_root)"
ensure_open_notebook_machine_cache_layout "${MACHINE_CACHE_ROOT}"

# shellcheck disable=SC1091
source "${ROOT_DIR}/tooling/scripts/dev/common.sh"

mkdir -p "${ARTIFACT_DIR}" "${RUNTIME_DIR}/surrealdb"

if [[ ! -f "${ROOT_DIR}/.env" ]]; then
  echo "ERROR: .env not found. Run: cp .env.example .env"
  exit 1
fi

set -a
# shellcheck source=/dev/null
source "${ROOT_DIR}/.env"
set +a

validate_no_forbidden_provider_env_vars
validate_no_forbidden_compat_env_vars

SURREAL_BIN="${SURREAL_BIN:-$(resolve_open_notebook_machine_surreal_binary_path "${MACHINE_CACHE_ROOT}")}"
if [[ ! -x "${SURREAL_BIN}" ]]; then
  if command -v surreal >/dev/null 2>&1; then
    SURREAL_BIN="$(command -v surreal)"
  else
    echo "ERROR: surreal binary not found. Expected at machine cache path or PATH."
    exit 1
  fi
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is required."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: npm is required."
  exit 1
fi

API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-5055}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
SURREAL_BIND="${SURREAL_BIND:-127.0.0.1:8000}"
SURREAL_USER="${SURREAL_USER:-root}"
SURREAL_PASSWORD="${SURREAL_PASSWORD:-root}"
SURREAL_URL="${SURREAL_URL:-ws://127.0.0.1:8000/rpc}"
SURREAL_LOG_LEVEL="${SURREAL_LOG_LEVEL:-info}"
PROMPTFOO_VERSION="${PROMPTFOO_VERSION:-0.120.25}"

api_base="http://${API_HOST}:${API_PORT}/api"

migration_chain="UNKNOWN"
smoke_fallback_channel="UNKNOWN"
smoke_real_model_channel="UNKNOWN"
promptfoo_gate="UNKNOWN"
ragas_gate="UNKNOWN"
local_runtime_health_gate="UNKNOWN"

SURREAL_PID=""
API_PID=""
WORKER_PID=""
FRONTEND_PID=""

write_gates_file() {
  cat > "${ARTIFACT_DIR}/gates.env" <<EOF
migration_chain=${migration_chain}
smoke_fallback_channel=${smoke_fallback_channel}
smoke_real_model_channel=${smoke_real_model_channel}
promptfoo_gate=${promptfoo_gate}
ragas_gate=${ragas_gate}
local_runtime_health_gate=${local_runtime_health_gate}
EOF
}

write_summary() {
  local decision="GO"
  if [[ "${migration_chain}" != "PASS" || "${smoke_fallback_channel}" != "PASS" || "${smoke_real_model_channel}" != "PASS" || "${promptfoo_gate}" != "PASS" || "${ragas_gate}" != "PASS" || "${local_runtime_health_gate}" != "PASS" ]]; then
    decision="NO-GO"
  fi

  cat > "${ARTIFACT_DIR}/release-risk-summary.md" <<EOF
# Release Risk Summary

decision=${decision}

- migration_chain: ${migration_chain}
- smoke_fallback_channel: ${smoke_fallback_channel}
- smoke_real_model_channel: ${smoke_real_model_channel}
- promptfoo_gate: ${promptfoo_gate}
- ragas_gate: ${ragas_gate}
- local_runtime_health_gate: ${local_runtime_health_gate}

## Minimal Actions
- Fix all FAIL/BLOCKER gates and rerun \`bash tooling/scripts/dev/run_auditable_release_gate.sh\`.
- Keep hard-block policy: all six gates must be PASS before release.
EOF

  echo "decision=${decision}"
  write_gates_file

  if [[ "${decision}" == "NO-GO" ]]; then
    return 1
  fi
  return 0
}

cleanup() {
  set +e
  if [[ -n "${FRONTEND_PID}" ]]; then
    safe_process_stop_pid "${FRONTEND_PID}" "release-gate-frontend" 10 || true
  fi
  if [[ -n "${WORKER_PID}" ]]; then
    safe_process_stop_pid "${WORKER_PID}" "release-gate-worker" 10 || true
  fi
  if [[ -n "${API_PID}" ]]; then
    safe_process_stop_pid "${API_PID}" "release-gate-api" 10 || true
  fi
  if [[ -n "${SURREAL_PID}" ]]; then
    safe_process_stop_pid "${SURREAL_PID}" "release-gate-surrealdb" 10 || true
  fi
  bash tooling/scripts/dev/stop_local.sh apps/web worker api surrealdb >/dev/null 2>&1 || true
}
trap cleanup EXIT

start_surreal() {
  local data_path="$1"
  local log_file="$2"
  local host="${SURREAL_BIND%:*}"
  local port="${SURREAL_BIND##*:}"

  mkdir -p "$(dirname "${data_path}")"
  nohup "${SURREAL_BIN}" start \
    --log "${SURREAL_LOG_LEVEL}" \
    --user "${SURREAL_USER}" \
    --pass "${SURREAL_PASSWORD}" \
    --bind "${SURREAL_BIND}" \
    "rocksdb:${data_path}" \
    > "${log_file}" 2>&1 &
  SURREAL_PID=$!

  for _ in $(seq 1 60); do
    if kill -0 "${SURREAL_PID}" >/dev/null 2>&1; then
      if command -v nc >/dev/null 2>&1; then
        nc -z "${host}" "${port}" >/dev/null 2>&1 && return 0
      else
        (echo >"/dev/tcp/${host}/${port}") >/dev/null 2>&1 && return 0
      fi
    fi
    sleep 1
  done
  return 1
}

auth_probe() {
  local ns="$1"
  local db="$2"
  local delay=1

  for _ in $(seq 1 6); do
    if printf 'INFO FOR ROOT;\n' | "${SURREAL_BIN}" sql \
      --endpoint "${SURREAL_URL}" \
      --username "${SURREAL_USER}" \
      --password "${SURREAL_PASSWORD}" \
      --auth-level root \
      --namespace "${ns}" \
      --database "${db}" \
      --hide-welcome \
      --json \
      > /dev/null 2>&1; then
      return 0
    fi
    sleep "${delay}"
    delay=$((delay * 2))
  done
  return 1
}

run_migration_chain() {
  local ns="$1"
  local db="$2"
  local log_file="$3"

  SURREAL_NAMESPACE="${ns}" \
  SURREAL_DATABASE="${db}" \
  SURREAL_URL="${SURREAL_URL}" \
  SURREAL_USER="${SURREAL_USER}" \
  SURREAL_PASSWORD="${SURREAL_PASSWORD}" \
    bash tooling/scripts/runtime/run_uv_managed.sh run python - <<'PY' > "${log_file}" 2>&1
import asyncio

from packages.core.database.async_migrate import AsyncMigrationManager
from packages.core.database.repository import ensure_record_id, repo_create, repo_query


async def main() -> None:
    mgr = AsyncMigrationManager()
    v0 = await mgr.get_current_version()
    if v0 != 0:
        raise SystemExit(f"Expected fresh DB version=0, got {v0}")

    await mgr.run_migration_up()
    v15 = await mgr.get_current_version()
    if v15 != 15:
        raise SystemExit(f"Expected version=15 after up, got {v15}")

    source_id = "source:migration_gate_probe"
    await repo_query(
        "UPSERT $id MERGE $data",
        {
            "id": ensure_record_id(source_id),
            "data": {
                "title": "migration gate probe",
                "topics": [],
                "full_text": "probe",
                "asset": {},
            },
        },
    )

    created = await repo_create(
        "auditable_run",
        {
            "source": ensure_record_id(source_id),
            "status": "completed",
            "model_id": "gate-model",
            "language": "zh-CN",
            "near_dedup_threshold": 0.97,
            "metrics": {
                "coverage_rate": 1.0,
                "missing_count": 0,
                "duplicate_count": 0,
                "uncited_claims_count": 0,
                "dedup_group_count": 0,
                "unknown_pid_count": 0,
                "unclassified_count": 0,
            },
            "coverage_json": {"coverage_rate": 1.0, "missing_pids": []},
            "dedup_json": {"group_count": 0},
            "result_markdown": "# gate",
            "source_paragraphs": [],
            "sections": [],
            "claims": [],
            "dedup_entries": [],
        },
    )
    record = created[0] if isinstance(created, list) else created
    run_id = str(record["id"])
    loaded = await repo_query("SELECT * FROM $id", {"id": ensure_record_id(run_id)})
    if not loaded:
        raise SystemExit("Failed to reload auditable_run record")
    loaded_metrics = loaded[0].get("metrics", {})
    if loaded_metrics.get("coverage_rate") != 1.0:
        raise SystemExit("metrics nested keys were not persisted")

    await mgr.runner.run_one_down()
    v14 = await mgr.get_current_version()
    if v14 != 14:
        raise SystemExit(f"Expected version=14 after one_down, got {v14}")

    await mgr.runner.run_one_up()
    v15b = await mgr.get_current_version()
    if v15b != 15:
        raise SystemExit(f"Expected version=15 after one_up restore, got {v15b}")

    print("migration_chain_ok=1")


asyncio.run(main())
PY
}

start_api_worker_frontend() {
  local ns="$1"
  local db="$2"
  local api_log="$3"
  local worker_log="$4"
  local frontend_log="$5"

  API_RELOAD=false \
  SURREAL_NAMESPACE="${ns}" \
  SURREAL_DATABASE="${db}" \
  SURREAL_URL="${SURREAL_URL}" \
  SURREAL_USER="${SURREAL_USER}" \
  SURREAL_PASSWORD="${SURREAL_PASSWORD}" \
    nohup bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/bin/run_api.py > "${api_log}" 2>&1 &
  API_PID=$!

  for _ in $(seq 1 80); do
    if curl -fsS "http://${API_HOST}:${API_PORT}/health" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  SURREAL_NAMESPACE="${ns}" \
  SURREAL_DATABASE="${db}" \
  SURREAL_URL="${SURREAL_URL}" \
  SURREAL_USER="${SURREAL_USER}" \
  SURREAL_PASSWORD="${SURREAL_PASSWORD}" \
    nohup bash tooling/scripts/runtime/run_uv_managed.sh run surreal-commands-worker --import-modules services.worker > "${worker_log}" 2>&1 &
  WORKER_PID=$!

  if [[ ! -d "${ROOT_DIR}/apps/web/node_modules" ]]; then
    (cd "${ROOT_DIR}/apps/web" && npm ci >/dev/null)
  fi

  pushd "${ROOT_DIR}/apps/web" >/dev/null
  nohup env \
    API_URL="http://${API_HOST}:${API_PORT}" \
    npm run dev -- --hostname "${FRONTEND_HOST}" --port "${FRONTEND_PORT}" \
    > "${frontend_log}" 2>&1 &
  FRONTEND_PID=$!
  popd >/dev/null

  for _ in $(seq 1 120); do
    if curl -fsS "http://${FRONTEND_HOST}:${FRONTEND_PORT}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

run_smoke() {
  local log_prefix="$1"
  local source_payload='{"type":"text","title":"auditable smoke source","content":"P1: Product requirements. P2: Implementation steps. P3: Risks and acceptance criteria.","notebooks":[],"async_processing":false}'

  local source_resp
  if ! source_resp="$(curl -fsS -X POST "${api_base}/sources/json" -H "Content-Type: application/json" -d "${source_payload}")"; then
    smoke_fallback_channel="FAIL"
    smoke_real_model_channel="BLOCKER"
    return 0
  fi
  printf '%s\n' "${source_resp}" > "${ARTIFACT_DIR}/source_create.json"

  local source_id
  source_id="$(printf '%s' "${source_resp}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
  echo "source_id=${source_id}" > "${ARTIFACT_DIR}/source_id.txt"

  if bash tooling/scripts/runtime/run_uv_managed.sh run python "${ROOT_DIR}/tooling/scripts/run_auditable_markdown.py" "${source_id}" \
      --api-base "${api_base}" \
      --model-id "__missing_model__" \
      --output "${ARTIFACT_DIR}/fallback" \
      > "${ARTIFACT_DIR}/${log_prefix}-fallback.log" 2>&1; then
    local fallback_run_id
    fallback_run_id="$(rg '^run_id=' "${ARTIFACT_DIR}/${log_prefix}-fallback.log" | tail -1 | cut -d= -f2-)"
    if [[ -n "${fallback_run_id}" ]]; then
      curl -fsS "${api_base}/auditable-runs/${fallback_run_id}" > "${ARTIFACT_DIR}/fallback_run.json"
      if python3 - <<'PY' "${ARTIFACT_DIR}/fallback_run.json" >/dev/null 2>&1
import json,sys
payload=json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["status"] == "completed"
assert "[[P" in payload.get("result_markdown", "")
PY
      then
        smoke_fallback_channel="PASS"
      else
        smoke_fallback_channel="FAIL"
      fi
    else
      smoke_fallback_channel="FAIL"
    fi
  else
    smoke_fallback_channel="FAIL"
  fi

  bootstrap_google_language_model() {
    python3 - <<'PY' "${api_base}" "${ARTIFACT_DIR}/model-bootstrap.log"
import json
import os
import sys
import urllib.error
import urllib.request

api_base = sys.argv[1]
log_path = sys.argv[2]
api_key = os.getenv("GEMINI_API_KEY", "").strip()
if not api_key:
    raise SystemExit("missing GEMINI_API_KEY")

preferred = [
    "gemini-2.5-pro",
    "gemini-2.0-pro",
    "gemini-1.5-pro",
    "gemini-pro",
]

def request(path: str, method: str = "GET", payload: dict | None = None) -> dict | list:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{api_base}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}

with open(log_path, "w", encoding="utf-8") as log:
    cred = request(
        "/credentials",
        method="POST",
        payload={
            "name": "gate-google",
            "provider": "google",
            "modalities": ["language"],
            "api_key": api_key,
        },
    )
    cred_id = cred.get("id", "")
    if not cred_id:
        raise SystemExit("failed to create credential")
    log.write(f"credential_id={cred_id}\n")

    discovered = request(f"/credentials/{cred_id}/discover", method="POST")
    items = discovered.get("discovered", [])
    if not items:
        raise SystemExit("no models discovered for google credential")

    names = [item.get("name", "") for item in items if item.get("name")]
    selected = ""
    lowered = {name.lower(): name for name in names}
    for choice in preferred:
        if choice in lowered:
            selected = lowered[choice]
            break
    if not selected:
        pro_candidates = [name for name in names if "pro" in name.lower()]
        selected = pro_candidates[0] if pro_candidates else names[0]
    log.write(f"selected_model={selected}\n")

    request(
        f"/credentials/{cred_id}/register-models",
        method="POST",
        payload={
            "models": [
                {"name": selected, "provider": "google", "model_type": "language"}
            ]
        },
    )
    log.write("register_models=ok\n")
    print(selected)
PY
  }

  local language_models_json
  language_models_json="$(curl -fsS "${api_base}/models?type=language")"
  printf '%s\n' "${language_models_json}" > "${ARTIFACT_DIR}/language_models.json"

  if [[ "${language_models_json}" == "[]" ]]; then
    if [[ -n "${GEMINI_API_KEY:-}" ]]; then
      if ! bootstrap_google_language_model >/dev/null 2>&1; then
        smoke_real_model_channel="BLOCKER"
        return 0
      fi
      language_models_json="$(curl -fsS "${api_base}/models?type=language")"
      printf '%s\n' "${language_models_json}" > "${ARTIFACT_DIR}/language_models.json"
    fi
  fi

  local model_id
  model_id="$(printf '%s' "${language_models_json}" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data[0]["id"] if data else "")')"
  if [[ -z "${model_id}" ]]; then
    smoke_real_model_channel="BLOCKER"
    return 0
  fi

  local model_test_resp
  model_test_resp="$(curl -sS -X POST "${api_base}/models/${model_id}/test")"
  printf '%s\n' "${model_test_resp}" > "${ARTIFACT_DIR}/model_test.json"
  if ! printf '%s' "${model_test_resp}" | python3 -c 'import json,sys; data=json.load(sys.stdin); assert data.get("success") is True'; then
    smoke_real_model_channel="BLOCKER"
    return 0
  fi

  if bash tooling/scripts/runtime/run_uv_managed.sh run python "${ROOT_DIR}/tooling/scripts/run_auditable_markdown.py" "${source_id}" \
      --api-base "${api_base}" \
      --model-id "${model_id}" \
      --output "${ARTIFACT_DIR}/real_model" \
      > "${ARTIFACT_DIR}/${log_prefix}-real.log" 2>&1; then
    local real_run_id
    real_run_id="$(rg '^run_id=' "${ARTIFACT_DIR}/${log_prefix}-real.log" | tail -1 | cut -d= -f2-)"
    if [[ -n "${real_run_id}" ]]; then
      curl -fsS "${api_base}/auditable-runs/${real_run_id}" > "${ARTIFACT_DIR}/real_run.json"
      if python3 - <<'PY' "${ARTIFACT_DIR}/real_run.json" >/dev/null 2>&1
import json,sys
payload=json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["status"] == "completed"
assert "[[P" in payload.get("result_markdown", "")
PY
      then
        smoke_real_model_channel="PASS"
      else
        smoke_real_model_channel="FAIL"
      fi
    else
      smoke_real_model_channel="FAIL"
    fi
  else
    smoke_real_model_channel="FAIL"
  fi
}

run_evals() {
  if (cd "${ROOT_DIR}/evals/promptfoo" && npx --yes "promptfoo@${PROMPTFOO_VERSION}" eval > "${ARTIFACT_DIR}/promptfoo.log" 2>&1); then
    promptfoo_gate="PASS"
  else
    promptfoo_gate="FAIL"
  fi

  if bash tooling/scripts/runtime/run_uv_managed.sh run python "${ROOT_DIR}/evals/ragas/run_ragas_eval.py" --config "${ROOT_DIR}/evals/ragas/config.yaml" > "${ARTIFACT_DIR}/ragas.log" 2>&1; then
    ragas_gate="PASS"
  else
    ragas_gate="FAIL"
  fi
}

MIGRATION_DATA_PATH="${RUNTIME_DIR}/surrealdb/migration_gate_${TIMESTAMP}.db"
SMOKE_DATA_PATH="${RUNTIME_DIR}/surrealdb/smoke_gate_${TIMESTAMP}.db"
MIGRATION_NS="migration_gate_${TIMESTAMP//-/_}"
MIGRATION_DB="migration_gate_${TIMESTAMP//-/_}"
SMOKE_NS="smoke_gate_${TIMESTAMP//-/_}"
SMOKE_DB="smoke_gate_${TIMESTAMP//-/_}"

echo "artifact_dir=${ARTIFACT_DIR}"
bash tooling/scripts/ci/release_local_ports.sh "${API_PORT}" "${FRONTEND_PORT}" "${SURREAL_BIND##*:}"

if start_surreal "${MIGRATION_DATA_PATH}" "${ARTIFACT_DIR}/surreal-migration.log" && auth_probe "${MIGRATION_NS}" "${MIGRATION_DB}"; then
  if run_migration_chain "${MIGRATION_NS}" "${MIGRATION_DB}" "${ARTIFACT_DIR}/migration-chain.log"; then
    migration_chain="PASS"
  else
    migration_chain="FAIL"
  fi
else
  migration_chain="FAIL"
fi

if start_surreal "${SMOKE_DATA_PATH}" "${ARTIFACT_DIR}/surreal-smoke.log" && auth_probe "${SMOKE_NS}" "${SMOKE_DB}" && start_api_worker_frontend "${SMOKE_NS}" "${SMOKE_DB}" "${ARTIFACT_DIR}/services.api.log" "${ARTIFACT_DIR}/worker.log" "${ARTIFACT_DIR}/apps/web.log"; then
  if curl -fsS "http://${API_HOST}:${API_PORT}/health" >/dev/null 2>&1 && kill -0 "${WORKER_PID}" >/dev/null 2>&1 && curl -fsS "http://${FRONTEND_HOST}:${FRONTEND_PORT}" >/dev/null 2>&1 && kill -0 "${SURREAL_PID}" >/dev/null 2>&1; then
    local_runtime_health_gate="PASS"
    run_smoke "smoke"
  else
    local_runtime_health_gate="FAIL"
    smoke_fallback_channel="BLOCKER"
    smoke_real_model_channel="BLOCKER"
  fi
else
  local_runtime_health_gate="FAIL"
  smoke_fallback_channel="BLOCKER"
  smoke_real_model_channel="BLOCKER"
fi

run_evals
write_summary
