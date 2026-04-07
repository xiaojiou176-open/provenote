#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"
source tooling/scripts/ci/commit_governance_lib.sh
enforce_commit_governance_env_safety

PATTERN='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9._/-]+\))?(!)?: .{1,100}$'

RANGE="$(resolve_commit_range)"
BASELINE="$(resolve_commit_governance_baseline)"
COMMITS=()
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  COMMITS+=("${line}")
done < <(git rev-list --reverse "${RANGE}" 2>/dev/null || true)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
  echo "[commit-msg-range] skip: no commits in range ${RANGE}"
  exit 0
fi

INVALIDS=()
CHECKED=0
SKIPPED=0
for commit in "${COMMITS[@]}"; do
  if ! commit_is_after_baseline "${commit}" "${BASELINE}"; then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi
  CHECKED=$((CHECKED + 1))

  subject="$(git show -s --format=%s "${commit}")"
  [[ -z "${subject}" ]] && continue
  if [[ "${subject}" =~ ^(Merge|Revert)\  ]]; then
    continue
  fi
  if [[ "${subject}" =~ ^(fixup\!|squash\!) ]]; then
    continue
  fi
  if [[ ! "${subject}" =~ ${PATTERN} ]]; then
    INVALIDS+=("${subject}")
  fi
done

if (( CHECKED == 0 )); then
  if [[ "${GITHUB_ACTIONS:-}" == "true" || "${CI:-}" == "true" ]]; then
    echo "[commit-msg-range] FAIL: no enforceable commits after baseline in CI."
    echo "[commit-msg-range] range=${RANGE} baseline=${BASELINE:-<none>} total=${#COMMITS[@]} skipped=${SKIPPED}"
    exit 1
  fi
  if [[ -n "${BASELINE}" ]]; then
    echo "[commit-msg-range] skip: no commits after baseline ${BASELINE:0:12} in ${RANGE}"
  else
    echo "[commit-msg-range] skip: no enforceable commits in ${RANGE}"
  fi
  exit 0
fi

if [[ ${#INVALIDS[@]} -gt 0 ]]; then
  echo "[commit-msg-range] FAIL: non-conventional commit subject(s) detected in ${RANGE}"
  for subject in "${INVALIDS[@]}"; do
    echo "  - ${subject}"
  done
  echo "[commit-msg-range] required format: <type>(optional-scope): <subject>"
  exit 1
fi

echo "[commit-msg-range] PASS: ${CHECKED} commit subject(s) validated in ${RANGE} (skipped baseline: ${SKIPPED})"
