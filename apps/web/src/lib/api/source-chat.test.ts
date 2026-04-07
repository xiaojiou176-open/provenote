import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  deleteMock: vi.fn(),
  getMock: vi.fn(),
  postMock: vi.fn(),
  putMock: vi.fn(),
  postApiStreamMock: vi.fn(),
}));

vi.mock("./client", () => ({
  default: {
    get: hoisted.getMock,
    post: hoisted.postMock,
    put: hoisted.putMock,
    delete: hoisted.deleteMock,
  },
}));

vi.mock("./request-helpers", () => ({
  postApiStream: hoisted.postApiStreamMock,
}));

import { sourceChatApi } from "./source-chat";

describe("sourceChatApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("creates a session and strips source prefix only from request body", async () => {
    hoisted.postMock.mockResolvedValue({
      data: { id: "session-1", source_id: "abc" },
    });

    const result = await sourceChatApi.createSession("source:abc", {
      title: "My session",
      model_id: "model-1",
    });

    expect(hoisted.postMock).toHaveBeenCalledWith("/sources/source:abc/chat/sessions", {
      title: "My session",
      model_id: "model-1",
      source_id: "abc",
    });
    expect(result.id).toBe("session-1");
  });

  it("lists, gets, updates, and deletes sessions", async () => {
    hoisted.getMock
      .mockResolvedValueOnce({ data: [{ id: "session-2" }] })
      .mockResolvedValueOnce({ data: { id: "session-2", messages: [] } });
    hoisted.putMock.mockResolvedValue({ data: { id: "session-2", title: "Renamed" } });

    const sessions = await sourceChatApi.listSessions("source-1");
    const session = await sourceChatApi.getSession("source-1", "session-2");
    const updated = await sourceChatApi.updateSession("source-1", "session-2", {
      title: "Renamed",
    });
    await sourceChatApi.deleteSession("source-1", "session-2");

    expect(hoisted.getMock).toHaveBeenNthCalledWith(1, "/sources/source-1/chat/sessions");
    expect(hoisted.getMock).toHaveBeenNthCalledWith(2, "/sources/source-1/chat/sessions/session-2");
    expect(hoisted.putMock).toHaveBeenCalledWith("/sources/source-1/chat/sessions/session-2", {
      title: "Renamed",
    });
    expect(hoisted.deleteMock).toHaveBeenCalledWith("/sources/source-1/chat/sessions/session-2");
    expect(sessions).toEqual([{ id: "session-2" }]);
    expect(session).toEqual({ id: "session-2", messages: [] });
    expect(updated.title).toBe("Renamed");
  });

  it("sends source chat messages through the streaming helper", async () => {
    const stream = new ReadableStream<Uint8Array>();
    const controller = new AbortController();
    hoisted.postApiStreamMock.mockResolvedValue(stream);

    const result = await sourceChatApi.sendMessage(
      "source-9",
      "session-9",
      { content: "hello", role: "user" },
      { signal: controller.signal },
    );

    expect(hoisted.postApiStreamMock).toHaveBeenCalledWith(
      "/api/sources/source-9/chat/sessions/session-9/messages",
      { content: "hello", role: "user" },
      { signal: controller.signal },
    );
    expect(result).toBe(stream);
  });
});
