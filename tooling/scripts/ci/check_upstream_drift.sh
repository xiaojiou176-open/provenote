#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"
# shellcheck source=/dev/null
source "${ROOT_DIR}/tooling/scripts/git/temporary_upstream_ref.sh"

usage() {
  cat <<'EOF'
Usage:
  tooling/scripts/ci/check_upstream_drift.sh [--branch <branch>] [--no-fetch] [--strict-divergence|--no-strict-divergence] [--delta-register <path>]

Description:
  Compare origin/<branch> and upstream/<branch>.
  - Exit 1: origin is behind upstream when the refs still share a merge-base.
  - Exit 0: in sync.
  - Exit 0: origin ahead of upstream (default).
  - Exit 0: no-merge-base selective-port topology, when current truth is expected to live in the selective-port ledger.
  - In strict mode: origin ahead must be fully registered in delta register when merge-base semantics still apply; no-merge-base topologies defer current-truth enforcement to check_selective_port_ledger.py.
  - When no persistent upstream remote is configured locally, the script fetches upstream/<branch>
    into a temporary ref and cleans it up before exit.

Defaults:
  - branch: upstream/HEAD (fallback: main)
  - strict mode: enabled automatically when CI env is present
  - delta register: docs/development.md

Examples:
  tooling/scripts/ci/check_upstream_drift.sh --branch main
  tooling/scripts/ci/check_upstream_drift.sh --branch main --strict-divergence
  tooling/scripts/ci/check_upstream_drift.sh --branch main --delta-register docs/development.md
EOF
}

log() {
  printf '[upstream-drift] %s\n' "$*"
}

default_upstream_branch() {
  local detected
  detected="$(git symbolic-ref --short refs/remotes/upstream/HEAD 2>/dev/null || true)"
  if [[ -n "${detected}" ]]; then
    printf '%s\n' "${detected#upstream/}"
    return 0
  fi
  printf 'main\n'
}

is_registered_commit() {
  local commit="$1"
  local registered
  for registered in "${REGISTERED_COMMITS[@]}"; do
    if [[ "${commit}" == "${registered}"* ]] || [[ "${registered}" == "${commit}"* ]]; then
      return 0
    fi
  done
  return 1
}

is_origin_only_commit() {
  local registered="$1"
  local commit
  for commit in "${ORIGIN_ONLY_COMMITS[@]}"; do
    if [[ "${commit}" == "${registered}"* ]] || [[ "${registered}" == "${commit}"* ]]; then
      return 0
    fi
  done
  return 1
}

is_delta_register_maintenance_commit() {
  local commit="$1"
  local path
  local has_path=0
  while IFS= read -r path; do
    [[ -z "${path}" ]] && continue
    has_path=1
    case "${path}" in
      docs/development.md)
        ;;
      *)
        return 1
        ;;
    esac
  done < <(git show --pretty=format: --name-only "${commit}")

  (( has_path == 1 )) || return 1
  return 0
}

validate_delta_register() {
  local register_path="$1"
  local register_sources=()
  local missing_commits=()
  local stale_rows=()
  local commit
  local registered

  if [[ ! -f "${register_path}" ]]; then
    log "ERROR: delta register not found: ${register_path}"
    log "SOP: create/register deltas in docs/development.md"
    return 1
  fi

  register_sources+=("${register_path}")
  while IFS= read -r supplemental; do
    register_sources+=("${supplemental}")
  done < <(find docs/ops -maxdepth 1 -type f -name 'proof-audit-report-*.md' 2>/dev/null | sort || true)

  # Expected row format:
  # | <commit-sha> | <type> | <scope> | <reason> | <owner> | <sync_strategy> | <rollback_tag> | <last_verified> |
  REGISTERED_COMMITS=()
  while IFS= read -r registered; do
    REGISTERED_COMMITS+=("${registered}")
  done < <(cat "${register_sources[@]}" 2>/dev/null | grep -E '^\|[[:space:]]*[0-9a-f]{7,40}[[:space:]]*\|' | sed -E 's/^\|[[:space:]]*([0-9a-f]{7,40}).*/\1/' | sort -u || true)

  if (( ${#REGISTERED_COMMITS[@]} == 0 )); then
    log "ERROR: no delta commits found in register: ${register_path}"
    log "SOP: add origin-only commits into the register table before CI re-run."
    return 1
  fi

  for commit in "${ORIGIN_ONLY_COMMITS[@]}"; do
    if is_registered_commit "${commit}"; then
      continue
    fi
    # Allow self-maintenance commits that only update delta register artifacts.
    if is_delta_register_maintenance_commit "${commit}"; then
      continue
    fi
    if ! is_registered_commit "${commit}"; then
      missing_commits+=("${commit}")
    fi
  done

  if (( ${#missing_commits[@]} > 0 )); then
    log "ERROR: unregistered origin-only commit(s):"
    for commit in "${missing_commits[@]}"; do
      log "  - ${commit}"
    done
    log "SOP: update ${register_path} and re-run drift check."
    return 1
  fi

  for registered in "${REGISTERED_COMMITS[@]}"; do
    if ! is_origin_only_commit "${registered}"; then
      stale_rows+=("${registered}")
    fi
  done

  if (( ${#stale_rows[@]} > 0 )); then
    log "NOTICE: stale register entry(s) not in current divergence:"
    for registered in "${stale_rows[@]}"; do
      log "  - ${registered}"
    done
  fi

  log "OK: delta register covers ${#ORIGIN_ONLY_COMMITS[@]} origin-only commit(s)."
  return 0
}

BRANCH=""
NO_FETCH=0
STRICT_DIVERGENCE=0
STRICT_DIVERGENCE_SET=0
DELTA_REGISTER_PATH="docs/development.md"
ORIGIN_ONLY_COMMITS=()
REGISTERED_COMMITS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch)
      [[ $# -ge 2 ]] || { log "ERROR: --branch requires a value."; exit 1; }
      BRANCH="$2"
      shift 2
      ;;
    --no-fetch)
      NO_FETCH=1
      shift
      ;;
    --strict-divergence)
      STRICT_DIVERGENCE=1
      STRICT_DIVERGENCE_SET=1
      shift
      ;;
    --no-strict-divergence)
      STRICT_DIVERGENCE=0
      STRICT_DIVERGENCE_SET=1
      shift
      ;;
    --delta-register)
      [[ $# -ge 2 ]] || { log "ERROR: --delta-register requires a value."; exit 1; }
      DELTA_REGISTER_PATH="$2"
      shift
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      log "ERROR: unknown argument '$1'."
      usage
      exit 1
      ;;
  esac
done

if ! git remote get-url origin >/dev/null 2>&1; then
  log "ERROR: missing origin remote."
  exit 1
fi

TEMP_UPSTREAM_REF=""
UPSTREAM_REF=""

cleanup_temp_upstream_ref() {
  if [[ -n "${TEMP_UPSTREAM_REF}" ]]; then
    git update-ref -d "${TEMP_UPSTREAM_REF}" >/dev/null 2>&1 || true
  fi
}

trap cleanup_temp_upstream_ref EXIT

if [[ "${STRICT_DIVERGENCE_SET}" -eq 0 ]] && [[ -n "${CI:-}" ]]; then
  STRICT_DIVERGENCE=1
fi

if [[ -z "${BRANCH}" ]]; then
  BRANCH="$(default_upstream_branch)"
fi

if [[ "${NO_FETCH}" -eq 0 ]]; then
  git fetch --prune origin
  TEMP_UPSTREAM_REF="$(fetch_open_notebook_temp_upstream_ref "${BRANCH}")"
  UPSTREAM_REF="${TEMP_UPSTREAM_REF}"
fi

if ! git show-ref --verify --quiet "refs/remotes/origin/${BRANCH}"; then
  log "ERROR: origin/${BRANCH} not found."
  exit 1
fi

if [[ -n "${UPSTREAM_REF}" ]]; then
  :
elif local_open_notebook_upstream_ref_exists "${BRANCH}"; then
  UPSTREAM_REF="$(resolve_open_notebook_temp_upstream_ref "${BRANCH}")"
elif git show-ref --verify --quiet "refs/remotes/upstream/${BRANCH}"; then
  UPSTREAM_REF="upstream/${BRANCH}"
else
  log "ERROR: upstream/${BRANCH} not found locally and --no-fetch was requested."
  log "SOP: rerun without --no-fetch or fetch a temporary upstream ref first."
  exit 1
fi

read -r ORIGIN_ONLY UPSTREAM_ONLY <<<"$(git rev-list --left-right --count "origin/${BRANCH}...${UPSTREAM_REF}")"

log "branch=${BRANCH} strict=${STRICT_DIVERGENCE} origin_only=${ORIGIN_ONLY} upstream_only=${UPSTREAM_ONLY}"

HAS_MERGE_BASE=1
if ! git merge-base "origin/${BRANCH}" "${UPSTREAM_REF}" >/dev/null 2>&1; then
  HAS_MERGE_BASE=0
fi

if (( HAS_MERGE_BASE == 0 )); then
  log "NO_MERGE_BASE: origin/${BRANCH} and upstream/${BRANCH} do not share ancestry."
  log "Current topology must be treated as a long-lived selective-port fork."
  log "Current-truth freshness and count alignment are enforced separately by tooling/scripts/ci/check_selective_port_ledger.py."
  exit 0
fi

if (( UPSTREAM_ONLY > 0 )); then
  log "DRIFT: origin/${BRANCH} is behind upstream/${BRANCH} by ${UPSTREAM_ONLY} commit(s)."
  log "SOP: run tooling/scripts/git/sync_upstream.sh --upstream-url <url> --branch ${BRANCH} --dry-run"
  exit 1
fi

if (( ORIGIN_ONLY > 0 )); then
  if [[ "${STRICT_DIVERGENCE}" -eq 1 ]]; then
    ORIGIN_ONLY_COMMITS=()
    while IFS= read -r commit; do
      ORIGIN_ONLY_COMMITS+=("${commit}")
    done < <(git rev-list --reverse "${UPSTREAM_REF}..origin/${BRANCH}")
    if ! validate_delta_register "${DELTA_REGISTER_PATH}"; then
      log "DRIFT: origin/${BRANCH} has ungoverned divergence; strict gate failed."
      exit 1
    fi
    log "OK: governed divergence accepted for origin/${BRANCH}."
    exit 0
  fi
  log "NOTICE: origin/${BRANCH} is ahead of upstream/${BRANCH} by ${ORIGIN_ONLY} commit(s)."
  exit 0
fi

log "OK: origin/${BRANCH} and upstream/${BRANCH} are in sync."
