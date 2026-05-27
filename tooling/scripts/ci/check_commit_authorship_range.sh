#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"
# shellcheck disable=SC1091
source tooling/scripts/ci/commit_governance_lib.sh
enforce_commit_governance_env_safety

CANONICAL_HUMAN_NAME="${NOTEBOOKLAB_CANONICAL_HUMAN_NAME:-}"
CANONICAL_HUMAN_EMAIL="${NOTEBOOKLAB_CANONICAL_HUMAN_EMAIL:-}"
if [[ -z "${CANONICAL_HUMAN_NAME}" ]]; then
  CANONICAL_HUMAN_NAME="$(git config --get user.name || true)"
fi
if [[ -z "${CANONICAL_HUMAN_EMAIL}" ]]; then
  CANONICAL_HUMAN_EMAIL="$(git config --get user.email || true)"
fi
DEPENDABOT_NAME="dependabot[bot]"
DEPENDABOT_EMAIL="49699333+dependabot[bot]@users.noreply.github.com"
GITHUB_COMMITTER_NAME="GitHub"
GITHUB_COMMITTER_EMAIL="noreply@github.com"

disallowed_identity_marker() {
  local value_lower=""
  value_lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "${value_lower}" in
    *codex*|*openai*|*claude*|*anthropic*|*"artificial intelligence"*|*"artificial-intelligence"*|*人工智能*|*机器人*)
      return 0
      ;;
  esac

  if [[ "${value_lower}" == *bot* && "${value_lower}" != *dependabot* ]]; then
    return 0
  fi

  if [[ "${value_lower}" == *ai* ]]; then
    case "${value_lower}" in
      *gmail*|*main*|*wait*|*detail*|*email*|*said*)
        return 1
        ;;
    esac
    return 0
  fi

  return 1
}

identity_is_human() {
  local name="$1"
  local email="$2"
  if [[ -n "${CANONICAL_HUMAN_NAME}" && -n "${CANONICAL_HUMAN_EMAIL}" ]]; then
    [[ "${name}" == "${CANONICAL_HUMAN_NAME}" && "${email}" == "${CANONICAL_HUMAN_EMAIL}" ]]
    return
  fi
  if [[ -z "${name}" || -z "${email}" ]]; then
    return 1
  fi
  if identity_is_dependabot "${name}" "${email}"; then
    return 1
  fi
  if [[ "${name}" == "${GITHUB_COMMITTER_NAME}" && "${email}" == "${GITHUB_COMMITTER_EMAIL}" ]]; then
    return 1
  fi
  if disallowed_identity_marker "${name}" || disallowed_identity_marker "${email}"; then
    return 1
  fi
  [[ "${email}" == *"@"* ]]
}

identity_is_dependabot() {
  local name="$1"
  local email="$2"
  [[ "${name}" == "${DEPENDABOT_NAME}" && "${email}" == "${DEPENDABOT_EMAIL}" ]]
}

identity_is_allowed_committer() {
  local name="$1"
  local email="$2"
  if identity_is_human "${name}" "${email}"; then
    return 0
  fi
  if identity_is_dependabot "${name}" "${email}"; then
    return 0
  fi
  [[ "${name}" == "${GITHUB_COMMITTER_NAME}" && "${email}" == "${GITHUB_COMMITTER_EMAIL}" ]]
}

RANGE="$(resolve_commit_range)"
BASELINE="$(resolve_commit_governance_baseline)"
COMMITS=()
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  COMMITS+=("${line}")
done < <(git rev-list --reverse "${RANGE}" 2>/dev/null || true)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
  if report_empty_enforceable_commit_set "commit-authorship-range" "${RANGE}" "${BASELINE}" "0" "0"; then
    exit 0
  fi
  echo "[commit-authorship-range] skip: no commits in range ${RANGE}"
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
  author_name="$(git show -s --format=%an "${commit}")"
  author_email="$(git show -s --format=%ae "${commit}")"
  committer_name="$(git show -s --format=%cn "${commit}")"
  committer_email="$(git show -s --format=%ce "${commit}")"
  body="$(git show -s --format=%B "${commit}")"
  subject="$(git show -s --format=%s "${commit}")"

  if [[ "${subject}" =~ ^Merge\ pull\ request\ \# ]] && [[ "${author_name}" == "${GITHUB_COMMITTER_NAME}" && "${author_email}" == "${GITHUB_COMMITTER_EMAIL}" ]]; then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  CHECKED=$((CHECKED + 1))

  if ! identity_is_human "${author_name}" "${author_email}" && ! identity_is_dependabot "${author_name}" "${author_email}"; then
    INVALIDS+=("${commit}: disallowed author ${author_name} <${author_email}>")
  fi

  if ! identity_is_allowed_committer "${committer_name}" "${committer_email}"; then
    INVALIDS+=("${commit}: disallowed committer ${committer_name} <${committer_email}>")
  fi

  if ! identity_is_dependabot "${author_name}" "${author_email}"; then
    for token in "${author_name}" "${author_email}" "${committer_name}" "${committer_email}"; do
      if disallowed_identity_marker "${token}"; then
        INVALIDS+=("${commit}: disallowed identity marker in '${token}'")
      fi
    done
  fi

  while IFS= read -r trailer; do
    [[ -z "${trailer}" ]] && continue
    normalized_trailer="$(printf '%s\n' "${trailer}" | sed -E 's/^[Cc][Oo]-[Aa][Uu][Tt][Hh][Oo][Rr][Ee][Dd]-[Bb][Yy]:/Co-authored-by:/')"
    if [[ ! "${normalized_trailer}" =~ ^Co-authored-by:[[:space:]]*(.+)[[:space:]]\<([^>]*)\>$ ]]; then
      INVALIDS+=("${commit}: malformed co-author trailer '${trailer}'")
      continue
    fi
    trailer_name="${BASH_REMATCH[1]}"
    trailer_email="${BASH_REMATCH[2]}"
    if ! identity_is_human "${trailer_name}" "${trailer_email}"; then
      INVALIDS+=("${commit}: co-author trailer must stay on the configured maintainer identity, got ${trailer_name} <${trailer_email}>")
    fi
    if disallowed_identity_marker "${trailer_name}" || disallowed_identity_marker "${trailer_email}"; then
      INVALIDS+=("${commit}: disallowed co-author identity marker in ${trailer_name} <${trailer_email}>")
    fi
  done < <(printf '%s\n' "${body}" | grep -i '^Co-authored-by:[[:space:]]*' || true)
done

if (( CHECKED == 0 )); then
  if report_empty_enforceable_commit_set "commit-authorship-range" "${RANGE}" "${BASELINE}" "${#COMMITS[@]}" "${SKIPPED}"; then
    exit 0
  fi
  if [[ "${GITHUB_ACTIONS:-}" == "true" || "${CI:-}" == "true" ]]; then
    echo "[commit-authorship-range] FAIL: no enforceable commits after baseline in CI."
    echo "[commit-authorship-range] range=${RANGE} baseline=${BASELINE:-<none>} total=${#COMMITS[@]} skipped=${SKIPPED}"
    exit 1
  fi
  if [[ -n "${BASELINE}" ]]; then
    echo "[commit-authorship-range] skip: no commits after baseline ${BASELINE:0:12} in ${RANGE}"
  else
    echo "[commit-authorship-range] skip: no enforceable commits in ${RANGE}"
  fi
  exit 0
fi

if [[ ${#INVALIDS[@]} -gt 0 ]]; then
  echo "[commit-authorship-range] FAIL: disallowed authorship metadata detected in ${RANGE}"
  for item in "${INVALIDS[@]}"; do
    echo "  - ${item}"
  done
  exit 1
fi

echo "[commit-authorship-range] PASS: ${CHECKED} commit authorship record(s) validated in ${RANGE} (skipped baseline: ${SKIPPED})"
