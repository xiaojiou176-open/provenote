import type { SettingsResponse } from "@/lib/types/api";
import apiClient from "./client";

export const settingsApi = {
  get: async () => {
    const response = await apiClient.get<SettingsResponse>("/settings");
    return response.data;
  },

  update: async (data: Partial<SettingsResponse>) => {
    const response = await apiClient.put<SettingsResponse>("/settings", data);
    return response.data;
  },
};
