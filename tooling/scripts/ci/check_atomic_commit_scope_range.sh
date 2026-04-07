#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"
source tooling/scripts/ci/commit_governance_lib.sh
enforce_commit_governance_env_safety

MAX_FILES="${ATOMIC_COMMIT_MAX_FILES:-20}"
MAX_TOP_LEVEL="${ATOMIC_COMMIT_MAX_TOP_LEVEL:-3}"

RANGE="$(resolve_commit_range)"
BASELINE="$(resolve_commit_governance_baseline)"
COMMITS=()
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  COMMITS+=("${line}")
done < <(git rev-list --reverse "${RANGE}" 2>/dev/null || true)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
  if report_empty_enforceable_commit_set "atomic-commit-range" "${RANGE}" "${BASELINE}" "0" "0"; then
    exit 0
  fi
  echo "[atomic-commit-range] skip: no commits in range ${RANGE}"
  exit 0
fi

FAILURES=0
SKIPPED=0
CHECKED=0
for commit in "${COMMITS[@]}"; do
  if ! commit_is_after_baseline "${commit}" "${BASELINE}"; then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi
  CHECKED=$((CHECKED + 1))

  FILES=()
  while IFS= read -r path; do
    [[ -z "${path}" ]] && continue
    FILES+=("${path}")
  done < <(git diff-tree --no-commit-id --name-only -r --diff-filter=ACMRT "${commit}")
  file_count="${#FILES[@]}"
  if (( file_count == 0 )); then
    continue
  fi

  top_level_lines=""
  for path in "${FILES[@]}"; do
    top="${path%%/*}"
    if [[ "${top}" == "${path}" ]]; then
      top="(repo-root)"
    fi
    top_level_lines+="${top}"$'\n'
  done
  top_level_count="$(
    printf '%s' "${top_level_lines}" \
      | sed '/^$/d' \
      | sort -u \
      | wc -l \
      | tr -d ' '
  )"

  if (( file_count > MAX_FILES || top_level_count > MAX_TOP_LEVEL )); then
    subject="$(git show -s --format=%s "${commit}")"
    tmp_files="$(mktemp)"
    printf '%s\n' "${FILES[@]}" > "${tmp_files}"
    branch_name="$(resolve_commit_governance_branch_name)"
    exception_id="$(resolve_atomic_commit_exception_id "pre-push" "${branch_name}" "${subject}" "${tmp_files}")"
    rm -f "${tmp_files}"
    if [[ -n "${exception_id}" ]]; then
      echo "[atomic-commit-range] ALLOW: ${commit} ${subject}"
      echo "  - exception: ${exception_id}"
      echo "  - files: ${file_count}, top-level scopes: ${top_level_count}"
      continue
    fi

    FAILURES=$((FAILURES + 1))
    echo "[atomic-commit-range] FAIL: ${commit} ${subject}"
    echo "  - files: ${file_count} (max ${MAX_FILES})"
    echo "  - top-level scopes: ${top_level_count} (max ${MAX_TOP_LEVEL})"
  fi
done

if (( CHECKED == 0 )); then
  if report_empty_enforceable_commit_set "atomic-commit-range" "${RANGE}" "${BASELINE}" "${#COMMITS[@]}" "${SKIPPED}"; then
    exit 0
  fi
  if [[ "${GITHUB_ACTIONS:-}" == "true" || "${CI:-}" == "true" ]]; then
    echo "[atomic-commit-range] FAIL: no enforceable commits after baseline in CI."
    echo "[atomic-commit-range] range=${RANGE} baseline=${BASELINE:-<none>} total=${#COMMITS[@]} skipped=${SKIPPED}"
    exit 1
  fi
  if [[ -n "${BASELINE}" ]]; then
    echo "[atomic-commit-range] skip: no commits after baseline ${BASELINE:0:12} in ${RANGE}"
  else
    echo "[atomic-commit-range] skip: no enforceable commits in ${RANGE}"
  fi
  exit 0
fi

if (( FAILURES > 0 )); then
  echo "[atomic-commit-range] FAIL: ${FAILURES} commit(s) violate atomic scope limits"
  exit 1
fi

echo "[atomic-commit-range] PASS: ${CHECKED} commit(s) validated in ${RANGE} (skipped baseline: ${SKIPPED})"
