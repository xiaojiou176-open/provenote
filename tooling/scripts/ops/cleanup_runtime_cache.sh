#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
RUNTIME_CACHE_DIR="${RUNTIME_CACHE_DIR:-${PROJECT_ROOT}/.runtime-cache}"
SPACE_SURFACES_REGISTRY="${SPACE_SURFACES_REGISTRY:-${PROJECT_ROOT}/config/runtime/space-surfaces.json}"
# shellcheck source=/dev/null
source "${PROJECT_ROOT}/tooling/scripts/runtime/cache_env.sh"
LOG_DIR="${LOG_DIR:-$(resolve_open_notebook_runtime_logs_dir "${PROJECT_ROOT}" "local")}"
MANAGED_VENV_DIR="${RUNTIME_CACHE_DIR}/venv"
NEXTJS_CACHE_DIR="${NEXTJS_CACHE_DIR:-$(resolve_open_notebook_repo_next_build_dir "${PROJECT_ROOT}")/cache}"
PLAYWRIGHT_REPORT_DIR="${PLAYWRIGHT_REPORT_DIR:-$(resolve_open_notebook_runtime_evidence_dir "${PROJECT_ROOT}" "playwright/report")}"
PLAYWRIGHT_RESULTS_DIR="${PLAYWRIGHT_RESULTS_DIR:-$(resolve_open_notebook_runtime_evidence_dir "${PROJECT_ROOT}" "playwright/results")}"

# Data directories
DATA_DIR="${PROJECT_ROOT}/.runtime-cache/state/local/data"
UPLOADS_DIR="${DATA_DIR}/uploads"
TIKTOKEN_CACHE_DIR="${DATA_DIR}/tiktoken-cache"
SQLITE_DB_DIR="${DATA_DIR}/sqlite-db"
CHECKPOINTS_DB="${SQLITE_DB_DIR}/checkpoints.sqlite"

# Test cache directories
PYTEST_CACHE_DIR="${RUNTIME_CACHE_DIR}/test/pytest_cache"
HYPOTHESIS_DIR="${RUNTIME_CACHE_DIR}/test/hypothesis"
BENCHMARKS_DIR="${RUNTIME_CACHE_DIR}/test/benchmarks"
RETRY_REPORTS_DIR="$(resolve_open_notebook_runtime_reports_dir "${PROJECT_ROOT}" "test-retry")"
LEGACY_PYTEST_CACHE_DIR="${PROJECT_ROOT}/.pytest_cache"
LEGACY_HYPOTHESIS_DIR="${PROJECT_ROOT}/.hypothesis"
LEGACY_BENCHMARKS_DIR="${PROJECT_ROOT}/.benchmarks"
LEGACY_EGG_INFO_DIR="${PROJECT_ROOT}/open_notebook.egg-info"
CURRENT_EGG_INFO_DIR="${PROJECT_ROOT}/notebooklab.egg-info"
CURRENT_AUDITABLE_EGG_INFO_DIR="${PROJECT_ROOT}/auditable_markdown_workbench.egg-info"
LEGACY_COVERAGE_FILE="${PROJECT_ROOT}/.coverage"
MUTANTS_ROOT="${PROJECT_ROOT}/mutants"
MUTANTS_RUNTIME_CACHE_DIR="${MUTANTS_ROOT}/.runtime-cache"
MUTANTS_LEGACY_PYTEST_CACHE_DIR="${MUTANTS_ROOT}/.pytest_cache"
MUTANTS_LEGACY_BENCHMARKS_DIR="${MUTANTS_ROOT}/.benchmarks"
MUTANTS_LEGACY_EGG_INFO_DIR="${MUTANTS_ROOT}/open_notebook.egg-info"

MAX_AGE_DAYS="${MAX_AGE_DAYS:-7}"
RUNTIME_CACHE_MAX_MB="${RUNTIME_CACHE_MAX_MB:-2048}"
LOGS_MAX_MB="${LOGS_MAX_MB:-512}"
NEXTJS_CACHE_MAX_MB="${NEXTJS_CACHE_MAX_MB:-1024}"
PLAYWRIGHT_MAX_MB="${PLAYWRIGHT_MAX_MB:-512}"
UPLOADS_MAX_MB="${UPLOADS_MAX_MB:-5120}"
TIKTOKEN_CACHE_MAX_MB="${TIKTOKEN_CACHE_MAX_MB:-256}"
PYTEST_CACHE_MAX_MB="${PYTEST_CACHE_MAX_MB:-128}"
TARGET_USAGE_PERCENT="${TARGET_USAGE_PERCENT:-80}"
DRY_RUN=false
SKIP_VACUUM=false

LOCK_ROOT="${PROJECT_ROOT}/.runtime-cache/locks"
LOCK_DIR="${LOCK_ROOT}/cleanup_runtime_cache.lock"
PROTECTED_PRUNE_PATHS=()
PRUNE_PATH_ARGS=()

usage() {
  cat <<EOF
Usage: $(basename "$0") [--dry-run] [--max-age-days N]

Options:
  --dry-run         Print planned deletions without removing files.
  --max-age-days N  Delete files older than N days (default: 7).
  --runtime-cache-max-mb N  Enforce runtime cache directory cap in MB (default: 2048).
  --logs-max-mb N   Enforce logs directory cap in MB (default: 512).
  --nextjs-cache-max-mb N   Enforce Next.js cache cap in MB (default: 1024).
  --playwright-max-mb N     Enforce Playwright artifacts cap in MB (default: 512).
  --uploads-max-mb N        Enforce uploads directory cap in MB (default: 5120).
  --tiktoken-cache-max-mb N Enforce tiktoken cache cap in MB (default: 256).
  --pytest-cache-max-mb N   Enforce pytest/hypothesis cache cap in MB (default: 128).
  --skip-vacuum     Skip SQLite VACUUM operation.
  --target-usage-percent N
                    Size cleanup target percent after trimming oldest files (default: 80).
  --runtime-cache-dir PATH
                    Override runtime cache directory (default: .runtime-cache).
  --logs-dir PATH   Override logs directory (default: .runtime-cache/logs).
  -h, --help        Show this help message.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --max-age-days)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --max-age-days" >&2
        exit 1
      fi
      MAX_AGE_DAYS="$2"
      shift 2
      ;;
    --runtime-cache-max-mb)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --runtime-cache-max-mb" >&2
        exit 1
      fi
      RUNTIME_CACHE_MAX_MB="$2"
      shift 2
      ;;
    --logs-max-mb)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --logs-max-mb" >&2
        exit 1
      fi
      LOGS_MAX_MB="$2"
      shift 2
      ;;
    --nextjs-cache-max-mb)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --nextjs-cache-max-mb" >&2
        exit 1
      fi
      NEXTJS_CACHE_MAX_MB="$2"
      shift 2
      ;;
    --playwright-max-mb)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --playwright-max-mb" >&2
        exit 1
      fi
      PLAYWRIGHT_MAX_MB="$2"
      shift 2
      ;;
    --uploads-max-mb)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --uploads-max-mb" >&2
        exit 1
      fi
      UPLOADS_MAX_MB="$2"
      shift 2
      ;;
    --tiktoken-cache-max-mb)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --tiktoken-cache-max-mb" >&2
        exit 1
      fi
      TIKTOKEN_CACHE_MAX_MB="$2"
      shift 2
      ;;
    --pytest-cache-max-mb)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --pytest-cache-max-mb" >&2
        exit 1
      fi
      PYTEST_CACHE_MAX_MB="$2"
      shift 2
      ;;
    --skip-vacuum)
      SKIP_VACUUM=true
      shift
      ;;
    --target-usage-percent)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --target-usage-percent" >&2
        exit 1
      fi
      TARGET_USAGE_PERCENT="$2"
      shift 2
      ;;
    --runtime-cache-dir)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --runtime-cache-dir" >&2
        exit 1
      fi
      RUNTIME_CACHE_DIR="$2"
      shift 2
      ;;
    --logs-dir)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --logs-dir" >&2
        exit 1
      fi
      LOG_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! [[ "$MAX_AGE_DAYS" =~ ^[0-9]+$ ]]; then
  echo "--max-age-days must be a non-negative integer" >&2
  exit 1
fi

if ! [[ "$RUNTIME_CACHE_MAX_MB" =~ ^[0-9]+$ ]]; then
  echo "--runtime-cache-max-mb must be a non-negative integer" >&2
  exit 1
fi

if ! [[ "$LOGS_MAX_MB" =~ ^[0-9]+$ ]]; then
  echo "--logs-max-mb must be a non-negative integer" >&2
  exit 1
fi

if ! [[ "$NEXTJS_CACHE_MAX_MB" =~ ^[0-9]+$ ]]; then
  echo "--nextjs-cache-max-mb must be a non-negative integer" >&2
  exit 1
fi

if ! [[ "$PLAYWRIGHT_MAX_MB" =~ ^[0-9]+$ ]]; then
  echo "--playwright-max-mb must be a non-negative integer" >&2
  exit 1
fi

if ! [[ "$UPLOADS_MAX_MB" =~ ^[0-9]+$ ]]; then
  echo "--uploads-max-mb must be a non-negative integer" >&2
  exit 1
fi

if ! [[ "$TIKTOKEN_CACHE_MAX_MB" =~ ^[0-9]+$ ]]; then
  echo "--tiktoken-cache-max-mb must be a non-negative integer" >&2
  exit 1
fi

if ! [[ "$PYTEST_CACHE_MAX_MB" =~ ^[0-9]+$ ]]; then
  echo "--pytest-cache-max-mb must be a non-negative integer" >&2
  exit 1
fi

if ! [[ "$TARGET_USAGE_PERCENT" =~ ^[0-9]+$ ]] || (( TARGET_USAGE_PERCENT < 10 || TARGET_USAGE_PERCENT > 100 )); then
  echo "--target-usage-percent must be an integer between 10 and 100" >&2
  exit 1
fi

log() {
  printf '[cleanup_runtime_cache] %s\n' "$*"
}

space_surface_field_for_path() {
  local target_path="$1"
  local field="$2"
  python3 - "$SPACE_SURFACES_REGISTRY" "$target_path" "$field" <<'PY'
import json
import sys
from pathlib import Path

registry_path = Path(sys.argv[1])
target_path = Path(sys.argv[2]).resolve()
field = sys.argv[3]
payload = json.loads(registry_path.read_text(encoding="utf-8"))

for item in payload.get("surfaces", []):
    raw_path = item.get("path", "")
    if not isinstance(raw_path, str) or "*" in raw_path:
        continue
    candidate = Path(raw_path.replace("${HOME}", str(Path.home()))).expanduser()
    if not candidate.is_absolute():
        candidate = (registry_path.parents[2] / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if candidate == target_path:
        value = item.get(field, "")
        print("" if value is None else value)
        raise SystemExit(0)
raise SystemExit(1)
PY
}

cleanup_policy_allows_dir() {
  local target_dir="$1"
  local label="$2"
  local surface_scope=""
  local surface_action=""

  surface_scope="$(space_surface_field_for_path "$target_dir" "scope" 2>/dev/null || true)"
  surface_action="$(space_surface_field_for_path "$target_dir" "default_action" 2>/dev/null || true)"

  if [[ -z "$surface_scope" || -z "$surface_action" ]]; then
    log "skip ${label}: undeclared in space-surfaces registry (${target_dir})"
    return 1
  fi

  if [[ "$surface_scope" != "repo_internal" ]]; then
    log "skip ${label}: non-repo-internal surface is never repo cleanup eligible (${target_dir})"
    return 1
  fi

  case "$surface_action" in
    safe_clear|cautious_clear)
      return 0
      ;;
    verify_before_clear|do_not_clear)
      log "skip ${label}: space policy requires manual review (${surface_action}) for ${target_dir}"
      return 1
      ;;
    *)
      log "skip ${label}: unknown space policy action ${surface_action} for ${target_dir}"
      return 1
      ;;
  esac
}

load_protected_prune_paths() {
  while IFS= read -r path; do
    [[ -n "$path" ]] || continue
    PROTECTED_PRUNE_PATHS+=("$path")
  done < <(
    python3 - "$SPACE_SURFACES_REGISTRY" "$PROJECT_ROOT" <<'PY'
import json
import sys
from pathlib import Path

registry_path = Path(sys.argv[1])
project_root = Path(sys.argv[2]).resolve()
payload = json.loads(registry_path.read_text(encoding="utf-8"))

for item in payload.get("surfaces", []):
    if item.get("scope") != "repo_internal":
        continue
    if item.get("default_action") not in {"verify_before_clear", "do_not_clear"}:
        continue
    raw_path = item.get("path", "")
    if not isinstance(raw_path, str) or "*" in raw_path:
        continue
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    runtime_root = (project_root / ".runtime-cache").resolve()
    if str(candidate).startswith(str(runtime_root)):
        print(candidate)
PY
  )
}

build_prune_path_args() {
  PRUNE_PATH_ARGS=(
    '('
    -path "${RUNTIME_CACHE_DIR}/bin"
    -o -path "${RUNTIME_CACHE_DIR}/bin/*"
    -o -path "${MANAGED_VENV_DIR}"
    -o -path "${MANAGED_VENV_DIR}/*"
  )

  local protected_path
  for protected_path in "${PROTECTED_PRUNE_PATHS[@]}"; do
    PRUNE_PATH_ARGS+=(-o -path "${protected_path}" -o -path "${protected_path}/*")
  done

  PRUNE_PATH_ARGS+=(')' -prune -o)
}

dir_size_bytes() {
  local target_dir="$1"
  du -sk "$target_dir" | awk '{print $1 * 1024}'
}

file_size_bytes() {
  local target_file="$1"
  wc -c < "$target_file" | tr -d '[:space:]'
}

file_mtime_epoch() {
  local target_file="$1"
  if [[ "$(uname -s)" == "Darwin" ]]; then
    stat -f "%m" "$target_file" 2>/dev/null
  else
    stat -c "%Y" "$target_file" 2>/dev/null
  fi
}

cleanup_dir_by_age() {
  local target_dir="$1"

  if [[ ! -d "$target_dir" ]]; then
    log "skip (not found): $target_dir"
    return
  fi

  log "scanning: $target_dir (older than ${MAX_AGE_DAYS} days)"

  local files_to_delete=()
  while IFS= read -r -d '' file; do
    files_to_delete+=("$file")
  done < <(
    find "$target_dir" \
      "${PRUNE_PATH_ARGS[@]}" \
      -type f \
      -mtime +"$MAX_AGE_DAYS" \
      ! -name '.gitkeep' \
      -print0
  )

  if [[ "${#files_to_delete[@]}" -eq 0 ]]; then
    log "no files to clean in $target_dir"
    return
  fi

  for file in "${files_to_delete[@]}"; do
    if [[ "$DRY_RUN" == true ]]; then
      log "[dry-run] delete file: $file"
    else
      rm -f -- "$file"
      log "deleted file: $file"
    fi
  done

}

enforce_size_limit() {
  local target_dir="$1"
  local max_mb="$2"
  local label="$3"

  if [[ ! -d "$target_dir" ]]; then
    return
  fi

  if (( max_mb == 0 )); then
    log "skip size cleanup for ${label} (max_mb=0): $target_dir"
    return
  fi

  local limit_bytes=$((max_mb * 1024 * 1024))
  local target_bytes=$((limit_bytes * TARGET_USAGE_PERCENT / 100))
  local current_bytes
  current_bytes="$(dir_size_bytes "$target_dir")"

  if (( current_bytes <= limit_bytes )); then
    log "size within limit for ${label}: ${current_bytes} bytes <= ${limit_bytes} bytes"
    return
  fi

  log "size limit exceeded for ${label}: ${current_bytes} bytes > ${limit_bytes} bytes; trimming to ${target_bytes} bytes"

  local candidates_file
  candidates_file="$(mktemp)"

  while IFS= read -r -d '' file; do
    local mtime
    mtime="$(file_mtime_epoch "$file" || echo 0)"
    printf '%s\t%s\n' "$mtime" "$file" >> "$candidates_file"
  done < <(
    find "$target_dir" \
      "${PRUNE_PATH_ARGS[@]}" \
      -type f \
      ! -name '.gitkeep' \
      -print0
  )

  while IFS=$'\t' read -r _mtime file; do
    if (( current_bytes <= target_bytes )); then
      break
    fi

    if [[ ! -f "$file" ]]; then
      continue
    fi

    local file_bytes
    file_bytes="$(file_size_bytes "$file")"

    if [[ "$DRY_RUN" == true ]]; then
      log "[dry-run] trim ${label}: $file (${file_bytes} bytes)"
    else
      rm -f -- "$file"
      log "trimmed ${label}: $file (${file_bytes} bytes)"
    fi

    current_bytes=$((current_bytes - file_bytes))
    if (( current_bytes < 0 )); then
      current_bytes=0
    fi
  done < <(sort -n "$candidates_file")

  rm -f "$candidates_file"
  log "post-trim estimate for ${label}: ${current_bytes} bytes"
}

cleanup_empty_dirs() {
  local target_dir="$1"
  if [[ ! -d "$target_dir" ]]; then
    return
  fi

  while IFS= read -r -d '' dir; do
    local protected_path=""
    if [[ "$dir" == "$LOCK_ROOT" || "$dir" == "$LOCK_ROOT/"* ]]; then
      continue
    fi
    for protected_path in "${PROTECTED_PRUNE_PATHS[@]}"; do
      if [[ "$dir" == "$protected_path" || "$dir" == "$protected_path/"* ]]; then
        continue 2
      fi
    done

    if [[ "$DRY_RUN" == true ]]; then
      log "[dry-run] delete empty dir: $dir"
    else
      rmdir -- "$dir" 2>/dev/null || true
    fi
  done < <(find "$target_dir" -depth -type d -empty ! -path "$target_dir" -print0)
}

cleanup_dir() {
  local target_dir="$1"
  local max_mb="$2"
  local label="$3"

  if ! cleanup_policy_allows_dir "$target_dir" "$label"; then
    return
  fi

  cleanup_dir_by_age "$target_dir"
  enforce_size_limit "$target_dir" "$max_mb" "$label"
  cleanup_empty_dirs "$target_dir"
}

purge_legacy_root_dir() {
  local target_dir="$1"
  local label="$2"

  if [[ ! -d "$target_dir" ]]; then
    return
  fi

  if [[ "$DRY_RUN" == true ]]; then
    log "[dry-run] purge legacy ${label}: $target_dir"
    return
  fi

  find "$target_dir" -mindepth 1 -depth -delete 2>/dev/null || true
  rmdir -- "$target_dir" 2>/dev/null || true
  log "purged legacy ${label}: $target_dir"
}

purge_named_dirs_under_tree() {
  local root_dir="$1"
  local dir_name="$2"
  local label="$3"

  if [[ ! -d "$root_dir" ]]; then
    return
  fi

  while IFS= read -r -d '' target_dir; do
    if [[ "$DRY_RUN" == true ]]; then
      log "[dry-run] purge ${label}: ${target_dir}"
      continue
    fi

    find "$target_dir" -mindepth 1 -depth -delete 2>/dev/null || true
    rmdir -- "$target_dir" 2>/dev/null || true
    log "purged ${label}: ${target_dir}"
  done < <(find "$root_dir" -type d -name "$dir_name" -print0 2>/dev/null)
}

vacuum_sqlite_db() {
  local db_path="$1"
  local label="$2"

  if [[ ! -f "$db_path" ]]; then
    log "skip vacuum (not found): $db_path"
    return
  fi

  if [[ "$SKIP_VACUUM" == true ]]; then
    log "skip vacuum (--skip-vacuum): $db_path"
    return
  fi

  local size_before
  size_before="$(file_size_bytes "$db_path")"

  if [[ "$DRY_RUN" == true ]]; then
    log "[dry-run] vacuum ${label}: $db_path (${size_before} bytes)"
    return
  fi

  if ! command -v sqlite3 &>/dev/null; then
    log "skip vacuum (sqlite3 not found): $db_path"
    return
  fi

  log "vacuuming ${label}: $db_path (${size_before} bytes)"
  sqlite3 "$db_path" "VACUUM;"

  local size_after
  size_after="$(file_size_bytes "$db_path")"
  local saved=$((size_before - size_after))
  log "vacuum complete for ${label}: ${size_before} -> ${size_after} bytes (saved ${saved} bytes)"
}

load_protected_prune_paths
build_prune_path_args

log "project root: $PROJECT_ROOT"
log "dry-run: $DRY_RUN"
log "max-age-days: $MAX_AGE_DAYS"
log "runtime-cache-dir: $RUNTIME_CACHE_DIR (max ${RUNTIME_CACHE_MAX_MB} MB)"
log "logs-dir: $LOG_DIR (max ${LOGS_MAX_MB} MB)"
log "nextjs-cache-dir: $NEXTJS_CACHE_DIR (max ${NEXTJS_CACHE_MAX_MB} MB)"
log "playwright-report-dir: $PLAYWRIGHT_REPORT_DIR (max ${PLAYWRIGHT_MAX_MB} MB)"
log "playwright-results-dir: $PLAYWRIGHT_RESULTS_DIR (max ${PLAYWRIGHT_MAX_MB} MB)"
log "uploads-dir: $UPLOADS_DIR (max ${UPLOADS_MAX_MB} MB)"
log "tiktoken-cache-dir: $TIKTOKEN_CACHE_DIR (max ${TIKTOKEN_CACHE_MAX_MB} MB)"
log "pytest-cache-dir: $PYTEST_CACHE_DIR (max ${PYTEST_CACHE_MAX_MB} MB)"
log "hypothesis-dir: $HYPOTHESIS_DIR (max ${PYTEST_CACHE_MAX_MB} MB)"
log "benchmarks-dir: $BENCHMARKS_DIR (max ${PYTEST_CACHE_MAX_MB} MB)"
log "skip-vacuum: $SKIP_VACUUM"
log "target-usage-percent: $TARGET_USAGE_PERCENT"
if (( ${#PROTECTED_PRUNE_PATHS[@]} > 0 )); then
  log "protected runtime subtrees: ${PROTECTED_PRUNE_PATHS[*]}"
fi

mkdir -p "$LOCK_ROOT"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  # Recover from stale lock directories left by interrupted processes.
  # Age threshold: 1 hour.
  lock_mtime="$(file_mtime_epoch "$LOCK_DIR" || echo 0)"
  now_epoch="$(date +%s)"
  lock_age_seconds="$((now_epoch - lock_mtime))"
  if (( lock_mtime > 0 && lock_age_seconds > 3600 )); then
    log "stale lock detected (${LOCK_DIR}, age=${lock_age_seconds}s); attempting recovery"
    rmdir "$LOCK_DIR" >/dev/null 2>&1 || true
    if mkdir "$LOCK_DIR" 2>/dev/null; then
      log "recovered stale lock: ${LOCK_DIR}"
    else
      log "skip: another cleanup process is active (${LOCK_DIR})"
      exit 0
    fi
  else
    log "skip: another cleanup process is active (${LOCK_DIR})"
    exit 0
  fi
fi
trap 'rmdir "$LOCK_DIR" >/dev/null 2>&1 || true' EXIT

cleanup_dir "$RUNTIME_CACHE_DIR" "$RUNTIME_CACHE_MAX_MB" "runtime-cache"
cleanup_dir "$LOG_DIR" "$LOGS_MAX_MB" "logs"
cleanup_dir "$RETRY_REPORTS_DIR" "$PLAYWRIGHT_MAX_MB" "retry-reports"

# Frontend build artifacts cleanup
if [[ -d "$NEXTJS_CACHE_DIR" ]]; then
  cleanup_dir "$NEXTJS_CACHE_DIR" "$NEXTJS_CACHE_MAX_MB" "nextjs-cache"
fi

# Playwright test artifacts cleanup
if [[ -d "$PLAYWRIGHT_REPORT_DIR" ]]; then
  cleanup_dir "$PLAYWRIGHT_REPORT_DIR" "$PLAYWRIGHT_MAX_MB" "playwright-report"
fi
if [[ -d "$PLAYWRIGHT_RESULTS_DIR" ]]; then
  cleanup_dir "$PLAYWRIGHT_RESULTS_DIR" "$PLAYWRIGHT_MAX_MB" "playwright-results"
fi

# Data directories cleanup
if [[ -d "$UPLOADS_DIR" ]]; then
  cleanup_dir "$UPLOADS_DIR" "$UPLOADS_MAX_MB" "uploads"
fi
if [[ -d "$TIKTOKEN_CACHE_DIR" ]]; then
  cleanup_dir "$TIKTOKEN_CACHE_DIR" "$TIKTOKEN_CACHE_MAX_MB" "tiktoken-cache"
fi

# SQLite checkpoint maintenance is intentionally skipped because the parent
# local data root is governed as verify-before-clear rather than auto-clean.
log "skip checkpoints-db vacuum: protected local state root (${CHECKPOINTS_DB})"

# Test cache cleanup
if [[ -d "$PYTEST_CACHE_DIR" ]]; then
  cleanup_dir "$PYTEST_CACHE_DIR" "$PYTEST_CACHE_MAX_MB" "pytest-cache"
fi
if [[ -d "$HYPOTHESIS_DIR" ]]; then
  cleanup_dir "$HYPOTHESIS_DIR" "$PYTEST_CACHE_MAX_MB" "hypothesis-cache"
fi
if [[ -d "$BENCHMARKS_DIR" ]]; then
  cleanup_dir "$BENCHMARKS_DIR" "$PYTEST_CACHE_MAX_MB" "benchmark-cache"
fi

purge_legacy_root_dir "$LEGACY_PYTEST_CACHE_DIR" "pytest-cache"
purge_legacy_root_dir "$LEGACY_HYPOTHESIS_DIR" "hypothesis-cache"
purge_legacy_root_dir "$LEGACY_BENCHMARKS_DIR" "benchmark-cache"
purge_legacy_root_dir "$LEGACY_EGG_INFO_DIR" "editable-metadata"
purge_legacy_root_dir "$CURRENT_EGG_INFO_DIR" "editable-metadata"
purge_legacy_root_dir "$CURRENT_AUDITABLE_EGG_INFO_DIR" "editable-metadata"
purge_named_dirs_under_tree "${PROJECT_ROOT}/tests" "__pycache__" "tests pycache"
purge_named_dirs_under_tree "${MUTANTS_ROOT}" "__pycache__" "mutants pycache"
purge_legacy_root_dir "$MUTANTS_LEGACY_PYTEST_CACHE_DIR" "mutants pytest-cache"
purge_legacy_root_dir "$MUTANTS_LEGACY_BENCHMARKS_DIR" "mutants benchmark-cache"
purge_legacy_root_dir "$MUTANTS_LEGACY_EGG_INFO_DIR" "mutants editable-metadata"
if [[ -f "$LEGACY_COVERAGE_FILE" ]]; then
  if [[ "$DRY_RUN" == true ]]; then
    log "[dry-run] purge legacy coverage file: $LEGACY_COVERAGE_FILE"
  else
    rm -f -- "$LEGACY_COVERAGE_FILE"
    log "purged legacy coverage file: $LEGACY_COVERAGE_FILE"
  fi
fi
if [[ -d "$MUTANTS_ROOT" ]]; then
  mkdir -p "$MUTANTS_RUNTIME_CACHE_DIR/test"
fi

log "done"
