#!/usr/bin/env bash
set -euo pipefail

MSG_FILE="${1:-}"
if [[ -z "$MSG_FILE" || ! -f "$MSG_FILE" ]]; then
  echo "[commit-msg] ERROR: missing commit message file path"
  echo "usage: bash tooling/scripts/ci/check_commit_message.sh .git/COMMIT_EDITMSG"
  exit 1
fi

FIRST_LINE="$(head -n 1 "$MSG_FILE" | tr -d '\r')"

if [[ -z "$FIRST_LINE" ]]; then
  echo "[commit-msg] ERROR: commit message subject cannot be empty"
  exit 1
fi

if [[ "$FIRST_LINE" =~ ^(Merge|Revert)\  ]]; then
  echo "[commit-msg] skip merge/revert commit message"
  exit 0
fi

if [[ "$FIRST_LINE" =~ ^(fixup\!|squash\!) ]]; then
  echo "[commit-msg] skip fixup!/squash! commit message"
  exit 0
fi

PATTERN='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9._/-]+\))?(!)?: .{1,100}$'
if [[ ! "$FIRST_LINE" =~ $PATTERN ]]; then
  cat <<'USAGE'
[commit-msg] ERROR: invalid conventional commit subject.

Required format:
  <type>(optional-scope): <subject>

Allowed types:
  feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert

Examples:
  feat(api): add transcript pagination cursor
  fix(apps/web): avoid duplicate submit on retry
  docs(ops): document atomic commit guard
USAGE
  echo "[commit-msg] got: $FIRST_LINE"
  exit 1
fi

if (( ${#FIRST_LINE} > 120 )); then
  echo "[commit-msg] ERROR: subject is too long (>120 chars)"
  exit 1
fi

echo "[commit-msg] PASS: $FIRST_LINE"
