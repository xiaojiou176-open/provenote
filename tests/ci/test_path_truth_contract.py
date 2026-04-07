from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CURRENT_FACING_DOCS = (
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "tests/README.md",
    "docs/index.md",
    "docs/installation.md",
    "docs/configuration.md",
    "docs/development.md",
    "docs/architecture.md",
    ".github/ISSUE_TEMPLATE/installation_issue.yml",
)

FORBIDDEN_TOKENS = (
    "services/services/api",
    "packages/packages/prompts",
    "tooling/tooling/scripts",
    ".runtime-cache/artifacts/staging",
    "frontend/",
)

BAD_BACKEND_COVERAGE_XML_PATH = "/".join(
    (
        ".runtime-cache/test/coverage/backend",
        ".runtime-cache/test/coverage/backend/coverage.xml",
    )
)

STRICT_COVERAGE_PATH_TARGETS = (
    "CLAUDE.md",
    "Makefile",
    "tests/README.md",
)

STRICT_EXECUTION_SURFACES = (
    ".devcontainer/postCreate.sh",
    "Makefile",
)

FORBIDDEN_EXECUTION_TOKENS = (
    'cd "${ROOT_DIR}/frontend"',
    "lfnovo/open_notebook",
    "ghcr.io/lfnovo/open-notebook",
)


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def test_path_truth_gate_script_exists() -> None:
    assert (REPO_ROOT / "tooling/scripts/ci/check_path_truth_drift.py").exists()


def test_current_facing_docs_do_not_reference_known_stale_paths() -> None:
    for rel_path in CURRENT_FACING_DOCS:
        text = _read(rel_path)
        for token in FORBIDDEN_TOKENS:
            assert token not in text, f"{rel_path} still contains {token}"


def test_strict_coverage_path_targets_do_not_reference_duplicated_backend_xml_path() -> (
    None
):
    for rel_path in STRICT_COVERAGE_PATH_TARGETS:
        text = _read(rel_path)
        assert BAD_BACKEND_COVERAGE_XML_PATH not in text, (
            f"{rel_path} still contains duplicated backend coverage XML path"
        )


def test_strict_execution_surfaces_do_not_reference_stale_execution_tokens() -> None:
    for rel_path in STRICT_EXECUTION_SURFACES:
        text = _read(rel_path)
        for token in FORBIDDEN_EXECUTION_TOKENS:
            assert token not in text, (
                f"{rel_path} still contains stale execution token {token}"
            )


def test_path_truth_gate_passes_on_current_repo_state() -> None:
    result = subprocess.run(
        ["python3", "tooling/scripts/ci/check_path_truth_drift.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS:" in result.stdout
