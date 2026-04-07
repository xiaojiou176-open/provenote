import type {
  AppendResearchThreadEntryRequest,
  CreateResearchThreadRequest,
  DraftResponse,
  ResearchThreadResponse,
} from "@/lib/types/api";
import apiClient from "./client";

const notebookResearchThreadsBasePath = (notebookId: string) =>
  `/notebooks/${notebookId}/research-threads`;
const researchThreadPath = (threadId: string) => `/research-threads/${threadId}`;

export const researchThreadsApi = {
  list: async (notebookId: string) => {
    const response = await apiClient.get<ResearchThreadResponse[]>(
      notebookResearchThreadsBasePath(notebookId),
    );
    return response.data;
  },

  create: async (notebookId: string, payload: CreateResearchThreadRequest) => {
    const response = await apiClient.post<ResearchThreadResponse>(
      notebookResearchThreadsBasePath(notebookId),
      payload,
    );
    return response.data;
  },

  get: async (threadId: string) => {
    const response = await apiClient.get<ResearchThreadResponse>(researchThreadPath(threadId));
    return response.data;
  },

  append: async (threadId: string, payload: AppendResearchThreadEntryRequest) => {
    const response = await apiClient.post<ResearchThreadResponse>(
      `${researchThreadPath(threadId)}/entries`,
      payload,
    );
    return response.data;
  },

  createDraft: async (threadId: string) => {
    const response = await apiClient.post<DraftResponse>(`${researchThreadPath(threadId)}/drafts`);
    return response.data;
  },
};
