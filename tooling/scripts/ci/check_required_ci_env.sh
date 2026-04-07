#!/usr/bin/env bash
set -euo pipefail

required_vars=(
  "GEMINI_API_KEY"
  "OPEN_NOTEBOOK_ENCRYPTION_KEY"
)

trim() {
  local value="${1:-}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "${value}"
}

is_placeholder() {
  local value_lc
  value_lc="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  [[ "${value_lc}" =~ (placeholder|dummy|example|changeme|change-me|your[_ -]?key|test[_ -]?key|fake|sample|todo|xxx) ]]
}

for env_var in "${required_vars[@]}"; do
  value="$(trim "${!env_var-}")"
  if [[ -z "${value}" ]]; then
    echo "[required-ci-env] ERROR: missing required CI env '${env_var}'."
    exit 1
  fi
  if is_placeholder "${value}"; then
    echo "[required-ci-env] ERROR: '${env_var}' is a placeholder value; real secret is required."
    exit 1
  fi
done

if [[ ! "${GEMINI_API_KEY}" =~ ^AIza[0-9A-Za-z_-]{35}$ ]]; then
  echo "[required-ci-env] ERROR: GEMINI_API_KEY does not match expected Google API key format."
  exit 1
fi

if [[ "${OPEN_NOTEBOOK_ENCRYPTION_KEY}" == "0p3n-N0t3b0ok" ]]; then
  echo "[required-ci-env] ERROR: OPEN_NOTEBOOK_ENCRYPTION_KEY uses insecure default value."
  exit 1
fi

if (( ${#OPEN_NOTEBOOK_ENCRYPTION_KEY} < 16 )); then
  echo "[required-ci-env] ERROR: OPEN_NOTEBOOK_ENCRYPTION_KEY must be at least 16 characters."
  exit 1
fi

echo "[required-ci-env] PASS: required CI secrets are present and non-placeholder."
