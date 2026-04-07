#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

# Optional override in CI/local: space-separated patterns like "apps/web/e2e/foo.spec.ts:12"
SMELL_SKIP_ALLOWLIST="${SMELL_SKIP_ALLOWLIST:-}"
SMELL_WEAK_ASSERT_ALLOWLIST="${SMELL_WEAK_ASSERT_ALLOWLIST:-}"

# Built-in temporary allowlist entries. Format: file:line|YYYY-MM-DD|reason
# Keep this list short and force expiry to prevent permanent test.skip accumulation.
declare -a BUILTIN_SKIP_ALLOWLIST=(
  "apps/web/e2e/real-backend-smoke.spec.ts:9|2026-06-30|Conditional guard for PLAYWRIGHT_REAL_BACKEND optional local runs"
)
declare -a BUILTIN_WEAK_ASSERT_ALLOWLIST=()
declare -a BUILTIN_HARD_WAIT_ALLOWLIST=()

TODAY="$(date +%F)"
FAILED=0

is_allowed_skip() {
  local key="$1"

  for raw in "${BUILTIN_SKIP_ALLOWLIST[@]-}"; do
    local entry expiry reason
    entry="${raw%%|*}"
    expiry="$(printf '%s' "$raw" | cut -d'|' -f2)"
    reason="$(printf '%s' "$raw" | cut -d'|' -f3-)"

    if [[ "$entry" == "$key" ]]; then
      if [[ "$TODAY" > "$expiry" ]]; then
        echo "EXPIRED_ALLOWLIST|$expiry|$reason"
        return 1
      fi
      echo "ALLOWLIST|$expiry|$reason"
      return 0
    fi
  done

  if [[ -n "$SMELL_SKIP_ALLOWLIST" ]]; then
    for extra in $SMELL_SKIP_ALLOWLIST; do
      if [[ "$extra" == "$key" ]]; then
        echo "ALLOWLIST|env|SMELL_SKIP_ALLOWLIST"
        return 0
      fi
    done
  fi

  return 1
}

is_allowed_weak_assert() {
  local key="$1"

  for raw in "${BUILTIN_WEAK_ASSERT_ALLOWLIST[@]-}"; do
    local entry expiry reason
    entry="${raw%%|*}"
    expiry="$(printf '%s' "$raw" | cut -d'|' -f2)"
    reason="$(printf '%s' "$raw" | cut -d'|' -f3-)"

    if [[ "$entry" == "$key" ]]; then
      if [[ "$TODAY" > "$expiry" ]]; then
        echo "EXPIRED_ALLOWLIST|$expiry|$reason"
        return 1
      fi
      echo "ALLOWLIST|$expiry|$reason"
      return 0
    fi
  done

  if [[ -n "$SMELL_WEAK_ASSERT_ALLOWLIST" ]]; then
    for extra in $SMELL_WEAK_ASSERT_ALLOWLIST; do
      if [[ "$extra" == "$key" ]]; then
        echo "ALLOWLIST|env|SMELL_WEAK_ASSERT_ALLOWLIST"
        return 0
      fi
    done
  fi

  return 1
}

is_allowed_hard_wait() {
  local key="$1"

  for raw in "${BUILTIN_HARD_WAIT_ALLOWLIST[@]-}"; do
    local entry expiry reason
    entry="${raw%%|*}"
    expiry="$(printf '%s' "$raw" | cut -d'|' -f2)"
    reason="$(printf '%s' "$raw" | cut -d'|' -f3-)"

    if [[ "$entry" == "$key" ]]; then
      if [[ "$TODAY" > "$expiry" ]]; then
        echo "EXPIRED_ALLOWLIST|$expiry|$reason"
        return 1
      fi
      echo "ALLOWLIST|$expiry|$reason"
      return 0
    fi
  done

  if [[ -n "$SMELL_SKIP_ALLOWLIST" ]]; then
    for extra in $SMELL_SKIP_ALLOWLIST; do
      if [[ "$extra" == "$key" ]]; then
        echo "ALLOWLIST|env|SMELL_SKIP_ALLOWLIST"
        return 0
      fi
    done
  fi

  return 1
}

collect_matches() {
  local regex="$1"
  local includes=(
    --glob '*.test.{js,jsx,ts,tsx,mjs,cjs}'
    --glob '*.spec.{js,jsx,ts,tsx,mjs,cjs}'
    --glob 'apps/web/e2e/*.{js,jsx,ts,tsx,mjs,cjs}'
  )

  if command -v rg >/dev/null 2>&1; then
    local output
    local status
    set +e
    output="$(
      rg -n --no-heading --color never --hidden \
        --glob '!**/node_modules/**' \
        --glob '!**/.next/**' \
        --glob '!**/dist/**' \
        --glob '!**/coverage/**' \
        "${includes[@]}" \
        "$regex" .
    )"
    status=$?
    set -e
    if [[ $status -eq 1 ]]; then
      return 0
    fi
    if [[ $status -ne 0 ]]; then
      echo "[test-smells] rg failed while evaluating regex: $regex" >&2
      exit $status
    fi
    printf '%s\n' "$output"
  else
    grep -RInE --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=coverage \
      --include='*.test.js' --include='*.test.jsx' --include='*.test.ts' --include='*.test.tsx' \
      --include='*.spec.js' --include='*.spec.jsx' --include='*.spec.ts' --include='*.spec.tsx' \
      "$regex" . || true
  fi
}

echo "[test-smells] Checking focused tests (.only / it.only / test.only / describe.only)"
ONLY_MATCHES="$(collect_matches '\.only\s*\(')"
if [[ -n "$ONLY_MATCHES" ]]; then
  echo "$ONLY_MATCHES"
  echo
  echo "[test-smells] ERROR: Found forbidden .only(...) usage. Remove focused tests before merge."
  FAILED=1
fi

echo "[test-smells] Checking skipped tests (it.skip / test.skip / describe.skip)"
SKIP_MATCHES="$(collect_matches '\b(it|test|describe)\.skip\s*\(')"
if [[ -n "$SKIP_MATCHES" ]]; then
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    file="${row%%:*}"
    file="${file#./}"
    rest="${row#*:}"
    line="${rest%%:*}"
    key="$file:$line"

    set +e
    allow_result="$(is_allowed_skip "$key")"
    allow_status=$?
    set -e

    if [[ $allow_status -eq 0 ]]; then
      echo "[test-smells] WARN: Allowed skip: $key ($allow_result)"
      continue
    fi

    if [[ "$allow_result" == EXPIRED_ALLOWLIST* ]]; then
      echo "[test-smells] ERROR: Expired skip allowlist: $key ($allow_result)"
      FAILED=1
      continue
    fi

    echo "[test-smells] ERROR: Disallowed skip: $key"
    echo "[test-smells]        Add a temporary allowlist entry with expiry in tooling/scripts/ci/check_test_smells.sh"
    FAILED=1
  done <<< "$SKIP_MATCHES"
fi

echo "[test-smells] Checking fake truth assertions (e.g. expect(true).toBe(true))"
FAKE_ASSERT_MATCHES="$(
  collect_matches 'expect\s*\(\s*true\s*\)\s*\.\s*to(Be|Equal|StrictEqual)\s*\(\s*true\s*\)|expect\s*\(\s*false\s*\)\s*\.\s*to(Be|Equal|StrictEqual)\s*\(\s*false\s*\)'
)"
if [[ -n "$FAKE_ASSERT_MATCHES" ]]; then
  echo "$FAKE_ASSERT_MATCHES"
  echo
  echo "[test-smells] ERROR: Found fake assertions with constant truth values."
  echo "[test-smells]        Replace with behavior-based assertions that can fail on regressions."
  FAILED=1
fi

echo "[test-smells] Checking tautological assertions (literal/identifier self-assertions)"
IDENTICAL_LITERAL_MATCHES="$(
  python3 tooling/scripts/ci/check_identical_literal_assertions.py
)"
if [[ -n "$IDENTICAL_LITERAL_MATCHES" ]]; then
  echo "$IDENTICAL_LITERAL_MATCHES"
  echo
  echo "[test-smells] ERROR: Found tautological assertions."
  echo "[test-smells]        Avoid self-assertions like expect(x).toBe(x) or expect('a').toBe('a')."
  FAILED=1
fi

echo "[test-smells] Checking weak assertions (.toBeDefined/.toBeTruthy/.toBeFalsy)"
WEAK_ASSERT_MATCHES="$(
  collect_matches '\.\s*to(BeDefined|BeTruthy|BeFalsy)\s*\('
)"
if [[ -n "$WEAK_ASSERT_MATCHES" ]]; then
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    file="${row%%:*}"
    file="${file#./}"
    rest="${row#*:}"
    line="${rest%%:*}"
    key="$file:$line"

    set +e
    allow_result="$(is_allowed_weak_assert "$key")"
    allow_status=$?
    set -e

    if [[ $allow_status -eq 0 ]]; then
      echo "[test-smells] WARN: Allowed weak assertion: $key ($allow_result)"
      continue
    fi

    if [[ "$allow_result" == EXPIRED_ALLOWLIST* ]]; then
      echo "[test-smells] ERROR: Expired weak-assert allowlist: $key ($allow_result)"
      FAILED=1
      continue
    fi

    echo "[test-smells] ERROR: Disallowed weak assertion: $key"
    echo "[test-smells]        Avoid .toBeDefined/.toBeTruthy/.toBeFalsy; use specific value/shape assertions."
    echo "[test-smells]        If unavoidable, add temporary allowlist with expiry in tooling/scripts/ci/check_test_smells.sh"
    FAILED=1
  done <<< "$WEAK_ASSERT_MATCHES"
fi

echo "[test-smells] Checking hard waits (page.waitForTimeout)"
HARD_WAIT_MATCHES="$(
  collect_matches 'page\.waitForTimeout\s*\('
)"
if [[ -n "$HARD_WAIT_MATCHES" ]]; then
  while IFS= read -r row; do
    [[ -z "$row" ]] && continue
    file="${row%%:*}"
    file="${file#./}"
    rest="${row#*:}"
    line="${rest%%:*}"
    key="$file:$line"

    set +e
    allow_result="$(is_allowed_hard_wait "$key")"
    allow_status=$?
    set -e

    if [[ $allow_status -eq 0 ]]; then
      echo "[test-smells] WARN: Allowed hard wait: $key ($allow_result)"
      continue
    fi

    if [[ "$allow_result" == EXPIRED_ALLOWLIST* ]]; then
      echo "[test-smells] ERROR: Expired hard-wait allowlist: $key ($allow_result)"
      FAILED=1
      continue
    fi

    echo "[test-smells] ERROR: Disallowed hard wait: $key"
    echo "[test-smells]        Replace page.waitForTimeout(...) with deterministic waits."
    echo "[test-smells]        If unavoidable, add temporary allowlist with expiry in tooling/scripts/ci/check_test_smells.sh"
    FAILED=1
  done <<< "$HARD_WAIT_MATCHES"
fi

if [[ $FAILED -ne 0 ]]; then
  echo "[test-smells] FAILED"
  exit 1
fi

echo "[test-smells] PASSED"
