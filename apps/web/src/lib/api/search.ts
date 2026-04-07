import type { AskRequest, SearchRequest, SearchResponse } from "@/lib/types/search";
import { postApiJson, postApiStream } from "./request-helpers";

export const searchApi = {
  // Standard search (non-streaming)
  search: async (params: SearchRequest) => {
    return postApiJson<SearchResponse, SearchRequest>("/search", params);
  },

  // Ask with streaming (uses relative URL for Docker compatibility)
  askKnowledgeBase: async (params: AskRequest, options?: { signal?: AbortSignal }) => {
    // Use relative URL to leverage Next.js rewrites
    // This works both in dev (Next.js proxy) and production (Docker network)
    if (options?.signal) {
      return postApiStream("/api/search/ask", params, { signal: options.signal });
    }
    return postApiStream("/api/search/ask", params);
  },
};
