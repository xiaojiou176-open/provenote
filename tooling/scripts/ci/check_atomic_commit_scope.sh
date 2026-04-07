#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"
source tooling/scripts/ci/commit_governance_lib.sh

MAX_FILES="${ATOMIC_COMMIT_MAX_FILES:-20}"
MAX_TOP_LEVEL="${ATOMIC_COMMIT_MAX_TOP_LEVEL:-3}"
ENFORCE="${ATOMIC_COMMIT_ENFORCE:-0}"

STAGED_FILES=()
while IFS= read -r line; do
  STAGED_FILES+=("$line")
done < <(git diff --cached --name-only --diff-filter=ACMRT)

if (( ${#STAGED_FILES[@]} == 0 )); then
  echo "[atomic-commit] skip: no staged files"
  exit 0
fi

TOP_LEVEL_LINES=""
for path in "${STAGED_FILES[@]}"; do
  top="${path%%/*}"
  if [[ "$top" == "$path" ]]; then
    top="(repo-root)"
  fi
  TOP_LEVEL_LINES+="${top}"$'\n'
done

TOP_LEVEL_COUNT="$(
  printf '%s' "$TOP_LEVEL_LINES" \
    | sed '/^$/d' \
    | sort -u \
    | wc -l \
    | tr -d ' '
)"
FILE_COUNT="${#STAGED_FILES[@]}"

WARNINGS=()
if (( FILE_COUNT > MAX_FILES )); then
  WARNINGS+=("staged files ${FILE_COUNT} > ${MAX_FILES}")
fi
if (( TOP_LEVEL_COUNT > MAX_TOP_LEVEL )); then
  WARNINGS+=("touched top-level scopes ${TOP_LEVEL_COUNT} > ${MAX_TOP_LEVEL}")
fi

if (( ${#WARNINGS[@]} == 0 )); then
  echo "[atomic-commit] PASS: ${FILE_COUNT} files across ${TOP_LEVEL_COUNT} scope(s)"
  exit 0
fi

echo "[atomic-commit] WARN: potential non-atomic commit detected"
echo "[atomic-commit] staged files: ${FILE_COUNT}, top-level scopes: ${TOP_LEVEL_COUNT}"
for warn in "${WARNINGS[@]}"; do
  echo "  - ${warn}"
done

echo "[atomic-commit] tip: split with 'git add -p' and follow docs/development.md"

tmp_files="$(mktemp)"
trap 'rm -f "${tmp_files}"' EXIT
printf '%s\n' "${STAGED_FILES[@]}" > "${tmp_files}"

branch_name="$(resolve_commit_governance_branch_name)"
exception_id="$(resolve_atomic_commit_exception_id "pre-commit" "${branch_name}" "" "${tmp_files}")"
if [[ -n "${exception_id}" ]]; then
  echo "[atomic-commit] ALLOW: audited migration exception '${exception_id}' matched on branch ${branch_name}"
  exit 0
fi

if [[ "$ENFORCE" == "1" ]]; then
  echo "[atomic-commit] ENFORCED: blocking commit (ATOMIC_COMMIT_ENFORCE=1)"
  exit 1
fi

exit 0
