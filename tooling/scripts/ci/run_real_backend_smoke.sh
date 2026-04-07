#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "${ROOT_DIR}"
# shellcheck source=/dev/null
source "${ROOT_DIR}/tooling/scripts/runtime/cache_env.sh"
MACHINE_CACHE_ROOT="$(resolve_open_notebook_machine_cache_root)"
ensure_open_notebook_machine_cache_layout "${MACHINE_CACHE_ROOT}"

TOOLCHAIN_FILE="${ROOT_DIR}/config/ci-toolchain.env"
if [[ -f "${TOOLCHAIN_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${TOOLCHAIN_FILE}"
fi

PLAYWRIGHT_API_PORT="${PLAYWRIGHT_API_PORT:-15055}"
PLAYWRIGHT_PORT="${PLAYWRIGHT_PORT:-3100}"
SURREAL_BIND="${SURREAL_BIND:-127.0.0.1:38080}"
SURREAL_USER="${SURREAL_USER:-root}"
SURREAL_PASSWORD="${SURREAL_PASSWORD:-root}"
SURREAL_NAMESPACE="${SURREAL_NAMESPACE:-open_notebook}"
SURREAL_DATABASE="${SURREAL_DATABASE:-open_notebook}"
OPEN_NOTEBOOK_PASSWORD="${OPEN_NOTEBOOK_PASSWORD:-open-notebook-test-password}"
SURREAL_CONTAINER="${SURREAL_CONTAINER:-surreal-e2e}"
LOCAL_SURREAL_BIN="${SURREAL_BIN:-$(resolve_open_notebook_machine_surreal_binary_path "${MACHINE_CACHE_ROOT}")}"
SURREAL_VERSION="${CI_SURREAL_VERSION:-2.3.10}"

backend_pid=""
backend_mode=""

sha256_file() {
  local target_file="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$target_file" | awk '{print $1}'
  else
    shasum -a 256 "$target_file" | awk '{print $1}'
  fi
}

platform_slug() {
  local os_name arch_name
  os_name="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch_name="$(uname -m)"
  case "$arch_name" in
    x86_64|amd64)
      arch_name="amd64"
      ;;
    arm64|aarch64)
      arch_name="arm64"
      ;;
    *)
      echo "[real-backend-smoke] WARN: unsupported Surreal architecture '${arch_name}'" >&2
      return 1
      ;;
  esac

  case "$os_name" in
    linux|darwin)
      printf '%s-%s' "$os_name" "$arch_name"
      ;;
    *)
      echo "[real-backend-smoke] WARN: unsupported Surreal platform '${os_name}'" >&2
      return 1
      ;;
  esac
}

expected_surreal_sha256() {
  local slug="$1"
  case "$slug" in
    linux-amd64)
      printf '%s' "${CI_SURREAL_LINUX_AMD64_SHA256:-}"
      ;;
    linux-arm64)
      printf '%s' "${CI_SURREAL_LINUX_ARM64_SHA256:-}"
      ;;
    darwin-amd64)
      printf '%s' "${CI_SURREAL_DARWIN_AMD64_SHA256:-}"
      ;;
    darwin-arm64)
      printf '%s' "${CI_SURREAL_DARWIN_ARM64_SHA256:-}"
      ;;
    *)
      return 1
      ;;
  esac
}

ensure_local_surreal_binary() {
  if [[ -x "${LOCAL_SURREAL_BIN}" ]]; then
    return 0
  fi

  local slug expected_sha asset_name asset_url tmp_dir archive_path actual_sha
  slug="$(platform_slug)" || return 1
  expected_sha="$(expected_surreal_sha256 "${slug}")"
  if [[ -z "${expected_sha}" ]]; then
    echo "[real-backend-smoke] WARN: no pinned checksum for '${slug}'" >&2
    return 1
  fi

  asset_name="surreal-v${SURREAL_VERSION}.${slug}.tgz"
  asset_url="https://github.com/surrealdb/surrealdb/releases/download/v${SURREAL_VERSION}/${asset_name}"
  tmp_dir="$(mktemp -d)"
  archive_path="${tmp_dir}/${asset_name}"

  mkdir -p "$(dirname "${LOCAL_SURREAL_BIN}")"
  echo "[real-backend-smoke] bootstrapping pinned surreal binary: ${asset_name}"
  if ! curl -fsSL --retry 3 --retry-delay 1 "${asset_url}" -o "${archive_path}"; then
    rm -rf "${tmp_dir}"
    echo "[real-backend-smoke] WARN: failed to download ${asset_url}" >&2
    return 1
  fi

  actual_sha="$(sha256_file "${archive_path}")"
  if [[ "${actual_sha}" != "${expected_sha}" ]]; then
    rm -rf "${tmp_dir}"
    echo "[real-backend-smoke] WARN: checksum mismatch for ${asset_name}: expected ${expected_sha}, got ${actual_sha}" >&2
    return 1
  fi

  tar -xzf "${archive_path}" -C "${tmp_dir}"
  if [[ ! -f "${tmp_dir}/surreal" ]]; then
    rm -rf "${tmp_dir}"
    echo "[real-backend-smoke] WARN: surreal binary missing from ${asset_name}" >&2
    return 1
  fi

  install -m 0755 "${tmp_dir}/surreal" "${LOCAL_SURREAL_BIN}"
  rm -rf "${tmp_dir}"
  return 0
}

cleanup() {
  if [[ -n "${backend_pid}" ]] && kill -0 "${backend_pid}" 2>/dev/null; then
    kill "${backend_pid}" >/dev/null 2>&1 || true
    wait "${backend_pid}" >/dev/null 2>&1 || true
  fi
  if [[ "${backend_mode}" == "docker" ]]; then
    docker rm -f "${SURREAL_CONTAINER}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

wait_for_port() {
  local host="$1"
  local port="$2"
  local label="$3"
  for _ in $(seq 1 30); do
    if (echo >"/dev/tcp/${host}/${port}") >/dev/null 2>&1; then
      echo "[real-backend-smoke] ${label} is ready at ${host}:${port}"
      return 0
    fi
    sleep 1
  done
  echo "[real-backend-smoke] ERROR: ${label} did not become ready at ${host}:${port}" >&2
  return 1
}

start_with_local_surreal() {
  echo "[real-backend-smoke] starting local surreal binary: ${LOCAL_SURREAL_BIN}"
  "${LOCAL_SURREAL_BIN}" start --no-banner --bind "${SURREAL_BIND}" --username "${SURREAL_USER}" --password "${SURREAL_PASSWORD}" memory >/tmp/open-notebook-real-smoke-surreal.log 2>&1 &
  backend_pid=$!
  backend_mode="local"
}

start_with_system_surreal() {
  echo "[real-backend-smoke] starting system surreal CLI"
  surreal start --no-banner --bind "${SURREAL_BIND}" --username "${SURREAL_USER}" --password "${SURREAL_PASSWORD}" memory >/tmp/open-notebook-real-smoke-surreal.log 2>&1 &
  backend_pid=$!
  backend_mode="system"
}

start_with_docker() {
  echo "[real-backend-smoke] starting docker surrealdb/surrealdb:v2.3.10"
  docker rm -f "${SURREAL_CONTAINER}" >/dev/null 2>&1 || true
  docker run -d --name "${SURREAL_CONTAINER}" -p "${SURREAL_BIND##*:}:8000" surrealdb/surrealdb:v2.3.10 start --log warn --user "${SURREAL_USER}" --pass "${SURREAL_PASSWORD}" memory >/tmp/open-notebook-real-smoke-surreal.log 2>&1
  backend_mode="docker"
}

bash tooling/scripts/ci/release_local_ports.sh "${PLAYWRIGHT_API_PORT}" "${PLAYWRIGHT_PORT}" "${SURREAL_BIND##*:}"

if ensure_local_surreal_binary; then
  start_with_local_surreal
elif command -v docker >/dev/null 2>&1 && timeout 15 docker info >/dev/null 2>&1; then
  start_with_docker
elif command -v surreal >/dev/null 2>&1; then
  start_with_system_surreal
else
  echo "[real-backend-smoke] ERROR: no local surreal binary, docker daemon, or surreal CLI available" >&2
  exit 1
fi

wait_for_port "${SURREAL_BIND%:*}" "${SURREAL_BIND##*:}" "SurrealDB"

cd apps/web
OPEN_NOTEBOOK_SKIP_MIGRATIONS=false \
PLAYWRIGHT_API_PORT="${PLAYWRIGHT_API_PORT}" \
OPEN_NOTEBOOK_PASSWORD="${OPEN_NOTEBOOK_PASSWORD}" \
SURREAL_EXTERNAL_URL="ws://${SURREAL_BIND}/rpc" \
SURREAL_USER="${SURREAL_USER}" \
SURREAL_PASSWORD="${SURREAL_PASSWORD}" \
SURREAL_NAMESPACE="${SURREAL_NAMESPACE}" \
SURREAL_DATABASE="${SURREAL_DATABASE}" \
npm run test:e2e:real-smoke -- --workers=1
