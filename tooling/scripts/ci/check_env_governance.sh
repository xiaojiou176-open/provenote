#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"
ENV_CONTRACT_JSON="${ROOT_DIR}/config/env-contract.json"

echo "[env-governance] running checks..."

if command -v rg >/dev/null 2>&1; then
  SEARCH_MODE="rg"
else
  SEARCH_MODE="grep"
fi

search_lines() {
  local pattern="$1"
  shift
  if [[ "${SEARCH_MODE}" == "rg" ]]; then
    rg -n "${pattern}" "$@"
  else
    grep -R -n -E "${pattern}" "$@"
  fi
}

search_disallowed() {
  local pattern="$1"
  local allow_pattern="$2"
  shift 2
  local matches
  matches="$(search_lines "${pattern}" "$@" || true)"
  if [[ -z "${matches}" ]]; then
    return 1
  fi
  if [[ -n "${allow_pattern}" ]]; then
    matches="$(printf '%s\n' "${matches}" | grep -E -v "${allow_pattern}" || true)"
  fi
  if [[ -n "${matches}" ]]; then
    printf '%s\n' "${matches}"
    return 0
  fi
  return 1
}

_trim_value() {
  local value="$1"
  value="${value%%#*}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  if [[ "${value}" == \"*\" && "${value}" == *\" ]]; then
    value="${value:1:${#value}-2}"
  elif [[ "${value}" == \'*\' && "${value}" == *\' ]]; then
    value="${value:1:${#value}-2}"
  fi
  printf '%s' "${value}"
}

env_var_set_in_file() {
  local env_var="$1"
  local file_path="$2"
  [[ -f "${file_path}" ]] || return 1
  local raw_value
  raw_value="$(awk -F= -v key="${env_var}" '
    $0 ~ "^[[:space:]]*" key "[[:space:]]*=" {
      value = substr($0, index($0, "=") + 1)
      print value
    }
  ' "${file_path}" | tail -n 1)"
  [[ -z "${raw_value}" ]] && return 1
  local normalized_value
  normalized_value="$(_trim_value "${raw_value}")"
  [[ -n "${normalized_value}" ]]
}

env_var_set_anywhere() {
  local env_var="$1"
  local env_value="${!env_var-}"
  if [[ -n "$(_trim_value "${env_value}")" ]]; then
    return 0
  fi
  if env_var_set_in_file "${env_var}" ".env"; then
    return 0
  fi
  return 1
}

read_contract_list() {
  local mode="$1"
  python3 - "${ENV_CONTRACT_JSON}" "${mode}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

contract_path = Path(sys.argv[1])
mode = sys.argv[2]
payload = json.loads(contract_path.read_text(encoding="utf-8"))

if mode == "runtime_allowlist":
    entries = payload["required"] + payload["optional"]
    values = [item["name"] for item in entries]
elif mode == "compat_forbidden":
    values = [item["name"] for item in payload["forbidden"]]
elif mode == "blocked_legacy":
    values = payload["blocked_legacy_provider_env_vars"]
else:
    raise SystemExit(f"unsupported mode: {mode}")

for value in values:
    print(value)
PY
}

LEGACY_PROVIDER_ENV_VARS_RAW="$(read_contract_list blocked_legacy)"

LEGACY_PROVIDER_ENV_VARS=()
while IFS= read -r env_var; do
  [[ -z "${env_var}" ]] && continue
  LEGACY_PROVIDER_ENV_VARS+=("${env_var}")
done <<< "${LEGACY_PROVIDER_ENV_VARS_RAW}"

if [[ ${#LEGACY_PROVIDER_ENV_VARS[@]} -eq 0 ]]; then
  echo "[env-governance] ERROR: failed to load non-google provider ENV blocklist from settings."
  exit 1
fi

blocked_list_count="${#LEGACY_PROVIDER_ENV_VARS[@]}"
if [[ "${blocked_list_count}" -lt 1 ]]; then
  echo "[env-governance] ERROR: blocked legacy provider list must not be empty."
  exit 1
fi

legacy_env_set_vars=()
for env_var in "${LEGACY_PROVIDER_ENV_VARS[@]}"; do
  if env_var_set_anywhere "${env_var}"; then
    legacy_env_set_vars+=("${env_var}")
  fi
done

if [[ ${#legacy_env_set_vars[@]} -gt 0 ]]; then
  echo "[env-governance] ERROR: blocked legacy provider ENV vars detected in process env or local .env:"
  printf '  - %s\n' "${legacy_env_set_vars[@]}"
  echo "[env-governance] Remove these vars to keep Gemini-only runtime governance."
  exit 1
fi

RUNTIME_ALLOWLIST_VARS=()
while IFS= read -r env_var; do
  [[ -z "${env_var}" ]] && continue
  RUNTIME_ALLOWLIST_VARS+=("${env_var}")
done < <(read_contract_list runtime_allowlist)

runtime_allowlist_count="${#RUNTIME_ALLOWLIST_VARS[@]}"
if [[ "${runtime_allowlist_count}" -lt 1 ]]; then
  echo "[env-governance] ERROR: runtime allowlist must not be empty."
  exit 1
fi

COMPAT_ENV_FORBIDDEN_VARS=()
while IFS= read -r env_var; do
  [[ -z "${env_var}" ]] && continue
  COMPAT_ENV_FORBIDDEN_VARS+=("${env_var}")
done < <(read_contract_list compat_forbidden)

compat_env_set_vars=()
for env_var in "${COMPAT_ENV_FORBIDDEN_VARS[@]}"; do
  if env_var_set_anywhere "${env_var}"; then
    compat_env_set_vars+=("${env_var}")
  fi
done

if [[ ${#compat_env_set_vars[@]} -gt 0 ]]; then
  echo "[env-governance] ERROR: compatibility env vars are forbidden; use canonical runtime keys only:"
  printf '  - %s\n' "${compat_env_set_vars[@]}"
  echo "[env-governance] Canonical policy: GEMINI_API_KEY + SURREAL_URL + SURREAL_PASSWORD."
  exit 1
fi

COMPAT_ENV_ASSIGN_PATTERN='(GOOGLE_API_KEY|SURREAL_ADDRESS|SURREAL_PORT|SURREAL_PASS|API_BASE_URL)\s*='
if search_lines "${COMPAT_ENV_ASSIGN_PATTERN}" .env.example docs/configuration.md; then
  echo "[env-governance] ERROR: forbidden compatibility env assignment templates detected in env governance docs/templates."
  exit 1
fi

LEGACY_PROVIDER_ENV_REGEX="$(printf '%s|' "${LEGACY_PROVIDER_ENV_VARS[@]}")"
LEGACY_PROVIDER_ENV_REGEX="${LEGACY_PROVIDER_ENV_REGEX%|}"
PROVIDER_ENV_ASSIGN_PATTERN="(${LEGACY_PROVIDER_ENV_REGEX})\\s*="

ENV_GOVERNANCE_FILES=(
  ".env.example"
  "docs/configuration.md"
)

ENV_POLICY_STRATEGY_DOCS=(
  "docs/configuration.md"
)

if search_lines "${PROVIDER_ENV_ASSIGN_PATTERN}" "${ENV_GOVERNANCE_FILES[@]}"; then
  echo "[env-governance] ERROR: non-google provider key/base-url assignment templates are forbidden in governance docs/templates."
  exit 1
fi

GEMINI_ENV_SOURCE_PATTERN='^\s*(GEMINI_API_KEY)\s*=\s*[^#[:space:]].+'

if search_lines "${GEMINI_ENV_SOURCE_PATTERN}" ".env.example"; then
  echo "[env-governance] ERROR: .env.example must not include concrete GEMINI API key values."
  exit 1
fi

for policy_doc in "${ENV_POLICY_STRATEGY_DOCS[@]}"; do
  if ! search_lines "Runtime Allowlist \\(${runtime_allowlist_count}\\)|runtime_allowlist\\(${runtime_allowlist_count}\\)" "${policy_doc}" >/dev/null; then
    echo "[env-governance] ERROR: runtime_allowlist(${runtime_allowlist_count}) documentation marker missing in ${policy_doc}."
    exit 1
  fi
  if ! search_lines "Blocked List \\(${blocked_list_count}\\)|blocked_list\\(${blocked_list_count}\\)" "${policy_doc}" >/dev/null; then
    echo "[env-governance] ERROR: blocked_list(${blocked_list_count}) documentation marker missing in ${policy_doc}."
    exit 1
  fi
  if ! search_lines 'phase1_ssot_naming\(canonical_only\)' "${policy_doc}" >/dev/null; then
    echo "[env-governance] ERROR: phase1_ssot_naming(canonical_only) marker missing in ${policy_doc}."
    exit 1
  fi
done

SSOT_NAMING_FORBIDDEN_PATTERN='(^|[^A-Za-z_])(any([ -]?of)|compatible|alias(es)?|fallback)([^A-Za-z_]|$)'
if [[ "${SEARCH_MODE}" == "rg" ]]; then
  ssot_naming_hits="$(rg -n -i "${SSOT_NAMING_FORBIDDEN_PATTERN}" "${ENV_POLICY_STRATEGY_DOCS[@]}" || true)"
else
  ssot_naming_hits="$(grep -R -n -E -i "${SSOT_NAMING_FORBIDDEN_PATTERN}" "${ENV_POLICY_STRATEGY_DOCS[@]}" || true)"
fi
if [[ -n "${ssot_naming_hits}" ]]; then
  printf '%s\n' "${ssot_naming_hits}"
  echo "[env-governance] ERROR: SSOT naming forbids any-of/compatible/alias/fallback wording in env policy strategy docs."
  exit 1
fi

for env_var in "${LEGACY_PROVIDER_ENV_VARS[@]}"; do
  if ! search_lines "\`${env_var}\`" docs/configuration.md >/dev/null; then
    echo "[env-governance] ERROR: blocked legacy env var missing from docs/configuration.md: ${env_var}"
    exit 1
  fi
done

PROVIDER_ENV_GET_PATTERN="(os\\.environ\\.get|os\\.getenv)\\(\\s*[\"'](${LEGACY_PROVIDER_ENV_REGEX})[\"']"

if search_lines "${PROVIDER_ENV_GET_PATTERN}" services packages; then
  echo "[env-governance] ERROR: non-google provider ENV fallback reads detected in runtime code."
  exit 1
fi

COMPAT_ENV_REGEX="$(printf '%s|' "${COMPAT_ENV_FORBIDDEN_VARS[@]}")"
COMPAT_ENV_REGEX="${COMPAT_ENV_REGEX%|}"
COMPAT_ENV_GET_PATTERN="(os\\.environ\\.get|os\\.getenv)\\(\\s*[\"'](${COMPAT_ENV_REGEX})[\"']"

if search_lines "${COMPAT_ENV_GET_PATTERN}" services packages; then
  echo "[env-governance] ERROR: forbidden compatibility ENV reads detected in runtime code."
  exit 1
fi

if search_lines '@router\.(get|post)\("/(env-status|migrate-from-env)"' services/api/routers | grep -v 'services/api/routers/credentials.py'; then
  echo "[env-governance] ERROR: legacy credential routes detected outside credentials router."
  exit 1
fi

# Tombstone routes are optional in Gemini-only mode.
# Governance should not require retaining removed legacy endpoints.

if ! search_lines 'Literal\["environment", "none"\]' packages/core/application/credential_models.py >/dev/null; then
  echo "[env-governance] ERROR: expected ENV-only source literal missing from credential status schema."
  exit 1
fi

if ! search_lines 'legacy_env_detected' packages/core/application/models.py services/api/credentials_service.py apps/web/src/lib/api/credentials.ts >/dev/null; then
  echo "[env-governance] ERROR: legacy_env_detected contract is missing."
  exit 1
fi

# Source of truth: keys must come only from process environment / .env.
HARDCODED_GOOGLE_KEY_PATTERN='AIza[0-9A-Za-z_-]{35}'
HARDCODED_KEY_ASSIGN_PATTERN='GEMINI_API_KEY\s*[:=]\s*["'\''][^"'\'']+["'\'']'
# shellcheck disable=SC2016
SHELL_KEY_VALUE_LOG_PATTERN='echo .*\$(GEMINI_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|AZURE_OPENAI_API_KEY)'
CODE_KEY_VALUE_LOG_PATTERN='(print|logger\.(debug|info|warning|error|exception)|console\.log)\([^)]*(os\.getenv\(|os\.environ\[|process\.env\.)[^)]*(GEMINI_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|AZURE_OPENAI_API_KEY)'
PLACEHOLDER_ALLOW_PATTERN='placeholder|dummy|example|your[-_ ]?key|change-me|test_google_live_smoke.py'

if search_disallowed "${HARDCODED_GOOGLE_KEY_PATTERN}" "${PLACEHOLDER_ALLOW_PATTERN}" services packages apps/web tooling/scripts tests; then
  echo "[env-governance] ERROR: hardcoded Google API key-like literal detected; use .env or process environment only."
  exit 1
fi

if search_disallowed "${HARDCODED_KEY_ASSIGN_PATTERN}" "${PLACEHOLDER_ALLOW_PATTERN}" services packages apps/web tooling/scripts tests; then
  echo "[env-governance] ERROR: hardcoded GEMINI key assignment detected; read from environment instead."
  exit 1
fi

if search_lines "${SHELL_KEY_VALUE_LOG_PATTERN}" services packages apps/web tooling/scripts; then
  echo "[env-governance] ERROR: shell log leaks key values via env expansion."
  exit 1
fi

if search_lines "${CODE_KEY_VALUE_LOG_PATTERN}" services packages apps/web tooling/scripts; then
  echo "[env-governance] ERROR: code log leaks key values via environment reads."
  exit 1
fi

python3 tooling/scripts/ci/check_gemini_runtime_policy.py

echo "[env-governance] all checks passed."
