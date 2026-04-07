from __future__ import annotations

import json
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
    "model.inspect",
    "settings.mutate",
    "ui_test.control",
    "computer_use.control",
}

ACTION_ROUTE_NAMES = {
    "notebook.mutate",
    "source.mutate",
    "note.mutate",
    "model.inspect",
    "settings.mutate",
    "ui_test.control",
    "computer_use.control",
}


class _StubClient:
    def __init__(self) -> None:
        self.search_calls: list[dict[str, object]] = []
        self.settings_update_calls: list[dict[str, object]] = []

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
async def test_mcp_tool_registration_is_exactly_the_12_contract_tools() -> None:
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
