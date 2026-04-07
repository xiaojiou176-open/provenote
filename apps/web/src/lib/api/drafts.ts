import type { AxiosResponse } from "axios";
import type { CreateDraftRequest, DraftResponse, RerunDraftRequest } from "@/lib/types/api";
import apiClient from "./client";

const notebookDraftsBasePath = (notebookId: string) => `/notebooks/${notebookId}/drafts`;
const draftPath = (draftId: string) => `/drafts/${draftId}`;

export const draftsApi = {
  list: async (notebookId: string) => {
    const response = await apiClient.get<DraftResponse[]>(notebookDraftsBasePath(notebookId));
    return response.data;
  },

  create: async (notebookId: string, payload: CreateDraftRequest) => {
    const response = await apiClient.post<DraftResponse>(
      notebookDraftsBasePath(notebookId),
      payload,
    );
    return response.data;
  },

  get: async (draftId: string) => {
    const response = await apiClient.get<DraftResponse>(draftPath(draftId));
    return response.data;
  },

  rerun: async (draftId: string, payload: RerunDraftRequest = {}) => {
    const response = await apiClient.post<DraftResponse>(`${draftPath(draftId)}/rerun`, payload);
    return response.data;
  },

  verify: async (draftId: string) => {
    const response = await apiClient.post<DraftResponse>(`${draftPath(draftId)}/verify`);
    return response.data;
  },

  downloadMarkdown: async (draftId: string): Promise<AxiosResponse<Blob>> =>
    apiClient.get(`${draftPath(draftId)}/markdown`, {
      responseType: "blob",
    }),

  downloadBundle: async (draftId: string): Promise<AxiosResponse<Blob>> =>
    apiClient.get(`${draftPath(draftId)}/bundle`, {
      responseType: "blob",
    }),
};
