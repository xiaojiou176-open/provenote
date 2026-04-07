#!/usr/bin/env bash
set -euo pipefail

is_ci_context() {
  [[ "${GITHUB_ACTIONS:-}" == "true" || "${CI:-}" == "true" ]]
}

is_ci_pull_request_context() {
  is_ci_context && [[ "${GITHUB_EVENT_NAME:-}" == "pull_request" ]] && [[ -n "${GITHUB_BASE_REF:-}" ]]
}

is_external_pr_fast_gate_context() {
  is_ci_pull_request_context && [[ "${OPEN_NOTEBOOK_EXTERNAL_PR_FAST_GATE:-0}" == "1" ]]
}

report_empty_enforceable_commit_set() {
  local prefix="$1"
  local range="$2"
  local baseline="$3"
  local total="$4"
  local skipped="$5"

  if is_external_pr_fast_gate_context; then
    echo "[${prefix}] skip: no enforceable commits visible in external pull_request fast gate."
    echo "[${prefix}] range=${range} baseline=${baseline:-<none>} total=${total} skipped=${skipped}"
    return 0
  fi

  return 1
}

enforce_commit_governance_env_safety() {
  if ! is_ci_context; then
    return 0
  fi

  local blocked_vars=(
    COMMIT_GOVERNANCE_BASELINE_SHA
    COMMIT_GOVERNANCE_RANGE
    ATOMIC_COMMIT_MAX_FILES
    ATOMIC_COMMIT_MAX_TOP_LEVEL
  )
  local var_name=""
  for var_name in "${blocked_vars[@]}"; do
    if [[ -n "${!var_name:-}" ]]; then
      echo "[commit-governance] FAIL: ${var_name} is forbidden in CI."
      exit 1
    fi
  done
}

resolve_first_existing_ref() {
  local candidate=""
  for candidate in "$@"; do
    [[ -z "${candidate}" ]] && continue
    if git rev-parse --verify --quiet "${candidate}" >/dev/null 2>&1; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

resolve_commit_governance_bootstrap_baseline() {
  local first_guard_commit=""
  first_guard_commit="$(
    git rev-list --reverse HEAD -- \
      tooling/scripts/ci/check_atomic_commit_scope.sh \
      tooling/scripts/ci/check_atomic_commit_scope_range.sh \
      tooling/scripts/ci/check_commit_message.sh \
      tooling/scripts/ci/check_commit_message_range.sh \
      .pre-commit-config.yaml \
      .github/workflows/test.yml \
      .github/workflows/auditable-quality-gate.yml \
      2>/dev/null | head -n 1 || true
  )"

  if [[ -n "${first_guard_commit}" ]] && git rev-parse --verify --quiet "${first_guard_commit}^{commit}" >/dev/null 2>&1; then
    echo "${first_guard_commit}"
    return
  fi

  echo ""
}

resolve_commit_range() {
  local explicit_range="${COMMIT_GOVERNANCE_RANGE:-}"
  local event_name="${GITHUB_EVENT_NAME:-}"
  local push_before="${GITHUB_EVENT_BEFORE:-}"
  local github_sha="${GITHUB_SHA:-HEAD}"
  local upstream_ref=""
  local fallback_ref=""
  local pr_base_ref=""
  local pr_head_ref=""
  local merge_base=""

  if [[ -n "${explicit_range}" ]]; then
    if git rev-list --max-count=1 "${explicit_range}" >/dev/null 2>&1; then
      echo "${explicit_range}"
      return
    fi
  fi

  if [[ "${event_name}" == "push" ]] && [[ -n "${push_before}" ]] && [[ "${push_before}" != "0000000000000000000000000000000000000000" ]]; then
    if git rev-parse --verify --quiet "${push_before}^{commit}" >/dev/null 2>&1; then
      echo "${push_before}..${github_sha}"
      return
    fi
  fi

  if is_ci_pull_request_context; then
    pr_base_ref="$(
      resolve_first_existing_ref \
        "origin/${GITHUB_BASE_REF}" \
        "refs/remotes/origin/${GITHUB_BASE_REF}" \
        "${GITHUB_BASE_REF}" || true
    )"
    pr_head_ref="$(
      resolve_first_existing_ref \
        "origin/${GITHUB_HEAD_REF:-}" \
        "refs/remotes/origin/${GITHUB_HEAD_REF:-}" \
        "${GITHUB_HEAD_REF:-}" || true
    )"
    if [[ -n "${pr_base_ref}" && -n "${pr_head_ref}" ]]; then
      merge_base="$(git merge-base "${pr_base_ref}" "${pr_head_ref}" 2>/dev/null || true)"
      if [[ -n "${merge_base}" ]]; then
        echo "${merge_base}..${pr_head_ref}"
        return
      fi
      echo "${pr_base_ref}...${pr_head_ref}"
      return
    fi
  fi

  if upstream_ref="$(git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null)"; then
    merge_base="$(git merge-base HEAD "${upstream_ref}" 2>/dev/null || true)"
    if [[ -n "${merge_base}" ]]; then
      echo "${merge_base}..HEAD"
      return
    fi
    echo "${upstream_ref}...HEAD"
    return
  fi

  fallback_ref="$(
    resolve_first_existing_ref \
      "origin/${GITHUB_BASE_REF:-}" \
      "refs/remotes/origin/${GITHUB_BASE_REF:-}" \
      "${GITHUB_BASE_REF:-}" \
      origin/main \
      origin/master \
      main \
      master \
      refs/remotes/origin/main \
      refs/remotes/origin/master || true
  )"

  if [[ -n "${fallback_ref}" ]]; then
    merge_base="$(git merge-base HEAD "${fallback_ref}" 2>/dev/null || true)"
    if [[ -n "${merge_base}" ]]; then
      echo "${merge_base}..HEAD"
      return
    fi
    echo "${fallback_ref}...HEAD"
    return
  fi

  if git rev-parse --verify --quiet HEAD~1 >/dev/null 2>&1; then
    echo "HEAD~1..HEAD"
  else
    echo "HEAD"
  fi
}

resolve_commit_governance_baseline() {
  local baseline="${COMMIT_GOVERNANCE_BASELINE_SHA:-}"
  local baseline_file="tooling/scripts/ci/commit_governance_baseline.txt"
  local baseline_raw=""
  local base_ref=""
  local normalized=""

  if is_ci_pull_request_context; then
    base_ref="origin/${GITHUB_BASE_REF}"
    baseline_raw="$(
      git show "${base_ref}:${baseline_file}" 2>/dev/null \
        | sed -e 's/#.*$//' -e '/^[[:space:]]*$/d' \
        | head -n 1 \
        | tr -d '[:space:]' || true
    )"
    baseline="${baseline_raw}"
  elif [[ -z "${baseline}" && -f "${baseline_file}" ]]; then
    baseline="$(sed -e 's/#.*$//' -e '/^[[:space:]]*$/d' "${baseline_file}" | head -n 1 | tr -d '[:space:]')"
  fi

  if [[ -z "${baseline}" ]]; then
    baseline="$(resolve_commit_governance_bootstrap_baseline)"
    if [[ -z "${baseline}" ]]; then
      echo ""
      return
    fi
  fi

  if normalized="$(git rev-parse --verify --quiet "${baseline}^{commit}" 2>/dev/null)"; then
    echo "${normalized}"
    return
  fi

  echo ""
}

commit_is_after_baseline() {
  local commit="$1"
  local baseline="$2"

  if [[ -z "${baseline}" ]]; then
    return 0
  fi

  if git merge-base --is-ancestor "${commit}" "${baseline}" >/dev/null 2>&1; then
    return 1
  fi

  return 0
}

resolve_commit_governance_branch_name() {
  local branch_name="${GITHUB_HEAD_REF:-}"

  if [[ -n "${branch_name}" ]]; then
    echo "${branch_name}"
    return
  fi

  branch_name="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  if [[ -n "${branch_name}" && "${branch_name}" != "HEAD" ]]; then
    echo "${branch_name}"
    return
  fi

  if [[ -n "${GITHUB_REF_NAME:-}" ]]; then
    echo "${GITHUB_REF_NAME}"
    return
  fi

  echo "${branch_name}"
}

commit_governance_root_dir() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd
}

resolve_atomic_commit_exception_id() {
  local mode="$1"
  local branch="$2"
  local subject="$3"
  local files_list_path="$4"
  local root_dir=""
  root_dir="$(commit_governance_root_dir)"

  python3 - "${root_dir}" "${mode}" "${branch}" "${subject}" "${files_list_path}" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

root_dir = Path(sys.argv[1])
mode = sys.argv[2]
branch = sys.argv[3]
subject = sys.argv[4]
files_list_path = Path(sys.argv[5])
config_path = root_dir / "config/ci/atomic-commit-exceptions.json"

if not config_path.exists():
    raise SystemExit(0)

payload = json.loads(config_path.read_text(encoding="utf-8"))
files = {
    line.strip()
    for line in files_list_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
}

branch_key = "pre_commit_branches" if mode == "pre-commit" else "pre_push_branches"

for exception in payload.get("exceptions", []):
    if mode not in exception.get("modes", []):
        continue
    allowed_branches = exception.get(branch_key, exception.get("branches", []))
    if branch not in allowed_branches:
        continue
    required_paths = set(exception.get("required_paths", []))
    if not required_paths.issubset(files):
        continue
    subject_regex = exception.get("subject_regex")
    if mode == "pre-push" and subject_regex and not re.search(subject_regex, subject):
        continue
    print(exception.get("id", ""))
    raise SystemExit(0)
PY
}
