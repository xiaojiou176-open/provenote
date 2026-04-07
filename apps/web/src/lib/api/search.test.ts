import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  postApiJsonMock: vi.fn(),
  postApiStreamMock: vi.fn(),
}));

vi.mock("./request-helpers", () => ({
  postApiJson: hoisted.postApiJsonMock,
  postApiStream: hoisted.postApiStreamMock,
}));

import { searchApi } from "./search";

describe("searchApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("search delegates to /search json endpoint", async () => {
    const payload = {
      query: "alpha",
      type: "text" as const,
      limit: 20,
      search_sources: true,
      search_notes: true,
      minimum_score: 0.2,
    };
    hoisted.postApiJsonMock.mockResolvedValue({
      results: [],
      total_count: 0,
      search_type: "text",
    });

    const result = await searchApi.search(payload);

    expect(hoisted.postApiJsonMock).toHaveBeenCalledWith("/search", payload);
    expect(result.total_count).toBe(0);
  });

  it("askKnowledgeBase delegates to streaming ask endpoint", async () => {
    const stream = new ReadableStream<Uint8Array>();
    const payload = {
      question: "what happened?",
      strategy_model: "s",
      answer_model: "a",
      final_answer_model: "f",
    };
    hoisted.postApiStreamMock.mockResolvedValue(stream);

    const result = await searchApi.askKnowledgeBase(payload);

    expect(hoisted.postApiStreamMock).toHaveBeenCalledWith("/api/search/ask", payload);
    expect(result).toBe(stream);
  });

  it("askKnowledgeBase forwards abort signal when provided", async () => {
    const stream = new ReadableStream<Uint8Array>();
    const payload = {
      question: "abort-aware request",
      strategy_model: "s",
      answer_model: "a",
      final_answer_model: "f",
    };
    const controller = new AbortController();
    hoisted.postApiStreamMock.mockResolvedValue(stream);

    const result = await searchApi.askKnowledgeBase(payload, { signal: controller.signal });

    expect(hoisted.postApiStreamMock).toHaveBeenCalledWith("/api/search/ask", payload, {
      signal: controller.signal,
    });
    expect(result).toBe(stream);
  });

  it("search propagates request errors without swallowing details", async () => {
    const payload = {
      query: "alpha",
      type: "vector" as const,
      limit: 20,
      search_sources: true,
      search_notes: true,
      minimum_score: 0.2,
    };
    const error = new Error("embedding model missing");
    hoisted.postApiJsonMock.mockRejectedValue(error);

    await expect(searchApi.search(payload)).rejects.toThrow("embedding model missing");
    expect(hoisted.postApiJsonMock).toHaveBeenCalledWith("/search", payload);
  });

  it("askKnowledgeBase propagates stream helper errors", async () => {
    const payload = {
      question: "what happened?",
      strategy_model: "s",
      answer_model: "a",
      final_answer_model: "f",
    };
    const error = new Error("stream bootstrap failed");
    hoisted.postApiStreamMock.mockRejectedValue(error);

    await expect(searchApi.askKnowledgeBase(payload)).rejects.toThrow("stream bootstrap failed");
    expect(hoisted.postApiStreamMock).toHaveBeenCalledWith("/api/search/ask", payload);
  });
});
