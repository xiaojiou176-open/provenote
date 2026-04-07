export interface NotebookResponse {
  id: string;
  name: string;
  description: string;
  archived: boolean;
  created: string;
  updated: string;
  source_count: number;
  note_count: number;
}

export interface NoteResponse {
  id: string;
  title: string | null;
  content: string | null;
  note_type: string | null;
  created: string;
  updated: string;
}

export interface SourceListResponse {
  id: string;
  title: string | null;
  topics?: string[]; // Make optional to match Python API
  asset: {
    file_path?: string;
    url?: string;
  } | null;
  embedded: boolean;
  embedded_chunks: number; // ADD: From Python API
  insights_count: number;
  created: string;
  updated: string;
  file_available?: boolean;
  // ADD: Async processing fields from Python API
  command_id?: string;
  status?: string;
  processing_info?: Record<string, unknown>;
}

export interface SourceDetailResponse extends SourceListResponse {
  full_text: string;
  notebooks?: string[]; // List of notebook IDs this source is linked to
}

export type SourceResponse = SourceDetailResponse;

export interface SourceStatusResponse {
  status?: string;
  message: string;
  processing_info?: Record<string, unknown>;
  command_id?: string;
}

export interface SourceProcessingReportResponse {
  source_id: string;
  source_type: string;
  title?: string | null;
  processing_status?: string | null;
  processing_message: string;
  processing_engine?: string | null;
  extracted_length: number;
  paragraph_count: number;
  embedded: boolean;
  embedded_chunks: number;
  insights_count: number;
  has_file: boolean;
  file_available?: boolean | null;
  command_id?: string | null;
  processing_info?: Record<string, unknown> | null;
}

export interface SettingsResponse {
  default_content_processing_engine_doc?: string;
  default_content_processing_engine_url?: string;
  default_embedding_option?: string;
  auto_delete_files?: string;
  youtube_preferred_languages?: string[];
}

export interface CreateNotebookRequest {
  name: string;
  description?: string;
}

export interface UpdateNotebookRequest {
  name?: string;
  description?: string;
  archived?: boolean;
}

export interface NotebookDeletePreview {
  notebook_id: string;
  notebook_name: string;
  note_count: number;
  exclusive_source_count: number;
  shared_source_count: number;
}

export interface NotebookDeleteResponse {
  message: string;
  deleted_notes: number;
  deleted_sources: number;
  unlinked_sources: number;
}

export interface CreateNoteRequest {
  title?: string;
  content: string;
  note_type?: string;
  notebook_id?: string;
}

export interface CreateSourceRequest {
  // Backward compatibility: support old single notebook_id
  notebook_id?: string;
  // New multi-notebook support
  notebooks?: string[];
  // Required fields
  type: "link" | "upload" | "text";
  url?: string;
  file_path?: string;
  content?: string;
  title?: string;
  transformations?: string[];
  embed?: boolean;
  delete_source?: boolean;
  // New async processing support
  async_processing?: boolean;
}

export interface UpdateNoteRequest {
  title?: string;
  content?: string;
  note_type?: string;
}

export interface UpdateSourceRequest {
  title?: string;
  type?: "link" | "upload" | "text";
  url?: string;
  content?: string;
}

export interface APIError {
  detail: string;
}

// Source Chat Types
// Base session interface with common fields
export interface BaseChatSession {
  id: string;
  title: string;
  created: string;
  updated: string;
  message_count?: number;
  model_override?: string | null;
}

export interface SourceChatSession extends BaseChatSession {
  source_id: string;
  model_override?: string;
}

export interface SourceChatMessage {
  id: string;
  type: "human" | "ai";
  content: string;
  timestamp?: string;
}

export interface SourceChatContextIndicator {
  sources: string[];
  insights: string[];
  notes: string[];
}

export interface SourceChatSessionWithMessages extends SourceChatSession {
  messages: SourceChatMessage[];
  context_indicators?: SourceChatContextIndicator;
}

export interface CreateSourceChatSessionRequest {
  source_id: string;
  title?: string;
  model_override?: string;
}

export interface UpdateSourceChatSessionRequest {
  title?: string;
  model_override?: string;
}

export interface SendMessageRequest {
  message: string;
  model_override?: string;
}

export interface SourceChatStreamEvent {
  type: "user_message" | "ai_message" | "context_indicators" | "complete" | "error";
  content?: string;
  data?: unknown;
  message?: string;
  timestamp?: string;
}

// Notebook Chat Types
export interface NotebookChatSession extends BaseChatSession {
  notebook_id: string;
}

export interface NotebookChatMessage {
  id: string;
  type: "human" | "ai";
  content: string;
  timestamp?: string;
}

export interface NotebookChatSessionWithMessages extends NotebookChatSession {
  messages: NotebookChatMessage[];
}

export interface CreateNotebookChatSessionRequest {
  notebook_id: string;
  title?: string;
  model_override?: string;
}

export interface UpdateNotebookChatSessionRequest {
  title?: string;
  model_override?: string | null;
}

export interface SendNotebookChatMessageRequest {
  session_id: string;
  message: string;
  context: {
    sources: Array<Record<string, unknown>>;
    notes: Array<Record<string, unknown>>;
  };
  model_override?: string;
}

export interface BuildContextRequest {
  notebook_id: string;
  context_config: {
    sources: Record<string, string>;
    notes: Record<string, string>;
  };
}

export interface BuildContextResponse {
  context: {
    sources: Array<Record<string, unknown>>;
    notes: Array<Record<string, unknown>>;
  };
  token_count: number;
  char_count: number;
}

export type AuditableRunStatus = "queued" | "running" | "completed" | "failed";

export interface AuditableRunMetrics {
  coverage_rate: number;
  missing_count: number;
  duplicate_count: number;
  uncited_claims_count: number;
  dedup_group_count: number;
  unknown_pid_count: number;
  unclassified_count: number;
}

export interface AuditableRunResponse {
  id: string;
  source_id: string;
  status: AuditableRunStatus;
  model_id: string;
  language: string;
  near_dedup_threshold: number;
  metrics: AuditableRunMetrics;
  coverage_json: Record<string, unknown>;
  dedup_json: Record<string, unknown>;
  result_markdown: string;
  source_paragraphs?: Array<Record<string, unknown>>;
  sections?: Array<Record<string, unknown>>;
  claims?: Array<Record<string, unknown>>;
  dedup_entries?: Array<Record<string, unknown>>;
  created: string;
  updated: string;
}

export interface CreateAuditableRunRequest {
  model_id?: string;
  language?: string;
  near_dedup_threshold?: number;
}

export interface AuditableRepairRequest {
  target_index: number;
  model_id?: string;
}

export type DraftStatus = "queued" | "running" | "completed" | "failed" | "verified";

export interface DraftResponse {
  id: string;
  notebook_id: string;
  title: string;
  status: DraftStatus;
  model_id: string;
  language: string;
  near_dedup_threshold: number;
  source_ids: string[];
  note_ids: string[];
  thread_ids: string[];
  version: number;
  parent_draft_id?: string | null;
  metrics: AuditableRunMetrics;
  coverage_json: Record<string, unknown>;
  dedup_json: Record<string, unknown>;
  result_markdown: string;
  source_paragraphs: Array<Record<string, unknown>>;
  sections: Array<Record<string, unknown>>;
  claims: Array<Record<string, unknown>>;
  dedup_entries: Array<Record<string, unknown>>;
  verified_brief_snapshot?: Record<string, unknown> | null;
  created: string;
  updated: string;
}

export interface CreateDraftRequest {
  title?: string;
  source_ids: string[];
  note_ids?: string[];
  thread_ids?: string[];
  model_id?: string;
  language?: string;
  near_dedup_threshold?: number;
}

export interface RerunDraftRequest {
  title?: string;
  source_ids?: string[];
  note_ids?: string[];
  thread_ids?: string[];
  model_id?: string;
  language?: string;
  near_dedup_threshold?: number;
}

export interface ResearchThreadResponse {
  id: string;
  notebook_id: string;
  title: string;
  seed_kind: "search" | "ask" | "notebook_chat" | "insight";
  source_ids: string[];
  note_ids: string[];
  entries: Array<Record<string, unknown>>;
  entry_count: number;
  created: string;
  updated: string;
}

export interface CreateResearchThreadRequest {
  title: string;
  seed_kind: "search" | "ask" | "notebook_chat" | "insight";
  source_ids?: string[];
  note_ids?: string[];
  question?: string;
  answer?: string;
  insight_id?: string;
  insight_type?: string;
  search_results?: Array<Record<string, unknown>>;
}

export interface AppendResearchThreadEntryRequest {
  entry_type: "search_result" | "answer_snapshot" | "note_snapshot" | "insight_snapshot";
  title?: string;
  content: string;
  source_ids?: string[];
  note_ids?: string[];
  metadata?: Record<string, unknown>;
}
