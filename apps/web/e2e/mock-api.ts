import type { Page, Request, Route } from "@playwright/test";

type ModelType = "language" | "embedding" | "text_to_speech" | "speech_to_text";

interface MockNotebook {
  id: string;
  name: string;
  description: string;
  archived: boolean;
  source_count: number;
  note_count: number;
  created: string;
  updated: string;
}

interface MockSource {
  id: string;
  title: string;
  created: string;
  updated: string;
  insights_count: number;
  embedded: boolean;
  embedded_chunks?: number;
  file_available?: boolean;
  notebooks?: string[];
  topics?: string[];
  status?: "new" | "queued" | "running" | "completed" | "failed";
  processing_info?: Record<string, unknown>;
  asset?: {
    url?: string;
    file_path?: string;
  } | null;
}

interface MockSourceDetail extends MockSource {
  full_text: string;
}

interface MockSourceInsight {
  id: string;
  source_id: string;
  insight_type: string;
  content: string;
  created: string;
  updated: string;
}

interface MockSourceChatMessage {
  id: string;
  type: "human" | "ai";
  content: string;
  timestamp?: string;
}

interface MockSourceChatSession {
  id: string;
  source_id: string;
  title: string;
  created: string;
  updated: string;
  model_override?: string | null;
  message_count?: number;
  messages?: MockSourceChatMessage[];
}

interface MockTransformation {
  id: string;
  name: string;
  title: string;
  description: string;
  prompt: string;
  apply_default: boolean;
  created: string;
  updated: string;
}

interface MockAuditableRun {
  id: string;
  source_id: string;
  status: "queued" | "running" | "completed" | "failed";
  model_id: string;
  language: string;
  markdown_url?: string;
  markdown_sha256?: string;
  markdown_path?: string;
  command_id?: string;
  created: string;
  updated: string;
  metrics?: {
    coverage_rate: number;
    missing_count: number;
    duplicate_count: number;
    uncited_claims_count: number;
    dedup_group_count: number;
    unknown_pid_count: number;
    unclassified_count: number;
  };
}

interface MockDraft {
  id: string;
  notebook_id: string;
  title: string;
  status: "queued" | "running" | "completed" | "failed" | "verified";
  model_id: string;
  language: string;
  near_dedup_threshold: number;
  source_ids: string[];
  note_ids: string[];
  thread_ids: string[];
  version: number;
  parent_draft_id?: string | null;
  metrics: {
    coverage_rate: number;
    missing_count: number;
    duplicate_count: number;
    uncited_claims_count: number;
    dedup_group_count: number;
    unknown_pid_count: number;
    unclassified_count: number;
  };
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

interface MockCommandJob {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed" | "canceled";
  result?: Record<string, unknown>;
  error_message?: string;
}

interface MockCredential {
  id: string;
  name: string;
  provider: string;
  modalities: string[];
  has_api_key: boolean;
  created: string;
  updated: string;
  model_count: number;
  base_url?: string | null;
  project?: string | null;
  location?: string | null;
  credentials_path?: string | null;
}

interface MockModel {
  id: string;
  name: string;
  provider: string;
  type: ModelType;
  credential?: string | null;
  created: string;
  updated: string;
}

interface MockSearchResponse {
  results: Array<{
    id: string;
    title: string;
    parent_id: string;
    final_score: number;
    matches?: string[];
    created: string;
    updated: string;
  }>;
  total_count: number;
  search_type: string;
}

interface AskEvent {
  type: "strategy" | "answer" | "final_answer" | "complete" | "error";
  reasoning?: string;
  searches?: Array<{ term: string; instructions: string }>;
  content?: string;
  message?: string;
}

interface MockCredentialStatus {
  configured: Record<string, boolean>;
  source: Record<string, "database" | "none">;
  legacy_env_detected: Record<string, boolean>;
  encryption_configured: boolean;
  policy_effective: Record<"language" | "embedding" | "speech_to_text" | "text_to_speech", boolean>;
  policy_active_provider: Record<
    "language" | "embedding" | "speech_to_text" | "text_to_speech",
    string | null
  >;
  policy_blockers: Record<
    "language" | "embedding" | "speech_to_text" | "text_to_speech",
    string | null
  >;
  provider_capabilities: Record<
    string,
    Record<
      "language" | "embedding" | "speech_to_text" | "text_to_speech",
      { status: string; detail: string }
    >
  >;
}

interface MockModelDefaults {
  default_chat_model: string | null;
  default_transformation_model: string | null;
  large_context_model: string | null;
  default_text_to_speech_model: string | null;
  default_speech_to_text_model: string | null;
  default_embedding_model: string | null;
  default_tools_model: string | null;
}

interface MockProviderPolicy {
  language: string[];
  embedding: string[];
  speech_to_text: string[];
  text_to_speech: string[];
}

interface MockDiscoveredModel {
  name: string;
  provider: string;
  description?: string;
}

interface MockSettings {
  default_content_processing_engine_doc?: string;
  default_content_processing_engine_url?: string;
  default_embedding_option?: string;
  auto_delete_files?: string;
  youtube_preferred_languages?: string[];
}

interface MockEpisodeProfile {
  id: string;
  name: string;
  description: string;
  speaker_config: string;
  outline_provider: string;
  outline_model: string;
  transcript_provider: string;
  transcript_model: string;
  default_briefing: string;
  num_segments: number;
}

interface MockSpeakerProfile {
  id: string;
  name: string;
  description: string;
  tts_provider: string;
  tts_model: string;
  speakers: Array<{
    name: string;
    voice_id: string;
    backstory: string;
    personality: string;
  }>;
}

interface MockPodcastEpisode {
  id: string;
  name: string;
  episode_profile: MockEpisodeProfile;
  speaker_profile: MockSpeakerProfile;
  briefing: string;
  audio_file?: string | null;
  audio_url?: string | null;
  transcript?: Record<string, unknown> | null;
  outline?: Record<string, unknown> | null;
  created?: string | null;
  job_status?: string | null;
  error_message?: string | null;
}

interface MockRebuildStatus {
  status: "queued" | "running" | "completed" | "failed";
  progress?: {
    total_items?: number;
    processed_items?: number;
    failed_items?: number;
    total?: number;
    processed?: number;
    percentage?: number;
  };
  stats?: {
    sources_processed?: number;
    notes_processed?: number;
    insights_processed?: number;
    sources?: number;
    notes?: number;
    insights?: number;
    failed?: number;
    failed_items?: number;
    processing_time?: number;
  };
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

export interface MockApiOptions {
  authEnabled?: boolean;
  notebooks?: MockNotebook[];
  sources?: MockSource[];
  sourceDetails?: MockSourceDetail[];
  sourceInsights?: MockSourceInsight[];
  sourceChatSessions?: MockSourceChatSession[];
  transformations?: MockTransformation[];
  defaultTransformationPrompt?: string;
  auditableRuns?: MockAuditableRun[];
  drafts?: MockDraft[];
  credentials?: MockCredential[];
  models?: MockModel[];
  modelDefaults?: Partial<MockModelDefaults>;
  credentialStatus?: Partial<MockCredentialStatus>;
  searchResponse?: MockSearchResponse;
  askEvents?: AskEvent[];
  discoveredByProvider?: Record<string, MockDiscoveredModel[]>;
  settings?: MockSettings;
  settingsUpdateStatus?: number;
  episodeProfiles?: MockEpisodeProfile[];
  speakerProfiles?: MockSpeakerProfile[];
  podcastEpisodes?: MockPodcastEpisode[];
  rebuildStatus?: MockRebuildStatus;
  failOnUnhandledRoute?: boolean;
}

interface MockState {
  authEnabled: boolean;
  notebooks: MockNotebook[];
  sources: MockSource[];
  sourceDetails: MockSourceDetail[];
  sourceInsights: MockSourceInsight[];
  sourceChatSessions: MockSourceChatSession[];
  transformations: MockTransformation[];
  defaultTransformationPrompt: string;
  auditableRuns: MockAuditableRun[];
  drafts: MockDraft[];
  commandJobsById: Record<string, MockCommandJob>;
  credentials: MockCredential[];
  models: MockModel[];
  modelDefaults: MockModelDefaults;
  providerPolicy: MockProviderPolicy;
  credentialStatus: MockCredentialStatus;
  searchResponse: MockSearchResponse;
  askEvents: AskEvent[];
  discoveredByProvider: Record<string, MockDiscoveredModel[]>;
  settings: MockSettings;
  settingsUpdateStatus: number | null;
  episodeProfiles: MockEpisodeProfile[];
  speakerProfiles: MockSpeakerProfile[];
  podcastEpisodes: MockPodcastEpisode[];
  rebuildStatusTemplate: MockRebuildStatus;
  rebuildStatusByCommand: Record<string, MockRebuildStatus & { command_id: string }>;
}

const now = () => new Date().toISOString();

const DEFAULT_MODEL_DEFAULTS: MockModelDefaults = {
  default_chat_model: null,
  default_transformation_model: null,
  large_context_model: null,
  default_text_to_speech_model: null,
  default_speech_to_text_model: null,
  default_embedding_model: null,
  default_tools_model: null,
};

const DEFAULT_SEARCH_RESPONSE: MockSearchResponse = {
  results: [],
  total_count: 0,
  search_type: "text",
};

const DEFAULT_PROVIDER_POLICY: MockProviderPolicy = {
  language: ["google"],
  embedding: ["google"],
  speech_to_text: ["google"],
  text_to_speech: ["google"],
};

const DEFAULT_ASK_EVENTS: AskEvent[] = [
  {
    type: "strategy",
    reasoning: "Use keyword search then synthesize.",
    searches: [{ term: "open notebook", instructions: "Find relevant entries." }],
  },
  { type: "answer", content: "Intermediate answer chunk." },
  { type: "final_answer", content: "Final synthesized answer for testing." },
  { type: "complete" },
];

const DEFAULT_CREDENTIAL_STATUS: MockCredentialStatus = {
  configured: {},
  source: {},
  legacy_env_detected: {},
  encryption_configured: true,
  policy_effective: {
    language: false,
    embedding: false,
    speech_to_text: false,
    text_to_speech: false,
  },
  policy_active_provider: {
    language: null,
    embedding: null,
    speech_to_text: null,
    text_to_speech: null,
  },
  policy_blockers: {
    language: "No configured provider available in chain: google",
    embedding: "No configured provider available in chain: google",
    speech_to_text: "No configured provider available in chain: google",
    text_to_speech: "No configured provider available in chain: google",
  },
  provider_capabilities: {
    google: {
      language: { status: "preview", detail: "mock" },
      embedding: { status: "preview", detail: "mock" },
      speech_to_text: { status: "preview", detail: "mock" },
      text_to_speech: { status: "preview", detail: "mock" },
    },
  },
};

const DEFAULT_SETTINGS: MockSettings = {
  default_content_processing_engine_doc: "auto",
  default_content_processing_engine_url: "auto",
  default_embedding_option: "ask",
  auto_delete_files: "no",
  youtube_preferred_languages: ["en"],
};

const DEFAULT_TRANSFORMATION_PROMPT = "";

const DEFAULT_REBUILD_STATUS: MockRebuildStatus = {
  status: "completed",
  progress: {
    total_items: 10,
    processed_items: 10,
    failed_items: 0,
    percentage: 100,
  },
  stats: {
    sources_processed: 6,
    notes_processed: 3,
    insights_processed: 1,
    failed_items: 0,
    processing_time: 1.5,
  },
};

function pickFirstModelId(models: MockModel[], type: ModelType): string | null {
  return models.find((model) => model.type === type)?.id ?? null;
}

function json(route: Route, body: unknown, status: number = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

function readBody(request: Request): Record<string, unknown> {
  const postData = request.postData();
  if (!postData) {
    return {};
  }

  try {
    return JSON.parse(postData) as Record<string, unknown>;
  } catch (error) {
    throw new SyntaxError(
      `Invalid JSON request body: ${error instanceof Error ? error.message : "parse failure"}`,
    );
  }
}

function getSortDirection(raw: string | null): "asc" | "desc" {
  return raw === "asc" ? "asc" : "desc";
}

function toTime(value: string | undefined) {
  return new Date(value ?? "").getTime() || 0;
}

function withUpdatedModelCounts(state: MockState) {
  for (const credential of state.credentials) {
    credential.model_count = state.models.filter(
      (model) => model.credential === credential.id,
    ).length;
  }
}

function refreshPolicyStatus(status: MockCredentialStatus) {
  const chain: Array<"google"> = ["google"];
  const modalities: Array<"language" | "embedding" | "speech_to_text" | "text_to_speech"> = [
    "language",
    "embedding",
    "speech_to_text",
    "text_to_speech",
  ];
  for (const modality of modalities) {
    const active = chain.find((provider) => status.configured[provider]) ?? null;
    status.policy_effective[modality] = active !== null;
    status.policy_active_provider[modality] = active;
    status.policy_blockers[modality] = active
      ? null
      : "No configured provider available in chain: google";
  }
}

function cleanupDeletedModelFromDefaults(defaults: MockModelDefaults, modelId: string) {
  for (const key of Object.keys(defaults) as Array<keyof MockModelDefaults>) {
    if (defaults[key] === modelId) {
      defaults[key] = null;
    }
  }
}

function createSourceDetail(source: MockSource): MockSourceDetail {
  return {
    ...source,
    asset: source.asset ?? null,
    embedded_chunks: source.embedded_chunks ?? 0,
    full_text:
      source.asset?.url ||
      source.asset?.file_path ||
      source.title ||
      `Mock source content for ${source.id}`,
    notebooks: source.notebooks ?? [],
    topics: source.topics ?? [],
    file_available:
      typeof source.file_available === "boolean"
        ? source.file_available
        : Boolean(source.asset?.file_path),
  };
}

function createSourceListItem(detail: MockSourceDetail): MockSource {
  return {
    id: detail.id,
    title: detail.title,
    created: detail.created,
    updated: detail.updated,
    insights_count: detail.insights_count,
    embedded: detail.embedded,
    embedded_chunks: detail.embedded_chunks,
    file_available: detail.file_available,
    notebooks: detail.notebooks,
    topics: detail.topics,
    status: detail.status,
    processing_info: detail.processing_info,
    asset: detail.asset,
  };
}

export async function setupMockApi(page: Page, options: MockApiOptions = {}) {
  const failOnUnhandledRoute = options.failOnUnhandledRoute ?? true;
  const state: MockState = {
    authEnabled: options.authEnabled ?? false,
    notebooks: [...(options.notebooks ?? [])],
    sources: [...(options.sources ?? [])],
    sourceDetails: [...(options.sourceDetails ?? [])],
    sourceInsights: [...(options.sourceInsights ?? [])],
    sourceChatSessions: [...(options.sourceChatSessions ?? [])],
    transformations: [...(options.transformations ?? [])],
    defaultTransformationPrompt:
      options.defaultTransformationPrompt ?? DEFAULT_TRANSFORMATION_PROMPT,
    auditableRuns: [...(options.auditableRuns ?? [])],
    drafts: [...(options.drafts ?? [])],
    commandJobsById: {},
    credentials: [...(options.credentials ?? [])],
    models: [...(options.models ?? [])],
    modelDefaults: {
      ...DEFAULT_MODEL_DEFAULTS,
      ...(options.modelDefaults ?? {}),
    },
    providerPolicy: {
      ...DEFAULT_PROVIDER_POLICY,
    },
    credentialStatus: {
      ...DEFAULT_CREDENTIAL_STATUS,
      ...(options.credentialStatus ?? {}),
      configured: {
        ...DEFAULT_CREDENTIAL_STATUS.configured,
        ...(options.credentialStatus?.configured ?? {}),
      },
      source: {
        ...DEFAULT_CREDENTIAL_STATUS.source,
        ...(options.credentialStatus?.source ?? {}),
      },
      legacy_env_detected: {
        ...DEFAULT_CREDENTIAL_STATUS.legacy_env_detected,
        ...(options.credentialStatus?.legacy_env_detected ?? {}),
      },
      policy_effective: {
        ...DEFAULT_CREDENTIAL_STATUS.policy_effective,
        ...(options.credentialStatus?.policy_effective ?? {}),
      },
      policy_active_provider: {
        ...DEFAULT_CREDENTIAL_STATUS.policy_active_provider,
        ...(options.credentialStatus?.policy_active_provider ?? {}),
      },
      policy_blockers: {
        ...DEFAULT_CREDENTIAL_STATUS.policy_blockers,
        ...(options.credentialStatus?.policy_blockers ?? {}),
      },
      provider_capabilities: {
        ...DEFAULT_CREDENTIAL_STATUS.provider_capabilities,
        ...(options.credentialStatus?.provider_capabilities ?? {}),
      },
    },
    searchResponse: options.searchResponse
      ? {
          ...options.searchResponse,
          results: [...options.searchResponse.results],
        }
      : {
          ...DEFAULT_SEARCH_RESPONSE,
          results: [...DEFAULT_SEARCH_RESPONSE.results],
        },
    askEvents: [...(options.askEvents ?? DEFAULT_ASK_EVENTS)],
    discoveredByProvider: Object.fromEntries(
      Object.entries(options.discoveredByProvider ?? {}).map(([provider, models]) => [
        provider,
        [...models],
      ]),
    ),
    settings: {
      ...DEFAULT_SETTINGS,
      ...(options.settings ?? {}),
    },
    settingsUpdateStatus: options.settingsUpdateStatus ?? null,
    episodeProfiles: [...(options.episodeProfiles ?? [])],
    speakerProfiles: [...(options.speakerProfiles ?? [])],
    podcastEpisodes: [...(options.podcastEpisodes ?? [])],
    rebuildStatusTemplate: options.rebuildStatus ?? DEFAULT_REBUILD_STATUS,
    rebuildStatusByCommand: {},
  };

  state.modelDefaults = {
    ...state.modelDefaults,
    default_chat_model:
      state.modelDefaults.default_chat_model ?? pickFirstModelId(state.models, "language"),
    default_transformation_model:
      state.modelDefaults.default_transformation_model ??
      pickFirstModelId(state.models, "language"),
    large_context_model:
      state.modelDefaults.large_context_model ?? pickFirstModelId(state.models, "language"),
    default_tools_model:
      state.modelDefaults.default_tools_model ?? pickFirstModelId(state.models, "language"),
    default_embedding_model:
      state.modelDefaults.default_embedding_model ?? pickFirstModelId(state.models, "embedding"),
    default_text_to_speech_model:
      state.modelDefaults.default_text_to_speech_model ??
      pickFirstModelId(state.models, "text_to_speech"),
    default_speech_to_text_model:
      state.modelDefaults.default_speech_to_text_model ??
      pickFirstModelId(state.models, "speech_to_text"),
  };

  if (state.sourceDetails.length === 0 && state.sources.length > 0) {
    state.sourceDetails = state.sources.map((source) => createSourceDetail(source));
  } else if (state.sourceDetails.length > 0 && state.sources.length === 0) {
    state.sources = state.sourceDetails.map((source) => createSourceListItem(source));
  }

  if (state.sourceDetails.length > 0) {
    const detailById = new Map(state.sourceDetails.map((source) => [source.id, source]));
    state.sources = state.sources.map((source) => {
      const detail = detailById.get(source.id);
      return detail ? createSourceListItem(detail) : source;
    });
  }

  withUpdatedModelCounts(state);

  await page.addInitScript(() => {
    localStorage.setItem("i18nextLng", "en-US");
  });

  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const { pathname } = url;
    const method = request.method();

    try {
      if (pathname === "/config") {
        return json(route, { apiUrl: "" });
      }

      if (pathname === "/api/config") {
        return json(route, {
          version: "e2e-test",
          latestVersion: null,
          hasUpdate: false,
          dbStatus: "online",
        });
      }

      if (pathname === "/api/auth/status") {
        return json(route, { auth_enabled: state.authEnabled });
      }

      if (!pathname.startsWith("/api/")) {
        return route.continue();
      }

      if (pathname === "/api/settings" && method === "GET") {
        return json(route, state.settings);
      }

      if (pathname === "/api/settings" && method === "PUT") {
        if (state.settingsUpdateStatus !== null && state.settingsUpdateStatus >= 400) {
          return json(route, { detail: "Mock settings update failed" }, state.settingsUpdateStatus);
        }
        const body = readBody(request);
        state.settings = {
          ...state.settings,
          ...body,
        };
        return json(route, state.settings);
      }

      if (pathname === "/api/transformations" && method === "GET") {
        return json(route, state.transformations);
      }

      if (pathname === "/api/transformations" && method === "POST") {
        const body = readBody(request);
        const transformation: MockTransformation = {
          id: `tr-${Date.now()}`,
          name: String(body.name ?? "new_transformation"),
          title: String(body.title ?? body.name ?? "New Transformation"),
          description: String(body.description ?? ""),
          prompt: String(body.prompt ?? ""),
          apply_default: Boolean(body.apply_default),
          created: now(),
          updated: now(),
        };
        state.transformations.unshift(transformation);
        return json(route, transformation, 201);
      }

      if (pathname === "/api/transformations/default-prompt" && method === "GET") {
        return json(route, { transformation_instructions: state.defaultTransformationPrompt });
      }

      if (pathname === "/api/transformations/default-prompt" && method === "PUT") {
        const body = readBody(request);
        state.defaultTransformationPrompt = String(body.transformation_instructions ?? "");
        return json(route, { transformation_instructions: state.defaultTransformationPrompt });
      }

      if (pathname === "/api/transformations/execute" && method === "POST") {
        const body = readBody(request);
        const transformationId = String(body.transformation_id ?? "");
        const inputText = String(body.input_text ?? "");
        const modelId = String(body.model_id ?? "");
        const transformation = state.transformations.find((item) => item.id === transformationId);
        const transformationName = transformation?.name ?? transformationId;
        return json(route, {
          output: `Mock output (${transformationName}): ${inputText.slice(0, 120)}`,
          transformation_id: transformationId,
          model_id: modelId,
        });
      }

      if (/^\/api\/transformations\/[^/]+$/.test(pathname) && method === "GET") {
        const transformationId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const transformation = state.transformations.find((item) => item.id === transformationId);
        if (!transformation) {
          return json(route, { detail: "Transformation not found" }, 404);
        }
        return json(route, transformation);
      }

      if (/^\/api\/transformations\/[^/]+$/.test(pathname) && method === "PUT") {
        const transformationId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const transformation = state.transformations.find((item) => item.id === transformationId);
        if (!transformation) {
          return json(route, { detail: "Transformation not found" }, 404);
        }
        const body = readBody(request);
        transformation.name = typeof body.name === "string" ? body.name : transformation.name;
        transformation.title = typeof body.title === "string" ? body.title : transformation.title;
        transformation.description =
          typeof body.description === "string" ? body.description : transformation.description;
        transformation.prompt =
          typeof body.prompt === "string" ? body.prompt : transformation.prompt;
        transformation.apply_default =
          typeof body.apply_default === "boolean"
            ? body.apply_default
            : transformation.apply_default;
        transformation.updated = now();
        return json(route, transformation);
      }

      if (/^\/api\/transformations\/[^/]+$/.test(pathname) && method === "DELETE") {
        const transformationId = decodeURIComponent(pathname.split("/")[3] ?? "");
        state.transformations = state.transformations.filter(
          (item) => item.id !== transformationId,
        );
        return json(route, {});
      }

      if (pathname === "/api/notebooks" && method === "GET") {
        const archivedParam = url.searchParams.get("archived");
        const archivedFilter = archivedParam === null ? undefined : archivedParam === "true";
        const orderBy = (url.searchParams.get("order_by") ?? "updated desc").toLowerCase();
        const [orderField, orderDirRaw] = orderBy.split(" ");
        const orderDir = getSortDirection(orderDirRaw);

        let notebooks = [...state.notebooks];
        if (archivedFilter !== undefined) {
          notebooks = notebooks.filter((notebook) => notebook.archived === archivedFilter);
        }

        const sorted = notebooks.sort((a, b) => {
          const left = orderField.includes("created") ? toTime(a.created) : toTime(a.updated);
          const right = orderField.includes("created") ? toTime(b.created) : toTime(b.updated);
          return orderDir === "asc" ? left - right : right - left;
        });

        return json(route, sorted);
      }
      if (pathname === "/api/notebooks" && method === "POST") {
        const body = readBody(request);
        const notebook: MockNotebook = {
          id: `nb-${Date.now()}`,
          name: String(body.name ?? "New Notebook"),
          description: String(body.description ?? ""),
          archived: false,
          source_count: 0,
          note_count: 0,
          created: now(),
          updated: now(),
        };
        state.notebooks.unshift(notebook);
        return json(route, notebook, 201);
      }

      if (/^\/api\/notebooks\/[^/]+$/.test(pathname) && method === "GET") {
        const notebookId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const notebook = state.notebooks.find((item) => item.id === notebookId);
        if (!notebook) {
          return json(route, { detail: "Notebook not found" }, 404);
        }
        return json(route, notebook);
      }

      if (/^\/api\/notebooks\/[^/]+$/.test(pathname) && method === "PUT") {
        const notebookId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const body = readBody(request);
        const notebook = state.notebooks.find((item) => item.id === notebookId);
        if (!notebook) {
          return json(route, { detail: "Notebook not found" }, 404);
        }

        notebook.name = typeof body.name === "string" ? body.name : notebook.name;
        notebook.description =
          typeof body.description === "string" ? body.description : notebook.description;
        notebook.archived = typeof body.archived === "boolean" ? body.archived : notebook.archived;
        notebook.updated = now();

        return json(route, notebook);
      }

      if (/^\/api\/notebooks\/[^/]+\/drafts$/.test(pathname) && method === "GET") {
        const notebookId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const drafts = state.drafts.filter((item) => item.notebook_id === notebookId);
        return json(route, drafts);
      }

      if (/^\/api\/notebooks\/[^/]+\/drafts$/.test(pathname) && method === "POST") {
        const notebookId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const body = readBody(request);
        const sourceIds = Array.isArray(body.source_ids)
          ? body.source_ids.map((value) => String(value))
          : [];
        const title =
          typeof body.title === "string" && body.title.trim()
            ? body.title
            : `Notebook Draft ${state.drafts.length + 1}`;
        const draft: MockDraft = {
          id: `draft-${Date.now()}`,
          notebook_id: notebookId,
          title,
          status: "completed",
          model_id: "model-draft",
          language: "zh-CN",
          near_dedup_threshold: 0.97,
          source_ids: sourceIds,
          note_ids: [],
          thread_ids: [],
          version: 1,
          parent_draft_id: null,
          metrics: {
            coverage_rate: 1,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            dedup_group_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          coverage_json: {},
          dedup_json: {},
          result_markdown: `# ${title}\n`,
          source_paragraphs: [],
          sections: [],
          claims: [],
          dedup_entries: [],
          verified_brief_snapshot: null,
          created: now(),
          updated: now(),
        };
        state.drafts.unshift(draft);
        return json(route, draft, 201);
      }

      if (pathname === "/api/notes" && method === "GET") {
        return json(route, []);
      }

      if (pathname === "/api/chat/sessions" && method === "GET") {
        return json(route, []);
      }

      if (pathname === "/api/chat/sessions" && method === "POST") {
        const body = readBody(request);
        const sessionId = `chat-${Date.now()}`;
        return json(
          route,
          {
            id: sessionId,
            notebook_id: String(body.notebook_id ?? ""),
            title: String(body.title ?? "New Session"),
            created: now(),
            updated: now(),
            message_count: 0,
            model_override:
              typeof body.model_override === "string"
                ? body.model_override
                : (null as string | null),
          },
          201,
        );
      }

      if (/^\/api\/chat\/sessions\/[^/]+$/.test(pathname) && method === "GET") {
        const sessionId = decodeURIComponent(pathname.split("/")[4] ?? "");
        return json(route, {
          id: sessionId,
          notebook_id: "nb-mock",
          title: "Mock Session",
          created: now(),
          updated: now(),
          message_count: 0,
          messages: [],
        });
      }

      if (/^\/api\/chat\/sessions\/[^/]+$/.test(pathname) && method === "PUT") {
        const sessionId = decodeURIComponent(pathname.split("/")[4] ?? "");
        const body = readBody(request);
        return json(route, {
          id: sessionId,
          notebook_id: "nb-mock",
          title: String(body.title ?? "Mock Session"),
          created: now(),
          updated: now(),
          message_count: 0,
          model_override:
            typeof body.model_override === "string" ? body.model_override : (null as string | null),
        });
      }

      if (/^\/api\/chat\/sessions\/[^/]+$/.test(pathname) && method === "DELETE") {
        return json(route, {});
      }

      if (pathname === "/api/chat/execute" && method === "POST") {
        const body = readBody(request);
        const userMessage = String(body.message ?? "");
        return json(route, {
          session_id: String(body.session_id ?? ""),
          messages: [
            {
              id: `human-${Date.now()}`,
              type: "human",
              content: userMessage,
              timestamp: now(),
            },
            {
              id: `ai-${Date.now()}`,
              type: "ai",
              content: `Mock notebook response: ${userMessage}`,
              timestamp: now(),
            },
          ],
        });
      }

      if (pathname === "/api/chat/context" && method === "POST") {
        return json(route, {
          context: {
            sources: [],
            notes: [],
          },
          token_count: 0,
          char_count: 0,
        });
      }

      if (pathname === "/api/sources" && method === "GET") {
        const sortBy = url.searchParams.get("sort_by") === "created" ? "created" : "updated";
        const sortOrder = getSortDirection(url.searchParams.get("sort_order"));
        const limit = Number(url.searchParams.get("limit") ?? "30");
        const offset = Number(url.searchParams.get("offset") ?? "0");
        const notebookId = url.searchParams.get("notebook_id");

        let sources = [...state.sources];
        if (notebookId) {
          sources = sources.filter((source) => (source.notebooks ?? []).includes(notebookId));
        }

        const sorted = sources.sort((a, b) => {
          const left = sortBy === "created" ? toTime(a.created) : toTime(a.updated);
          const right = sortBy === "created" ? toTime(b.created) : toTime(b.updated);
          return sortOrder === "asc" ? left - right : right - left;
        });

        const paged = sorted.slice(offset, offset + limit);
        return json(route, paged);
      }

      if (/^\/api\/sources\/[^/]+$/.test(pathname) && method === "GET") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const sourceDetail = state.sourceDetails.find((source) => source.id === sourceId);
        if (!sourceDetail) {
          return json(route, { detail: "Source not found" }, 404);
        }
        return json(route, sourceDetail);
      }

      if (/^\/api\/sources\/[^/]+$/.test(pathname) && method === "PUT") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const body = readBody(request);
        const source = state.sources.find((item) => item.id === sourceId);
        const sourceDetail = state.sourceDetails.find((item) => item.id === sourceId);
        if (!source || !sourceDetail) {
          return json(route, { detail: "Source not found" }, 404);
        }
        if (typeof body.title === "string") {
          source.title = body.title;
          sourceDetail.title = body.title;
        }
        source.updated = now();
        sourceDetail.updated = source.updated;
        return json(route, sourceDetail);
      }

      if (/^\/api\/sources\/[^/]+\/status$/.test(pathname) && method === "GET") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const source = state.sources.find((item) => item.id === sourceId);
        if (!source) {
          return json(route, { detail: "Source not found" }, 404);
        }
        return json(route, {
          status: source.status ?? "completed",
          message: source.status === "failed" ? "Processing failed" : "Ready",
          processing_info: source.processing_info ?? {},
          command_id: undefined,
        });
      }

      if (/^\/api\/sources\/[^/]+\/retry$/.test(pathname) && method === "POST") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const source = state.sources.find((item) => item.id === sourceId);
        const sourceDetail = state.sourceDetails.find((item) => item.id === sourceId);
        if (!source || !sourceDetail) {
          return json(route, { detail: "Source not found" }, 404);
        }
        source.status = "queued";
        source.processing_info = { progress: 0 };
        sourceDetail.status = "queued";
        sourceDetail.processing_info = { progress: 0 };
        return json(route, { id: sourceId, status: "queued" });
      }

      if (/^\/api\/sources\/[^/]+\/download$/.test(pathname) && method === "GET") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const sourceDetail = state.sourceDetails.find((item) => item.id === sourceId);
        if (!sourceDetail) {
          return json(route, { detail: "Source not found" }, 404);
        }
        const filename =
          sourceDetail.asset?.file_path?.split("/").pop() ?? `source-${sourceId}.txt`;
        return route.fulfill({
          status: 200,
          headers: {
            "content-type": "text/plain; charset=utf-8",
            "content-disposition": `attachment; filename=\"${filename}\"`,
          },
          body: sourceDetail.full_text,
        });
      }

      if (/^\/api\/sources\/[^/]+\/insights$/.test(pathname) && method === "GET") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const insights = state.sourceInsights.filter((item) => item.source_id === sourceId);
        return json(route, insights);
      }

      if (/^\/api\/sources\/[^/]+\/insights$/.test(pathname) && method === "POST") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const body = readBody(request);
        const insightId = `insight-${Date.now()}`;
        const commandId = `cmd-${Date.now()}`;
        const insight: MockSourceInsight = {
          id: insightId,
          source_id: sourceId,
          insight_type: String(body.transformation_id ?? "summary"),
          content: `Mock insight for ${sourceId}`,
          created: now(),
          updated: now(),
        };
        state.sourceInsights.unshift(insight);
        const source = state.sources.find((item) => item.id === sourceId);
        if (source) {
          source.insights_count += 1;
        }
        const sourceDetail = state.sourceDetails.find((item) => item.id === sourceId);
        if (sourceDetail) {
          sourceDetail.insights_count += 1;
        }
        state.commandJobsById[commandId] = {
          job_id: commandId,
          status: "completed",
          result: { insight_id: insightId },
        };
        return json(route, {
          status: "pending",
          message: "Insight generation started",
          source_id: sourceId,
          transformation_id: String(body.transformation_id ?? ""),
          command_id: commandId,
        });
      }

      if (/^\/api\/insights\/[^/]+$/.test(pathname) && method === "GET") {
        const insightId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const insight = state.sourceInsights.find((item) => item.id === insightId);
        if (!insight) {
          return json(route, { detail: "Insight not found" }, 404);
        }
        return json(route, insight);
      }

      if (/^\/api\/insights\/[^/]+$/.test(pathname) && method === "DELETE") {
        const insightId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const insight = state.sourceInsights.find((item) => item.id === insightId);
        if (insight) {
          const source = state.sources.find((item) => item.id === insight.source_id);
          const sourceDetail = state.sourceDetails.find((item) => item.id === insight.source_id);
          if (source && source.insights_count > 0) {
            source.insights_count -= 1;
          }
          if (sourceDetail && sourceDetail.insights_count > 0) {
            sourceDetail.insights_count -= 1;
          }
        }
        state.sourceInsights = state.sourceInsights.filter((item) => item.id !== insightId);
        return json(route, {});
      }

      if (/^\/api\/commands\/jobs\/[^/]+$/.test(pathname) && method === "GET") {
        const commandId = decodeURIComponent(pathname.split("/")[4] ?? "");
        const status = state.commandJobsById[commandId];
        if (!status) {
          return json(route, { detail: "Command not found" }, 404);
        }
        return json(route, status);
      }

      if (/^\/api\/sources\/[^/]+\/chat\/sessions$/.test(pathname) && method === "GET") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const sessions = state.sourceChatSessions.filter((item) => item.source_id === sourceId);
        return json(route, sessions);
      }

      if (/^\/api\/sources\/[^/]+\/chat\/sessions$/.test(pathname) && method === "POST") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const body = readBody(request);
        const session: MockSourceChatSession = {
          id: `source-chat-${Date.now()}`,
          source_id: sourceId,
          title: String(body.title ?? "New Session"),
          created: now(),
          updated: now(),
          model_override:
            typeof body.model_override === "string" ? body.model_override : (null as string | null),
          message_count: 0,
          messages: [],
        };
        state.sourceChatSessions.unshift(session);
        return json(route, session, 201);
      }

      if (/^\/api\/sources\/[^/]+\/chat\/sessions\/[^/]+$/.test(pathname) && method === "GET") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const sessionId = decodeURIComponent(pathname.split("/")[6] ?? "");
        const session = state.sourceChatSessions.find(
          (item) => item.id === sessionId && item.source_id === sourceId,
        );
        if (!session) {
          return json(route, { detail: "Session not found" }, 404);
        }
        return json(route, {
          ...session,
          messages: session.messages ?? [],
          context_indicators: {
            sources: [sourceId],
            insights: [],
            notes: [],
          },
        });
      }

      if (/^\/api\/sources\/[^/]+\/chat\/sessions\/[^/]+$/.test(pathname) && method === "PUT") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const sessionId = decodeURIComponent(pathname.split("/")[6] ?? "");
        const body = readBody(request);
        const session = state.sourceChatSessions.find(
          (item) => item.id === sessionId && item.source_id === sourceId,
        );
        if (!session) {
          return json(route, { detail: "Session not found" }, 404);
        }
        session.title = typeof body.title === "string" ? body.title : session.title;
        session.model_override =
          typeof body.model_override === "string" ? body.model_override : session.model_override;
        session.updated = now();
        return json(route, session);
      }

      if (/^\/api\/sources\/[^/]+\/chat\/sessions\/[^/]+$/.test(pathname) && method === "DELETE") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const sessionId = decodeURIComponent(pathname.split("/")[6] ?? "");
        state.sourceChatSessions = state.sourceChatSessions.filter(
          (item) => !(item.id === sessionId && item.source_id === sourceId),
        );
        return json(route, {});
      }

      if (/^\/api\/sources\/[^/]+\/auditable-runs$/.test(pathname) && method === "GET") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const runs = state.auditableRuns.filter((item) => item.source_id === sourceId);
        return json(route, runs);
      }

      if (/^\/api\/sources\/[^/]+\/auditable-runs$/.test(pathname) && method === "POST") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const run: MockAuditableRun = {
          id: `auditable-${Date.now()}`,
          source_id: sourceId,
          status: "completed",
          model_id: "model-auditable",
          language: "en",
          created: now(),
          updated: now(),
          metrics: {
            coverage_rate: 0.95,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            dedup_group_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
        };
        state.auditableRuns.unshift(run);
        return json(route, run, 201);
      }

      if (/^\/api\/auditable-runs\/[^/]+$/.test(pathname) && method === "GET") {
        const runId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const run = state.auditableRuns.find((item) => item.id === runId);
        if (!run) {
          return json(route, { detail: "Run not found" }, 404);
        }
        return json(route, run);
      }

      if (/^\/api\/drafts\/[^/]+$/.test(pathname) && method === "GET") {
        const draftId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const draft = state.drafts.find((item) => item.id === draftId);
        if (!draft) {
          return json(route, { detail: "Draft not found" }, 404);
        }
        return json(route, draft);
      }

      if (/^\/api\/drafts\/[^/]+\/rerun$/.test(pathname) && method === "POST") {
        const draftId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const existing = state.drafts.find((item) => item.id === draftId);
        if (!existing) {
          return json(route, { detail: "Draft not found" }, 404);
        }
        const rerun: MockDraft = {
          ...existing,
          id: `draft-${Date.now()}`,
          parent_draft_id: existing.id,
          version: existing.version + 1,
          updated: now(),
          created: now(),
        };
        state.drafts.unshift(rerun);
        return json(route, rerun, 201);
      }

      if (/^\/api\/drafts\/[^/]+\/markdown$/.test(pathname) && method === "GET") {
        const draftId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const draft = state.drafts.find((item) => item.id === draftId);
        if (!draft) {
          return json(route, { detail: "Draft not found" }, 404);
        }
        return route.fulfill({
          status: 200,
          headers: {
            "content-type": "text/markdown; charset=utf-8",
            "content-disposition": `attachment; filename="${draft.id}.md"`,
          },
          body: draft.result_markdown,
        });
      }

      if (/^\/api\/auditable-runs\/[^/]+\/markdown$/.test(pathname) && method === "GET") {
        const runId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const run = state.auditableRuns.find((item) => item.id === runId);
        if (!run) {
          return json(route, { detail: "Run not found" }, 404);
        }
        return route.fulfill({
          status: 200,
          headers: {
            "content-type": "text/markdown; charset=utf-8",
            "content-disposition": `attachment; filename=\"auditable-${runId}.md\"`,
          },
          body: `# Auditable Run ${runId}\n\nStatus: ${run.status}\n`,
        });
      }

      if (/^\/api\/sources\/[^/]+$/.test(pathname) && method === "DELETE") {
        const sourceId = decodeURIComponent(pathname.split("/")[3] ?? "");
        state.sources = state.sources.filter((source) => source.id !== sourceId);
        state.sourceDetails = state.sourceDetails.filter((source) => source.id !== sourceId);
        state.sourceInsights = state.sourceInsights.filter(
          (insight) => insight.source_id !== sourceId,
        );
        state.sourceChatSessions = state.sourceChatSessions.filter(
          (session) => session.source_id !== sourceId,
        );
        state.auditableRuns = state.auditableRuns.filter((run) => run.source_id !== sourceId);
        return json(route, {});
      }

      if (pathname === "/api/search" && method === "POST") {
        return json(route, state.searchResponse);
      }

      if (pathname === "/api/search/ask" && method === "POST") {
        const events = state.askEvents.some((event) => event.type === "complete")
          ? state.askEvents
          : [...state.askEvents, { type: "complete" as const }];

        const streamBody = events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join("");
        return route.fulfill({
          status: 200,
          contentType: "text/event-stream",
          headers: {
            "cache-control": "no-cache",
            connection: "keep-alive",
          },
          body: streamBody,
        });
      }

      if (pathname === "/api/embeddings/rebuild" && method === "POST") {
        const commandId = `cmd-${Date.now()}`;
        const startedAt = now();
        const template = state.rebuildStatusTemplate;
        const status: MockRebuildStatus & { command_id: string } = {
          ...template,
          command_id: commandId,
          started_at: template.started_at ?? startedAt,
          completed_at:
            template.status === "completed" || template.status === "failed"
              ? (template.completed_at ?? now())
              : template.completed_at,
        };
        state.rebuildStatusByCommand[commandId] = status;
        const estimatedItems = status.progress?.total_items ?? status.progress?.total ?? 0;
        return json(route, {
          command_id: commandId,
          message: "Rebuild started",
          estimated_items: estimatedItems,
        });
      }

      if (/^\/api\/embeddings\/rebuild\/[^/]+\/status$/.test(pathname) && method === "GET") {
        const commandId = decodeURIComponent(pathname.split("/")[4] ?? "");
        const status = state.rebuildStatusByCommand[commandId];
        if (!status) {
          return json(route, { detail: "Command not found" }, 404);
        }
        return json(route, status);
      }

      if (
        (pathname === "/api/podcasts/episodes" || pathname === "/api/podcasts/episodes/") &&
        method === "GET"
      ) {
        return json(route, state.podcastEpisodes);
      }

      if (/^\/api\/podcasts\/episodes\/[^/]+$/.test(pathname) && method === "DELETE") {
        const episodeId = decodeURIComponent(pathname.split("/")[4] ?? "");
        state.podcastEpisodes = state.podcastEpisodes.filter((episode) => episode.id !== episodeId);
        return json(route, {});
      }

      if (/^\/api\/podcasts\/episodes\/[^/]+\/retry$/.test(pathname) && method === "POST") {
        const episodeId = decodeURIComponent(pathname.split("/")[4] ?? "");
        const episode = state.podcastEpisodes.find((item) => item.id === episodeId);
        if (!episode) {
          return json(route, { detail: "Episode not found" }, 404);
        }
        episode.job_status = "pending";
        episode.error_message = null;
        return json(route, {
          job_id: `job-${Date.now()}`,
          message: "Retry queued",
        });
      }

      if (pathname === "/api/podcasts/generate" && method === "POST") {
        const body = readBody(request);
        const profileName = String(body.episode_profile ?? "");
        const episodeProfile =
          state.episodeProfiles.find((profile) => profile.name === profileName) ??
          state.episodeProfiles[0];
        const speakerProfile =
          state.speakerProfiles.find(
            (profile) => profile.name === episodeProfile?.speaker_config,
          ) ?? state.speakerProfiles[0];

        if (episodeProfile && speakerProfile) {
          state.podcastEpisodes.unshift({
            id: `ep-${Date.now()}`,
            name: String(body.episode_name ?? "Generated Episode"),
            episode_profile: episodeProfile,
            speaker_profile: speakerProfile,
            briefing: String(body.briefing_suffix ?? ""),
            job_status: "pending",
            created: now(),
            audio_file: null,
            audio_url: null,
            transcript: null,
            outline: null,
            error_message: null,
          });
        }

        return json(route, {
          job_id: `job-${Date.now()}`,
          status: "queued",
          message: "Podcast generation queued",
          episode_profile: profileName,
          episode_name: String(body.episode_name ?? "Generated Episode"),
        });
      }

      if (pathname === "/api/episode-profiles" && method === "GET") {
        return json(route, state.episodeProfiles);
      }

      if (pathname === "/api/episode-profiles" && method === "POST") {
        const body = readBody(request);
        const created: MockEpisodeProfile = {
          id: `epf-${Date.now()}`,
          name: String(body.name ?? "New Profile"),
          description: String(body.description ?? ""),
          speaker_config: String(body.speaker_config ?? ""),
          outline_provider: String(body.outline_provider ?? "google"),
          outline_model: String(body.outline_model ?? ""),
          transcript_provider: String(body.transcript_provider ?? "google"),
          transcript_model: String(body.transcript_model ?? ""),
          default_briefing: String(body.default_briefing ?? ""),
          num_segments: Number(body.num_segments ?? 3),
        };
        state.episodeProfiles.push(created);
        return json(route, created, 201);
      }

      if (/^\/api\/episode-profiles\/[^/]+$/.test(pathname) && method === "PUT") {
        const profileId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const profile = state.episodeProfiles.find((item) => item.id === profileId);
        if (!profile) {
          return json(route, { detail: "Episode profile not found" }, 404);
        }

        const body = readBody(request);
        Object.assign(profile, body);
        return json(route, profile);
      }

      if (/^\/api\/episode-profiles\/[^/]+$/.test(pathname) && method === "DELETE") {
        const profileId = decodeURIComponent(pathname.split("/")[3] ?? "");
        state.episodeProfiles = state.episodeProfiles.filter((item) => item.id !== profileId);
        return json(route, {});
      }

      if (/^\/api\/episode-profiles\/[^/]+\/duplicate$/.test(pathname) && method === "POST") {
        const profileId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const profile = state.episodeProfiles.find((item) => item.id === profileId);
        if (!profile) {
          return json(route, { detail: "Episode profile not found" }, 404);
        }

        const duplicated: MockEpisodeProfile = {
          ...profile,
          id: `epf-${Date.now()}`,
          name: `${profile.name} Copy`,
        };
        state.episodeProfiles.push(duplicated);
        return json(route, duplicated, 201);
      }

      if (pathname === "/api/speaker-profiles" && method === "GET") {
        return json(route, state.speakerProfiles);
      }

      if (pathname === "/api/speaker-profiles" && method === "POST") {
        const body = readBody(request);
        const created: MockSpeakerProfile = {
          id: `spk-${Date.now()}`,
          name: String(body.name ?? "New Speaker"),
          description: String(body.description ?? ""),
          tts_provider: String(body.tts_provider ?? "google"),
          tts_model: String(body.tts_model ?? ""),
          speakers: Array.isArray(body.speakers)
            ? (body.speakers as MockSpeakerProfile["speakers"])
            : [],
        };
        state.speakerProfiles.push(created);
        return json(route, created, 201);
      }

      if (/^\/api\/speaker-profiles\/[^/]+$/.test(pathname) && method === "PUT") {
        const profileId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const profile = state.speakerProfiles.find((item) => item.id === profileId);
        if (!profile) {
          return json(route, { detail: "Speaker profile not found" }, 404);
        }

        const body = readBody(request);
        Object.assign(profile, body);
        return json(route, profile);
      }

      if (/^\/api\/speaker-profiles\/[^/]+$/.test(pathname) && method === "DELETE") {
        const profileId = decodeURIComponent(pathname.split("/")[3] ?? "");
        state.speakerProfiles = state.speakerProfiles.filter((item) => item.id !== profileId);
        return json(route, {});
      }

      if (/^\/api\/speaker-profiles\/[^/]+\/duplicate$/.test(pathname) && method === "POST") {
        const profileId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const profile = state.speakerProfiles.find((item) => item.id === profileId);
        if (!profile) {
          return json(route, { detail: "Speaker profile not found" }, 404);
        }

        const duplicated: MockSpeakerProfile = {
          ...profile,
          id: `spk-${Date.now()}`,
          name: `${profile.name} Copy`,
        };
        state.speakerProfiles.push(duplicated);
        return json(route, duplicated, 201);
      }

      if (pathname === "/api/models" && method === "GET") {
        return json(route, state.models);
      }

      if (pathname === "/api/models/defaults" && method === "GET") {
        return json(route, state.modelDefaults);
      }

      if (pathname === "/api/providers/policy" && method === "GET") {
        return json(route, state.providerPolicy);
      }

      if (pathname === "/api/providers/policy" && method === "PUT") {
        const body = readBody(request);
        state.providerPolicy = {
          ...state.providerPolicy,
          ...body,
        };
        return json(route, state.providerPolicy);
      }

      if (pathname === "/api/models/defaults" && method === "PUT") {
        const body = readBody(request);
        state.modelDefaults = {
          ...state.modelDefaults,
          ...body,
        };
        return json(route, state.modelDefaults);
      }

      if (pathname === "/api/models/providers" && method === "GET") {
        const available = Array.from(new Set(state.models.map((model) => model.provider)));
        return json(route, {
          available,
          unavailable: [],
          supported_types: {},
        });
      }

      if (/^\/api\/models\/[^/]+\/test$/.test(pathname) && method === "POST") {
        return json(route, { success: true, message: "Model test succeeded." });
      }

      if (/^\/api\/models\/[^/]+$/.test(pathname) && method === "DELETE") {
        const modelId = decodeURIComponent(pathname.split("/")[3] ?? "");
        state.models = state.models.filter((model) => model.id !== modelId);
        cleanupDeletedModelFromDefaults(state.modelDefaults, modelId);
        withUpdatedModelCounts(state);
        return json(route, {});
      }

      if (pathname === "/api/models/auto-assign" && method === "POST") {
        return json(route, { assigned: {}, skipped: [], missing: [] });
      }

      if (pathname === "/api/credentials/status" && method === "GET") {
        return json(route, state.credentialStatus);
      }

      if (
        (pathname === "/api/credentials" || pathname === "/api/credentials/") &&
        method === "GET"
      ) {
        return json(route, state.credentials);
      }

      if (
        (pathname === "/api/credentials" || pathname === "/api/credentials/") &&
        method === "POST"
      ) {
        const body = readBody(request);
        const provider = String(body.provider ?? "google");
        const credential: MockCredential = {
          id: `cred-${Date.now()}`,
          name: String(body.name ?? `${provider} Config`),
          provider,
          modalities: Array.isArray(body.modalities)
            ? body.modalities.map((item) => String(item))
            : ["language"],
          has_api_key: Boolean(body.api_key),
          created: now(),
          updated: now(),
          model_count: 0,
          base_url: typeof body.base_url === "string" ? body.base_url : null,
          project: typeof body.project === "string" ? body.project : null,
          location: typeof body.location === "string" ? body.location : null,
          credentials_path:
            typeof body.credentials_path === "string" ? body.credentials_path : null,
        };

        state.credentials.push(credential);
        state.credentialStatus.configured[provider] = true;
        state.credentialStatus.source[provider] = "database";
        state.credentialStatus.legacy_env_detected[provider] = false;
        refreshPolicyStatus(state.credentialStatus);
        return json(route, credential, 201);
      }

      if (/^\/api\/credentials\/[^/]+$/.test(pathname) && method === "GET") {
        const credentialId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const credential = state.credentials.find((item) => item.id === credentialId);
        if (!credential) {
          return json(route, { detail: "Credential not found" }, 404);
        }
        return json(route, credential);
      }

      if (/^\/api\/credentials\/[^/]+$/.test(pathname) && method === "PUT") {
        const credentialId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const credential = state.credentials.find((item) => item.id === credentialId);
        if (!credential) {
          return json(route, { detail: "Credential not found" }, 404);
        }

        const body = readBody(request);
        credential.name = typeof body.name === "string" ? body.name : credential.name;
        credential.base_url =
          typeof body.base_url === "string" ? body.base_url : credential.base_url;
        credential.modalities = Array.isArray(body.modalities)
          ? body.modalities.map((item) => String(item))
          : credential.modalities;
        credential.updated = now();
        if (typeof body.api_key === "string" && body.api_key.length > 0) {
          credential.has_api_key = true;
        }

        return json(route, credential);
      }

      if (/^\/api\/credentials\/[^/]+$/.test(pathname) && method === "DELETE") {
        const credentialId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const credential = state.credentials.find((item) => item.id === credentialId);
        if (!credential) {
          return json(route, { detail: "Credential not found" }, 404);
        }

        const deleteModels = url.searchParams.get("delete_models") === "true";
        state.credentials = state.credentials.filter((item) => item.id !== credentialId);

        if (deleteModels) {
          state.models = state.models.filter((model) => model.credential !== credentialId);
        }

        withUpdatedModelCounts(state);
        const stillConfigured = state.credentials.some(
          (item) => item.provider === credential.provider,
        );
        state.credentialStatus.configured[credential.provider] = stillConfigured;
        state.credentialStatus.source[credential.provider] = stillConfigured ? "database" : "none";
        refreshPolicyStatus(state.credentialStatus);

        return json(route, {
          message: "Credential deleted",
          deleted_models: deleteModels ? 1 : 0,
        });
      }

      if (/^\/api\/credentials\/[^/]+\/test$/.test(pathname) && method === "POST") {
        const credentialId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const credential = state.credentials.find((item) => item.id === credentialId);
        return json(route, {
          provider: credential?.provider ?? "unknown",
          success: true,
          message: "Connection successful",
        });
      }

      if (/^\/api\/credentials\/[^/]+\/discover$/.test(pathname) && method === "POST") {
        const credentialId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const credential = state.credentials.find((item) => item.id === credentialId);
        if (!credential) {
          return json(route, { detail: "Credential not found" }, 404);
        }

        const discovered = state.discoveredByProvider[credential.provider] ?? [
          {
            name: "gemini-2.5-flash",
            provider: credential.provider,
            description: "Mock discovered model",
          },
        ];

        return json(route, {
          credential_id: credentialId,
          provider: credential.provider,
          discovered,
        });
      }

      if (/^\/api\/credentials\/[^/]+\/register-models$/.test(pathname) && method === "POST") {
        const credentialId = decodeURIComponent(pathname.split("/")[3] ?? "");
        const credential = state.credentials.find((item) => item.id === credentialId);
        if (!credential) {
          return json(route, { detail: "Credential not found" }, 404);
        }

        const body = readBody(request);
        const submitted = Array.isArray(body.models) ? body.models : [];

        let created = 0;
        let existing = 0;

        for (const candidate of submitted) {
          const entry = candidate as Record<string, unknown>;
          const name = String(entry.name ?? "").trim();
          const provider = String(entry.provider ?? credential.provider);
          const modelType = String(entry.model_type ?? "language") as ModelType;
          if (!name) {
            continue;
          }

          const alreadyExists = state.models.some(
            (model) =>
              model.name === name &&
              model.provider === provider &&
              model.type === modelType &&
              model.credential === credentialId,
          );

          if (alreadyExists) {
            existing += 1;
            continue;
          }

          created += 1;
          state.models.push({
            id: `model-${Date.now()}-${created}`,
            name,
            provider,
            type: modelType,
            credential: credentialId,
            created: now(),
            updated: now(),
          });
        }

        withUpdatedModelCounts(state);
        return json(route, { created, existing });
      }

      const message = `Unhandled mock route: ${method} ${pathname}`;
      if (failOnUnhandledRoute) {
        throw new Error(message);
      }
      return json(route, { detail: message }, 404);
    } catch (error) {
      if (error instanceof SyntaxError) {
        return json(route, { detail: "Invalid JSON request body" }, 400);
      }
      throw error;
    }
  });

  return state;
}
