from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "tooling/scripts/ci/check_public_identity_surface.py"
SPEC = importlib.util.spec_from_file_location(
    "check_public_identity_surface", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_public_identity_required_files_exist_in_repo() -> None:
    for rel_path in GUARD.REQUIRED_FILES:
        assert (REPO_ROOT / rel_path).is_file(), (
            f"missing public identity stewardship file: {rel_path}"
        )


def test_public_identity_guard_passes_against_repo_surface() -> None:
    assert GUARD.collect_failures(REPO_ROOT) == []


def test_public_identity_guard_flags_upstream_self_links_in_current_surface(
    tmp_path: Path,
) -> None:
    for rel_path in GUARD.REQUIRED_FILES:
        _write(tmp_path / rel_path, "ok\n")

    for rel_path, tokens in GUARD.REQUIRED_TOKENS.items():
        _write(tmp_path / rel_path, "\n".join(tokens) + "\n")

    bad_readme = tmp_path / "README.md"
    bad_readme.write_text(
        bad_readme.read_text(encoding="utf-8")
        + "https://github.com/lfnovo/open-notebook\n",
        encoding="utf-8",
    )

    failures = GUARD.collect_failures(tmp_path)

    assert (
        "README.md must not contain upstream self-link token: "
        "'https://github.com/lfnovo/open-notebook'"
    ) in failures


def test_public_identity_guard_requires_fork_stewardship_files(
    tmp_path: Path,
) -> None:
    for rel_path, tokens in GUARD.REQUIRED_TOKENS.items():
        if rel_path in GUARD.REQUIRED_FILES:
            continue
        _write(tmp_path / rel_path, "\n".join(tokens) + "\n")

    failures = GUARD.collect_failures(tmp_path)

    assert "required fork stewardship file missing: NOTICE.md" in failures
    assert "required fork stewardship file missing: MAINTAINERS.md" in failures


def test_public_identity_guard_covers_issue_templates_in_current_surface() -> None:
    for rel_path in (
        ".github/ISSUE_TEMPLATE/installation_issue.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
    ):
        assert rel_path in GUARD.CURRENT_FACING_FILES


def test_public_identity_guard_flags_upstream_links_in_installation_template(
    tmp_path: Path,
) -> None:
    for rel_path in GUARD.REQUIRED_FILES:
        _write(tmp_path / rel_path, "ok\n")

    for rel_path, tokens in GUARD.REQUIRED_TOKENS.items():
        _write(tmp_path / rel_path, "\n".join(tokens) + "\n")

    template = tmp_path / ".github/ISSUE_TEMPLATE/installation_issue.yml"
    template.write_text(
        template.read_text(encoding="utf-8") + "https://discord.gg/37XJPXfz2w\n",
        encoding="utf-8",
    )

    failures = GUARD.collect_failures(tmp_path)

    assert (
        ".github/ISSUE_TEMPLATE/installation_issue.yml must not contain upstream self-link token: "
        "'https://discord.gg/37XJPXfz2w'"
    ) in failures
