#!/usr/bin/env bash
set -euo pipefail

OPEN_NOTEBOOK_DEFAULT_UPSTREAM_URL="https://github.com/lfnovo/open-notebook.git"
OPEN_NOTEBOOK_TEMP_UPSTREAM_NAMESPACE="${OPEN_NOTEBOOK_TEMP_UPSTREAM_NAMESPACE:-refs/open-notebook/upstream-cache}"

resolve_open_notebook_upstream_url() {
  if [[ -n "${OPEN_NOTEBOOK_UPSTREAM_URL:-}" ]]; then
    printf '%s\n' "${OPEN_NOTEBOOK_UPSTREAM_URL}"
    return 0
  fi

  if [[ -n "${UPSTREAM_REPO_URL:-}" ]]; then
    printf '%s\n' "${UPSTREAM_REPO_URL}"
    return 0
  fi

  printf '%s\n' "${OPEN_NOTEBOOK_DEFAULT_UPSTREAM_URL}"
}

resolve_open_notebook_temp_upstream_ref() {
  local branch="${1:-main}"
  printf '%s/%s\n' "${OPEN_NOTEBOOK_TEMP_UPSTREAM_NAMESPACE%/}" "${branch}"
}

local_open_notebook_upstream_ref_exists() {
  local branch="${1:-main}"
  local target_ref
  target_ref="$(resolve_open_notebook_temp_upstream_ref "${branch}")"
  git show-ref --verify --quiet "${target_ref}"
}

fetch_open_notebook_temp_upstream_ref() {
  local branch="${1:-main}"
  local upstream_url="${2:-}"
  local target_ref=""

  if [[ -z "${upstream_url}" ]]; then
    upstream_url="$(resolve_open_notebook_upstream_url)"
  fi

  target_ref="$(resolve_open_notebook_temp_upstream_ref "${branch}")"
  git fetch --no-tags "${upstream_url}" "+refs/heads/${branch}:${target_ref}" >/dev/null
  printf '%s\n' "${target_ref}"
}

cleanup_open_notebook_temp_upstream_refs() {
  local ref_name=""
  while IFS= read -r ref_name; do
    [[ -z "${ref_name}" ]] && continue
    git update-ref -d "${ref_name}" >/dev/null 2>&1 || true
  done < <(git for-each-ref --format='%(refname)' "${OPEN_NOTEBOOK_TEMP_UPSTREAM_NAMESPACE}" 2>/dev/null || true)
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  command="${1:-}"
  shift || true

  case "${command}" in
    fetch-ref)
      branch="main"
      upstream_url=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --branch)
            branch="${2:-}"
            shift 2
            ;;
          --upstream-url)
            upstream_url="${2:-}"
            shift 2
            ;;
          *)
            echo "unknown argument: $1" >&2
            exit 1
            ;;
        esac
      done
      fetch_open_notebook_temp_upstream_ref "${branch}" "${upstream_url}"
      ;;
    cleanup)
      cleanup_open_notebook_temp_upstream_refs
      ;;
    resolve-ref)
      branch="main"
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --branch)
            branch="${2:-}"
            shift 2
            ;;
          *)
            echo "unknown argument: $1" >&2
            exit 1
            ;;
        esac
      done
      resolve_open_notebook_temp_upstream_ref "${branch}"
      ;;
    resolve-url)
      resolve_open_notebook_upstream_url
      ;;
    *)
      cat <<'USAGE' >&2
Usage:
  temporary_upstream_ref.sh fetch-ref [--branch <branch>] [--upstream-url <url>]
  temporary_upstream_ref.sh cleanup
  temporary_upstream_ref.sh resolve-ref [--branch <branch>]
  temporary_upstream_ref.sh resolve-url
USAGE
      exit 1
      ;;
  esac
fi
