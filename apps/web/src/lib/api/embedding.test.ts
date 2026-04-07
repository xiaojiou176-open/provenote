import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
}));

vi.mock("./client", () => ({
  default: {
    get: hoisted.getMock,
    post: hoisted.postMock,
  },
}));

import { embeddingApi } from "./embedding";

describe("embeddingApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("embeds content with async processing flag", async () => {
    hoisted.postMock.mockResolvedValue({
      data: { success: true, message: "queued", command_id: "cmd-1" },
    });

    const result = await embeddingApi.embedContent("item-1", "source", true);

    expect(hoisted.postMock).toHaveBeenCalledWith("/embed", {
      item_id: "item-1",
      item_type: "source",
      async_processing: true,
    });
    expect(result.command_id).toBe("cmd-1");
  });

  it("rebuilds embeddings and returns command metadata", async () => {
    hoisted.postMock.mockResolvedValue({
      data: { command_id: "cmd-2", message: "started", estimated_items: 42 },
    });

    const result = await embeddingApi.rebuildEmbeddings({
      mode: "all",
      include_sources: true,
      include_notes: false,
      include_insights: true,
    });

    expect(hoisted.postMock).toHaveBeenCalledWith("/embeddings/rebuild", {
      mode: "all",
      include_sources: true,
      include_notes: false,
      include_insights: true,
    });
    expect(result.estimated_items).toBe(42);
  });

  it("gets rebuild status by command id", async () => {
    hoisted.getMock.mockResolvedValue({
      data: {
        command_id: "cmd-3",
        status: "completed",
        progress: { total_items: 10, processed_items: 10, percentage: 100 },
      },
    });

    const result = await embeddingApi.getRebuildStatus("cmd-3");

    expect(hoisted.getMock).toHaveBeenCalledWith("/embeddings/rebuild/cmd-3/status");
    expect(result.status).toBe("completed");
  });
});
