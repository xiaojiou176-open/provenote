#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"
uv sync

cd "${ROOT_DIR}/apps/web"
npm ci
npm run test:e2e:install
