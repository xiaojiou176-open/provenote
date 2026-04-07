#!/usr/bin/env bash

FORBIDDEN_PROVIDER_ENV_VARS=(
  OPENAI_API_KEY ANTHROPIC_API_KEY GROQ_API_KEY
  MISTRAL_API_KEY DEEPSEEK_API_KEY XAI_API_KEY OPENROUTER_API_KEY VOYAGE_API_KEY
  ELEVENLABS_API_KEY OLLAMA_API_BASE OLLAMA_BASE_URL VERTEX_PROJECT VERTEX_LOCATION
  GOOGLE_APPLICATION_CREDENTIALS AZURE_OPENAI_API_KEY AZURE_OPENAI_ENDPOINT
  AZURE_OPENAI_API_VERSION AZURE_OPENAI_ENDPOINT_LLM AZURE_OPENAI_ENDPOINT_EMBEDDING
  AZURE_OPENAI_ENDPOINT_STT AZURE_OPENAI_ENDPOINT_TTS OPENAI_COMPATIBLE_BASE_URL
  OPENAI_COMPATIBLE_API_KEY OPENAI_COMPATIBLE_BASE_URL_LLM OPENAI_COMPATIBLE_BASE_URL_EMBEDDING
  OPENAI_COMPATIBLE_BASE_URL_STT OPENAI_COMPATIBLE_BASE_URL_TTS
)

FORBIDDEN_COMPAT_ENV_VARS=(
  API_BASE_URL
)

init_local_runtime_dirs() {
  local root_dir="$1"
  # shellcheck source=/dev/null
  source "${root_dir}/tooling/scripts/runtime/cache_env.sh"
  local machine_cache_root
  machine_cache_root="$(resolve_open_notebook_machine_cache_root)"
  local managed_uv_environment
  RUNTIME_DIR="${root_dir}/.runtime-cache/local"
  LOG_DIR="$(resolve_open_notebook_runtime_logs_dir "${root_dir}" "local")"
  PID_DIR="${RUNTIME_DIR}/pids"
  managed_uv_environment="$(resolve_open_notebook_repo_managed_uv_environment "${root_dir}")"
  export UV_PROJECT_ENVIRONMENT="${managed_uv_environment}"
  export SETUPTOOLS_EGG_BASE="${root_dir}/.runtime-cache/build/egg-info"
  export OPEN_NOTEBOOK_LOG_DIR="${LOG_DIR}"
  ensure_open_notebook_machine_cache_layout "${machine_cache_root}"
  mkdir -p "${RUNTIME_DIR}" "${LOG_DIR}" "${PID_DIR}" "${root_dir}/.runtime-cache/build/egg-info"
}

ensure_env_file_and_load() {
  local root_dir="$1"
  local env_file="${root_dir}/.env"
  if [[ ! -f "${env_file}" ]]; then
    echo "ERROR: .env not found. Run: cp .env.example .env"
    exit 1
  fi

  set -a
  # shellcheck source=/dev/null
  source "${env_file}"
  set +a
}

require_command() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "ERROR: '${command_name}' is not installed."
    exit 1
  fi
}

validate_encryption_key() {
  local key="${OPEN_NOTEBOOK_ENCRYPTION_KEY:-}"
  if [[ -z "${key}" || "${key}" == "change-me-to-a-secret-string" ]]; then
    echo "ERROR: OPEN_NOTEBOOK_ENCRYPTION_KEY is missing or still default placeholder."
    exit 1
  fi

  if [[ ${#key} -lt 16 ]]; then
    echo "ERROR: OPEN_NOTEBOOK_ENCRYPTION_KEY must be at least 16 characters."
    exit 1
  fi
}

validate_no_forbidden_provider_env_vars() {
  local forbidden_vars_found=()
  local env_var
  for env_var in "${FORBIDDEN_PROVIDER_ENV_VARS[@]}"; do
    if [[ -n "${!env_var:-}" ]]; then
      forbidden_vars_found+=("${env_var}")
    fi
  done

  if [[ ${#forbidden_vars_found[@]} -gt 0 ]]; then
    echo "ERROR: non-google provider env vars detected: ${forbidden_vars_found[*]}"
    echo "Remove provider keys/base URLs from environment or .env."
    echo "Use UI Credential Store: Settings -> API Keys."
    exit 1
  fi
}

validate_no_forbidden_compat_env_vars() {
  local forbidden_vars_found=()
  local env_var
  for env_var in "${FORBIDDEN_COMPAT_ENV_VARS[@]}"; do
    if [[ -n "${!env_var:-}" ]]; then
      forbidden_vars_found+=("${env_var}")
    fi
  done

  if [[ ${#forbidden_vars_found[@]} -gt 0 ]]; then
    echo "ERROR: legacy/compat env vars detected: ${forbidden_vars_found[*]}"
    echo "Use canonical vars only: GEMINI_API_KEY, API_URL, INTERNAL_API_URL."
    exit 1
  fi
}

run_common_startup_checks() {
  local root_dir="$1"
  local required_cmd="${2:-}"
  ensure_env_file_and_load "${root_dir}"
  if [[ -n "${required_cmd}" ]]; then
    require_command "${required_cmd}"
  fi
  validate_encryption_key
  validate_no_forbidden_provider_env_vars
  validate_no_forbidden_compat_env_vars
}

safe_process_is_valid_pid() {
  local pid="${1:-}"
  [[ "${pid}" =~ ^[1-9][0-9]*$ ]]
}

safe_process_record_meta_path() {
  local pid_file="$1"
  printf '%s.meta' "${pid_file}"
}

safe_process_normalize_path() {
  local target_path="$1"

  if [[ -z "${target_path}" || ! -d "${target_path}" ]]; then
    printf '%s\n' "${target_path}"
    return 0
  fi

  (
    cd "${target_path}" >/dev/null 2>&1 && pwd -P
  ) || printf '%s\n' "${target_path}"
}

safe_process_ps_command() {
  local pid="$1"
  local proc_cmdline="/proc/${pid}/cmdline"

  if [[ -r "${proc_cmdline}" ]]; then
    tr '\000' ' ' < "${proc_cmdline}" | sed 's/[[:space:]]*$//'
    return 0
  fi

  ps -ww -ww -p "${pid}" -o args= 2>/dev/null | sed 's/^[[:space:]]*//'
}

safe_process_ps_started_at() {
  local pid="$1"
  ps -p "${pid}" -o lstart= 2>/dev/null | sed 's/^[[:space:]]*//'
}

safe_process_ps_state() {
  local pid="$1"
  ps -p "${pid}" -o stat= 2>/dev/null | sed 's/^[[:space:]]*//'
}

safe_process_ps_cwd() {
  local pid="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    return 0
  fi
  lsof -a -p "${pid}" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1
}

safe_process_remove_record() {
  local pid_file="$1"
  rm -f "${pid_file}" "$(safe_process_record_meta_path "${pid_file}")"
}

safe_process_pid_is_alive() {
  local pid="$1"
  local state

  if ! safe_process_is_valid_pid "${pid}"; then
    return 1
  fi
  if ! kill -0 "${pid}" >/dev/null 2>&1; then
    return 1
  fi

  state="$(safe_process_ps_state "${pid}")"
  if [[ -z "${state}" || "${state}" == Z* ]]; then
    return 1
  fi
  return 0
}

safe_process_write_record() {
  local pid_file="$1"
  local pid="$2"
  local service="$3"
  local command_pattern="$4"
  local cwd="$5"
  local port="${6:-}"
  local started_at

  if ! safe_process_is_valid_pid "${pid}"; then
    echo "ERROR: refusing to record invalid pid '${pid}' for ${service}" >&2
    return 1
  fi

  started_at="$(safe_process_ps_started_at "${pid}")"
  if [[ -z "${started_at}" ]]; then
    echo "ERROR: unable to resolve start time for pid ${pid} (${service})" >&2
    return 1
  fi

  cwd="$(safe_process_normalize_path "${cwd}")"

  printf '%s\n' "${pid}" > "${pid_file}"
  {
    printf 'SAFE_PROCESS_SERVICE=%q\n' "${service}"
    printf 'SAFE_PROCESS_PID=%q\n' "${pid}"
    printf 'SAFE_PROCESS_COMMAND_PATTERN=%q\n' "${command_pattern}"
    printf 'SAFE_PROCESS_CWD=%q\n' "${cwd}"
    printf 'SAFE_PROCESS_PORT=%q\n' "${port}"
    printf 'SAFE_PROCESS_STARTED_AT=%q\n' "${started_at}"
  } > "$(safe_process_record_meta_path "${pid_file}")"
}

safe_process_validate_record() {
  local pid_file="$1"
  local meta_file pid current_started current_command current_cwd

  SAFE_PROCESS_RECORD_ERROR=""
  SAFE_PROCESS_RECORD_PID=""
  SAFE_PROCESS_RECORD_SERVICE=""
  SAFE_PROCESS_RECORD_COMMAND_PATTERN=""
  SAFE_PROCESS_RECORD_CWD=""
  SAFE_PROCESS_RECORD_PORT=""

  if [[ ! -f "${pid_file}" ]]; then
    SAFE_PROCESS_RECORD_ERROR="missing_pid_file"
    return 1
  fi

  meta_file="$(safe_process_record_meta_path "${pid_file}")"
  if [[ ! -f "${meta_file}" ]]; then
    SAFE_PROCESS_RECORD_ERROR="missing_meta_file"
    return 1
  fi

  pid="$(cat "${pid_file}")"
  if ! safe_process_is_valid_pid "${pid}"; then
    SAFE_PROCESS_RECORD_ERROR="invalid_pid"
    return 1
  fi

  unset SAFE_PROCESS_SERVICE SAFE_PROCESS_PID SAFE_PROCESS_COMMAND_PATTERN SAFE_PROCESS_CWD SAFE_PROCESS_PORT SAFE_PROCESS_STARTED_AT
  # shellcheck disable=SC1090
  source "${meta_file}"

  if [[ "${SAFE_PROCESS_PID:-}" != "${pid}" ]]; then
    SAFE_PROCESS_RECORD_ERROR="pid_mismatch"
    return 1
  fi

  SAFE_PROCESS_RECORD_PID="${pid}"
  SAFE_PROCESS_RECORD_SERVICE="${SAFE_PROCESS_SERVICE:-}"
  SAFE_PROCESS_RECORD_COMMAND_PATTERN="${SAFE_PROCESS_COMMAND_PATTERN:-}"
  SAFE_PROCESS_RECORD_CWD="${SAFE_PROCESS_CWD:-}"
  SAFE_PROCESS_RECORD_PORT="${SAFE_PROCESS_PORT:-}"

  if ! safe_process_pid_is_alive "${pid}"; then
    SAFE_PROCESS_RECORD_ERROR="not_running"
    return 1
  fi

  current_started="$(safe_process_ps_started_at "${pid}")"
  if [[ -z "${current_started}" || -z "${SAFE_PROCESS_STARTED_AT:-}" || "${current_started}" != "${SAFE_PROCESS_STARTED_AT}" ]]; then
    SAFE_PROCESS_RECORD_ERROR="pid_reused"
    return 1
  fi

  if [[ -n "${SAFE_PROCESS_RECORD_COMMAND_PATTERN}" ]]; then
    current_command="$(safe_process_ps_command "${pid}")"
    if [[ "${current_command}" != *"${SAFE_PROCESS_RECORD_COMMAND_PATTERN}"* ]]; then
      SAFE_PROCESS_RECORD_ERROR="command_mismatch"
      return 1
    fi
  fi

  if [[ -n "${SAFE_PROCESS_RECORD_CWD}" ]] && command -v lsof >/dev/null 2>&1; then
    current_cwd="$(safe_process_ps_cwd "${pid}")"
    current_cwd="$(safe_process_normalize_path "${current_cwd}")"
    if [[ -n "${current_cwd}" && "${current_cwd}" != "$(safe_process_normalize_path "${SAFE_PROCESS_RECORD_CWD}")" ]]; then
      SAFE_PROCESS_RECORD_ERROR="cwd_mismatch"
      return 1
    fi
  fi

  return 0
}

safe_process_prepare_pid_file() {
  local pid_file="$1"

  if [[ ! -f "${pid_file}" ]]; then
    return 1
  fi

  if safe_process_validate_record "${pid_file}"; then
    return 0
  fi

  case "${SAFE_PROCESS_RECORD_ERROR}" in
    missing_meta_file|invalid_pid|pid_mismatch|not_running|pid_reused)
      safe_process_remove_record "${pid_file}"
      return 1
      ;;
    *)
      echo "ERROR: refusing to reuse unsafe pid record '${pid_file}' (${SAFE_PROCESS_RECORD_ERROR})" >&2
      return 2
      ;;
  esac
}

safe_process_stop_pid() {
  local pid="$1"
  local label="${2:-process}"
  local timeout_seconds="${3:-10}"
  local max_attempts attempts_left

  if ! safe_process_is_valid_pid "${pid}"; then
    return 0
  fi

  if ! safe_process_pid_is_alive "${pid}"; then
    wait "${pid}" >/dev/null 2>&1 || true
    return 0
  fi

  kill "${pid}" >/dev/null 2>&1 || true

  max_attempts=$((timeout_seconds * 2))
  if (( max_attempts < 1 )); then
    max_attempts=1
  fi

  attempts_left="${max_attempts}"
  while (( attempts_left > 0 )); do
    if ! safe_process_pid_is_alive "${pid}"; then
      wait "${pid}" >/dev/null 2>&1 || true
      return 0
    fi
    sleep 0.5
    ((attempts_left--))
  done

  echo "${label}: still running after ${timeout_seconds}s grace period; refusing to send SIGKILL" >&2
  return 1
}

safe_process_stop_recorded() {
  local pid_file="$1"
  local label="${2:-$(basename "${pid_file}")}"
  local timeout_seconds="${3:-10}"
  local pid

  if ! safe_process_validate_record "${pid_file}"; then
    case "${SAFE_PROCESS_RECORD_ERROR}" in
      missing_meta_file|invalid_pid|pid_mismatch|not_running|pid_reused)
        safe_process_remove_record "${pid_file}"
        return 0
        ;;
      *)
        echo "${label}: refusing to stop unsafe record (${SAFE_PROCESS_RECORD_ERROR})" >&2
        return 1
        ;;
    esac
  fi

  pid="${SAFE_PROCESS_RECORD_PID}"
  echo "Stopping ${label} (pid=${pid})..."
  if safe_process_stop_pid "${pid}" "${label}" "${timeout_seconds}"; then
    safe_process_remove_record "${pid_file}"
    echo "${label}: stopped"
    return 0
  fi

  return 1
}

safe_process_port_is_listening() {
  local port="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    return 1
  fi
  lsof -ti "tcp:${port}" -sTCP:LISTEN 2>/dev/null | grep -q .
}

safe_process_port_listener_summary() {
  local port="$1"
  local pid command

  if ! command -v lsof >/dev/null 2>&1; then
    return 0
  fi

  while IFS= read -r pid; do
    [[ -z "${pid}" ]] && continue
    command="$(safe_process_ps_command "${pid}")"
    printf 'pid=%s command=%s\n' "${pid}" "${command}"
  done < <(lsof -ti "tcp:${port}" -sTCP:LISTEN 2>/dev/null || true)
}

safe_process_require_port_free() {
  local port="$1"
  local label="$2"

  if ! safe_process_port_is_listening "${port}"; then
    return 0
  fi

  echo "ERROR: ${label} requires port ${port}, but the port is already occupied." >&2
  echo "Refusing to stop unowned listener(s)." >&2
  while IFS= read -r line; do
    [[ -z "${line}" ]] && continue
    echo "  ${line}" >&2
  done < <(safe_process_port_listener_summary "${port}")
  return 1
}

safe_process_release_recorded_port() {
  local pid_dir="$1"
  local port="$2"
  local timeout_seconds="${3:-10}"
  local pid_file
  local matched=0
  local status=0

  if [[ ! -d "${pid_dir}" ]]; then
    return 1
  fi

  while IFS= read -r pid_file; do
    [[ -z "${pid_file}" ]] && continue
    if ! safe_process_validate_record "${pid_file}"; then
      case "${SAFE_PROCESS_RECORD_ERROR}" in
        missing_meta_file|invalid_pid|pid_mismatch|not_running|pid_reused)
          safe_process_remove_record "${pid_file}"
          ;;
      esac
      continue
    fi
    if [[ "${SAFE_PROCESS_RECORD_PORT}" != "${port}" ]]; then
      continue
    fi
    matched=1
    if ! safe_process_stop_recorded "${pid_file}" "${SAFE_PROCESS_RECORD_SERVICE:-$(basename "${pid_file}" .pid)}" "${timeout_seconds}"; then
      status=1
    fi
  done < <(find "${pid_dir}" -maxdepth 1 -type f -name '*.pid' | sort)

  if (( matched == 0 )); then
    return 1
  fi
  return "${status}"
}
