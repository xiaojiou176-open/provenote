from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_WORKFLOW = REPO_ROOT / ".github/workflows/test.yml"
AUDITABLE_WORKFLOW = REPO_ROOT / ".github/workflows/auditable-quality-gate.yml"

LEGACY_API_FILTER = '"services/services/api/**"'
CANONICAL_API_FILTER = '"services/api/**"'


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_active_workflows_do_not_reference_legacy_api_filter_path() -> None:
    for workflow_path in (TEST_WORKFLOW, AUDITABLE_WORKFLOW):
        workflow = _read(workflow_path)
        assert LEGACY_API_FILTER not in workflow, (
            f"{workflow_path.name} must not reference the legacy API filter path "
            f"{LEGACY_API_FILTER}"
        )


def test_tests_workflow_heavy_change_filters_reference_canonical_api_path() -> None:
    workflow = _read(TEST_WORKFLOW)
    assert workflow.count(CANONICAL_API_FILTER) >= 3, (
        f"{TEST_WORKFLOW.name} must use the canonical API filter path "
        f"{CANONICAL_API_FILTER} for heavy job change detection"
    )


def test_auditable_workflow_is_manual_only_advisory() -> None:
    workflow = _read(AUDITABLE_WORKFLOW)
    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
    assert "push:" not in workflow
    assert "name: Promptfoo Evaluation" in workflow
    assert "name: Ragas Evaluation" in workflow
    assert "name: Property Tests" not in workflow
