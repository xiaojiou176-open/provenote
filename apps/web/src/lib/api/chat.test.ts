import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  apiClientMock: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("./client", () => ({
  default: hoisted.apiClientMock,
}));

import { chatApi } from "./chat";

describe("chatApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lists sessions by notebook id", async () => {
    hoisted.apiClientMock.get.mockResolvedValue({ data: [{ id: "s-1" }] });

    const result = await chatApi.listSessions("nb-1");

    expect(hoisted.apiClientMock.get).toHaveBeenCalledWith("/chat/sessions", {
      params: { notebook_id: "nb-1" },
    });
    expect(result).toEqual([{ id: "s-1" }]);
  });

  it("creates and gets sessions", async () => {
    hoisted.apiClientMock.post.mockResolvedValueOnce({ data: { id: "s-2" } });
    hoisted.apiClientMock.get.mockResolvedValueOnce({ data: { id: "s-2", messages: [] } });

    const created = await chatApi.createSession({ notebook_id: "nb-1", title: "new chat" });
    const loaded = await chatApi.getSession("s-2");

    expect(hoisted.apiClientMock.post).toHaveBeenCalledWith("/chat/sessions", {
      notebook_id: "nb-1",
      title: "new chat",
    });
    expect(hoisted.apiClientMock.get).toHaveBeenCalledWith("/chat/sessions/s-2");
    expect(created).toEqual({ id: "s-2" });
    expect(loaded).toEqual({ id: "s-2", messages: [] });
  });

  it("updates and deletes sessions", async () => {
    hoisted.apiClientMock.put.mockResolvedValue({ data: { id: "s-3", title: "updated" } });
    hoisted.apiClientMock.delete.mockResolvedValue({ data: undefined });

    const updated = await chatApi.updateSession("s-3", { title: "updated" });
    await chatApi.deleteSession("s-3");

    expect(hoisted.apiClientMock.put).toHaveBeenCalledWith("/chat/sessions/s-3", {
      title: "updated",
    });
    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/chat/sessions/s-3");
    expect(updated).toEqual({ id: "s-3", title: "updated" });
  });

  it("sends message and builds context", async () => {
    hoisted.apiClientMock.post
      .mockResolvedValueOnce({
        data: { session_id: "s-4", messages: [{ role: "assistant", content: "ok" }] },
      })
      .mockResolvedValueOnce({
        data: { chunks: [{ source_id: "src-1" }], summary: "context" },
      });

    const messageResult = await chatApi.sendMessage({
      notebook_id: "nb-1",
      message: "hello",
      mode: "answer",
    });
    const contextResult = await chatApi.buildContext({
      notebook_id: "nb-1",
      query: "hello",
      source_ids: ["src-1"],
    });

    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(1, "/chat/execute", {
      notebook_id: "nb-1",
      message: "hello",
      mode: "answer",
    });
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(2, "/chat/context", {
      notebook_id: "nb-1",
      query: "hello",
      source_ids: ["src-1"],
    });
    expect(messageResult.session_id).toBe("s-4");
    expect(contextResult.summary).toBe("context");
  });
});
