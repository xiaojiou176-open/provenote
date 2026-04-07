import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { sourceChatApi } from "@/lib/api/source-chat";
import { useTranslation } from "@/lib/hooks/use-translation";
import { useSourceChat } from "./useSourceChat";

const hoisted = vi.hoisted(() => ({
  toastErrorMock: vi.fn(),
  toastSuccessMock: vi.fn(),
}));

let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

vi.mock("sonner", () => ({
  toast: {
    success: hoisted.toastSuccessMock,
    error: hoisted.toastErrorMock,
  },
}));

vi.mock("@/lib/api/source-chat", () => ({
  sourceChatApi: {
    listSessions: vi.fn(),
    getSession: vi.fn(),
    createSession: vi.fn(),
    updateSession: vi.fn(),
    deleteSession: vi.fn(),
    sendMessage: vi.fn(),
  },
}));

vi.mock("@/lib/hooks/use-translation");

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) =>
    createElement(QueryClientProvider, { client }, children);
}

function createStream(lines: string[]) {
  return new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(`${lines.join("\n")}\n`));
      controller.close();
    },
  });
}

describe("useSourceChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);

    vi.mocked(useTranslation).mockReturnValue({
      t: Object.assign((key: string) => key, {
        chat: {
          sessionCreated: "Session created",
          sessionUpdated: "Session updated",
          sessionDeleted: "Session deleted",
        },
      }),
    } as unknown as ReturnType<typeof useTranslation>);

    vi.mocked(sourceChatApi.listSessions).mockResolvedValue([
      {
        id: "sess-1",
        source_id: "source-1",
        title: "First",
        created: "2026-01-01T00:00:00Z",
        updated: "2026-01-02T00:00:00Z",
      },
      {
        id: "sess-2",
        source_id: "source-1",
        title: "Second",
        created: "2026-01-03T00:00:00Z",
        updated: "2026-01-04T00:00:00Z",
      },
    ]);

    vi.mocked(sourceChatApi.getSession).mockImplementation(async (_sourceId, sessionId) => ({
      id: sessionId,
      source_id: "source-1",
      title: "Session",
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-02T00:00:00Z",
      messages:
        sessionId === "sess-1"
          ? [{ id: "m-1", type: "human", content: "hello" }]
          : [{ id: "m-2", type: "human", content: "other" }],
    }));
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("auto-selects most recent session when list loads", async () => {
    const { result } = renderHook(() => useSourceChat("source-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });
  });

  it("switches session and clears local message state immediately", async () => {
    const { result } = renderHook(() => useSourceChat("source-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.messages.length).toBe(1);
    });

    act(() => {
      result.current.switchSession("sess-2");
    });

    expect(result.current.currentSessionId).toBe("sess-2");
    expect(result.current.messages).toEqual([]);
    expect(result.current.contextIndicators).toBeNull();
  });

  it("auto-creates a session, streams ai output, and stores context indicators", async () => {
    vi.mocked(sourceChatApi.listSessions).mockReset();
    vi.mocked(sourceChatApi.listSessions).mockResolvedValue([]);
    vi.mocked(sourceChatApi.getSession).mockImplementation(async (_sourceId, sessionId) => ({
      id: sessionId,
      source_id: "source-1",
      title: "Session",
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-02T00:00:00Z",
      messages:
        sessionId === "sess-new"
          ? [
              { id: "temp-human", type: "human", content: "question" },
              { id: "persisted-ai", type: "ai", content: "draft answer" },
            ]
          : [{ id: "m-1", type: "human", content: "hello" }],
    }));
    vi.mocked(sourceChatApi.createSession).mockResolvedValueOnce({
      id: "sess-new",
      source_id: "source-1",
      title: "question",
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-01T00:00:00Z",
    });
    vi.mocked(sourceChatApi.sendMessage).mockResolvedValueOnce(
      new ReadableStream<Uint8Array>({
        start(controller) {
          controller.enqueue(
            new TextEncoder().encode(
              [
                'data: {"type":"ai_message","content":"draft answer"}',
                'data: {"type":"context_indicators","data":{"sources":{"included":1},"notes":{"included":0}}}',
                'data: {"type":"complete"}',
                "",
              ].join("\n"),
            ),
          );
          controller.close();
        },
      }),
    );

    const { result } = renderHook(() => useSourceChat("source-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loadingSessions).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage("question", "model-fast");
    });

    await waitFor(() => {
      expect(sourceChatApi.createSession).toHaveBeenCalledWith("source-1", {
        title: "question",
      });
      expect(sourceChatApi.sendMessage).toHaveBeenCalledWith(
        "source-1",
        "sess-new",
        { message: "question", model_override: "model-fast" },
        expect.objectContaining({ signal: expect.any(AbortSignal) }),
      );
      expect(result.current.currentSessionId).toBe("sess-new");
      expect(result.current.messages.map((msg) => msg.content)).toContain("draft answer");
      expect(result.current.contextIndicators).toEqual({
        sources: { included: 1 },
        notes: { included: 0 },
      });
      expect(result.current.isStreaming).toBe(false);
    });
  });

  it("aborts in-flight stream requests when cancelStreaming is called", async () => {
    let capturedSignal: AbortSignal | undefined;
    vi.mocked(sourceChatApi.sendMessage).mockImplementationOnce(
      async (_sourceId, _sessionId, _payload, options) => {
        capturedSignal = options?.signal;
        await new Promise(() => {});
        throw new Error("unreachable");
      },
    );

    const { result } = renderHook(() => useSourceChat("source-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });

    act(() => {
      void result.current.sendMessage("cancel me");
    });

    await waitFor(() => {
      expect(result.current.isStreaming).toBe(true);
      expect(capturedSignal).not.toBeUndefined();
    });

    act(() => {
      result.current.cancelStreaming();
    });

    expect(capturedSignal?.aborted).toBe(true);
    expect(result.current.isStreaming).toBe(false);
  });

  it("removes optimistic messages and reports translated errors when streaming fails", async () => {
    vi.mocked(sourceChatApi.sendMessage).mockResolvedValueOnce(
      new ReadableStream<Uint8Array>({
        start(controller) {
          controller.enqueue(
            new TextEncoder().encode('data: {"type":"error","message":"stream exploded"}\n'),
          );
          controller.close();
        },
      }),
    );

    const { result } = renderHook(() => useSourceChat("source-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });

    await act(async () => {
      await result.current.sendMessage("boom");
    });

    await waitFor(() => {
      expect(result.current.messages).toEqual([{ id: "m-1", type: "human", content: "hello" }]);
      expect(result.current.isStreaming).toBe(false);
      expect(hoisted.toastErrorMock).toHaveBeenCalled();
    });
  });

  it("surfaces translated errors when session create/update/delete mutations fail", async () => {
    vi.mocked(sourceChatApi.listSessions).mockResolvedValue([]);
    vi.mocked(sourceChatApi.createSession).mockRejectedValueOnce(new Error("create failed"));
    vi.mocked(sourceChatApi.updateSession).mockRejectedValueOnce(new Error("update failed"));
    vi.mocked(sourceChatApi.deleteSession).mockRejectedValueOnce(new Error("delete failed"));

    const { result } = renderHook(() => useSourceChat("source-1"), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.createSession({ title: "New title" });
      result.current.updateSession("sess-1", { title: "Rename" });
      result.current.deleteSession("sess-1");
    });

    await waitFor(() => {
      expect(hoisted.toastErrorMock).toHaveBeenCalledTimes(3);
    });
  });

  it("shows an error when the response body is missing", async () => {
    vi.mocked(sourceChatApi.sendMessage).mockResolvedValueOnce(undefined as never);

    const { result } = renderHook(() => useSourceChat("source-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });

    await act(async () => {
      await result.current.sendMessage("no body");
    });

    expect(result.current.messages).toEqual([{ id: "m-1", type: "human", content: "hello" }]);
    expect(hoisted.toastErrorMock).toHaveBeenCalled();
  });

  it("ignores malformed SSE chunks but keeps valid streamed content", async () => {
    vi.mocked(sourceChatApi.sendMessage).mockResolvedValueOnce(
      createStream([
        'data: {"type":"ai_message","content":"draft answer"}',
        "data: {invalid-json",
        'data: {"type":"complete"}',
      ]),
    );

    const { result } = renderHook(() => useSourceChat("source-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });

    await act(async () => {
      await result.current.sendMessage("parse branch");
    });

    expect(result.current.messages.map((msg) => msg.content)).toContain("draft answer");
    expect(result.current.isStreaming).toBe(false);
    expect(consoleErrorSpy).toHaveBeenCalled();
  });

  it("surfaces auto-create errors when sendMessage starts without a session", async () => {
    vi.mocked(sourceChatApi.listSessions).mockResolvedValue([]);
    vi.mocked(sourceChatApi.createSession).mockRejectedValueOnce(new Error("auto-create failed"));

    const { result } = renderHook(() => useSourceChat("source-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loadingSessions).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage("new thread question");
    });

    expect(result.current.currentSessionId).toBeNull();
    expect(result.current.isStreaming).toBe(false);
    expect(hoisted.toastErrorMock).toHaveBeenCalled();
  });

  it("skips replayed ai frames and updates the latest streamed ai message", async () => {
    vi.mocked(sourceChatApi.getSession).mockResolvedValue({
      id: "sess-1",
      source_id: "source-1",
      title: "Session",
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-02T00:00:00Z",
      messages: [
        { id: "h-1", type: "human", content: "hello" },
        { id: "a-existing", type: "ai", content: "already persisted" },
      ],
    } as never);
    vi.mocked(sourceChatApi.sendMessage).mockResolvedValueOnce(
      createStream([
        'data: {"type":"ai_message","content":"already persisted"}',
        'data: {"type":"ai_message","content":"draft"}',
        'data: {"type":"ai_message","content":"final"}',
        'data: {"type":"complete"}',
      ]),
    );

    const { result } = renderHook(() => useSourceChat("source-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
      expect(result.current.messages.some((msg) => msg.content === "already persisted")).toBe(true);
    });

    await act(async () => {
      await result.current.sendMessage("stream update");
    });

    const aiContents = result.current.messages
      .filter((msg) => msg.type === "ai")
      .map((msg) => msg.content);
    expect(aiContents).toContain("already persisted");
    expect(aiContents).toContain("final");
    expect(aiContents).not.toContain("draft");
  });

  it("swallows AbortError from stream reader without user-facing error", async () => {
    vi.mocked(sourceChatApi.sendMessage).mockResolvedValueOnce({
      getReader: () => ({
        read: vi.fn().mockRejectedValue(new DOMException("aborted", "AbortError")),
      }),
    } as never);

    const { result } = renderHook(() => useSourceChat("source-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });

    await act(async () => {
      await result.current.sendMessage("abort me");
    });

    expect(result.current.isStreaming).toBe(false);
    expect(hoisted.toastErrorMock).not.toHaveBeenCalled();
  });

  it("transitions through successful create/update/delete session actions", async () => {
    vi.mocked(sourceChatApi.listSessions).mockResolvedValue([]);
    vi.mocked(sourceChatApi.createSession).mockResolvedValueOnce({
      id: "sess-new",
      source_id: "source-1",
      title: "Created",
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-01T00:00:00Z",
    });
    vi.mocked(sourceChatApi.updateSession).mockResolvedValueOnce({});
    vi.mocked(sourceChatApi.deleteSession).mockResolvedValueOnce({});

    const { result } = renderHook(() => useSourceChat("source-1"), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.createSession({ title: "manual" });
    });

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-new");
      expect(hoisted.toastSuccessMock).toHaveBeenCalledWith("Session created");
    });

    act(() => {
      result.current.updateSession("sess-new", { title: "renamed" });
    });

    await waitFor(() => {
      expect(sourceChatApi.updateSession).toHaveBeenCalledWith("source-1", "sess-new", {
        title: "renamed",
      });
      expect(hoisted.toastSuccessMock).toHaveBeenCalledWith("Session updated");
    });

    act(() => {
      result.current.deleteSession("sess-new");
    });

    await waitFor(() => {
      expect(result.current.currentSessionId).toBeNull();
      expect(hoisted.toastSuccessMock).toHaveBeenCalledWith("Session deleted");
    });
  });
});
