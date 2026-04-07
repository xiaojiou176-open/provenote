import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  QUERY_KEYS,
  queryClient,
  resolveQueryCacheGovernance,
  resolveRuntimeEnv,
} from "./query-client";

describe("queryClient setup", () => {
  beforeEach(() => {
    queryClient.clear();
  });

  it("falls back to defaults when runtime env is unavailable", () => {
    const governance = resolveQueryCacheGovernance(undefined);

    expect(governance.staleTimeMs).toBe(5 * 60 * 1000);
    expect(governance.gcTimeMs).toBe(10 * 60 * 1000);
    expect(governance.maxEntries).toBe(500);
  });

  it("reads and bounds cache governance values from runtime env", () => {
    const governance = resolveQueryCacheGovernance({
      VITE_QUERY_CACHE_STALE_TIME_MS: "12345",
      VITE_QUERY_CACHE_GC_TIME_MS: "1000",
      VITE_QUERY_CACHE_MAX_ENTRIES: "99999",
    });

    expect(governance.staleTimeMs).toBe(12345);
    expect(governance.gcTimeMs).toBe(60 * 1000);
    expect(governance.maxEntries).toBe(5000);
  });

  it("falls back on invalid env values and floors decimals within bounds", () => {
    const governance = resolveQueryCacheGovernance({
      VITE_QUERY_CACHE_STALE_TIME_MS: "not-a-number",
      VITE_QUERY_CACHE_GC_TIME_MS: "62000.9",
      VITE_QUERY_CACHE_MAX_ENTRIES: "99",
    });

    expect(governance.staleTimeMs).toBe(5 * 60 * 1000);
    expect(governance.gcTimeMs).toBe(62000);
    expect(governance.maxEntries).toBe(100);
  });

  it("clamps explicit runtime env to min/max boundaries", () => {
    const governance = resolveQueryCacheGovernance({
      VITE_QUERY_CACHE_STALE_TIME_MS: "-100",
      VITE_QUERY_CACHE_GC_TIME_MS: "Infinity",
      VITE_QUERY_CACHE_MAX_ENTRIES: "6000",
    });

    expect(governance.staleTimeMs).toBe(0);
    expect(governance.gcTimeMs).toBe(10 * 60 * 1000);
    expect(governance.maxEntries).toBe(5000);
  });

  it("uses expected default query and mutation options", () => {
    const defaults = queryClient.getDefaultOptions();

    expect(defaults.queries?.staleTime).toBe(5 * 60 * 1000);
    expect(defaults.queries?.gcTime).toBe(10 * 60 * 1000);
    expect(defaults.queries?.retry).toBe(2);
    expect(defaults.queries?.refetchOnWindowFocus).toBe(false);
    expect(defaults.mutations?.retry).toBe(1);
  });

  it("builds stable query keys for each domain", () => {
    expect(QUERY_KEYS.notebooks).toEqual(["notebooks"]);
    expect(QUERY_KEYS.notebook("nb-1")).toEqual(["notebooks", "nb-1"]);
    expect(QUERY_KEYS.notebookDrafts("nb-1")).toEqual(["notebooks", "nb-1", "drafts"]);
    expect(QUERY_KEYS.notebookResearchThreads("nb-1")).toEqual([
      "notebooks",
      "nb-1",
      "research-threads",
    ]);
    expect(QUERY_KEYS.researchThread("thread-1")).toEqual(["research-threads", "thread-1"]);
    expect(QUERY_KEYS.notes("nb-1")).toEqual(["notes", "nb-1"]);
    expect(QUERY_KEYS.note("n-1")).toEqual(["notes", "n-1"]);
    expect(QUERY_KEYS.sources("nb-1")).toEqual(["sources", "nb-1"]);
    expect(QUERY_KEYS.sourcesInfinite("nb-1")).toEqual(["sources", "infinite", "nb-1"]);
    expect(QUERY_KEYS.source("src-1")).toEqual(["sources", "src-1"]);
    expect(QUERY_KEYS.settings).toEqual(["settings"]);
    expect(QUERY_KEYS.sourceChatSessions("src-1")).toEqual(["source-chat", "src-1", "sessions"]);
    expect(QUERY_KEYS.sourceChatSession("src-1", "s-1")).toEqual([
      "source-chat",
      "src-1",
      "sessions",
      "s-1",
    ]);
    expect(QUERY_KEYS.notebookChatSessions("nb-1")).toEqual(["notebook-chat", "nb-1", "sessions"]);
    expect(QUERY_KEYS.notebookChatSession("s-1")).toEqual(["notebook-chat", "sessions", "s-1"]);
    expect(QUERY_KEYS.podcastEpisodes).toEqual(["podcasts", "episodes"]);
    expect(QUERY_KEYS.podcastEpisode("ep-1")).toEqual(["podcasts", "episodes", "ep-1"]);
    expect(QUERY_KEYS.episodeProfiles).toEqual(["podcasts", "episode-profiles"]);
    expect(QUERY_KEYS.speakerProfiles).toEqual(["podcasts", "speaker-profiles"]);
  });

  it("resolves runtime env from importMeta first, then process, then empty object", () => {
    const fromImportMeta = resolveRuntimeEnv(
      { VITE_QUERY_CACHE_STALE_TIME_MS: "7777" },
      { VITE_QUERY_CACHE_STALE_TIME_MS: "8888" },
    );
    const fromProcess = resolveRuntimeEnv(undefined, {
      VITE_QUERY_CACHE_STALE_TIME_MS: "9999",
    });
    const fromNone = resolveRuntimeEnv(undefined, undefined);

    expect(fromImportMeta).toEqual({ VITE_QUERY_CACHE_STALE_TIME_MS: "7777" });
    expect(fromProcess).toEqual({ VITE_QUERY_CACHE_STALE_TIME_MS: "9999" });
    expect(fromNone).toEqual({});
  });

  it("enforces max query cache entries when new queries are added", () => {
    const removeQueriesSpy = vi.spyOn(queryClient, "removeQueries");

    for (let index = 0; index < 510; index += 1) {
      queryClient.setQueryData(["cache-governance", index], index);
    }

    const allQueries = queryClient.getQueryCache().getAll();

    expect(allQueries.length).toBe(500);
    expect(removeQueriesSpy).toHaveBeenCalled();
    removeQueriesSpy.mockRestore();
  });

  it("does not evict when cache stays within limit", () => {
    const removeQueriesSpy = vi.spyOn(queryClient, "removeQueries");

    for (let index = 0; index < 20; index += 1) {
      queryClient.setQueryData(["small-cache", index], index);
    }

    expect(queryClient.getQueryCache().getAll().length).toBe(20);
    expect(removeQueriesSpy).not.toHaveBeenCalled();
    removeQueriesSpy.mockRestore();
  });

  it("sorts inactive queries safely when some updated timestamps are missing", () => {
    const removeQueriesSpy = vi.spyOn(queryClient, "removeQueries");

    for (let index = 0; index < 510; index += 1) {
      queryClient.setQueryData(["cache-sort", index], index);
    }

    const allQueries = queryClient.getQueryCache().getAll();
    const oldestInactive = allQueries.find((query) => !query.isActive());
    if (oldestInactive) {
      oldestInactive.state.dataUpdatedAt = undefined as unknown as number;
    }

    queryClient.setQueryData(["cache-sort", 9999], 9999);

    expect(queryClient.getQueryCache().getAll().length).toBe(500);
    expect(removeQueriesSpy).toHaveBeenCalled();
    removeQueriesSpy.mockRestore();
  });

  it("handles undefined timestamps for both sort operands when enforcing cache size", () => {
    const removeQueriesSpy = vi.spyOn(queryClient, "removeQueries");

    for (let index = 0; index < 510; index += 1) {
      queryClient.setQueryData(["cache-sort-nullish", index], index);
    }

    for (const query of queryClient.getQueryCache().getAll()) {
      if (!query.isActive()) {
        query.state.dataUpdatedAt = undefined as unknown as number;
      }
    }

    queryClient.setQueryData(["cache-sort-nullish", 9999], 9999);

    expect(queryClient.getQueryCache().getAll().length).toBe(500);
    expect(removeQueriesSpy).toHaveBeenCalled();
    removeQueriesSpy.mockRestore();
  });
});
