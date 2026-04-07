from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from packages.core.application.models import (
    ComputerUseConfirmResponse,
    ComputerUseSessionResponse,
    UITestReportResponse,
    UITestRunResponse,
)
from packages.core.mcp import server
from packages.core.mcp.server import (
    _ensure_non_empty,
    _requires_auth,
    mcp,
)

EXPECTED_TOOL_NAMES = {
    "notebook.list",
    "notebook.mutate",
    "source.list",
    "source.mutate",
    "note.list",
    "note.mutate",
    "knowledge.search",
    "chat.run",
    "draft.list",
    "draft.create",
    "draft.verify",
    "draft.download",
    "research_thread.list",
    "research_thread.create",
    "research_thread.append",
    "research_thread.to_draft",
    "auditable_run.list",
    "auditable_run.create",
    "auditable_run.download",
    "auditable_run.repair_claim",
    "auditable_run.repair_section",
    "model.inspect",
    "settings.mutate",
    "ui_test.control",
    "computer_use.control",
}

HOST_EXAMPLE_BUNDLE_SKILL_PATHS = (
    Path(
        "examples/hosts/claude-code/provenote-outcome-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md"
    ),
    Path(
        "examples/hosts/codex/provenote-outcome-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md"
    ),
    Path(
        "examples/hosts/cursor/provenote-outcome-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md"
    ),
    Path(
        "examples/hosts/opencode/provenote-outcome-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md"
    ),
    Path(
        "examples/hosts/openclaw/provenote-claude-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md"
    ),
    Path(
        "examples/hosts/openclaw/provenote-cursor-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md"
    ),
    Path(
        "examples/hosts/openclaw/provenote-codex-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md"
    ),
    Path("examples/hosts/openclaw/clawhub/provenote-mcp-outcome-workflows/SKILL.md"),
)

HOST_EXAMPLE_BUNDLE_SKILL_REQUIRED_SNIPPETS = (
    "provenote-mcp",
    "list drafts",
    "list research threads",
    "list auditable runs",
    "one narrow write-oriented workflow succeeds",
    "inspectable repo-owned surface",
    "not a marketplace or directory listing",
)

OPENCLAW_ONLY_SKILL_PATHS = (
    Path(
        "examples/hosts/openclaw/provenote-claude-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md"
    ),
    Path(
        "examples/hosts/openclaw/provenote-cursor-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md"
    ),
    Path(
        "examples/hosts/openclaw/provenote-codex-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md"
    ),
)

ACTION_ROUTE_NAMES = {
    "notebook.mutate",
    "source.mutate",
    "note.mutate",
    "model.inspect",
    "settings.mutate",
    "ui_test.control",
    "computer_use.control",
}


def test_pyproject_script_target_has_stdio_entrypoint() -> None:
    assert callable(server.main)


def test_openclaw_example_bundle_skills_keep_repo_owned_mcp_boundary() -> None:
    for skill_path in HOST_EXAMPLE_BUNDLE_SKILL_PATHS:
        content = skill_path.read_text(encoding="utf-8")
        for snippet in HOST_EXAMPLE_BUNDLE_SKILL_REQUIRED_SNIPPETS:
            assert snippet in content, f"{skill_path} missing {snippet!r}"

    for skill_path in OPENCLAW_ONLY_SKILL_PATHS:
        content = skill_path.read_text(encoding="utf-8")
        assert (
            "not a claim that Provenote already ships official OpenClaw support"
            in content
        ), f"{skill_path} missing OpenClaw-specific boundary"


class _StubClient:
    def __init__(self) -> None:
        self.search_calls: list[dict[str, object]] = []
        self.settings_update_calls: list[dict[str, object]] = []
        self.draft_create_calls: list[tuple[str, dict[str, object]]] = []
        self.thread_create_calls: list[tuple[str, dict[str, object]]] = []
        self.thread_append_calls: list[tuple[str, dict[str, object]]] = []
        self.auditable_list_calls: list[str] = []
        self.auditable_create_calls: list[tuple[str, dict[str, object]]] = []

    def search(self, **kwargs: object) -> dict[str, object]:
        self.search_calls.append(kwargs)
        return {"results": [], "total_count": 0, "search_type": kwargs["search_type"]}

    def get_settings(self) -> dict[str, object]:
        return {
            "default_embedding_option": "ask",
            "youtube_preferred_languages": ["en"],
        }

    def update_settings(self, **kwargs: object) -> dict[str, object]:
        self.settings_update_calls.append(kwargs)
        return kwargs

    def get_drafts(self, notebook_id: str) -> list[dict[str, object]]:
        return [{"id": "draft:1", "notebook_id": notebook_id, "status": "completed"}]

    def create_draft(self, notebook_id: str, **payload: object) -> dict[str, object]:
        self.draft_create_calls.append((notebook_id, dict(payload)))
        return {"id": "draft:created", "notebook_id": notebook_id, **payload}

    def verify_draft(self, draft_id: str) -> dict[str, object]:
        return {"id": draft_id, "status": "verified"}

    def get_draft_markdown(self, draft_id: str) -> str:
        return f"# {draft_id}"

    def get_research_threads(self, notebook_id: str) -> list[dict[str, object]]:
        return [{"id": "research_thread:1", "notebook_id": notebook_id}]

    def create_research_thread(
        self, notebook_id: str, **payload: object
    ) -> dict[str, object]:
        self.thread_create_calls.append((notebook_id, dict(payload)))
        return {"id": "research_thread:created", "notebook_id": notebook_id, **payload}

    def append_research_thread(
        self, thread_id: str, **payload: object
    ) -> dict[str, object]:
        self.thread_append_calls.append((thread_id, dict(payload)))
        return {"id": thread_id, "entry_count": 2, **payload}

    def create_draft_from_thread(self, thread_id: str) -> dict[str, object]:
        return {"id": "draft:from-thread", "thread_id": thread_id}

    def get_auditable_runs(self, source_id: str) -> list[dict[str, object]]:
        self.auditable_list_calls.append(source_id)
        return [
            {"id": "auditable_run:1", "source_id": source_id, "status": "completed"}
        ]

    def create_auditable_run(
        self, source_id: str, **payload: object
    ) -> dict[str, object]:
        self.auditable_create_calls.append((source_id, dict(payload)))
        return {"id": "auditable_run:1", "source_id": source_id, **payload}

    def get_auditable_run_markdown(self, run_id: str) -> str:
        return f"# {run_id}"

    def repair_auditable_claim(
        self, run_id: str, **payload: object
    ) -> dict[str, object]:
        return {"id": run_id, "target_type": "claim", **payload}

    def repair_auditable_section(
        self, run_id: str, **payload: object
    ) -> dict[str, object]:
        return {"id": run_id, "target_type": "section", **payload}


def _assert_tool_schema_object(tool: Any) -> dict[str, Any]:
    schema = tool.parameters
    assert isinstance(schema, dict)
    assert schema.get("type") == "object"
    assert isinstance(schema.get("properties", {}), dict)
    return schema


def _sample_value_for_schema_field(field_schema: Any) -> Any:
    if not isinstance(field_schema, dict):
        return "x"

    if "enum" in field_schema and field_schema["enum"]:
        enum_value = field_schema["enum"][0]
        if enum_value is None:
            return "x"
        return enum_value

    field_type = field_schema.get("type")
    if field_type == "string":
        return "x"
    if field_type == "integer":
        return 1
    if field_type == "number":
        return 0.5
    if field_type == "boolean":
        return True
    if field_type == "array":
        return ["x"]
    if field_type == "object":
        return {}

    any_of = field_schema.get("anyOf")
    if isinstance(any_of, list) and any_of:
        for option in any_of:
            value = _sample_value_for_schema_field(option)
            if value is not None:
                return value

    return "x"


def _build_minimal_required_args(schema: dict[str, Any]) -> dict[str, Any]:
    args: dict[str, Any] = {}
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    if not isinstance(required, list) or not isinstance(properties, dict):
        return args

    for key in required:
        args[key] = _sample_value_for_schema_field(properties.get(key))
    return args


async def _assert_invalid_action_rejected(tool: Any) -> None:
    schema = _assert_tool_schema_object(tool)
    properties = schema.get("properties", {})
    action_schema = properties.get("action")
    assert isinstance(action_schema, dict)

    args = _build_minimal_required_args(schema)
    args["action"] = "__invalid_action__"
    with pytest.raises(ValueError):
        await tool.run(args)


@pytest.mark.asyncio
async def test_mcp_tool_registration_matches_expected_contract_tools() -> None:
    tools = await mcp.get_tools()
    assert set(tools) == EXPECTED_TOOL_NAMES


@pytest.mark.asyncio
async def test_action_routes_expose_action_field_and_reject_invalid_action() -> None:
    tools = await mcp.get_tools()
    assert ACTION_ROUTE_NAMES.issubset(tools)
    for route in ACTION_ROUTE_NAMES:
        await _assert_invalid_action_rejected(tools[route])


@pytest.mark.asyncio
async def test_settings_mutate_contract_get_update_and_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools = await mcp.get_tools()
    stub = _StubClient()
    monkeypatch.setattr(server, "_api_client", lambda: stub)

    get_result = await tools["settings.mutate"].run({"action": "get"})
    get_payload = json.loads(get_result.content[0].text)
    assert get_payload == {
        "default_embedding_option": "ask",
        "youtube_preferred_languages": ["en"],
    }

    update_result = await tools["settings.mutate"].run(
        {
            "action": "update",
            "data": {
                "updates": {
                    "default_embedding_option": "ALWAYS",
                    "youtube_preferred_languages": [" en ", "zh-CN"],
                }
            },
        }
    )
    update_payload = json.loads(update_result.content[0].text)
    assert update_payload == {
        "default_embedding_option": "always",
        "youtube_preferred_languages": ["en", "zh-CN"],
    }
    assert stub.settings_update_calls == [update_payload]

    with pytest.raises(ValueError, match="Unsupported settings keys"):
        await tools["settings.mutate"].run(
            {"action": "update", "data": {"updates": {"unexpected": True}}}
        )
    with pytest.raises(ValueError, match="youtube_preferred_languages cannot be empty"):
        await tools["settings.mutate"].run(
            {
                "action": "update",
                "data": {"updates": {"youtube_preferred_languages": []}},
            }
        )


@pytest.mark.asyncio
async def test_outcome_first_tools_call_object_specific_client_methods(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools = await mcp.get_tools()
    stub = _StubClient()
    monkeypatch.setattr(server, "_api_client", lambda: stub)

    draft_list = await tools["draft.list"].run({"notebook_id": "notebook:1"})
    draft_create = await tools["draft.create"].run(
        {
            "notebook_id": "notebook:1",
            "title": "Wave 3 Draft",
            "source_ids": ["source:1"],
            "thread_ids": ["research_thread:1"],
        }
    )
    draft_verify = await tools["draft.verify"].run({"draft_id": "draft:1"})
    draft_download = await tools["draft.download"].run({"draft_id": "draft:1"})
    thread_list = await tools["research_thread.list"].run({"notebook_id": "notebook:1"})
    thread_create = await tools["research_thread.create"].run(
        {
            "notebook_id": "notebook:1",
            "title": "Search thread",
            "seed_kind": "search",
            "source_ids": ["source:1"],
        }
    )
    insight_thread_create = await tools["research_thread.create"].run(
        {
            "notebook_id": "notebook:1",
            "title": "Insight thread",
            "seed_kind": "insight",
            "source_ids": ["source:1"],
            "question": "Continue from this insight",
            "insight_id": "source_insight:1",
            "insight_type": "summary",
            "search_results": [{"title": "Snapshot"}],
        }
    )
    thread_append = await tools["research_thread.append"].run(
        {
            "thread_id": "research_thread:1",
            "entry_type": "answer_snapshot",
            "content": "grounded answer",
        }
    )
    thread_to_draft = await tools["research_thread.to_draft"].run(
        {"thread_id": "research_thread:1"}
    )
    auditable_list = await tools["auditable_run.list"].run({"source_id": "source:1"})
    auditable_create = await tools["auditable_run.create"].run(
        {"source_id": "source:1", "near_dedup_threshold": 0.97}
    )
    auditable_download = await tools["auditable_run.download"].run(
        {"run_id": "auditable_run:1"}
    )
    auditable_claim = await tools["auditable_run.repair_claim"].run(
        {"run_id": "auditable_run:1", "target_index": 0}
    )
    auditable_section = await tools["auditable_run.repair_section"].run(
        {"run_id": "auditable_run:1", "target_index": 1}
    )

    assert json.loads(draft_list.content[0].text) == [
        {"id": "draft:1", "notebook_id": "notebook:1", "status": "completed"}
    ]
    assert stub.draft_create_calls == [
        (
            "notebook:1",
            {
                "source_ids": ["source:1"],
                "note_ids": [],
                "thread_ids": ["research_thread:1"],
                "title": "Wave 3 Draft",
            },
        )
    ]
    assert json.loads(draft_create.content[0].text)["id"] == "draft:created"
    assert json.loads(draft_verify.content[0].text)["status"] == "verified"
    assert json.loads(draft_download.content[0].text) == {
        "draft_id": "draft:1",
        "filename": "draft-draft_1.md",
        "markdown": "# draft:1",
    }
    assert json.loads(thread_list.content[0].text) == [
        {"id": "research_thread:1", "notebook_id": "notebook:1"}
    ]
    assert stub.thread_create_calls == [
        (
            "notebook:1",
            {
                "title": "Search thread",
                "seed_kind": "search",
                "source_ids": ["source:1"],
                "note_ids": [],
                "question": None,
                "answer": None,
                "search_results": [],
            },
        ),
        (
            "notebook:1",
            {
                "title": "Insight thread",
                "seed_kind": "insight",
                "source_ids": ["source:1"],
                "note_ids": [],
                "question": "Continue from this insight",
                "answer": None,
                "search_results": [{"title": "Snapshot"}],
                "insight_id": "source_insight:1",
                "insight_type": "summary",
            },
        ),
    ]
    assert json.loads(thread_create.content[0].text)["id"] == "research_thread:created"
    assert json.loads(insight_thread_create.content[0].text)["seed_kind"] == "insight"
    assert stub.thread_append_calls == [
        (
            "research_thread:1",
            {
                "entry_type": "answer_snapshot",
                "title": None,
                "content": "grounded answer",
                "source_ids": [],
                "note_ids": [],
                "metadata": {},
            },
        )
    ]
    assert json.loads(thread_append.content[0].text)["entry_count"] == 2
    assert json.loads(thread_to_draft.content[0].text)["id"] == "draft:from-thread"
    assert stub.auditable_list_calls == ["source:1"]
    assert json.loads(auditable_list.content[0].text) == [
        {"id": "auditable_run:1", "source_id": "source:1", "status": "completed"}
    ]
    assert stub.auditable_create_calls == [
        (
            "source:1",
            {
                "near_dedup_threshold": 0.97,
            },
        )
    ]
    assert json.loads(auditable_create.content[0].text)["id"] == "auditable_run:1"
    assert json.loads(auditable_download.content[0].text) == {
        "run_id": "auditable_run:1",
        "filename": "auditable-auditable_run_1.md",
        "markdown": "# auditable_run:1",
    }
    assert json.loads(auditable_claim.content[0].text)["target_type"] == "claim"
    assert json.loads(auditable_section.content[0].text)["target_type"] == "section"


@pytest.mark.asyncio
async def test_research_thread_create_rejects_insight_seed_without_insight_id() -> None:
    tools = await mcp.get_tools()

    with pytest.raises(ValueError, match="insight_id is required"):
        await tools["research_thread.create"].run(
            {
                "notebook_id": "notebook:1",
                "title": "Insight thread",
                "seed_kind": "insight",
                "source_ids": ["source:1"],
            }
        )


@pytest.mark.asyncio
async def test_ui_test_and_computer_use_control_action_contracts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools = await mcp.get_tools()

    class _StubUITestService:
        async def run(self, request: object) -> UITestRunResponse:
            del request
            return UITestRunResponse(
                id="ui_test_run:1",
                status="queued",
                dry_run=True,
                command=["npm", "run", "test:e2e", "--", "--project=chromium"],
                return_code=None,
                created="2026-01-01T00:00:00+00:00",
                updated="2026-01-01T00:00:00+00:00",
            )

        async def get(self, run_id: str) -> UITestRunResponse:
            assert run_id == "ui_test_run:1"
            return UITestRunResponse(
                id=run_id,
                status="completed",
                dry_run=True,
                command=["npm", "run", "test:e2e", "--", "--project=chromium"],
                return_code=0,
                created="2026-01-01T00:00:00+00:00",
                updated="2026-01-01T00:00:03+00:00",
            )

        async def report(self, run_id: str) -> UITestReportResponse:
            assert run_id == "ui_test_run:1"
            return UITestReportResponse(
                id=run_id,
                status="completed",
                dry_run=True,
                command=["npm", "run", "test:e2e", "--", "--project=chromium"],
                return_code=0,
                stdout="ok",
                stderr="",
                started_at="2026-01-01T00:00:01+00:00",
                finished_at="2026-01-01T00:00:03+00:00",
                duration_seconds=2.0,
                created="2026-01-01T00:00:00+00:00",
                updated="2026-01-01T00:00:03+00:00",
            )

    class _StubComputerUseService:
        async def create_session(self, request: object) -> ComputerUseSessionResponse:
            del request
            return ComputerUseSessionResponse(
                session_id="computer_use:1",
                status="awaiting_confirmation",
                objective="check flow",
                require_confirmation=True,
                dry_run=True,
                created="2026-01-01T00:00:00+00:00",
                updated="2026-01-01T00:00:00+00:00",
                confirmation_required=True,
                pending_action_id="computer_use:1:action:1",
            )

        async def get_session(self, session_id: str) -> ComputerUseSessionResponse:
            assert session_id == "computer_use:1"
            return ComputerUseSessionResponse(
                session_id=session_id,
                status="ready",
                objective="check flow",
                require_confirmation=True,
                dry_run=True,
                created="2026-01-01T00:00:00+00:00",
                updated="2026-01-01T00:00:05+00:00",
                confirmation_required=False,
                pending_action_id=None,
            )

        async def confirm_action(
            self, session_id: str, request: object
        ) -> ComputerUseConfirmResponse:
            del request
            assert session_id == "computer_use:1"
            return ComputerUseConfirmResponse(
                session_id=session_id,
                status="ready",
                approved=True,
                message="Confirmation accepted",
            )

    monkeypatch.setattr(server, "ui_test_service", _StubUITestService())
    monkeypatch.setattr(server, "computer_use_service", _StubComputerUseService())

    run_payload = json.loads(
        (
            await tools["ui_test.control"].run(
                {
                    "action": "run",
                    "data": {
                        "project": "chromium",
                        "dry_run": True,
                        "timeout_seconds": 30,
                    },
                }
            )
        )
        .content[0]
        .text
    )
    assert run_payload["id"] == "ui_test_run:1"

    run_get_payload = json.loads(
        (
            await tools["ui_test.control"].run(
                {"action": "get_run", "data": {"run_id": "ui_test_run:1"}}
            )
        )
        .content[0]
        .text
    )
    assert run_get_payload["status"] == "completed"

    report_payload = json.loads(
        (
            await tools["ui_test.control"].run(
                {"action": "get_report", "data": {"run_id": "ui_test_run:1"}}
            )
        )
        .content[0]
        .text
    )
    assert report_payload["stdout"] == "ok"

    session_payload = json.loads(
        (
            await tools["computer_use.control"].run(
                {
                    "action": "start",
                    "data": {
                        "objective": "check flow",
                        "require_confirmation": True,
                        "dry_run": True,
                    },
                }
            )
        )
        .content[0]
        .text
    )
    assert session_payload["session_id"] == "computer_use:1"

    session_get_payload = json.loads(
        (
            await tools["computer_use.control"].run(
                {"action": "get_session", "data": {"session_id": "computer_use:1"}}
            )
        )
        .content[0]
        .text
    )
    assert session_get_payload["status"] == "ready"

    confirm_payload = json.loads(
        (
            await tools["computer_use.control"].run(
                {
                    "action": "confirm",
                    "data": {
                        "session_id": "computer_use:1",
                        "confirmation_token": "token-1",
                        "action_idempotency_key": "idem-1",
                    },
                }
            )
        )
        .content[0]
        .text
    )
    assert confirm_payload["approved"] is True


@pytest.mark.asyncio
async def test_action_routes_reject_invalid_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools = await mcp.get_tools()
    monkeypatch.setattr(server, "_api_client", lambda: _StubClient())

    with pytest.raises(ValueError, match="timeout_seconds must be between 1 and 7200"):
        await tools["ui_test.control"].run(
            {
                "action": "run",
                "data": {"project": "chromium", "dry_run": True, "timeout_seconds": 0},
            }
        )
    with pytest.raises(ValueError, match="objective cannot be empty"):
        await tools["computer_use.control"].run(
            {
                "action": "start",
                "data": {
                    "objective": "   ",
                    "require_confirmation": True,
                    "dry_run": True,
                },
            }
        )
    with pytest.raises(ValueError, match="action_idempotency_key cannot be empty"):
        await tools["computer_use.control"].run(
            {
                "action": "confirm",
                "data": {
                    "session_id": "computer_use:1",
                    "confirmation_token": "token-1",
                    "action_idempotency_key": "  ",
                },
            }
        )


def test_ensure_non_empty_validates_inputs() -> None:
    assert _ensure_non_empty(" hello ", "field") == "hello"
    with pytest.raises(ValueError, match="cannot be empty"):
        _ensure_non_empty("   ", "field")
    with pytest.raises(ValueError, match="exceeds max length"):
        _ensure_non_empty("x" * 5, "field", max_length=4)


def test_requires_auth_for_non_local_hosts() -> None:
    assert _requires_auth("http://example.com:5055") is True
    assert _requires_auth("http://localhost:5055") is False
    assert _requires_auth("http://127.0.0.1:5055") is False


def test_api_client_requires_password_for_remote_hosts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_URL", "https://remote.example.com")
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="OPEN_NOTEBOOK_PASSWORD is required"):
        server._api_client()


def test_api_client_rejects_inline_remote_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inline_creds_url = "https://" + "user:pass" + "@remote.example.com"
    monkeypatch.setenv("OPEN_NOTEBOOK_URL", inline_creds_url)
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "env-secret")
    with pytest.raises(
        RuntimeError, match="Credentials in OPEN_NOTEBOOK_URL are not allowed"
    ):
        server._api_client()
