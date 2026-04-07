#!/usr/bin/env bash
#
# Heavy pre-commit checks that are moved to pre-push
# to improve local commit speed.
#
# Run manually with: git commit -m "message" && bash tooling/scripts/hooks/heavy_checks.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$REPO_ROOT"

echo "🔍 Running heavy quality checks..."

# These checks are computationally expensive or network-dependent
# They run on pre-push instead of pre-commit

# 1. Full mypy type check (can be slow on large codebases)
echo "→ Full mypy type check..."
bash tooling/scripts/runtime/run_uv_managed.sh run --extra dev python -m mypy services packages tooling || {
    echo "❌ Mypy type check failed"
    exit 1
}

# 2. Frontend build check (ensures no build-time errors)
echo "→ Frontend build check..."
cd apps/web
npm run build > /dev/null 2>&1 || {
    echo "❌ Frontend build failed"
    exit 1
}
cd ..

# 3. Pre-commit outdated check (network call)
echo "→ Pre-commit hooks freshness check..."
pre-commit autoupdate --freeze 2>&1 | grep -q "already up to date" || {
    echo "⚠️  Some pre-commit hooks have updates available"
    echo "    Run: pre-commit autoupdate"
}

echo "✅ Heavy checks passed"
