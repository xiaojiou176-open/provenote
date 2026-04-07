#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"

echo "[secret-leak-guard] scanning repository for hardcoded secrets and key leak patterns..."

if command -v rg >/dev/null 2>&1; then
  SEARCH_MODE="rg"
else
  SEARCH_MODE="grep"
fi

search_lines() {
  local pattern="$1"
  shift
  if [[ "${SEARCH_MODE}" == "rg" ]]; then
    rg -n -I --hidden --glob '!.git/**' --glob '!node_modules/**' --glob '!.venv/**' --glob '!.runtime-cache/**' --glob '!apps/web/node_modules/**' --glob '!.runtime-cache/test/playwright/report/**' --glob '!.runtime-cache/test/playwright/results/**' --glob '!dist/**' --glob '!build/**' --glob '!coverage/**' "${pattern}" "$@"
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

SECRET_LITERAL_PATTERN='(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|-----BEGIN ([A-Z ]+)?PRIVATE KEY-----)'
HARDCODED_GOOGLE_KEY_ASSIGN_PATTERN='(GEMINI_API_KEY|GOOGLE_API_KEY)\s*[:=]\s*["'\''][^"'\'']+["'\'']'
# shellcheck disable=SC2016
SHELL_KEY_VALUE_LOG_PATTERN='echo .*\$(GEMINI_API_KEY|GOOGLE_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|AZURE_OPENAI_API_KEY)'
CODE_KEY_VALUE_LOG_PATTERN='(print|logger\.(debug|info|warning|error|exception)|console\.log)\([^)]*(os\.getenv\(|os\.environ\[|process\.env\.)[^)]*(GEMINI_API_KEY|GOOGLE_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|AZURE_OPENAI_API_KEY)'
PLACEHOLDER_ALLOW_PATTERN='placeholder|dummy|example|your[-_ ]?key|change-me|test_google_live_smoke.py'

TARGETS=(
  "services"
  "packages"
  "apps/web"
  "tooling/scripts"
  "tests"
  "config"
  "docs"
  ".devcontainer"
  "ops/compose/docker-compose.yml"
  "examples"
  ".env.example"
)

if search_disallowed "${SECRET_LITERAL_PATTERN}" "${PLACEHOLDER_ALLOW_PATTERN}" "${TARGETS[@]}"; then
  echo "[secret-leak-guard] ERROR: detected secret-like literal in tracked sources/docs."
  exit 1
fi

if search_disallowed "${HARDCODED_GOOGLE_KEY_ASSIGN_PATTERN}" "${PLACEHOLDER_ALLOW_PATTERN}" services packages apps/web tooling/scripts tests; then
  echo "[secret-leak-guard] ERROR: detected hardcoded GEMINI/GOOGLE key assignment."
  exit 1
fi

if search_lines "${SHELL_KEY_VALUE_LOG_PATTERN}" services packages apps/web tooling/scripts tests; then
  echo "[secret-leak-guard] ERROR: detected shell key-value logging via env expansion."
  exit 1
fi

if search_lines "${CODE_KEY_VALUE_LOG_PATTERN}" services packages apps/web tooling/scripts tests; then
  echo "[secret-leak-guard] ERROR: detected key-value logging via environment reads."
  exit 1
fi

echo "[secret-leak-guard] all checks passed."
