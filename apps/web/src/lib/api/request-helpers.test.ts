import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  postMock: vi.fn(),
  getStoredAuthTokenMock: vi.fn(),
}));

vi.mock("./client", () => ({
  default: {
    post: hoisted.postMock,
  },
}));

vi.mock("@/lib/auth-storage", () => ({
  getStoredAuthToken: hoisted.getStoredAuthTokenMock,
}));

import { postApiJson, postApiStream } from "./request-helpers";

describe("request helpers", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.getStoredAuthTokenMock.mockReturnValue(null);
    global.fetch = vi.fn();
  });

  it("returns JSON response payload from apiClient", async () => {
    hoisted.postMock.mockResolvedValue({
      data: { ok: true, id: "json-1" },
    });

    const result = await postApiJson("/api/demo", { hello: "world" });

    expect(hoisted.postMock).toHaveBeenCalledWith("/api/demo", { hello: "world" });
    expect(result).toEqual({ ok: true, id: "json-1" });
  });

  it("streams successful fetch responses and forwards auth/custom headers", async () => {
    const stream = new ReadableStream<Uint8Array>();
    const controller = new AbortController();
    hoisted.getStoredAuthTokenMock.mockReturnValue("token-123");
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      body: stream,
    } as Response);

    const result = await postApiStream(
      "/api/stream",
      { query: "abc" },
      {
        headers: { "X-Trace": "trace-1" },
        signal: controller.signal,
      },
    );

    expect(fetch).toHaveBeenCalledWith("/api/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Trace": "trace-1",
        Authorization: "Bearer token-123",
      },
      body: JSON.stringify({ query: "abc" }),
      signal: controller.signal,
    });
    expect(result).toBe(stream);
  });

  it("prefers API detail/message when stream request fails", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 422,
      statusText: "Unprocessable Entity",
      json: async () => ({ detail: "bad query" }),
    } as Response);

    await expect(postApiStream("/api/stream", { query: "abc" })).rejects.toThrow("bad query");
  });

  it("falls back to status text when error body is not json", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Server exploded",
      json: async () => {
        throw new Error("not json");
      },
    } as Response);

    await expect(postApiStream("/api/stream", { query: "abc" })).rejects.toThrow("Server exploded");
  });

  it("throws when a successful response has no body", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      body: null,
    } as Response);

    await expect(postApiStream("/api/stream", { query: "abc" })).rejects.toThrow(
      "No response body received",
    );
  });
});
