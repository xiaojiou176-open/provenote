import { getStoredAuthToken } from "@/lib/auth-storage";
import apiClient from "./client";

export async function postApiJson<TResponse, TPayload>(
  path: string,
  payload: TPayload,
): Promise<TResponse> {
  const response = await apiClient.post<TResponse>(path, payload);
  return response.data;
}

export async function postApiStream<TPayload>(
  path: string,
  payload: TPayload,
  options: {
    headers?: Record<string, string>;
    signal?: AbortSignal;
  } = {},
): Promise<ReadableStream<Uint8Array>> {
  const { headers = {}, signal } = options;
  const token = getStoredAuthToken();
  const response = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...headers,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    let errorMessage = `HTTP error! status: ${response.status}`;
    try {
      const errorData = (await response.json()) as {
        detail?: string;
        message?: string;
      };
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  if (!response.body) {
    throw new Error("No response body received");
  }

  return response.body;
}
