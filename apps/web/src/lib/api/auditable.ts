import type { AxiosResponse } from "axios";
import type {
  AuditableRepairRequest,
  AuditableRunResponse,
  CreateAuditableRunRequest,
} from "@/lib/types/api";
import apiClient from "./client";

const sourceAuditableRunsBasePath = (sourceId: string) => `/sources/${sourceId}/auditable-runs`;
const auditableRunPath = (runId: string) => `/auditable-runs/${runId}`;

export const auditableApi = {
  listRuns: async (sourceId: string) => {
    const response = await apiClient.get<AuditableRunResponse[]>(
      sourceAuditableRunsBasePath(sourceId),
    );
    return response.data;
  },

  startRun: async (sourceId: string, data: CreateAuditableRunRequest = {}) => {
    const response = await apiClient.post<AuditableRunResponse>(
      sourceAuditableRunsBasePath(sourceId),
      data,
    );
    return response.data;
  },

  getRun: async (runId: string) => {
    const response = await apiClient.get<AuditableRunResponse>(auditableRunPath(runId));
    return response.data;
  },

  repairClaim: async (runId: string, payload: AuditableRepairRequest) => {
    const response = await apiClient.post<AuditableRunResponse>(
      `${auditableRunPath(runId)}/repair-claim`,
      payload,
    );
    return response.data;
  },

  repairSection: async (runId: string, payload: AuditableRepairRequest) => {
    const response = await apiClient.post<AuditableRunResponse>(
      `${auditableRunPath(runId)}/repair-section`,
      payload,
    );
    return response.data;
  },

  downloadMarkdown: async (runId: string): Promise<AxiosResponse<Blob>> => {
    return apiClient.get(`${auditableRunPath(runId)}/markdown`, {
      responseType: "blob",
    });
  },
};
