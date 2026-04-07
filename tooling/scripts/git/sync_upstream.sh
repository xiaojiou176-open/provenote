#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"
# shellcheck source=/dev/null
source "${ROOT_DIR}/tooling/scripts/git/temporary_upstream_ref.sh"

usage() {
  cat <<'EOF'
Usage:
  tooling/scripts/git/sync_upstream.sh [--upstream-url <url>] [--branch <branch>] [--dry-run] [--no-push] [--delta-register <path>]

Description:
  1) Fetch origin and a temporary upstream ref.
  2) Create rollback tag: rollback/sync-<branch>-<timestamp>.
  3) Fast-forward target branch from the temporary upstream ref (ff-only).
  4) Push target branch to origin (unless --no-push).
  5) Print conflict/rollback playbook and drift verification entry.

Defaults:
  - branch: main
  - delta register: docs/development.md

Examples:
  tooling/scripts/git/sync_upstream.sh --upstream-url https://github.com/lfnovo/open-notebook.git --branch main --dry-run
  tooling/scripts/git/sync_upstream.sh --upstream-url https://github.com/lfnovo/open-notebook.git --branch main

Rollback:
  git tag -l 'rollback/sync-main-*' --sort=-creatordate | head -n 1

Notes:
  - Non-destructive only: no reset/clean/force operations.
  - Working tree must be clean before actual sync.
  - In --dry-run mode, dirty tree is allowed for rehearsal.
EOF
}

log() {
  printf '[sync-upstream] %s\n' "$*"
}

run() {
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    printf '[sync-upstream][dry-run] %s\n' "$*"
    return 0
  fi
  "$@"
}

ensure_repo() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    log "ERROR: not inside a git repository."
    exit 1
  fi
}

ensure_clean_tree() {
  if [[ -n "$(git status --porcelain)" ]]; then
    log "ERROR: working tree is not clean; commit/stash first."
    exit 1
  fi
}

print_conflict_playbook() {
  local target_branch="$1"
  local delta_register="$2"
  local upstream_url="$3"
  local integration_branch
  integration_branch="integration/${target_branch}-from-upstream-$(date +%Y%m%d)"
  log "CONFLICT PLAYBOOK:"
  log "  git fetch --prune origin"
  log "  temp_ref=\"\$(bash tooling/scripts/git/temporary_upstream_ref.sh resolve-ref --branch ${target_branch})\""
  log "  git fetch --no-tags ${upstream_url} +refs/heads/${target_branch}:\${temp_ref}"
  log "  git log --oneline --left-right origin/${target_branch}...\${temp_ref}"
  log "  git checkout -b ${integration_branch} \${temp_ref}"
  log "  git rev-list --reverse \${temp_ref}..origin/${target_branch}"
  log "  # cherry-pick required origin-only commits, resolve conflicts, run tests"
  log "  bash tooling/scripts/ci/check_upstream_drift.sh --branch ${target_branch} --strict-divergence --delta-register ${delta_register}"
}

print_rollback_drill() {
  local target_branch="$1"
  local rollback_tag="$2"
  local drill_branch
  drill_branch="drill/rollback-${target_branch}-$(date +%Y%m%d)"
  log "ROLLBACK DRILL:"
  log "  git show --no-patch ${rollback_tag}"
  log "  git checkout -b ${drill_branch} ${rollback_tag}"
  log "  git log -1 --oneline"
  log "  git checkout ${target_branch}"
  log "  git branch -D ${drill_branch}"
}

default_upstream_branch() {
  printf 'main\n'
}

DRY_RUN=0
NO_PUSH=0
UPSTREAM_URL=""
TARGET_BRANCH=""
DELTA_REGISTER_PATH="docs/development.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --upstream-url)
      [[ $# -ge 2 ]] || { log "ERROR: --upstream-url requires a value."; exit 1; }
      UPSTREAM_URL="$2"
      shift 2
      ;;
    --branch)
      [[ $# -ge 2 ]] || { log "ERROR: --branch requires a value."; exit 1; }
      TARGET_BRANCH="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --no-push)
      NO_PUSH=1
      shift
      ;;
    --delta-register)
      [[ $# -ge 2 ]] || { log "ERROR: --delta-register requires a value."; exit 1; }
      DELTA_REGISTER_PATH="$2"
      shift 2
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

ensure_repo

if ! git remote get-url origin >/dev/null 2>&1; then
  log "ERROR: 'origin' remote is required."
  exit 1
fi
if [[ -z "${UPSTREAM_URL}" ]]; then
  UPSTREAM_URL="$(resolve_open_notebook_upstream_url)"
fi

TEMP_UPSTREAM_REF=""
cleanup_temp_upstream_ref() {
  if [[ -n "${TEMP_UPSTREAM_REF}" ]]; then
    git update-ref -d "${TEMP_UPSTREAM_REF}" >/dev/null 2>&1 || true
  fi
}
trap cleanup_temp_upstream_ref EXIT

run git fetch --prune origin

if [[ -z "${TARGET_BRANCH}" ]]; then
  TARGET_BRANCH="$(default_upstream_branch)"
fi

TEMP_UPSTREAM_REF="$(fetch_open_notebook_temp_upstream_ref "${TARGET_BRANCH}" "${UPSTREAM_URL}")"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  if [[ -n "$(git status --porcelain)" ]]; then
    log "NOTICE: working tree is dirty; dry-run mode skips clean-tree enforcement."
  fi
else
  ensure_clean_tree
fi

if ! git show-ref --verify --quiet "refs/remotes/origin/${TARGET_BRANCH}"; then
  log "ERROR: origin/${TARGET_BRANCH} not found."
  exit 1
fi

read -r ORIGIN_ONLY UPSTREAM_ONLY <<<"$(git rev-list --left-right --count "origin/${TARGET_BRANCH}...${TEMP_UPSTREAM_REF}")"
log "drift snapshot: branch=${TARGET_BRANCH} origin_only=${ORIGIN_ONLY} upstream_only=${UPSTREAM_ONLY}"

if (( ORIGIN_ONLY > 0 && UPSTREAM_ONLY > 0 )); then
  log "ERROR: origin/${TARGET_BRANCH} and upstream/${TARGET_BRANCH} have diverged."
  print_conflict_playbook "${TARGET_BRANCH}" "${DELTA_REGISTER_PATH}" "${UPSTREAM_URL}"
  exit 1
fi

if git show-ref --verify --quiet "refs/heads/${TARGET_BRANCH}"; then
  run git checkout "${TARGET_BRANCH}"
else
  if git show-ref --verify --quiet "refs/remotes/origin/${TARGET_BRANCH}"; then
    run git checkout -b "${TARGET_BRANCH}" "origin/${TARGET_BRANCH}"
  else
    run git checkout -b "${TARGET_BRANCH}" "${TEMP_UPSTREAM_REF}"
  fi
fi

ROLLBACK_TAG="rollback/sync-${TARGET_BRANCH}-$(date +%Y%m%d-%H%M%S)"
run git tag "${ROLLBACK_TAG}"
log "created rollback tag: ${ROLLBACK_TAG}"

if ! run git merge --ff-only "${TEMP_UPSTREAM_REF}"; then
  log "ERROR: fast-forward failed (branch has diverged)."
  print_conflict_playbook "${TARGET_BRANCH}" "${DELTA_REGISTER_PATH}" "${UPSTREAM_URL}"
  log "rollback: git checkout ${ROLLBACK_TAG}"
  exit 1
fi

if [[ "${NO_PUSH}" -eq 0 ]]; then
  run git push origin "${TARGET_BRANCH}"
fi

log "sync complete for ${TARGET_BRANCH}."
log "rollback command: git checkout ${ROLLBACK_TAG}"
print_rollback_drill "${TARGET_BRANCH}" "${ROLLBACK_TAG}"
log "verification: bash tooling/scripts/ci/check_upstream_drift.sh --branch ${TARGET_BRANCH} --strict-divergence --delta-register ${DELTA_REGISTER_PATH}"
