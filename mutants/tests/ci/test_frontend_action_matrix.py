from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "tooling/scripts/ci/check_frontend_action_matrix.py"
MATRIX_PATH = REPO_ROOT / "apps/web/e2e/action-matrix.json"


def _run_check(
    matrix_path: Path | None = None,
    runtime_evidence_path: Path | None = None,
    require_runtime_evidence: bool = False,
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPT_PATH)]
    if matrix_path is not None:
        cmd.extend(["--matrix", str(matrix_path)])
    if runtime_evidence_path is not None:
        cmd.extend(["--runtime-evidence", str(runtime_evidence_path)])
    if require_runtime_evidence:
        cmd.append("--require-runtime-evidence")
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _load_matrix(path: Path = MATRIX_PATH) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_runtime_evidence_payload(
    matrix_payload: dict[str, object],
) -> dict[str, object]:
    actions = matrix_payload["actions"]
    entries = []
    for action in actions:
        if action["test_type"] != "real-backend":
            continue
        runtime_evidence = action["runtime_evidence"]
        entries.append(
            {
                "action_id": runtime_evidence["action_id"],
                "spec_id": action["spec_id"],
                "route": action["route"],
                "layers": runtime_evidence["required_layers"],
                "observed_at": "2026-01-01T00:00:00Z",
                "details": {"status": "ok"},
            }
        )
    return {
        "generated_at": "2026-01-01T00:00:00Z",
        "source": "real-backend-smoke.spec.ts",
        "entries": entries,
    }


def test_action_matrix_count_contract_matches_known_baseline() -> None:
    payload = _load_matrix()
    expected = payload["meta"]["expected_counts"]
    actions = payload["actions"]

    counts: Counter[str] = Counter(action["selector_type"] for action in actions)
    assert len(actions) == expected["total"]
    assert counts["data-testid"] == expected["data-testid"]
    assert counts["id"] == expected["id"]
    assert counts["role"] == expected["role"]


def test_action_matrix_has_unique_action_ids() -> None:
    payload = _load_matrix()
    actions = payload["actions"]

    action_ids = [action["action_id"] for action in actions]
    assert len(action_ids) == len(set(action_ids))


def test_action_matrix_requires_route_expected_result_test_type_and_spec_id() -> None:
    payload = _load_matrix()
    actions = payload["actions"]

    for action in actions:
        assert action["route"]
        assert action["expected_result"]
        assert action["test_type"] in {
            "mocked",
            "real-backend",
            "live",
            "a11y",
            "cross-browser-smoke",
        }
        assert action["spec_id"].endswith(".spec.ts")


def test_action_matrix_real_backend_actions_define_runtime_contract() -> None:
    payload = _load_matrix()
    actions = payload["actions"]

    real_backend_actions = [
        action for action in actions if action["test_type"] == "real-backend"
    ]
    assert real_backend_actions
    for action in real_backend_actions:
        runtime_evidence = action["runtime_evidence"]
        assert runtime_evidence["action_id"] == action["action_id"]
        assert runtime_evidence["required_layers"]


def test_check_frontend_action_matrix_script_passes_repo_matrix() -> None:
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS [ACTION-MATRIX-001]" in result.stdout


def test_check_frontend_action_matrix_fails_on_count_mismatch(tmp_path: Path) -> None:
    payload = _load_matrix()
    payload["actions"] = payload["actions"][:-1]

    broken_path = tmp_path / "action-matrix-count-broken.json"
    broken_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    result = _run_check(broken_path)
    assert result.returncode == 1
    assert "FAIL [ACTION-MATRIX-COUNT-001]" in result.stdout


def test_check_frontend_action_matrix_fails_on_role_count_mismatch(
    tmp_path: Path,
) -> None:
    payload = _load_matrix()
    payload["meta"]["expected_counts"]["role"] += 1

    broken_path = tmp_path / "action-matrix-role-count-broken.json"
    broken_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    result = _run_check(broken_path)
    assert result.returncode == 1
    assert "FAIL [ACTION-MATRIX-COUNT-004]" in result.stdout


def test_check_frontend_action_matrix_fails_on_missing_evidence_path(
    tmp_path: Path,
) -> None:
    payload = _load_matrix()
    payload["actions"][0]["paths"] = ["apps/web/e2e/does-not-exist.spec.ts"]

    broken_path = tmp_path / "action-matrix-path-broken.json"
    broken_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    result = _run_check(broken_path)
    assert result.returncode == 1
    assert "FAIL [ACTION-MATRIX-PATH-002]" in result.stdout


def test_check_frontend_action_matrix_fails_on_missing_route_metadata(
    tmp_path: Path,
) -> None:
    payload = _load_matrix()
    payload["actions"][0].pop("route", None)

    broken_path = tmp_path / "action-matrix-metadata-broken.json"
    broken_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    result = _run_check(broken_path)
    assert result.returncode == 1
    assert "FAIL [ACTION-MATRIX-SCHEMA-005]" in result.stdout


def test_check_frontend_action_matrix_runtime_contract_passes_when_complete(
    tmp_path: Path,
) -> None:
    payload = _load_matrix()
    runtime_payload = _build_runtime_evidence_payload(payload)
    runtime_path = tmp_path / "action-matrix-runtime-evidence.json"
    runtime_path.write_text(
        json.dumps(runtime_payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    result = _run_check(
        runtime_evidence_path=runtime_path, require_runtime_evidence=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "runtime=6/6 validated" in result.stdout


def test_check_frontend_action_matrix_fails_when_runtime_is_required_without_file() -> (
    None
):
    result = _run_check(require_runtime_evidence=True)
    assert result.returncode == 1
    assert "FAIL [ACTION-MATRIX-RUNTIME-002]" in result.stdout


def test_check_frontend_action_matrix_fails_on_missing_runtime_entry(
    tmp_path: Path,
) -> None:
    payload = _load_matrix()
    runtime_payload = _build_runtime_evidence_payload(payload)
    runtime_payload["entries"] = runtime_payload["entries"][:-1]

    runtime_path = tmp_path / "action-matrix-runtime-missing-entry.json"
    runtime_path.write_text(
        json.dumps(runtime_payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    result = _run_check(
        runtime_evidence_path=runtime_path, require_runtime_evidence=True
    )
    assert result.returncode == 1
    assert "FAIL [ACTION-MATRIX-RUNTIME-009]" in result.stdout
