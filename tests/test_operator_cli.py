from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.core.operator import cli


class _StubOperatorClient:
    def get_health(self) -> dict[str, object]:
        return {"status": "healthy"}

    def get_notebook(self, notebook_id: str) -> dict[str, object]:
        return {"id": notebook_id, "name": "Notebook"}

    def get_research_threads(self, notebook_id: str) -> list[dict[str, object]]:
        return [{"id": "research_thread:1", "notebook_id": notebook_id}]

    def get_drafts(self, notebook_id: str) -> list[dict[str, object]]:
        return [{"id": "draft:1", "notebook_id": notebook_id, "status": "completed"}]

    def get_auditable_runs(self, source_id: str) -> list[dict[str, object]]:
        return [
            {"id": "auditable_run:1", "source_id": source_id, "status": "completed"}
        ]

    def get_draft(self, draft_id: str) -> dict[str, object]:
        return {"id": draft_id, "status": "completed"}

    def get_research_thread(self, thread_id: str) -> dict[str, object]:
        return {"id": thread_id, "title": "Thread"}

    def get_auditable_run(self, run_id: str) -> dict[str, object]:
        return {"id": run_id, "status": "completed"}

    def create_draft_from_thread(self, thread_id: str) -> dict[str, object]:
        return {"id": "draft:from-thread", "thread_id": thread_id}

    def verify_draft(self, draft_id: str) -> dict[str, object]:
        return {"id": draft_id, "status": "verified"}

    def get_draft_markdown(self, draft_id: str) -> str:
        return f"# {draft_id}"

    def get_draft_bundle(self, draft_id: str) -> tuple[str, bytes]:
        return (f"{draft_id.replace(':', '_')}.zip", b"bundle-bytes")

    def create_auditable_run(
        self,
        source_id: str,
        model_id: str | None = None,
        language: str | None = None,
        near_dedup_threshold: float | None = None,
    ) -> dict[str, object]:
        return {
            "id": "auditable_run:1",
            "source_id": source_id,
            "model_id": model_id,
            "language": language,
            "near_dedup_threshold": near_dedup_threshold,
        }

    def get_auditable_run_markdown(self, run_id: str) -> str:
        return f"# {run_id}"


def test_status_command_reports_operator_surface(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        cli,
        "_fetch_health",
        lambda api_base, password: {"status": "healthy"},
    )

    exit_code = cli.main(["--api-base", "http://localhost:5055", "status", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["api_base"] == "http://localhost:5055"
    assert payload["healthy"] is True
    assert payload["health"]["status"] == "healthy"
    assert payload["entrypoints"]["operator"] == "notebooklab"
    assert payload["entrypoints"]["mcp"] == "notebooklab-mcp"
    assert payload["inspect_surfaces"] == [
        "notebook",
        "draft",
        "research_thread",
        "auditable_run",
    ]
    assert payload["operator_workflows"] == [
        "research-thread-to-draft",
        "auditable-markdown",
    ]


def test_status_command_requires_healthy_when_requested(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        cli,
        "_fetch_health",
        lambda api_base, password: {"error": "connection refused"},
    )

    exit_code = cli.main(
        [
            "--api-base",
            "http://localhost:5055",
            "status",
            "--json",
            "--require-healthy",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["healthy"] is False
    assert payload["health"]["error"] == "connection refused"


def test_inspect_notebook_reports_current_outcome_state(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        cli, "_build_client", lambda *args, **kwargs: _StubOperatorClient()
    )

    exit_code = cli.main(
        [
            "--api-base",
            "http://localhost:5055",
            "inspect",
            "notebook",
            "notebook:1",
            "--source-id",
            "source:7",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["notebook"]["id"] == "notebook:1"
    assert payload["drafts"][0]["id"] == "draft:1"
    assert payload["research_threads"][0]["id"] == "research_thread:1"
    assert payload["auditable_runs"][0]["source_id"] == "source:7"


def test_inspect_draft_returns_payload(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        cli, "_build_client", lambda *args, **kwargs: _StubOperatorClient()
    )

    exit_code = cli.main(
        [
            "--api-base",
            "http://localhost:5055",
            "inspect",
            "draft",
            "draft:1",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["object_type"] == "draft"
    assert payload["object_id"] == "draft:1"
    assert payload["payload"]["status"] == "completed"


def test_research_thread_to_draft_can_verify_and_download(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli, "_build_client", lambda *args, **kwargs: _StubOperatorClient()
    )

    exit_code = cli.main(
        [
            "--api-base",
            "http://localhost:5055",
            "research-thread-to-draft",
            "research_thread:1",
            "--verify",
            "--download-markdown",
            "--download-bundle",
            "--output-dir",
            str(tmp_path),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    markdown_path = Path(payload["saved_markdown"])
    bundle_path = Path(payload["saved_bundle"])
    assert exit_code == 0
    assert payload["thread_id"] == "research_thread:1"
    assert payload["draft"]["id"] == "draft:from-thread"
    assert payload["verified_payload"]["status"] == "verified"
    assert markdown_path.read_text(encoding="utf-8") == "# draft:from-thread"
    assert bundle_path.read_bytes() == b"bundle-bytes"


def test_auditable_markdown_can_download(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli, "_build_client", lambda *args, **kwargs: _StubOperatorClient()
    )

    exit_code = cli.main(
        [
            "--api-base",
            "http://localhost:5055",
            "auditable-markdown",
            "123",
            "--output",
            str(tmp_path),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    saved_path = Path(payload["saved_markdown"])
    assert exit_code == 0
    assert payload["source_id"] == "source:123"
    assert payload["run"]["id"] == "auditable_run:1"
    assert saved_path.read_text(encoding="utf-8") == "# auditable_run:1"
