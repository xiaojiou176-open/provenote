from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOST_EXAMPLES_ROOT = REPO_ROOT / "examples" / "hosts"
CLAUDE_CODE_BUNDLE_ROOT = (
    HOST_EXAMPLES_ROOT / "claude-code" / "notebooklab-outcome-bundle"
)
CODEX_BUNDLE_ROOT = HOST_EXAMPLES_ROOT / "codex" / "notebooklab-outcome-bundle"
CURSOR_BUNDLE_ROOT = HOST_EXAMPLES_ROOT / "cursor" / "notebooklab-outcome-bundle"
OPENCODE_BUNDLE_ROOT = HOST_EXAMPLES_ROOT / "opencode" / "notebooklab-outcome-bundle"
OPENCLAW_BUNDLE_ROOT = HOST_EXAMPLES_ROOT / "openclaw" / "notebooklab-claude-bundle"
OPENCLAW_CURSOR_BUNDLE_ROOT = (
    HOST_EXAMPLES_ROOT / "openclaw" / "notebooklab-cursor-bundle"
)
OPENCLAW_CODEX_BUNDLE_ROOT = HOST_EXAMPLES_ROOT / "openclaw" / "notebooklab-codex-bundle"
OPENCLAW_EXAMPLES_INDEX = HOST_EXAMPLES_ROOT / "openclaw" / "README.md"


def test_host_examples_readme_exists() -> None:
    readme = HOST_EXAMPLES_ROOT / "README.md"
    assert readme.exists(), "host examples index should exist"
    text = readme.read_text(encoding="utf-8")
    assert "tracked, repo-owned host artifacts" in text
    assert "public-ready starter packages" in text
    assert (
        "official Claude Code, Codex, Cursor, OpenCode, or OpenClaw listing is live"
        in text
    )
    assert "[openclaw/README.md]" in text
    assert "[openclaw/CLAWHUB_SUBMISSION.md]" in text


def test_openclaw_examples_index_exists_and_lists_bundle_families() -> None:
    assert OPENCLAW_EXAMPLES_INDEX.exists(), "OpenClaw host index should exist"
    text = OPENCLAW_EXAMPLES_INDEX.read_text(encoding="utf-8")
    assert "tracked public-ready OpenClaw-compatible bundle artifacts" in text
    assert "notebooklab-claude-bundle" in text
    assert "notebooklab-cursor-bundle" in text
    assert "notebooklab-codex-bundle" in text
    assert "the ClawHub skill listing is now live" in text
    assert "not every OpenClaw marketplace, directory, or registry surface is live" in text


def test_openclaw_clawhub_submission_pack_exists() -> None:
    submission_pack = HOST_EXAMPLES_ROOT / "openclaw" / "CLAWHUB_SUBMISSION.md"
    assert submission_pack.exists(), "OpenClaw submission pack should exist"
    text = submission_pack.read_text(encoding="utf-8")
    assert "public-ready package available" in text
    assert "official marketplace listing live" in text
    assert "authenticated publish and sync flows" in text


def test_openclaw_submission_pack_exists_and_keeps_claim_ladder() -> None:
    text = (HOST_EXAMPLES_ROOT / "openclaw" / "CLAWHUB_SUBMISSION.md").read_text(
        encoding="utf-8"
    )
    assert "public-ready package available" in text
    assert "publicly discoverable listing live" in text
    assert "official marketplace listing live" in text
    assert "authenticated publish and sync flows" in text


def test_openclaw_bundle_example_contains_expected_roots() -> None:
    assert OPENCLAW_BUNDLE_ROOT.exists(), "OpenClaw bundle example should exist"
    assert (OPENCLAW_BUNDLE_ROOT / ".mcp.json").exists()
    assert (OPENCLAW_BUNDLE_ROOT / ".claude-plugin" / "plugin.json").exists()
    assert (
        OPENCLAW_BUNDLE_ROOT / "commands" / "notebooklab-mcp-outcome-workflows.md"
    ).exists()
    assert (
        OPENCLAW_BUNDLE_ROOT / "skills" / "notebooklab-mcp-outcome-workflows" / "SKILL.md"
    ).exists()


def test_claude_code_bundle_example_contains_expected_roots() -> None:
    assert CLAUDE_CODE_BUNDLE_ROOT.exists()
    assert (CLAUDE_CODE_BUNDLE_ROOT / ".mcp.json").exists()
    assert (CLAUDE_CODE_BUNDLE_ROOT / ".claude-plugin" / "plugin.json").exists()
    assert (
        CLAUDE_CODE_BUNDLE_ROOT / "commands" / "notebooklab-mcp-outcome-workflows.md"
    ).exists()
    assert (
        CLAUDE_CODE_BUNDLE_ROOT
        / "skills"
        / "notebooklab-mcp-outcome-workflows"
        / "SKILL.md"
    ).exists()


def test_codex_bundle_example_contains_expected_roots() -> None:
    assert CODEX_BUNDLE_ROOT.exists()
    assert (CODEX_BUNDLE_ROOT / ".mcp.json").exists()
    assert (CODEX_BUNDLE_ROOT / ".codex-plugin" / "plugin.json").exists()
    assert (CODEX_BUNDLE_ROOT / "config.toml.example").exists()
    assert (
        CODEX_BUNDLE_ROOT / "skills" / "notebooklab-mcp-outcome-workflows" / "SKILL.md"
    ).exists()


def test_cursor_bundle_example_contains_expected_roots() -> None:
    assert CURSOR_BUNDLE_ROOT.exists()
    assert (CURSOR_BUNDLE_ROOT / ".mcp.json").exists()
    assert (
        CURSOR_BUNDLE_ROOT
        / ".cursor"
        / "commands"
        / "notebooklab-mcp-outcome-workflows.md"
    ).exists()
    assert (
        CURSOR_BUNDLE_ROOT / "skills" / "notebooklab-mcp-outcome-workflows" / "SKILL.md"
    ).exists()


def test_opencode_bundle_example_contains_expected_roots() -> None:
    assert OPENCODE_BUNDLE_ROOT.exists()
    assert (OPENCODE_BUNDLE_ROOT / ".mcp.json").exists()
    assert (OPENCODE_BUNDLE_ROOT / "opencode.json").exists()
    assert (
        OPENCODE_BUNDLE_ROOT / "skills" / "notebooklab-mcp-outcome-workflows" / "SKILL.md"
    ).exists()


def test_openclaw_bundle_example_targets_notebooklab_mcp() -> None:
    payload = json.loads(
        (OPENCLAW_BUNDLE_ROOT / ".mcp.json").read_text(encoding="utf-8")
    )
    assert payload["mcp"]["servers"]["notebooklab"]["command"] == ["notebooklab-mcp"]


def test_direct_host_starter_bundles_target_notebooklab_mcp() -> None:
    for bundle_root in (
        CLAUDE_CODE_BUNDLE_ROOT,
        CODEX_BUNDLE_ROOT,
        CURSOR_BUNDLE_ROOT,
        OPENCODE_BUNDLE_ROOT,
    ):
        payload = json.loads((bundle_root / ".mcp.json").read_text(encoding="utf-8"))
        assert payload["mcp"]["servers"]["notebooklab"]["command"] == ["notebooklab-mcp"]


def test_opencode_bundle_keeps_repo_owned_local_config() -> None:
    payload = json.loads(
        (OPENCODE_BUNDLE_ROOT / "opencode.json").read_text(encoding="utf-8")
    )
    assert payload["$schema"] == "https://opencode.ai/config.json"
    assert payload["mcp"]["notebooklab"]["type"] == "local"
    assert payload["mcp"]["notebooklab"]["command"] == ["notebooklab-mcp"]


def test_openclaw_bundle_skill_keeps_non_claim_boundary() -> None:
    text = (
        OPENCLAW_BUNDLE_ROOT / "skills" / "notebooklab-mcp-outcome-workflows" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "not a claim that Notebooklab already ships official OpenClaw support" in text
    assert "not a marketplace or directory listing" in text


def test_openclaw_submission_pack_exists() -> None:
    submission = HOST_EXAMPLES_ROOT / "openclaw" / "CLAWHUB_SUBMISSION.md"
    assert submission.exists(), "OpenClaw submission pack should exist"
    text = submission.read_text(encoding="utf-8")
    assert "ClawHub Submission Pack" in text
    assert "`public-ready package available`" in text
    assert "the ClawHub skill listing is now live" in text
    assert "broader OpenClaw bundle/plugin storefront work only if the maintainer wants more than the current live ClawHub page" in text


def test_direct_bundle_readmes_keep_public_ready_not_listing_boundary() -> None:
    claude_text = (CLAUDE_CODE_BUNDLE_ROOT / "README.md").read_text(encoding="utf-8")
    codex_text = (CODEX_BUNDLE_ROOT / "README.md").read_text(encoding="utf-8")
    assert "tracked public-ready starter bundle" in claude_text
    assert "public-ready package available from this repository" in claude_text
    assert "tracked public-ready starter bundle" in codex_text
    assert "public-ready package available from this repository" in codex_text


def test_cursor_bundle_example_contains_expected_marker_and_command_root() -> None:
    assert OPENCLAW_CURSOR_BUNDLE_ROOT.exists()
    assert (OPENCLAW_CURSOR_BUNDLE_ROOT / ".cursor-plugin" / "plugin.json").exists()
    assert (OPENCLAW_CURSOR_BUNDLE_ROOT / ".mcp.json").exists()
    assert (
        OPENCLAW_CURSOR_BUNDLE_ROOT
        / ".cursor"
        / "commands"
        / "notebooklab-mcp-outcome-workflows.md"
    ).exists()


def test_codex_bundle_example_contains_expected_marker_and_skill_root() -> None:
    assert OPENCLAW_CODEX_BUNDLE_ROOT.exists()
    assert (OPENCLAW_CODEX_BUNDLE_ROOT / ".codex-plugin" / "plugin.json").exists()
    assert (OPENCLAW_CODEX_BUNDLE_ROOT / ".mcp.json").exists()
    assert (
        OPENCLAW_CODEX_BUNDLE_ROOT
        / "skills"
        / "notebooklab-mcp-outcome-workflows"
        / "SKILL.md"
    ).exists()


def test_cursor_bundle_command_file_is_tracked_and_not_ignored() -> None:
    command_file = (
        OPENCLAW_CURSOR_BUNDLE_ROOT
        / ".cursor"
        / "commands"
        / "notebooklab-mcp-outcome-workflows.md"
    )
    relative_path = str(command_file.relative_to(REPO_ROOT))

    tracked_result = subprocess.run(
        [
            "git",
            "ls-files",
            "--error-unmatch",
            "--",
            relative_path,
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert relative_path in tracked_result.stdout

    ignore_result = subprocess.run(
        [
            "git",
            "check-ignore",
            "--no-index",
            "--verbose",
            "--",
            relative_path,
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert (
        "!.cursor/commands/notebooklab-mcp-outcome-workflows.md" in ignore_result.stdout
    )
