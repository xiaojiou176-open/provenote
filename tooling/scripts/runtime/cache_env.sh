#!/usr/bin/env bash

resolve_open_notebook_machine_cache_root() {
  if [[ -n "${OPEN_NOTEBOOK_MACHINE_CACHE_ROOT:-}" ]]; then
    printf '%s\n' "${OPEN_NOTEBOOK_MACHINE_CACHE_ROOT}"
    return 0
  fi

  if [[ -n "${XDG_CACHE_HOME:-}" ]]; then
    printf '%s/notebooklab\n' "${XDG_CACHE_HOME%/}"
    return 0
  fi

  if [[ -n "${HOME:-}" ]]; then
    printf '%s/.cache/notebooklab\n' "${HOME%/}"
    return 0
  fi

  printf '/tmp/notebooklab\n'
}

resolve_open_notebook_repo_managed_uv_environment() {
  local project_root="$1"
  printf '%s/.runtime-cache/venv/default\n' "${project_root%/}"
}

resolve_open_notebook_repo_pycache_dir() {
  local project_root="$1"
  printf '%s/.runtime-cache/pycache\n' "${project_root%/}"
}

resolve_open_notebook_repo_next_build_dir() {
  local project_root="$1"
  printf '%s/apps/web/.runtime-cache/build/next\n' "${project_root%/}"
}

resolve_open_notebook_repo_next_playwright_build_dir() {
  local project_root="$1"
  printf '%s/apps/web/.runtime-cache/build/next-playwright\n' "${project_root%/}"
}

resolve_open_notebook_repo_next_playwright_manual_build_dir() {
  local project_root="$1"
  printf '%s/apps/web/.runtime-cache/build/next-playwright-manual\n' "${project_root%/}"
}

resolve_open_notebook_managed_uv_environment() {
  local machine_cache_root="${1:-$(resolve_open_notebook_machine_cache_root)}"
  printf '%s/python/uv-project-environment\n' "${machine_cache_root%/}"
}

resolve_open_notebook_machine_uv_cache_dir() {
  local machine_cache_root="${1:-$(resolve_open_notebook_machine_cache_root)}"
  printf '%s/python/uv-cache\n' "${machine_cache_root%/}"
}

resolve_open_notebook_machine_playwright_cache_dir() {
  local machine_cache_root="${1:-$(resolve_open_notebook_machine_cache_root)}"
  printf '%s/playwright/ms-playwright\n' "${machine_cache_root%/}"
}

resolve_open_notebook_machine_tooling_bin_dir() {
  local machine_cache_root="${1:-$(resolve_open_notebook_machine_cache_root)}"
  printf '%s/tooling/bin\n' "${machine_cache_root%/}"
}

resolve_open_notebook_machine_browser_root() {
  local machine_cache_root="${1:-$(resolve_open_notebook_machine_cache_root)}"
  printf '%s/browser\n' "${machine_cache_root%/}"
}

resolve_open_notebook_chrome_user_data_dir() {
  local machine_cache_root="${1:-$(resolve_open_notebook_machine_cache_root)}"
  printf '%s/chrome-user-data\n' "$(resolve_open_notebook_machine_browser_root "${machine_cache_root}")"
}

resolve_open_notebook_browser_instance_state_file() {
  local project_root="$1"
  printf '%s/.runtime-cache/browser/chrome-instance.json\n' "${project_root%/}"
}

resolve_open_notebook_machine_surreal_binary_path() {
  local machine_cache_root="${1:-$(resolve_open_notebook_machine_cache_root)}"
  printf '%s/surreal\n' "$(resolve_open_notebook_machine_tooling_bin_dir "${machine_cache_root}")"
}

resolve_open_notebook_machine_ci_cache_root() {
  local machine_cache_root="${1:-$(resolve_open_notebook_machine_cache_root)}"
  printf '%s/ci-host\n' "${machine_cache_root%/}"
}

resolve_open_notebook_machine_ci_npm_cache_dir() {
  local machine_cache_root="${1:-$(resolve_open_notebook_machine_cache_root)}"
  printf '%s/npm-cache\n' "$(resolve_open_notebook_machine_ci_cache_root "${machine_cache_root}")"
}

resolve_open_notebook_repo_runtime_cache_dir() {
  local project_root="$1"
  printf '%s/.runtime-cache\n' "${project_root%/}"
}

resolve_open_notebook_repo_ci_cache_root() {
  local project_root="$1"
  printf '%s/ci-host\n' "$(resolve_open_notebook_repo_runtime_cache_dir "${project_root}")"
}

resolve_open_notebook_runtime_run_root() {
  local project_root="$1"
  printf '%s/runs/current\n' "$(resolve_open_notebook_repo_runtime_cache_dir "${project_root}")"
}

resolve_open_notebook_runtime_logs_dir() {
  local project_root="$1"
  local scope="${2:-local}"
  printf '%s/logs/%s\n' "$(resolve_open_notebook_runtime_run_root "${project_root}")" "${scope}"
}

resolve_open_notebook_runtime_evidence_dir() {
  local project_root="$1"
  local scope="${2:-common}"
  printf '%s/evidence/%s\n' "$(resolve_open_notebook_runtime_run_root "${project_root}")" "${scope}"
}

resolve_open_notebook_runtime_reports_dir() {
  local project_root="$1"
  local scope="${2:-common}"
  printf '%s/reports/%s\n' "$(resolve_open_notebook_runtime_run_root "${project_root}")" "${scope}"
}

ensure_open_notebook_machine_cache_layout() {
  local machine_cache_root="${1:-$(resolve_open_notebook_machine_cache_root)}"

  mkdir -p \
    "${machine_cache_root}" \
    "$(resolve_open_notebook_machine_uv_cache_dir "${machine_cache_root}")" \
    "$(resolve_open_notebook_machine_playwright_cache_dir "${machine_cache_root}")" \
    "$(resolve_open_notebook_chrome_user_data_dir "${machine_cache_root}")" \
    "$(resolve_open_notebook_machine_tooling_bin_dir "${machine_cache_root}")" \
    "$(resolve_open_notebook_machine_ci_npm_cache_dir "${machine_cache_root}")"
}

wipe_open_notebook_runtime_cache_contents() {
  local runtime_cache_dir="$1"
  wipe_open_notebook_directory_contents "${runtime_cache_dir}" "${2:-12}"
}

wipe_open_notebook_directory_contents() {
  local target_dir="$1"
  local max_attempts="${2:-5}"
  local attempt=1
  local remaining_entry=""
  local empty_checks=0
  local removed_empty_dir=0
  mkdir -p "${target_dir}"

  while (( attempt <= max_attempts )); do
    while IFS= read -r -d '' runtime_entry; do
      rm -rf -- "${runtime_entry}" 2>/dev/null || true
    done < <(find "${target_dir}" -mindepth 1 ! -type d -print0 2>/dev/null || true)

    sleep 0.02
    while :; do
      removed_empty_dir=0
      while IFS= read -r -d '' runtime_entry; do
        if rmdir "${runtime_entry}" 2>/dev/null; then
          removed_empty_dir=1
        fi
      done < <(find "${target_dir}" -mindepth 1 -depth -type d -empty -print0 2>/dev/null || true)

      if (( removed_empty_dir == 0 )); then
        break
      fi
    done

    remaining_entry="$(find "${target_dir}" -mindepth 1 -print -quit 2>/dev/null || true)"
    if [[ -z "${remaining_entry}" ]]; then
      empty_checks=$((empty_checks + 1))
      if (( empty_checks >= 2 )); then
        return 0
      fi
    else
      empty_checks=0
    fi
    sleep 0.1
    attempt=$((attempt + 1))
  done

  echo "[runtime-cache] ERROR: failed to fully wipe ${target_dir}; remaining entry: ${remaining_entry}" >&2
  return 1
}
