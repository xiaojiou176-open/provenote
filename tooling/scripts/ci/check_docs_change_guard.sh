#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"

MODE="pre-commit"

usage() {
  cat <<USAGE
Usage: $(basename "$0") [--mode pre-commit|pre-push]
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[docs-change-guard] ERROR: unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ "${MODE}" != "pre-commit" && "${MODE}" != "pre-push" ]]; then
  echo "[docs-change-guard] ERROR: invalid mode '${MODE}', expected pre-commit or pre-push."
  exit 1
fi

is_ci_context() {
  [[ "${GITHUB_ACTIONS:-}" == "true" || "${CI:-}" == "true" ]]
}

if is_ci_context && [[ -n "${SKIP_DOCS_CHANGE_GUARD:-}" ]]; then
  echo "[docs-change-guard] FAIL: SKIP_DOCS_CHANGE_GUARD is forbidden in CI."
  exit 1
fi

if [[ "${SKIP_DOCS_CHANGE_GUARD:-0}" == "1" ]]; then
  echo "[docs-change-guard] skipped via SKIP_DOCS_CHANGE_GUARD=1"
  exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[docs-change-guard] ERROR: not inside a git repository."
  exit 1
fi

collect_files_pre_commit() {
  git diff --cached --name-only --diff-filter=ACMR
}

collect_files_pre_push() {
  local upstream_ref=""
  local merge_base=""
  local fallback_ref=""

  if upstream_ref="$(git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null)"; then
    merge_base="$(git merge-base HEAD "${upstream_ref}" 2>/dev/null || true)"
    if [[ -n "${merge_base}" ]]; then
      git diff --name-only --diff-filter=ACMR "${merge_base}..HEAD"
      return
    fi
    git diff --name-only --diff-filter=ACMR "${upstream_ref}...HEAD"
    return
  fi

  for ref in origin/main origin/master main master; do
    if git rev-parse --verify --quiet "${ref}" >/dev/null 2>&1; then
      fallback_ref="${ref}"
      break
    fi
    if git rev-parse --verify --quiet "refs/remotes/${ref}" >/dev/null 2>&1; then
      fallback_ref="refs/remotes/${ref}"
      break
    fi
  done

  if [[ -n "${fallback_ref}" ]]; then
    merge_base="$(git merge-base HEAD "${fallback_ref}" 2>/dev/null || true)"
    if [[ -n "${merge_base}" ]]; then
      git diff --name-only --diff-filter=ACMR "${merge_base}..HEAD"
      return
    fi
    git diff --name-only --diff-filter=ACMR "${fallback_ref}...HEAD"
    return
  fi

  # Last-resort fallback when no upstream/default branch is available.
  git diff-tree --no-commit-id --name-only -r HEAD --diff-filter=ACMR
}

CHANGED_FILES=()
if [[ "${MODE}" == "pre-push" ]]; then
  while IFS= read -r file; do
    [[ -n "${file}" ]] || continue
    CHANGED_FILES+=("${file}")
  done < <(collect_files_pre_push)
else
  while IFS= read -r file; do
    [[ -n "${file}" ]] || continue
    CHANGED_FILES+=("${file}")
  done < <(collect_files_pre_commit)
fi

if [[ ${#CHANGED_FILES[@]} -eq 0 ]]; then
  echo "[docs-change-guard] no changed files (mode=${MODE})."
  exit 0
fi

has_doc_change=0
has_trigger_change=0

# Code/config paths that can change repo contract and should be accompanied by docs updates.
TRIGGER_PATTERNS=(
  'services/api/**'
  'packages/core/**'
  'services/worker/**'
  'apps/web/src/**'
  'tooling/scripts/ci/**'
  '.github/workflows/**'
  'pyproject.toml'
  'uv.lock'
  'requirements*.txt'
  'apps/web/package.json'
  'apps/web/package-lock.json'
  'apps/web/tsconfig*.json'
  '.env.example'
)

# Documentation entrypoints accepted as companion updates.
DOC_PATTERNS=(
  'docs/**'
  'README*.md'
  'AGENTS.md'
  'CLAUDE.md'
)

SEARCH_CMD_PRIMARY='rg -n "<keyword>" AGENTS.md CLAUDE.md README*.md docs config contracts tooling services packages apps tests ops evals mutants'
SEARCH_CMD_INDEX="rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*.md'"
SEARCH_EVIDENCE_HIT_REGEX='[A-Za-z0-9_./-]+:[0-9]+'

SEARCH_EVIDENCE_TRIGGER_PATTERNS=(
  'AGENTS.md'
  'CLAUDE.md'
  'tooling/scripts/ci/check_navigation_docs_pair.py'
  'tooling/scripts/ci/check_docs_change_guard.sh'
)

get_file_content() {
  local file="$1"
  if [[ "${MODE}" == "pre-commit" ]]; then
    if git cat-file -e ":${file}" 2>/dev/null; then
      git show ":${file}" 2>/dev/null || true
      return
    fi
  fi
  if [[ -f "${file}" ]]; then
    cat "${file}"
  fi
}

for file in "${CHANGED_FILES[@]}"; do
  for pattern in "${DOC_PATTERNS[@]}"; do
    # shellcheck disable=SC2053
    if [[ "$file" == $pattern ]]; then
      has_doc_change=1
      break
    fi
  done

  for pattern in "${TRIGGER_PATTERNS[@]}"; do
    # shellcheck disable=SC2053
    if [[ "$file" == $pattern ]]; then
      has_trigger_change=1
      break
    fi
  done
done

if [[ ${has_trigger_change} -eq 1 && ${has_doc_change} -eq 0 ]]; then
  echo "[docs-change-guard] FAIL: code/config changes detected without docs updates (mode=${MODE})."
  echo "[docs-change-guard] Add at least one docs file in this change set: docs/**, README*.md, AGENTS.md, or CLAUDE.md."
  echo "[docs-change-guard] Changed files:"
  for file in "${CHANGED_FILES[@]}"; do
    echo "  - ${file}"
  done
  exit 1
fi

require_search_evidence=0
for file in "${CHANGED_FILES[@]}"; do
  for pattern in "${SEARCH_EVIDENCE_TRIGGER_PATTERNS[@]}"; do
    # shellcheck disable=SC2053
    if [[ "$file" == $pattern ]]; then
      require_search_evidence=1
      break
    fi
  done
done

if [[ ${require_search_evidence} -eq 1 ]]; then
  has_search_cmd_primary=0
  has_search_cmd_index=0
  has_search_hit=0

  for file in "${CHANGED_FILES[@]}"; do
    is_doc_file=0
    for pattern in "${DOC_PATTERNS[@]}"; do
      # shellcheck disable=SC2053
      if [[ "$file" == $pattern ]]; then
        is_doc_file=1
        break
      fi
    done

    if [[ ${is_doc_file} -eq 0 ]]; then
      continue
    fi

    content="$(get_file_content "$file")"
    if [[ -z "${content}" ]]; then
      continue
    fi

    if grep -Fq "${SEARCH_CMD_PRIMARY}" <<<"${content}"; then
      has_search_cmd_primary=1
    fi
    if grep -Fq "${SEARCH_CMD_INDEX}" <<<"${content}"; then
      has_search_cmd_index=1
    fi
    if grep -Eq "${SEARCH_EVIDENCE_HIT_REGEX}" <<<"${content}"; then
      has_search_hit=1
    fi
  done

  if [[ ${has_search_cmd_primary} -ne 1 || ${has_search_cmd_index} -ne 1 || ${has_search_hit} -ne 1 ]]; then
    echo "[docs-change-guard] FAIL: navigation/gate related changes require Search-Before-Write evidence."
    echo "[docs-change-guard] Add/keep evidence in changed docs with:"
    echo "  1) command: ${SEARCH_CMD_PRIMARY}"
    echo "  2) command: ${SEARCH_CMD_INDEX}"
    echo "  3) at least one hit token like path:line (e.g. README.md:1)"
    exit 1
  fi
fi

echo "[docs-change-guard] PASS (mode=${MODE}, changed=${#CHANGED_FILES[@]})"
exit 0
