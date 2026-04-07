import type {
  CreateSourceChatSessionRequest,
  SendMessageRequest,
  SourceChatSession,
  SourceChatSessionWithMessages,
  UpdateSourceChatSessionRequest,
} from "@/lib/types/api";
import apiClient from "./client";
import { postApiStream } from "./request-helpers";

export const sourceChatApi = {
  // Session management
  createSession: async (
    sourceId: string,
    data: Omit<CreateSourceChatSessionRequest, "source_id">,
  ) => {
    // Extract clean ID without "source:" prefix for the request body
    const cleanId = sourceId.startsWith("source:") ? sourceId.slice(7) : sourceId;
    const response = await apiClient.post<SourceChatSession>(
      `/sources/${sourceId}/chat/sessions`,
      { ...data, source_id: cleanId }, // Include source_id in the request body
    );
    return response.data;
  },

  listSessions: async (sourceId: string) => {
    const response = await apiClient.get<SourceChatSession[]>(`/sources/${sourceId}/chat/sessions`);
    return response.data;
  },

  getSession: async (sourceId: string, sessionId: string) => {
    const response = await apiClient.get<SourceChatSessionWithMessages>(
      `/sources/${sourceId}/chat/sessions/${sessionId}`,
    );
    return response.data;
  },

  updateSession: async (
    sourceId: string,
    sessionId: string,
    data: UpdateSourceChatSessionRequest,
  ) => {
    const response = await apiClient.put<SourceChatSession>(
      `/sources/${sourceId}/chat/sessions/${sessionId}`,
      data,
    );
    return response.data;
  },

  deleteSession: async (sourceId: string, sessionId: string) => {
    await apiClient.delete(`/sources/${sourceId}/chat/sessions/${sessionId}`);
  },

  // Messaging with streaming
  sendMessage: async (
    sourceId: string,
    sessionId: string,
    data: SendMessageRequest,
    options?: { signal?: AbortSignal },
  ) => {
    // Use relative URL to leverage Next.js rewrites
    // This works both in dev (Next.js proxy) and production (Docker network)
    return postApiStream(
      `/api/sources/${sourceId}/chat/sessions/${sessionId}/messages`,
      data,
      options?.signal ? { signal: options.signal } : undefined,
    );
  },
};
