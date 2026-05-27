"""First-party MCP server for Notebooklab."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, TypedDict
from urllib.parse import urlparse

from fastmcp import FastMCP

from packages.core.application.chat_service import chat_service
from packages.core.application.client import APIClient
from packages.core.application.computer_use_service import computer_use_service
from packages.core.application.models import (
    ComputerUseConfirmRequest,
    ComputerUseSessionCreateRequest,
    UITestRunRequest,
)
from packages.core.application.ui_test_service import ui_test_service
from packages.core.mcp.schemas import (
    COMPUTER_USE_CONTROL_SCHEMAS,
    MODEL_INSPECT_SCHEMAS,
    NOTE_MUTATE_SCHEMAS,
    NOTEBOOK_MUTATE_SCHEMAS,
    SETTINGS_MUTATE_SCHEMAS,
    SOURCE_MUTATE_SCHEMAS,
    UI_TEST_CONTROL_SCHEMAS,
    AuditableRepairClaimData,
    AuditableRepairSectionData,
    AuditableRunCreateData,
    AuditableRunDownloadMarkdownData,
    AuditableRunListData,
    ChatRunData,
    ComputerUseConfirmData,
    ComputerUseControlAction,
    ComputerUseControlEnvelope,
    ComputerUseGetSessionData,
    ComputerUseStartData,
    DraftCreateData,
    DraftDownloadMarkdownData,
    DraftListData,
    DraftVerifyData,
    KnowledgeSearchData,
    ModelInspectAction,
    ModelInspectEnvelope,
    ModelListData,
    NotebookCreateData,
    NotebookDeleteData,
    NotebookGetData,
    NotebookListData,
    NotebookMutateAction,
    NotebookMutateEnvelope,
    NotebookUpdateData,
    NoteCreateData,
    NoteDeleteData,
    NoteGetData,
    NoteListData,
    NoteMutateAction,
    NoteMutateEnvelope,
    NoteUpdateData,
    ResearchThreadAppendData,
    ResearchThreadCreateData,
    ResearchThreadListData,
    ResearchThreadToDraftData,
    SettingsMutateAction,
    SettingsMutateEnvelope,
    SettingsUpdateData,
    SourceCreateTextData,
    SourceDeleteData,
    SourceGetData,
    SourceListData,
    SourceMutateAction,
    SourceMutateEnvelope,
    SourceUpdateData,
    UITestControlAction,
    UITestControlEnvelope,
    UITestRunData,
    UITestRunLookupData,
)
from packages.core.mcp.validation import (
    ensure_allowed,
    ensure_bool,
    ensure_int_range,
    ensure_non_empty,
    ensure_score,
    normalize_string_list,
    validate_action_data,
    validate_settings_updates,
)
from packages.core.utils.encryption import get_secret_from_env

MCP_INSTRUCTIONS = (
    "Use these tools to manage Notebooklab resources through the local API. "
    "All operations are authenticated using OPEN_NOTEBOOK_PASSWORD when configured."
)


class _ResearchThreadCreateKwargs(TypedDict, total=False):
    notebook_id: str
    title: str
    seed_kind: str
    source_ids: list[str]
    note_ids: list[str]
    question: Optional[str]
    answer: Optional[str]
    insight_id: str
    insight_type: str
    search_results: list[dict[str, Any]]


mcp = FastMCP(name="notebooklab", instructions=MCP_INSTRUCTIONS)

# Keep historical test/import anchors stable while the implementation lives
# in a smaller helper module.
_ensure_non_empty = ensure_non_empty


async def _compat_get_tools() -> dict[str, Any]:
    tools = await mcp.list_tools()
    indexed: dict[str, Any] = {}
    for tool in tools:
        tool_name = getattr(tool, "name", None)
        if not isinstance(tool_name, str) or not tool_name:
            continue
        indexed[tool_name] = await mcp.get_tool(tool_name)
    return indexed


if not hasattr(mcp, "get_tools"):
    setattr(mcp, "get_tools", _compat_get_tools)


def _api_client() -> APIClient:
    base_url = os.getenv("OPEN_NOTEBOOK_URL")
    if base_url and _requires_auth(base_url):
        _ensure_remote_auth(base_url)
    return APIClient(base_url=base_url)


def _requires_auth(base_url: str) -> bool:
    parsed = urlparse(base_url)
    host = (parsed.hostname or "").lower()
    return host not in {"localhost", "127.0.0.1", "::1"}


def _ensure_remote_auth(base_url: str) -> None:
    parsed = urlparse(base_url)
    if parsed.username or parsed.password:
        raise RuntimeError(
            "Credentials in OPEN_NOTEBOOK_URL are not allowed. Use OPEN_NOTEBOOK_PASSWORD."
        )
    try:
        password = get_secret_from_env("OPEN_NOTEBOOK_PASSWORD")
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    if not password:
        raise RuntimeError(
            "OPEN_NOTEBOOK_PASSWORD is required when OPEN_NOTEBOOK_URL targets non-local host."
        )


def _unwrap(result: Any) -> Dict[str, Any]:
    return result if isinstance(result, dict) else result[0]


@mcp.tool(name="notebook.list")
def notebook_list(data: Optional[Dict[str, Any]] = None) -> list[dict[str, Any]]:
    """List notebooks."""
    payload = NotebookListData.model_validate(data or {})
    return _api_client().get_notebooks(archived=payload.archived)


@mcp.tool(name="notebook.mutate")
def notebook_mutate(
    action: str, data: Optional[Dict[str, Any]] = None
) -> dict[str, Any]:
    """Mutate notebook resources via action+data schema."""
    envelope = NotebookMutateEnvelope.model_validate(
        {"action": action, "data": data or {}}
    )
    payload = validate_action_data(
        envelope.action, envelope.data, NOTEBOOK_MUTATE_SCHEMAS
    )

    client = _api_client()
    if envelope.action is NotebookMutateAction.create:
        assert isinstance(payload, NotebookCreateData)
        return _unwrap(
            client.create_notebook(
                name=ensure_non_empty(payload.name, "name", max_length=120),
                description=payload.description.strip(),
            )
        )
    if envelope.action is NotebookMutateAction.get:
        assert isinstance(payload, NotebookGetData)
        return _unwrap(
            client.get_notebook(
                ensure_non_empty(payload.notebook_id, "notebook_id", max_length=120)
            )
        )
    if envelope.action is NotebookMutateAction.update:
        assert isinstance(payload, NotebookUpdateData)
        updates: dict[str, Any] = {}
        if payload.name is not None:
            updates["name"] = ensure_non_empty(payload.name, "name", max_length=120)
        if payload.description is not None:
            updates["description"] = payload.description.strip()
        if payload.archived is not None:
            updates["archived"] = payload.archived
        return _unwrap(
            client.update_notebook(
                ensure_non_empty(payload.notebook_id, "notebook_id", max_length=120),
                **updates,
            )
        )

    assert isinstance(payload, NotebookDeleteData)
    return _unwrap(
        client.delete_notebook(
            ensure_non_empty(payload.notebook_id, "notebook_id", max_length=120)
        )
    )


@mcp.tool(name="source.list")
def source_list(data: Optional[Dict[str, Any]] = None) -> list[dict[str, Any]]:
    """List sources, optionally filtered by notebook."""
    payload = SourceListData.model_validate(data or {})
    notebook_id = (
        ensure_non_empty(payload.notebook_id, "notebook_id", max_length=120)
        if payload.notebook_id is not None
        else None
    )
    return _api_client().get_sources(notebook_id=notebook_id)


@mcp.tool(name="source.mutate")
def source_mutate(action: str, data: Optional[Dict[str, Any]] = None) -> dict[str, Any]:
    """Mutate source resources via action+data schema."""
    envelope = SourceMutateEnvelope.model_validate(
        {"action": action, "data": data or {}}
    )
    payload = validate_action_data(
        envelope.action, envelope.data, SOURCE_MUTATE_SCHEMAS
    )

    client = _api_client()
    if envelope.action is SourceMutateAction.create_text:
        assert isinstance(payload, SourceCreateTextData)
        return _unwrap(
            client.create_source(
                notebook_id=ensure_non_empty(
                    payload.notebook_id, "notebook_id", max_length=120
                ),
                source_type="text",
                content=ensure_non_empty(
                    payload.content, "content", max_length=200_000
                ),
                title=(payload.title or "").strip() or None,
                embed=payload.embed,
            )
        )
    if envelope.action is SourceMutateAction.get:
        assert isinstance(payload, SourceGetData)
        return _unwrap(
            client.get_source(
                ensure_non_empty(payload.source_id, "source_id", max_length=120)
            )
        )
    if envelope.action is SourceMutateAction.update:
        assert isinstance(payload, SourceUpdateData)
        updates: dict[str, Any] = {}
        if payload.title is not None:
            updates["title"] = payload.title.strip()
        if payload.topics is not None:
            updates["topics"] = payload.topics
        return _unwrap(
            client.update_source(
                ensure_non_empty(payload.source_id, "source_id", max_length=120),
                **updates,
            )
        )

    assert isinstance(payload, SourceDeleteData)
    return _unwrap(
        client.delete_source(
            ensure_non_empty(payload.source_id, "source_id", max_length=120)
        )
    )


@mcp.tool(name="note.list")
def note_list(data: Optional[Dict[str, Any]] = None) -> list[dict[str, Any]]:
    """List notes, optionally filtered by notebook."""
    payload = NoteListData.model_validate(data or {})
    notebook_id = (
        ensure_non_empty(payload.notebook_id, "notebook_id", max_length=120)
        if payload.notebook_id is not None
        else None
    )
    return _api_client().get_notes(notebook_id=notebook_id)


@mcp.tool(name="note.mutate")
def note_mutate(action: str, data: Optional[Dict[str, Any]] = None) -> dict[str, Any]:
    """Mutate note resources via action+data schema."""
    envelope = NoteMutateEnvelope.model_validate({"action": action, "data": data or {}})
    payload = validate_action_data(envelope.action, envelope.data, NOTE_MUTATE_SCHEMAS)

    client = _api_client()
    if envelope.action is NoteMutateAction.create:
        assert isinstance(payload, NoteCreateData)
        return _unwrap(
            client.create_note(
                content=ensure_non_empty(
                    payload.content, "content", max_length=200_000
                ),
                title=(payload.title or "").strip() or None,
                note_type=payload.note_type,
                notebook_id=payload.notebook_id.strip()
                if payload.notebook_id
                else None,
            )
        )
    if envelope.action is NoteMutateAction.get:
        assert isinstance(payload, NoteGetData)
        return _unwrap(
            client.get_note(
                ensure_non_empty(payload.note_id, "note_id", max_length=120)
            )
        )
    if envelope.action is NoteMutateAction.update:
        assert isinstance(payload, NoteUpdateData)
        updates: dict[str, Any] = {}
        if payload.title is not None:
            updates["title"] = payload.title.strip()
        if payload.content is not None:
            updates["content"] = ensure_non_empty(
                payload.content, "content", max_length=200_000
            )
        if payload.note_type is not None:
            updates["note_type"] = payload.note_type
        return _unwrap(
            client.update_note(
                ensure_non_empty(payload.note_id, "note_id", max_length=120),
                **updates,
            )
        )

    assert isinstance(payload, NoteDeleteData)
    return _unwrap(
        client.delete_note(ensure_non_empty(payload.note_id, "note_id", max_length=120))
    )


@mcp.tool(name="knowledge.search")
def knowledge_search(data: Dict[str, Any]) -> dict[str, Any] | list[dict[str, Any]]:
    """Search sources and notes."""
    payload = KnowledgeSearchData.model_validate(data)
    return _api_client().search(
        query=ensure_non_empty(payload.query, "query", max_length=2_000),
        search_type=ensure_allowed(
            payload.search_type, "search_type", {"text", "vector"}
        ),
        limit=ensure_int_range(payload.limit, "limit", minimum=1, maximum=1000),
        search_sources=payload.search_sources,
        search_notes=payload.search_notes,
        minimum_score=ensure_score(payload.minimum_score, "minimum_score"),
    )


@mcp.tool(name="chat.run")
async def chat_run(data: Dict[str, Any]) -> dict[str, Any]:
    """Send a chat message and return model response."""
    payload = ChatRunData.model_validate(data)
    notebook_id = ensure_non_empty(payload.notebook_id, "notebook_id", max_length=120)
    message = ensure_non_empty(payload.message, "message", max_length=20_000)

    current_session_id = payload.session_id
    if not current_session_id:
        session = await chat_service.create_session(
            notebook_id=notebook_id,
            model_override=payload.model_override,
        )
        current_session_id = str(session.get("id", ""))
        if not current_session_id:
            raise RuntimeError("Failed to create chat session")

    context = await chat_service.build_context(notebook_id, {})
    result = await chat_service.execute_chat(
        session_id=current_session_id,
        message=message,
        context=context,
        model_override=payload.model_override,
    )
    return {"session_id": current_session_id, "response": result}


@mcp.tool(name="draft.list")
def draft_list(notebook_id: str) -> list[dict[str, Any]]:
    """List drafts for a notebook outcome lane."""
    payload = DraftListData.model_validate({"notebook_id": notebook_id})
    return _api_client().get_drafts(
        ensure_non_empty(payload.notebook_id, "notebook_id", max_length=120)
    )


@mcp.tool(name="draft.create")
def draft_create(
    notebook_id: str,
    source_ids: list[str],
    title: Optional[str] = None,
    note_ids: Optional[list[str]] = None,
    thread_ids: Optional[list[str]] = None,
    model_id: Optional[str] = None,
    language: Optional[str] = None,
    near_dedup_threshold: Optional[float] = None,
) -> dict[str, Any]:
    """Create a notebook draft from selected sources, notes, and research threads."""
    payload = DraftCreateData.model_validate(
        {
            "notebook_id": notebook_id,
            "source_ids": source_ids,
            "title": title,
            "note_ids": note_ids or [],
            "thread_ids": thread_ids or [],
            "model_id": model_id,
            "language": language,
            "near_dedup_threshold": near_dedup_threshold,
        }
    )
    request: dict[str, Any] = {
        "source_ids": normalize_string_list(payload.source_ids, "source_ids"),
        "note_ids": normalize_string_list(payload.note_ids, "note_ids"),
        "thread_ids": normalize_string_list(payload.thread_ids, "thread_ids"),
    }
    if payload.title is not None and payload.title.strip():
        request["title"] = payload.title.strip()
    if payload.model_id is not None and payload.model_id.strip():
        request["model_id"] = payload.model_id.strip()
    if payload.language is not None and payload.language.strip():
        request["language"] = payload.language.strip()
    if payload.near_dedup_threshold is not None:
        request["near_dedup_threshold"] = payload.near_dedup_threshold
    return _unwrap(
        _api_client().create_draft(
            notebook_id=ensure_non_empty(
                payload.notebook_id, "notebook_id", max_length=120
            ),
            **request,
        )
    )


@mcp.tool(name="draft.verify")
def draft_verify(draft_id: str) -> dict[str, Any]:
    """Verify a notebook draft and freeze its snapshot."""
    payload = DraftVerifyData.model_validate({"draft_id": draft_id})
    verified_draft_id = ensure_non_empty(payload.draft_id, "draft_id", max_length=120)
    return _unwrap(_api_client().verify_draft(verified_draft_id))


@mcp.tool(name="draft.download")
def draft_download(draft_id: str) -> dict[str, Any]:
    """Return draft markdown as tool-consumable text."""
    payload = DraftDownloadMarkdownData.model_validate({"draft_id": draft_id})
    draft_id = ensure_non_empty(payload.draft_id, "draft_id", max_length=120)
    return {
        "draft_id": draft_id,
        "filename": f"draft-{draft_id.replace(':', '_')}.md",
        "markdown": _api_client().get_draft_markdown(draft_id),
    }


@mcp.tool(name="research_thread.list")
def research_thread_list(notebook_id: str) -> list[dict[str, Any]]:
    """List research threads for a notebook."""
    payload = ResearchThreadListData.model_validate({"notebook_id": notebook_id})
    validated_notebook_id = ensure_non_empty(
        payload.notebook_id, "notebook_id", max_length=120
    )
    return _api_client().get_research_threads(validated_notebook_id)


@mcp.tool(name="research_thread.create")
def research_thread_create(
    notebook_id: str,
    title: str,
    seed_kind: str,
    source_ids: Optional[list[str]] = None,
    note_ids: Optional[list[str]] = None,
    question: Optional[str] = None,
    answer: Optional[str] = None,
    insight_id: Optional[str] = None,
    insight_type: Optional[str] = None,
    search_results: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Create a research thread outcome artifact."""
    payload = ResearchThreadCreateData.model_validate(
        {
            "notebook_id": notebook_id,
            "title": title,
            "seed_kind": seed_kind,
            "source_ids": source_ids or [],
            "note_ids": note_ids or [],
            "question": question,
            "answer": answer,
            "insight_id": insight_id,
            "insight_type": insight_type,
            "search_results": search_results or [],
        }
    )
    normalized_insight_id = (payload.insight_id or "").strip() or None
    normalized_insight_type = (payload.insight_type or "").strip() or None
    create_kwargs: _ResearchThreadCreateKwargs = {
        "notebook_id": ensure_non_empty(
            payload.notebook_id, "notebook_id", max_length=120
        ),
        "title": ensure_non_empty(payload.title, "title", max_length=200),
        "seed_kind": payload.seed_kind,
        "source_ids": normalize_string_list(payload.source_ids, "source_ids"),
        "note_ids": normalize_string_list(payload.note_ids, "note_ids"),
        "question": (payload.question or "").strip() or None,
        "answer": (payload.answer or "").strip() or None,
        "search_results": payload.search_results,
    }
    if normalized_insight_id is not None:
        create_kwargs["insight_id"] = normalized_insight_id
    if normalized_insight_type is not None:
        create_kwargs["insight_type"] = normalized_insight_type
    return _unwrap(_api_client().create_research_thread(**create_kwargs))


@mcp.tool(name="research_thread.append")
def research_thread_append(
    thread_id: str,
    entry_type: str,
    content: str,
    title: Optional[str] = None,
    source_ids: Optional[list[str]] = None,
    note_ids: Optional[list[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> dict[str, Any]:
    """Append a new entry to an existing research thread."""
    payload = ResearchThreadAppendData.model_validate(
        {
            "thread_id": thread_id,
            "entry_type": entry_type,
            "content": content,
            "title": title,
            "source_ids": source_ids or [],
            "note_ids": note_ids or [],
            "metadata": metadata or {},
        }
    )
    return _unwrap(
        _api_client().append_research_thread(
            thread_id=ensure_non_empty(payload.thread_id, "thread_id", max_length=120),
            entry_type=payload.entry_type,
            content=ensure_non_empty(payload.content, "content", max_length=50_000),
            title=(payload.title or "").strip() or None,
            source_ids=normalize_string_list(payload.source_ids, "source_ids"),
            note_ids=normalize_string_list(payload.note_ids, "note_ids"),
            metadata=payload.metadata,
        )
    )


@mcp.tool(name="research_thread.to_draft")
def research_thread_to_draft(thread_id: str) -> dict[str, Any]:
    """Promote a research thread into a notebook draft."""
    payload = ResearchThreadToDraftData.model_validate({"thread_id": thread_id})
    validated_thread_id = ensure_non_empty(
        payload.thread_id, "thread_id", max_length=120
    )
    return _unwrap(_api_client().create_draft_from_thread(validated_thread_id))


@mcp.tool(name="auditable_run.list")
def auditable_run_list(source_id: str) -> list[dict[str, Any]]:
    """List auditable runs for a source."""
    payload = AuditableRunListData.model_validate({"source_id": source_id})
    validated_source_id = ensure_non_empty(
        payload.source_id, "source_id", max_length=120
    )
    return _api_client().get_auditable_runs(validated_source_id)


@mcp.tool(name="auditable_run.create")
def auditable_run_create(
    source_id: str,
    model_id: Optional[str] = None,
    language: Optional[str] = None,
    near_dedup_threshold: Optional[float] = None,
) -> dict[str, Any]:
    """Create an auditable run for a source outcome lane."""
    payload = AuditableRunCreateData.model_validate(
        {
            "source_id": source_id,
            "model_id": model_id,
            "language": language,
            "near_dedup_threshold": near_dedup_threshold,
        }
    )
    request: dict[str, Any] = {}
    if payload.model_id is not None and payload.model_id.strip():
        request["model_id"] = payload.model_id.strip()
    if payload.language is not None and payload.language.strip():
        request["language"] = payload.language.strip()
    if payload.near_dedup_threshold is not None:
        request["near_dedup_threshold"] = payload.near_dedup_threshold
    return _unwrap(
        _api_client().create_auditable_run(
            source_id=ensure_non_empty(payload.source_id, "source_id", max_length=120),
            **request,
        )
    )


@mcp.tool(name="auditable_run.download")
def auditable_run_download(run_id: str) -> dict[str, Any]:
    """Return auditable markdown as tool-consumable text."""
    payload = AuditableRunDownloadMarkdownData.model_validate({"run_id": run_id})
    run_id = ensure_non_empty(payload.run_id, "run_id", max_length=120)
    return {
        "run_id": run_id,
        "filename": f"auditable-{run_id.replace(':', '_')}.md",
        "markdown": _api_client().get_auditable_run_markdown(run_id),
    }


@mcp.tool(name="auditable_run.repair_claim")
def auditable_run_repair_claim(
    run_id: str, target_index: int, model_id: Optional[str] = None
) -> dict[str, Any]:
    """Repair one claim inside an auditable run."""
    payload = AuditableRepairClaimData.model_validate(
        {"run_id": run_id, "target_index": target_index, "model_id": model_id}
    )
    return _unwrap(
        _api_client().repair_auditable_claim(
            run_id=ensure_non_empty(payload.run_id, "run_id", max_length=120),
            target_index=ensure_int_range(
                payload.target_index, "target_index", minimum=0, maximum=10_000
            ),
            model_id=(payload.model_id or "").strip() or None,
        )
    )


@mcp.tool(name="auditable_run.repair_section")
def auditable_run_repair_section(
    run_id: str, target_index: int, model_id: Optional[str] = None
) -> dict[str, Any]:
    """Repair one section inside an auditable run."""
    payload = AuditableRepairSectionData.model_validate(
        {"run_id": run_id, "target_index": target_index, "model_id": model_id}
    )
    return _unwrap(
        _api_client().repair_auditable_section(
            run_id=ensure_non_empty(payload.run_id, "run_id", max_length=120),
            target_index=ensure_int_range(
                payload.target_index, "target_index", minimum=0, maximum=10_000
            ),
            model_id=(payload.model_id or "").strip() or None,
        )
    )


@mcp.tool(name="model.inspect")
def model_inspect(action: str, data: Optional[Dict[str, Any]] = None) -> dict[str, Any]:
    """Inspect model and provider metadata via action+data schema."""
    envelope = ModelInspectEnvelope.model_validate(
        {"action": action, "data": data or {}}
    )
    payload = validate_action_data(
        envelope.action, envelope.data, MODEL_INSPECT_SCHEMAS
    )
    client = _api_client()

    if envelope.action is ModelInspectAction.list:
        assert isinstance(payload, ModelListData)
        return {"items": client.get_models(model_type=payload.model_type)}
    if envelope.action is ModelInspectAction.defaults:
        return _unwrap(client.get_default_models())
    if envelope.action is ModelInspectAction.provider_policy:
        return _unwrap(client.get_provider_policy())

    return _unwrap(client.get_provider_bootstrap_diagnostics())


@mcp.tool(name="settings.mutate")
def settings_mutate(
    action: str, data: Optional[Dict[str, Any]] = None
) -> dict[str, Any]:
    """Mutate or retrieve settings via action+data schema."""
    envelope = SettingsMutateEnvelope.model_validate(
        {"action": action, "data": data or {}}
    )
    payload = validate_action_data(
        envelope.action, envelope.data, SETTINGS_MUTATE_SCHEMAS
    )
    client = _api_client()

    if envelope.action is SettingsMutateAction.get:
        return _unwrap(client.get_settings())

    assert isinstance(payload, SettingsUpdateData)
    return _unwrap(client.update_settings(**validate_settings_updates(payload.updates)))


@mcp.tool(name="ui_test.control")
async def ui_test_control(
    action: str, data: Optional[Dict[str, Any]] = None
) -> dict[str, Any]:
    """Control UI test runs via action+data schema."""
    envelope = UITestControlEnvelope.model_validate(
        {"action": action, "data": data or {}}
    )
    payload = validate_action_data(
        envelope.action, envelope.data, UI_TEST_CONTROL_SCHEMAS
    )

    if envelope.action is UITestControlAction.run:
        assert isinstance(payload, UITestRunData)
        request = UITestRunRequest(
            dry_run=ensure_bool(payload.dry_run, "dry_run"),
            project=payload.project,
            spec=(
                ensure_non_empty(payload.spec, "spec", max_length=2000)
                if payload.spec is not None
                else None
            ),
            timeout_seconds=ensure_int_range(
                payload.timeout_seconds,
                "timeout_seconds",
                minimum=1,
                maximum=7200,
            ),
        )
        return (await ui_test_service.run(request)).model_dump()

    assert isinstance(payload, UITestRunLookupData)
    run_id = ensure_non_empty(payload.run_id, "run_id", max_length=160)
    if envelope.action is UITestControlAction.get_run:
        return (await ui_test_service.get(run_id)).model_dump()

    return (await ui_test_service.report(run_id)).model_dump()


@mcp.tool(name="computer_use.control")
async def computer_use_control(
    action: str,
    data: Optional[Dict[str, Any]] = None,
) -> dict[str, Any]:
    """Control computer-use sessions via action+data schema."""
    envelope = ComputerUseControlEnvelope.model_validate(
        {"action": action, "data": data or {}}
    )
    payload = validate_action_data(
        envelope.action,
        envelope.data,
        COMPUTER_USE_CONTROL_SCHEMAS,
    )

    if envelope.action is ComputerUseControlAction.start:
        assert isinstance(payload, ComputerUseStartData)
        request = ComputerUseSessionCreateRequest(
            objective=ensure_non_empty(payload.objective, "objective", max_length=4000),
            require_confirmation=ensure_bool(
                payload.require_confirmation,
                "require_confirmation",
            ),
            dry_run=ensure_bool(payload.dry_run, "dry_run"),
        )
        return (await computer_use_service.create_session(request)).model_dump()

    if envelope.action is ComputerUseControlAction.get_session:
        assert isinstance(payload, ComputerUseGetSessionData)
        return (
            await computer_use_service.get_session(
                ensure_non_empty(payload.session_id, "session_id", max_length=160)
            )
        ).model_dump()

    assert isinstance(payload, ComputerUseConfirmData)
    confirm_request = ComputerUseConfirmRequest(
        confirmation_token=ensure_non_empty(
            payload.confirmation_token,
            "confirmation_token",
            max_length=256,
        ),
        action_idempotency_key=ensure_non_empty(
            payload.action_idempotency_key,
            "action_idempotency_key",
            max_length=256,
        ),
    )
    return (
        await computer_use_service.confirm_action(
            ensure_non_empty(payload.session_id, "session_id", max_length=160),
            confirm_request,
        )
    ).model_dump()


def main() -> None:
    """Run the Notebooklab MCP server over stdio."""
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
