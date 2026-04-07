#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PYPROJECT_PATH="${ROOT_DIR}/pyproject.toml"
TEMP_DIR="${ROOT_DIR}/.runtime-cache/temp"
mkdir -p "${TEMP_DIR}"

PROFILE_INPUT="${MUTATION_PROFILE:-}"
VALIDATE_ONLY="${MUTATION_PROFILE_VALIDATE_ONLY:-0}"

if [[ -n "${MUTATION_MAX_CHILDREN:-}" ]]; then
  MAX_CHILDREN="${MUTATION_MAX_CHILDREN}"
else
  CPU_COUNT="$(getconf _NPROCESSORS_ONLN 2>/dev/null || true)"
  if [[ -z "${CPU_COUNT}" && "$(uname -s)" == "Darwin" ]]; then
    CPU_COUNT="$(sysctl -n hw.logicalcpu 2>/dev/null || true)"
  fi
  if [[ -z "${CPU_COUNT}" || "${CPU_COUNT}" -lt 1 ]]; then
    CPU_COUNT=4
  fi
  MAX_CHILDREN="${CPU_COUNT}"
  if [[ "${MAX_CHILDREN}" -gt 8 ]]; then
    MAX_CHILDREN=8
  fi
fi

BACKUP_PATH="$(mktemp "${TEMP_DIR}/pyproject.toml.backup.XXXXXX")"
RENDERED_PATH="$(mktemp "${TEMP_DIR}/pyproject.toml.rendered.XXXXXX")"
BASELINE_STATS_PATH="$(mktemp "${TEMP_DIR}/mutation-baseline.XXXXXX.json")"
RUNTIME_SURVIVOR_TEST="${ROOT_DIR}/tests/test_mutation_survivor_killers_runtime.py"
RUNTIME_SURVIVOR_TEST_SELECTION="tests/test_mutation_survivor_killers_runtime.py"
SURVIVOR_TEST_SOURCE="${ROOT_DIR}/mutants/tests/test_mutation_survivor_killers.py"
LOCAL_MUTATION_CLEANUP="${LOCAL_MUTATION_CLEANUP:-}"

if [[ -z "${LOCAL_MUTATION_CLEANUP}" ]]; then
  if [[ -n "${CI:-}" ]]; then
    LOCAL_MUTATION_CLEANUP=0
  else
    LOCAL_MUTATION_CLEANUP=1
  fi
fi

cleanup() {
  if [[ -f "${BACKUP_PATH}" ]]; then
    cp "${BACKUP_PATH}" "${PYPROJECT_PATH}"
  fi
  rm -f "${BACKUP_PATH}" "${RENDERED_PATH}" "${BASELINE_STATS_PATH}" "${RUNTIME_SURVIVOR_TEST}"
  rm -rf \
    "${ROOT_DIR}/open_notebook.egg-info" \
    "${ROOT_DIR}/mutants/.pytest_cache" \
    "${ROOT_DIR}/mutants/.benchmarks" \
    "${ROOT_DIR}/mutants/open_notebook.egg-info" 2>/dev/null || true
  if [[ "${LOCAL_MUTATION_CLEANUP}" == "1" ]] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git restore --worktree --source=HEAD -- \
      mutants/packages/core/utils/chunking.py \
      mutants/packages/core/utils/text_utils.py \
      mutants/mutmut-cicd-stats.json \
      mutants/mutmut-stats.json \
      mutants/mutation-guard-report.json >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

cp "${PYPROJECT_PATH}" "${BACKUP_PATH}"
if [[ -f "${SURVIVOR_TEST_SOURCE}" ]]; then
  cp "${SURVIVOR_TEST_SOURCE}" "${RUNTIME_SURVIVOR_TEST}"
  export MUTATION_EXTRA_TEST_SELECTION="${RUNTIME_SURVIVOR_TEST_SELECTION}"
else
  export MUTATION_EXTRA_TEST_SELECTION=""
fi

SELECTED_PROFILE="$(
  python3 - "${PYPROJECT_PATH}" "${PROFILE_INPUT}" "${RENDERED_PATH}" <<'PY'
import os
import pathlib
import sys
import tomllib

pyproject = pathlib.Path(sys.argv[1])
profile_input = sys.argv[2].strip()
rendered_path = pathlib.Path(sys.argv[3])
text = pyproject.read_text(encoding="utf-8")
data = tomllib.loads(text)

profiles = (
    data.get("tool", {})
    .get("open_notebook", {})
    .get("mutation_profiles", {})
)

default_profile = profiles.get("default", "core")
profile_name = profile_input or default_profile
profile_cfg = profiles.get(profile_name)
if not isinstance(profile_cfg, dict):
    available = sorted([k for k, v in profiles.items() if isinstance(v, dict)])
    raise SystemExit(
        f"Unknown MUTATION_PROFILE={profile_name!r}. Available profiles: {available}"
    )

paths = profile_cfg.get("paths_to_mutate", [])
tests = profile_cfg.get("pytest_add_cli_args_test_selection", [])
if not paths or not tests:
    raise SystemExit(
        f"Profile {profile_name!r} must define non-empty paths_to_mutate and "
        "pytest_add_cli_args_test_selection"
    )

lines = text.splitlines()
start = None
end = None
for i, line in enumerate(lines):
    if line.strip() == "[tool.mutmut]":
        start = i
        continue
    if start is not None and line.startswith("[") and i > start:
        end = i
        break

if start is None:
    raise SystemExit("Cannot locate [tool.mutmut] block in pyproject.toml")
if end is None:
    end = len(lines)

def to_list_block(key: str, items: list[str]) -> list[str]:
    block = [f"{key} = ["]
    block.extend([f'    "{item}",' for item in items])
    block.append("]")
    return block

replacement = [
    "[tool.mutmut]",
    *to_list_block("paths_to_mutate", paths),
    *to_list_block("pytest_add_cli_args_test_selection", tests),
    'also_copy = ["packages/core/settings.py", "packages/core/utils/encryption.py", "api"]',
    'do_not_mutate = ["*/site-packages/*", "*/tests/*"]',
]

extra_test = os.environ.get("MUTATION_EXTRA_TEST_SELECTION", "").strip()
if extra_test:
    for line in to_list_block("pytest_add_cli_args_test_selection", [*tests, extra_test]):
        if line.startswith("pytest_add_cli_args_test_selection"):
            replacement = [
                entry
                for entry in replacement
                if not entry.startswith("pytest_add_cli_args_test_selection")
            ]
            break
    replacement = [
        "[tool.mutmut]",
        *to_list_block("paths_to_mutate", paths),
        *to_list_block("pytest_add_cli_args_test_selection", [*tests, extra_test]),
        'also_copy = ["packages/core/settings.py", "packages/core/utils/encryption.py", "api"]',
        'do_not_mutate = ["*/site-packages/*", "*/tests/*"]',
    ]

new_lines = lines[:start] + replacement + lines[end:]
rendered_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print(profile_name)
PY
)"

cp "${RENDERED_PATH}" "${PYPROJECT_PATH}"
echo "[mutation-profile] profile=${SELECTED_PROFILE} max_children=${MAX_CHILDREN}"

if [[ "${VALIDATE_ONLY}" == "1" ]]; then
  echo "[mutation-profile] validate-only mode: configuration rendered successfully"
  exit 0
fi

cd "${ROOT_DIR}"
if [[ -f "mutants/mutmut-cicd-stats.json" ]]; then
  cp "mutants/mutmut-cicd-stats.json" "${BASELINE_STATS_PATH}"
else
  rm -f "${BASELINE_STATS_PATH}"
fi
bash tooling/scripts/runtime/run_uv_managed.sh run mutmut run --max-children="${MAX_CHILDREN}"
bash tooling/scripts/runtime/run_uv_managed.sh run mutmut export-cicd-stats
if [[ -f "${BASELINE_STATS_PATH}" ]]; then
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_mutation_guard.py --baseline-stats "${BASELINE_STATS_PATH}"
else
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_mutation_guard.py
fi
bash tooling/scripts/runtime/run_uv_managed.sh run python - <<'PY'
import json
from pathlib import Path

stats_path = Path("mutants/mutmut-cicd-stats.json")
if not stats_path.exists():
    raise SystemExit(0)
stats = json.loads(stats_path.read_text(encoding="utf-8"))
total = int(stats.get("total", 0))
killed = int(stats.get("killed", 0))
survived = int(stats.get("survived", 0))
if total > 0:
    score = (killed / total) * 100.0
    survived_ratio = (survived / total) * 100.0
    print(
        f"[mutation-profile] post-run-summary "
        f"total={total} killed={killed} survived={survived} "
        f"score={score:.2f}% survived_ratio={survived_ratio:.2f}%"
    )
PY
bash tooling/scripts/runtime/run_uv_managed.sh run mutmut results
