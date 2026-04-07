#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

usage() {
  cat <<'USAGE'
Usage:
  tooling/scripts/github/sync-secrets-and-vars.sh --repo owner/repo [options]

Required:
  --repo <owner/repo>

Optional:
  --environment <name>
  --secrets <A,B,C>
  --vars <X,Y,Z>
  --secrets-file <path>
  --vars-file <path>
  --dry-run
  -h, --help
USAGE
}

die() { echo "[sync-gh-env] ERROR: $*" >&2; exit 1; }

trim() {
  local s="$1"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

in_array() {
  local needle="$1"; shift
  local x
  for x in "$@"; do [[ "$x" == "$needle" ]] && return 0; done
  return 1
}

append_unique() {
  local arr_name="$1"
  local value="$2"
  local existing=()
  eval "local existing=(\"\${${arr_name}[@]-}\")"
  if ! in_array "$value" "${existing[@]}"; then
    eval "${arr_name}+=(\"$value\")"
  fi
}

split_csv_into_array() {
  local csv="$1"
  local arr_name="$2"
  local old_ifs="$IFS"
  IFS=','
  # shellcheck disable=SC2206
  local raw=($csv)
  IFS="$old_ifs"
  local item cleaned
  for item in "${raw[@]}"; do
    cleaned="$(trim "$item")"
    [[ -z "$cleaned" ]] && continue
    append_unique "$arr_name" "$cleaned"
  done
}

load_names_from_file() {
  local file="$1"
  local arr_name="$2"
  [[ -f "$file" ]] || die "file not found: $file"
  local line cleaned
  while IFS= read -r line || [[ -n "$line" ]]; do
    cleaned="${line%%#*}"
    cleaned="$(trim "$cleaned")"
    [[ -z "$cleaned" ]] && continue
    append_unique "$arr_name" "$cleaned"
  done < "$file"
}

REPO=""
ENVIRONMENT=""
DRY_RUN=0
SECRETS_CSV=""
VARS_CSV=""
SECRETS_FILE=""
VARS_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="${2:-}"; shift 2 ;;
    --environment) ENVIRONMENT="${2:-}"; shift 2 ;;
    --secrets) SECRETS_CSV="${2:-}"; shift 2 ;;
    --vars) VARS_CSV="${2:-}"; shift 2 ;;
    --secrets-file) SECRETS_FILE="${2:-}"; shift 2 ;;
    --vars-file) VARS_FILE="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[[ -n "$REPO" ]] || die "--repo is required"
command -v gh >/dev/null 2>&1 || die "gh CLI not found"
gh auth status -h github.com >/dev/null 2>&1 || die "gh is not authenticated"

SECRET_NAMES=()
VAR_NAMES=()

[[ -n "$SECRETS_CSV" ]] && split_csv_into_array "$SECRETS_CSV" SECRET_NAMES
[[ -n "$VARS_CSV" ]] && split_csv_into_array "$VARS_CSV" VAR_NAMES
[[ -n "$SECRETS_FILE" ]] && load_names_from_file "$SECRETS_FILE" SECRET_NAMES
[[ -n "$VARS_FILE" ]] && load_names_from_file "$VARS_FILE" VAR_NAMES

[[ ${#SECRET_NAMES[@]} -gt 0 || ${#VAR_NAMES[@]} -gt 0 ]] || die "nothing to sync"

MISSING=()
for name in "${SECRET_NAMES[@]}"; do
  [[ -n "${!name+x}" ]] || MISSING+=("$name")
done
for name in "${VAR_NAMES[@]}"; do
  [[ -n "${!name+x}" ]] || MISSING+=("$name")
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "[sync-gh-env] missing local env vars:" >&2
  printf '  - %s\n' "${MISSING[@]}" >&2
  exit 1
fi

target_desc="repo=${REPO}"
if [[ -n "$ENVIRONMENT" ]]; then target_desc+=", environment=${ENVIRONMENT}"; else target_desc+=", scope=repo"; fi
echo "[sync-gh-env] syncing -> ${target_desc}"

for name in "${SECRET_NAMES[@]}"; do
  value="${!name}"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    if [[ -n "$ENVIRONMENT" ]]; then
      echo "[dry-run] gh secret set ${name} -R ${REPO} -e ${ENVIRONMENT} -b <redacted>"
    else
      echo "[dry-run] gh secret set ${name} -R ${REPO} -b <redacted>"
    fi
  else
    if [[ -n "$ENVIRONMENT" ]]; then
      gh secret set "$name" -R "$REPO" -e "$ENVIRONMENT" -b "$value" >/dev/null
    else
      gh secret set "$name" -R "$REPO" -b "$value" >/dev/null
    fi
    echo "[ok] secret: ${name}"
  fi
done

for name in "${VAR_NAMES[@]}"; do
  value="${!name}"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    if [[ -n "$ENVIRONMENT" ]]; then
      echo "[dry-run] gh variable set ${name} -R ${REPO} -e ${ENVIRONMENT} --body <redacted>"
    else
      echo "[dry-run] gh variable set ${name} -R ${REPO} --body <redacted>"
    fi
  else
    if [[ -n "$ENVIRONMENT" ]]; then
      gh variable set "$name" -R "$REPO" -e "$ENVIRONMENT" --body "$value" >/dev/null
    else
      gh variable set "$name" -R "$REPO" --body "$value" >/dev/null
    fi
    echo "[ok] variable: ${name}"
  fi
done

echo "[sync-gh-env] done"
