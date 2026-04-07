"""MCP request/response schema definitions for Provenote server tools."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NotebookListData(StrictModel):
    archived: Optional[bool] = None


class SourceListData(StrictModel):
    notebook_id: Optional[str] = None


class NoteListData(StrictModel):
    notebook_id: Optional[str] = None


class KnowledgeSearchData(StrictModel):
    query: str
    search_type: str = "text"
    limit: int = 20
    search_sources: bool = True
    search_notes: bool = True
    minimum_score: float = 0.2


class ChatRunData(StrictModel):
    notebook_id: str
    message: str
    session_id: Optional[str] = None
    model_override: Optional[str] = None


class DraftListData(StrictModel):
    notebook_id: str


class DraftCreateData(StrictModel):
    notebook_id: str
    source_ids: list[str]
    title: Optional[str] = None
    note_ids: list[str] = Field(default_factory=list)
    thread_ids: list[str] = Field(default_factory=list)
    model_id: Optional[str] = None
    language: Optional[str] = None
    near_dedup_threshold: Optional[float] = None


class DraftVerifyData(StrictModel):
    draft_id: str


class DraftDownloadMarkdownData(StrictModel):
    draft_id: str


class ResearchThreadListData(StrictModel):
    notebook_id: str


class ResearchThreadCreateData(StrictModel):
    notebook_id: str
    title: str
    seed_kind: Literal["search", "ask", "notebook_chat", "insight"]
    source_ids: list[str] = Field(default_factory=list)
    note_ids: list[str] = Field(default_factory=list)
    question: Optional[str] = None
    answer: Optional[str] = None
    insight_id: Optional[str] = None
    insight_type: Optional[str] = None
    search_results: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_insight_seed_requires_provenance(self) -> "ResearchThreadCreateData":
        if self.seed_kind == "insight" and not (self.insight_id or "").strip():
            raise ValueError("insight_id is required when seed_kind='insight'")
        return self


class ResearchThreadAppendData(StrictModel):
    thread_id: str
    entry_type: Literal[
        "search_result", "answer_snapshot", "note_snapshot", "insight_snapshot"
    ]
    content: str
    title: Optional[str] = None
    source_ids: list[str] = Field(default_factory=list)
    note_ids: list[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResearchThreadToDraftData(StrictModel):
    thread_id: str


class AuditableRunListData(StrictModel):
    source_id: str


class AuditableRunCreateData(StrictModel):
    source_id: str
    model_id: Optional[str] = None
    language: Optional[str] = None
    near_dedup_threshold: Optional[float] = None


class AuditableRunDownloadMarkdownData(StrictModel):
    run_id: str


class AuditableRepairClaimData(StrictModel):
    run_id: str
    target_index: int
    model_id: Optional[str] = None


class AuditableRepairSectionData(StrictModel):
    run_id: str
    target_index: int
    model_id: Optional[str] = None


class NotebookMutateAction(str, Enum):
    create = "create"
    get = "get"
    update = "update"
    delete = "delete"


class NotebookMutateEnvelope(StrictModel):
    action: NotebookMutateAction
    data: Dict[str, Any] = Field(default_factory=dict)


class NotebookCreateData(StrictModel):
    name: str
    description: str = ""


class NotebookGetData(StrictModel):
    notebook_id: str


class NotebookUpdateData(StrictModel):
    notebook_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    archived: Optional[bool] = None

    @model_validator(mode="after")
    def validate_updates_present(self) -> "NotebookUpdateData":
        if self.name is None and self.description is None and self.archived is None:
            raise ValueError("At least one update field is required")
        return self


class NotebookDeleteData(StrictModel):
    notebook_id: str


NotebookMutateData = (
    NotebookCreateData | NotebookGetData | NotebookUpdateData | NotebookDeleteData
)
NOTEBOOK_MUTATE_SCHEMAS: dict[NotebookMutateAction, type[NotebookMutateData]] = {
    NotebookMutateAction.create: NotebookCreateData,
    NotebookMutateAction.get: NotebookGetData,
    NotebookMutateAction.update: NotebookUpdateData,
    NotebookMutateAction.delete: NotebookDeleteData,
}


class SourceMutateAction(str, Enum):
    create_text = "create_text"
    get = "get"
    update = "update"
    delete = "delete"


class SourceMutateEnvelope(StrictModel):
    action: SourceMutateAction
    data: Dict[str, Any] = Field(default_factory=dict)


class SourceCreateTextData(StrictModel):
    notebook_id: str
    content: str
    title: Optional[str] = None
    embed: bool = True


class SourceGetData(StrictModel):
    source_id: str


class SourceUpdateData(StrictModel):
    source_id: str
    title: Optional[str] = None
    topics: Optional[list[str]] = None

    @model_validator(mode="after")
    def validate_updates_present(self) -> "SourceUpdateData":
        if self.title is None and self.topics is None:
            raise ValueError("At least one update field is required")
        return self


class SourceDeleteData(StrictModel):
    source_id: str


SourceMutateData = (
    SourceCreateTextData | SourceGetData | SourceUpdateData | SourceDeleteData
)
SOURCE_MUTATE_SCHEMAS: dict[SourceMutateAction, type[SourceMutateData]] = {
    SourceMutateAction.create_text: SourceCreateTextData,
    SourceMutateAction.get: SourceGetData,
    SourceMutateAction.update: SourceUpdateData,
    SourceMutateAction.delete: SourceDeleteData,
}


class NoteMutateAction(str, Enum):
    create = "create"
    get = "get"
    update = "update"
    delete = "delete"


class NoteMutateEnvelope(StrictModel):
    action: NoteMutateAction
    data: Dict[str, Any] = Field(default_factory=dict)


class NoteCreateData(StrictModel):
    content: str
    notebook_id: Optional[str] = None
    title: Optional[str] = None
    note_type: str = "human"


class NoteGetData(StrictModel):
    note_id: str


class NoteUpdateData(StrictModel):
    note_id: str
    title: Optional[str] = None
    content: Optional[str] = None
    note_type: Optional[str] = None

    @model_validator(mode="after")
    def validate_updates_present(self) -> "NoteUpdateData":
        if self.title is None and self.content is None and self.note_type is None:
            raise ValueError("At least one update field is required")
        return self


class NoteDeleteData(StrictModel):
    note_id: str


NoteMutateData = NoteCreateData | NoteGetData | NoteUpdateData | NoteDeleteData
NOTE_MUTATE_SCHEMAS: dict[NoteMutateAction, type[NoteMutateData]] = {
    NoteMutateAction.create: NoteCreateData,
    NoteMutateAction.get: NoteGetData,
    NoteMutateAction.update: NoteUpdateData,
    NoteMutateAction.delete: NoteDeleteData,
}


class ModelInspectAction(str, Enum):
    list = "list"
    defaults = "defaults"
    provider_policy = "provider_policy"
    provider_bootstrap_diagnostics = "provider_bootstrap_diagnostics"


class ModelInspectEnvelope(StrictModel):
    action: ModelInspectAction
    data: Dict[str, Any] = Field(default_factory=dict)


class ModelListData(StrictModel):
    model_type: Optional[str] = None


class EmptyData(StrictModel):
    pass


ModelInspectData = ModelListData | EmptyData
MODEL_INSPECT_SCHEMAS: dict[ModelInspectAction, type[ModelInspectData]] = {
    ModelInspectAction.list: ModelListData,
    ModelInspectAction.defaults: EmptyData,
    ModelInspectAction.provider_policy: EmptyData,
    ModelInspectAction.provider_bootstrap_diagnostics: EmptyData,
}


class SettingsMutateAction(str, Enum):
    get = "get"
    update = "update"


class SettingsMutateEnvelope(StrictModel):
    action: SettingsMutateAction
    data: Dict[str, Any] = Field(default_factory=dict)


class SettingsUpdateData(StrictModel):
    updates: Dict[str, Any]


SettingsMutateData = EmptyData | SettingsUpdateData
SETTINGS_MUTATE_SCHEMAS: dict[SettingsMutateAction, type[SettingsMutateData]] = {
    SettingsMutateAction.get: EmptyData,
    SettingsMutateAction.update: SettingsUpdateData,
}


class UITestControlAction(str, Enum):
    run = "run"
    get_run = "get_run"
    get_report = "get_report"


class UITestControlEnvelope(StrictModel):
    action: UITestControlAction
    data: Dict[str, Any] = Field(default_factory=dict)


class UITestRunData(StrictModel):
    project: Literal["chromium", "firefox", "webkit"] = "chromium"
    spec: Optional[str] = None
    dry_run: bool = False
    timeout_seconds: int = 600


class UITestRunLookupData(StrictModel):
    run_id: str


UITestControlData = UITestRunData | UITestRunLookupData
UI_TEST_CONTROL_SCHEMAS: dict[UITestControlAction, type[UITestControlData]] = {
    UITestControlAction.run: UITestRunData,
    UITestControlAction.get_run: UITestRunLookupData,
    UITestControlAction.get_report: UITestRunLookupData,
}


class ComputerUseControlAction(str, Enum):
    start = "start"
    get_session = "get_session"
    confirm = "confirm"


class ComputerUseControlEnvelope(StrictModel):
    action: ComputerUseControlAction
    data: Dict[str, Any] = Field(default_factory=dict)


class ComputerUseStartData(StrictModel):
    objective: str
    require_confirmation: bool = True
    dry_run: bool = True


class ComputerUseGetSessionData(StrictModel):
    session_id: str


class ComputerUseConfirmData(StrictModel):
    session_id: str
    confirmation_token: str
    action_idempotency_key: str


ComputerUseControlData = (
    ComputerUseStartData | ComputerUseGetSessionData | ComputerUseConfirmData
)
COMPUTER_USE_CONTROL_SCHEMAS: dict[
    ComputerUseControlAction, type[ComputerUseControlData]
] = {
    ComputerUseControlAction.start: ComputerUseStartData,
    ComputerUseControlAction.get_session: ComputerUseGetSessionData,
    ComputerUseControlAction.confirm: ComputerUseConfirmData,
}
