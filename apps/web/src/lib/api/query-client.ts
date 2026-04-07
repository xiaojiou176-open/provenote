import { QueryClient } from "@tanstack/react-query";

type RuntimeEnv = Record<string, unknown>;

const QUERY_CACHE_DEFAULTS = {
  staleTimeMs: 5 * 60 * 1000,
  gcTimeMs: 10 * 60 * 1000,
  maxEntries: 500,
} as const;

const QUERY_CACHE_LIMITS = {
  staleTimeMs: { min: 0, max: 24 * 60 * 60 * 1000 },
  gcTimeMs: { min: 60 * 1000, max: 24 * 60 * 60 * 1000 },
  maxEntries: { min: 100, max: 5000 },
} as const;

export const resolveRuntimeEnv = (
  importMetaEnv: RuntimeEnv | undefined,
  processEnv: RuntimeEnv | undefined,
): RuntimeEnv => {
  if (importMetaEnv && typeof importMetaEnv === "object") {
    return importMetaEnv;
  }
  if (processEnv && typeof processEnv === "object") {
    return processEnv;
  }
  return {};
};

const readRuntimeEnv = (): RuntimeEnv => {
  const importMetaEnv = (import.meta as ImportMeta & { env?: RuntimeEnv }).env;
  const processEnv = (globalThis as typeof globalThis & { process?: { env?: RuntimeEnv } }).process
    ?.env;
  return resolveRuntimeEnv(importMetaEnv, processEnv);
};

const readBoundedEnvNumber = (
  env: RuntimeEnv | undefined,
  key: string,
  fallback: number,
  limits: { min: number; max: number },
): number => {
  const rawValue = env?.[key];
  if (rawValue === undefined) {
    return fallback;
  }

  const parsedValue = Number(rawValue);
  if (!Number.isFinite(parsedValue)) {
    return fallback;
  }

  return Math.min(limits.max, Math.max(limits.min, Math.floor(parsedValue)));
};

export const resolveQueryCacheGovernance = (env: RuntimeEnv | undefined = readRuntimeEnv()) => ({
  staleTimeMs: readBoundedEnvNumber(
    env,
    "VITE_QUERY_CACHE_STALE_TIME_MS",
    QUERY_CACHE_DEFAULTS.staleTimeMs,
    QUERY_CACHE_LIMITS.staleTimeMs,
  ),
  gcTimeMs: readBoundedEnvNumber(
    env,
    "VITE_QUERY_CACHE_GC_TIME_MS",
    QUERY_CACHE_DEFAULTS.gcTimeMs,
    QUERY_CACHE_LIMITS.gcTimeMs,
  ),
  maxEntries: readBoundedEnvNumber(
    env,
    "VITE_QUERY_CACHE_MAX_ENTRIES",
    QUERY_CACHE_DEFAULTS.maxEntries,
    QUERY_CACHE_LIMITS.maxEntries,
  ),
});

const queryCacheGovernance = resolveQueryCacheGovernance();

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: queryCacheGovernance.staleTimeMs,
      gcTime: queryCacheGovernance.gcTimeMs,
      retry: 2,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

const enforceQueryCacheLimit = () => {
  const allQueries = queryClient.getQueryCache().getAll();
  const overflowCount = allQueries.length - queryCacheGovernance.maxEntries;
  if (overflowCount <= 0) {
    return;
  }

  const inactiveQueries = allQueries
    .filter((query) => !query.isActive())
    .sort((a, b) => (a.state.dataUpdatedAt ?? 0) - (b.state.dataUpdatedAt ?? 0));

  for (const query of inactiveQueries.slice(0, overflowCount)) {
    queryClient.removeQueries({ queryKey: query.queryKey, exact: true });
  }
};

queryClient.getQueryCache().subscribe((event) => {
  if (event?.type !== "added") {
    return;
  }
  enforceQueryCacheLimit();
});

export const QUERY_KEYS = {
  notebooks: ["notebooks"] as const,
  notebook: (id: string) => ["notebooks", id] as const,
  notebookDrafts: (notebookId: string) => ["notebooks", notebookId, "drafts"] as const,
  notebookResearchThreads: (notebookId: string) =>
    ["notebooks", notebookId, "research-threads"] as const,
  researchThread: (threadId: string) => ["research-threads", threadId] as const,
  draft: (draftId: string) => ["drafts", draftId] as const,
  notes: (notebookId?: string) => ["notes", notebookId] as const,
  note: (id: string) => ["notes", id] as const,
  sources: (notebookId?: string) => ["sources", notebookId] as const,
  sourcesInfinite: (notebookId: string) => ["sources", "infinite", notebookId] as const,
  source: (id: string) => ["sources", id] as const,
  settings: ["settings"] as const,
  sourceChatSessions: (sourceId: string) => ["source-chat", sourceId, "sessions"] as const,
  sourceChatSession: (sourceId: string, sessionId: string) =>
    ["source-chat", sourceId, "sessions", sessionId] as const,
  notebookChatSessions: (notebookId: string) => ["notebook-chat", notebookId, "sessions"] as const,
  notebookChatSession: (sessionId: string) => ["notebook-chat", "sessions", sessionId] as const,
  podcastEpisodes: ["podcasts", "episodes"] as const,
  podcastEpisode: (episodeId: string) => ["podcasts", "episodes", episodeId] as const,
  episodeProfiles: ["podcasts", "episode-profiles"] as const,
  speakerProfiles: ["podcasts", "speaker-profiles"] as const,
};
