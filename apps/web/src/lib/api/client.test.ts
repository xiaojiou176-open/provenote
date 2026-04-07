import { beforeEach, describe, expect, it, vi } from "vitest";

import { getApiUrl } from "@/lib/config";
import apiClient from "./client";

vi.mock("@/lib/config", () => ({
  getApiUrl: vi.fn(),
}));

type RequestConfigLike = {
  baseURL?: string;
  headers: Record<string, string>;
  method?: string;
  data?: unknown;
};

type RequestHandler = (config: RequestConfigLike) => Promise<RequestConfigLike>;
type ResponseSuccessHandler = <T>(response: T) => T;
type ResponseErrorHandler = (error: unknown) => Promise<never>;

function requestHandler(): RequestHandler {
  const handlers = (
    apiClient.interceptors.request as unknown as {
      handlers: Array<{ fulfilled: RequestHandler }>;
    }
  ).handlers;
  return handlers[0].fulfilled;
}

function responseErrorHandler(): ResponseErrorHandler {
  const handlers = (
    apiClient.interceptors.response as unknown as {
      handlers: Array<{ rejected: ResponseErrorHandler }>;
    }
  ).handlers;
  return handlers[0].rejected;
}

function responseSuccessHandler(): ResponseSuccessHandler {
  const handlers = (
    apiClient.interceptors.response as unknown as {
      handlers: Array<{ fulfilled: ResponseSuccessHandler }>;
    }
  ).handlers;
  return handlers[0].fulfilled;
}

describe("api client interceptors", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    vi.mocked(getApiUrl).mockResolvedValue("http://services.api.example");
  });

  it("adds baseURL, auth header and json content type for write requests", async () => {
    sessionStorage.setItem("auth-storage", JSON.stringify({ state: { token: "token-123" } }));
    const handleRequest = requestHandler();

    const config = await handleRequest({
      headers: {},
      method: "post",
      data: { hello: "world" },
    });

    expect(getApiUrl).toHaveBeenCalledTimes(1);
    expect(config.baseURL).toBe("http://services.api.example/api");
    expect(config.headers.Authorization).toBe("Bearer token-123");
    expect(config.headers["Content-Type"]).toBe("application/json");
  });

  it("keeps provided baseURL and removes content type for FormData", async () => {
    const handleRequest = requestHandler();
    const payload = new FormData();
    payload.append("name", "demo");

    const config = await handleRequest({
      baseURL: "https://fixed.example/api",
      headers: { "Content-Type": "application/json" },
      method: "patch",
      data: payload,
    });

    expect(getApiUrl).not.toHaveBeenCalled();
    expect(config.baseURL).toBe("https://fixed.example/api");
    expect(config.headers["Content-Type"]).toBeUndefined();
  });

  it("logs parse errors when auth storage is invalid json", async () => {
    const handleRequest = requestHandler();
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    sessionStorage.setItem("auth-storage", "{bad-json");

    await handleRequest({
      headers: {},
      method: "get",
    });

    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });

  it("migrates legacy auth token from localStorage to sessionStorage", async () => {
    const handleRequest = requestHandler();
    localStorage.setItem("auth-storage", JSON.stringify({ state: { token: "legacy-token" } }));

    const config = await handleRequest({
      headers: {},
      method: "get",
    });

    expect(config.headers.Authorization).toBe("Bearer legacy-token");
    expect(localStorage.getItem("auth-storage")).toBeNull();
    expect(sessionStorage.getItem("auth-storage")).toContain("legacy-token");
  });

  it("does not attach auth header when running without window", async () => {
    const handleRequest = requestHandler();
    vi.stubGlobal("window", undefined);

    const config = await handleRequest({
      headers: {},
      method: "get",
    });

    expect(config.headers.Authorization).toBeUndefined();
    vi.unstubAllGlobals();
  });

  it("clears auth storage and redirects on 401", async () => {
    const removeSpy = vi.spyOn(Storage.prototype, "removeItem");
    const handleError = responseErrorHandler();
    const fakeWindow = {
      localStorage,
      sessionStorage,
      location: { href: "/dashboard" },
    };
    vi.stubGlobal("window", fakeWindow);

    const error = { response: { status: 401 } };
    await expect(handleError(error)).rejects.toBe(error);
    expect(removeSpy).toHaveBeenCalledWith("auth-storage");
    expect(fakeWindow.location.href).toBe("/login");
  });

  it("passes through successful responses", () => {
    const handleResponse = responseSuccessHandler();
    const response = { data: { ok: true } };

    expect(handleResponse(response)).toBe(response);
  });

  it("does not clear auth storage for non-401 errors", async () => {
    const removeSpy = vi.spyOn(Storage.prototype, "removeItem");
    const handleError = responseErrorHandler();
    const error = { response: { status: 500 } };

    await expect(handleError(error)).rejects.toBe(error);
    expect(removeSpy).not.toHaveBeenCalled();
  });

  it("does not redirect on 401 when window is unavailable", async () => {
    const handleError = responseErrorHandler();
    const clearSpy = vi.spyOn(Storage.prototype, "removeItem");
    vi.stubGlobal("window", undefined);
    const error = { response: { status: 401 } };

    await expect(handleError(error)).rejects.toBe(error);
    expect(clearSpy).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
});
