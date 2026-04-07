import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { chatApi } from "@/lib/api/chat";
import { useTranslation } from "@/lib/hooks/use-translation";
import { useNotebookChat } from "./useNotebookChat";

const hoisted = vi.hoisted(() => ({
  toastError: vi.fn(),
  toastSuccess: vi.fn(),
}));

let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

vi.mock("sonner", () => ({
  toast: {
    success: hoisted.toastSuccess,
    error: hoisted.toastError,
  },
}));

vi.mock("@/lib/api/chat", () => ({
  chatApi: {
    listSessions: vi.fn(),
    getSession: vi.fn(),
    createSession: vi.fn(),
    updateSession: vi.fn(),
    deleteSession: vi.fn(),
    buildContext: vi.fn(),
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

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

async function waitForInitialContextCounts(result: {
  current: {
    tokenCount: number;
    charCount: number;
  };
}) {
  await waitFor(() => {
    expect(result.current.tokenCount).toBe(12);
    expect(result.current.charCount).toBe(34);
  });
}

describe("useNotebookChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        chat: {
          sessionCreated: "Session created",
          sessionUpdated: "Session updated",
          sessionDeleted: "Session deleted",
        },
      },
    } as unknown as ReturnType<typeof useTranslation>);

    vi.mocked(chatApi.listSessions).mockResolvedValue([]);
    vi.mocked(chatApi.buildContext).mockResolvedValue({
      context: { sources: [], notes: [] },
      token_count: 12,
      char_count: 34,
    });
    vi.mocked(chatApi.getSession).mockResolvedValue({
      id: "sess-1",
      notebook_id: "nb-1",
      title: "Session",
      messages: [],
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-02T00:00:00Z",
    });
    vi.mocked(chatApi.updateSession).mockResolvedValue({});
    vi.mocked(chatApi.deleteSession).mockResolvedValue({});
    vi.mocked(chatApi.createSession).mockResolvedValue({
      id: "sess-new",
      notebook_id: "nb-1",
      title: "Created",
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-01T00:00:00Z",
    });
    vi.mocked(chatApi.sendMessage).mockResolvedValue({
      messages: [
        {
          id: "assistant-1",
          type: "ai",
          content: "Response content",
          timestamp: "2026-01-02T00:00:00Z",
        },
      ],
    } as never);
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("stores pending model override when no session exists", async () => {
    const params = {
      notebookId: "nb-1",
      sources: [] as never[],
      notes: [] as never[],
      contextSelections: { sources: {}, notes: {} },
    };

    const { result } = renderHook(() => useNotebookChat(params), { wrapper: createWrapper() });

    await waitForInitialContextCounts(result);
    await waitFor(() => {
      expect(result.current.loadingSessions).toBe(false);
    });

    act(() => {
      result.current.setModelOverride("gemini-3.0-pro");
    });

    expect(result.current.pendingModelOverride).toBe("gemini-3.0-pro");
  });

  it("updates model override on active session", async () => {
    vi.mocked(chatApi.listSessions).mockResolvedValue([
      {
        id: "sess-1",
        notebook_id: "nb-1",
        title: "First",
        created: "2026-01-01T00:00:00Z",
        updated: "2026-01-02T00:00:00Z",
      },
    ]);

    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "nb-1",
          sources: [],
          notes: [],
          contextSelections: { sources: {}, notes: {} },
        }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });

    act(() => {
      result.current.setModelOverride("gemini-3.1-pro");
    });

    await waitFor(() => {
      expect(chatApi.updateSession).toHaveBeenCalledWith("sess-1", {
        model_override: "gemini-3.1-pro",
      });
    });
  });

  it("auto-creates a session and sends a message with built context", async () => {
    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "nb-1",
          sources: [{ id: "source-1" }] as never,
          notes: [{ id: "note-1" }] as never,
          contextSelections: {
            sources: { "source-1": "insights" },
            notes: { "note-1": "full" },
          },
        }),
      { wrapper: createWrapper() },
    );

    act(() => {
      result.current.setModelOverride("gemini-3.1-pro");
    });

    await act(async () => {
      await result.current.sendMessage("Need a notebook summary");
    });

    expect(chatApi.createSession).toHaveBeenCalledWith({
      notebook_id: "nb-1",
      title: "Need a notebook summary",
      model_override: "gemini-3.1-pro",
    });
    expect(chatApi.buildContext).toHaveBeenCalledWith({
      notebook_id: "nb-1",
      context_config: {
        sources: { "source-1": "insights" },
        notes: { "note-1": "full content" },
      },
    });
    expect(chatApi.sendMessage).toHaveBeenCalledWith({
      session_id: "sess-new",
      message: "Need a notebook summary",
      context: { sources: [], notes: [] },
      model_override: undefined,
    });
    expect(result.current.currentSessionId).toBe("sess-new");
    expect(result.current.tokenCount).toBe(12);
    expect(result.current.charCount).toBe(34);
    expect(result.current.pendingModelOverride).toBeNull();
    expect(result.current.isSending).toBe(false);
  });

  it("removes optimistic message and surfaces translated error when sending fails", async () => {
    vi.mocked(chatApi.listSessions).mockResolvedValue([
      {
        id: "sess-1",
        notebook_id: "nb-1",
        title: "First",
        created: "2026-01-01T00:00:00Z",
        updated: "2026-01-02T00:00:00Z",
      },
    ]);
    vi.mocked(chatApi.sendMessage).mockRejectedValue(new Error("send failed"));

    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "nb-1",
          sources: [],
          notes: [],
          contextSelections: { sources: {}, notes: {} },
        }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });

    await act(async () => {
      await result.current.sendMessage("broken");
    });

    expect(hoisted.toastError).toHaveBeenCalled();
    expect(result.current.messages).toEqual([]);
    expect(result.current.isSending).toBe(false);
  });

  it("switches sessions and clears local optimistic messages", async () => {
    vi.mocked(chatApi.listSessions).mockResolvedValue([
      {
        id: "sess-1",
        notebook_id: "nb-1",
        title: "First",
        created: "2026-01-01T00:00:00Z",
        updated: "2026-01-02T00:00:00Z",
      },
      {
        id: "sess-2",
        notebook_id: "nb-1",
        title: "Second",
        created: "2026-01-03T00:00:00Z",
        updated: "2026-01-04T00:00:00Z",
      },
    ]);
    vi.mocked(chatApi.getSession).mockImplementation(async (sessionId) => {
      if (sessionId === "sess-1") {
        return {
          id: "sess-1",
          notebook_id: "nb-1",
          title: "Session",
          messages: [
            {
              id: "msg-1",
              type: "human",
              content: "existing",
              timestamp: "2026-01-02T00:00:00Z",
            },
          ],
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-02T00:00:00Z",
        } as never;
      }

      return {
        id: "sess-2",
        notebook_id: "nb-1",
        title: "Second",
        messages: [],
        created: "2026-01-03T00:00:00Z",
        updated: "2026-01-04T00:00:00Z",
      } as never;
    });

    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "nb-1",
          sources: [],
          notes: [],
          contextSelections: { sources: {}, notes: {} },
        }),
      { wrapper: createWrapper() },
    );

    await waitForInitialContextCounts(result);

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
      expect(result.current.messages).toHaveLength(1);
    });

    act(() => {
      result.current.switchSession("sess-2");
    });

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-2");
      expect(result.current.messages).toEqual([]);
    });
  });

  it("deletes the active session and clears session-specific state", async () => {
    vi.mocked(chatApi.listSessions)
      .mockResolvedValueOnce([
        {
          id: "sess-1",
          notebook_id: "nb-1",
          title: "First",
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-02T00:00:00Z",
        },
      ])
      .mockResolvedValue([]);
    vi.mocked(chatApi.getSession).mockResolvedValue({
      id: "sess-1",
      notebook_id: "nb-1",
      title: "Session",
      messages: [
        {
          id: "msg-1",
          type: "human",
          content: "existing",
          timestamp: "2026-01-02T00:00:00Z",
        },
      ],
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-02T00:00:00Z",
    } as never);

    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "nb-1",
          sources: [],
          notes: [],
          contextSelections: { sources: {}, notes: {} },
        }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });

    await act(async () => {
      result.current.deleteSession("sess-1");
    });

    await waitFor(() => {
      expect(result.current.currentSessionId).toBeNull();
      expect(result.current.messages).toEqual([]);
    });
    expect(hoisted.toastSuccess).toHaveBeenCalledWith("Session deleted");
  });

  it("aborts an in-flight send when switching sessions", async () => {
    const deferredContext = createDeferred<{
      context: { sources: []; notes: [] };
      token_count: number;
      char_count: number;
    }>();

    vi.mocked(chatApi.listSessions).mockResolvedValue([
      {
        id: "sess-1",
        notebook_id: "nb-1",
        title: "First",
        created: "2026-01-01T00:00:00Z",
        updated: "2026-01-02T00:00:00Z",
      },
      {
        id: "sess-2",
        notebook_id: "nb-1",
        title: "Second",
        created: "2026-01-03T00:00:00Z",
        updated: "2026-01-04T00:00:00Z",
      },
    ]);
    vi.mocked(chatApi.buildContext).mockReturnValue(deferredContext.promise);

    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "nb-1",
          sources: [],
          notes: [],
          contextSelections: { sources: {}, notes: {} },
        }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });

    await act(async () => {
      void result.current.sendMessage("interrupt me");
    });

    await waitFor(() => {
      expect(result.current.isSending).toBe(true);
    });

    act(() => {
      result.current.switchSession("sess-2");
    });

    deferredContext.resolve({
      context: { sources: [], notes: [] },
      token_count: 20,
      char_count: 40,
    });

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-2");
      expect(result.current.messages).toEqual([]);
      expect(result.current.isSending).toBe(false);
    });
  });

  it("resets token and char counts when notebook id is empty", async () => {
    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "",
          sources: [],
          notes: [],
          contextSelections: { sources: {}, notes: {} },
        }),
      { wrapper: createWrapper() },
    );

    expect(result.current.tokenCount).toBe(0);
    expect(result.current.charCount).toBe(0);
  });

  it("keeps pending model override and reports error when auto-create session fails", async () => {
    vi.mocked(chatApi.createSession).mockRejectedValueOnce(new Error("create failed"));

    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "nb-1",
          sources: [],
          notes: [],
          contextSelections: { sources: {}, notes: {} },
        }),
      { wrapper: createWrapper() },
    );

    act(() => {
      result.current.setModelOverride("gemini-3.1-pro");
    });

    await act(async () => {
      await result.current.sendMessage("broken create");
    });

    expect(result.current.currentSessionId).toBeNull();
    expect(result.current.pendingModelOverride).toBe("gemini-3.1-pro");
    expect(hoisted.toastError).toHaveBeenCalled();
  });

  it("reports buildContext failures and removes the optimistic message", async () => {
    vi.mocked(chatApi.listSessions).mockResolvedValue([
      {
        id: "sess-1",
        notebook_id: "nb-1",
        title: "First",
        created: "2026-01-01T00:00:00Z",
        updated: "2026-01-02T00:00:00Z",
      },
    ]);
    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "nb-1",
          sources: [],
          notes: [],
          contextSelections: { sources: {}, notes: {} },
        }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });

    vi.mocked(chatApi.buildContext).mockRejectedValueOnce(new Error("context failed"));

    await act(async () => {
      await result.current.sendMessage("context failure");
    });

    await waitFor(() => {
      expect(result.current.messages).toEqual([]);
      expect(hoisted.toastError).toHaveBeenCalled();
    });
  });

  it("surfaces update/delete session mutation errors", async () => {
    vi.mocked(chatApi.listSessions).mockResolvedValue([
      {
        id: "sess-1",
        notebook_id: "nb-1",
        title: "First",
        created: "2026-01-01T00:00:00Z",
        updated: "2026-01-02T00:00:00Z",
      },
    ]);
    vi.mocked(chatApi.updateSession).mockRejectedValueOnce(new Error("update failed"));
    vi.mocked(chatApi.deleteSession).mockRejectedValueOnce(new Error("delete failed"));

    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "nb-1",
          sources: [],
          notes: [],
          contextSelections: { sources: {}, notes: {} },
        }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });

    act(() => {
      result.current.updateSession("sess-1", { title: "Rename" });
      result.current.deleteSession("sess-1");
    });

    await waitFor(() => {
      expect(hoisted.toastError).toHaveBeenCalledTimes(2);
    });
  });

  it("logs context count failures without clobbering counters", async () => {
    vi.mocked(chatApi.buildContext).mockRejectedValue(new Error("count failed"));

    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "nb-1",
          sources: [],
          notes: [],
          contextSelections: { sources: {}, notes: {} },
        }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalled();
    });

    expect(result.current.tokenCount).toBe(0);
    expect(result.current.charCount).toBe(0);
  });

  it("maps source full and note not-in selections when building context", async () => {
    vi.mocked(chatApi.listSessions).mockResolvedValue([
      {
        id: "sess-1",
        notebook_id: "nb-1",
        title: "First",
        created: "2026-01-01T00:00:00Z",
        updated: "2026-01-02T00:00:00Z",
      },
    ]);

    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "nb-1",
          sources: [{ id: "source-1" }] as never,
          notes: [{ id: "note-1" }] as never,
          contextSelections: {
            sources: { "source-1": "full" },
            notes: {},
          },
        }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.currentSessionId).toBe("sess-1");
    });

    await act(async () => {
      await result.current.sendMessage("include full source");
    });

    expect(chatApi.buildContext).toHaveBeenCalledWith({
      notebook_id: "nb-1",
      context_config: {
        sources: { "source-1": "full content" },
        notes: { "note-1": "not in" },
      },
    });
  });

  it("handles successful create and update session mutations", async () => {
    vi.mocked(chatApi.listSessions).mockResolvedValue([]);

    const { result } = renderHook(
      () =>
        useNotebookChat({
          notebookId: "nb-1",
          sources: [],
          notes: [],
          contextSelections: { sources: {}, notes: {} },
        }),
      { wrapper: createWrapper() },
    );

    act(() => {
      result.current.createSession("manual session");
    });

    await waitFor(() => {
      expect(chatApi.createSession).toHaveBeenCalledWith({
        notebook_id: "nb-1",
        title: "manual session",
      });
      expect(result.current.currentSessionId).toBe("sess-new");
      expect(hoisted.toastSuccess).toHaveBeenCalledWith("Session created");
    });

    act(() => {
      result.current.updateSession("sess-new", { title: "renamed" });
    });

    await waitFor(() => {
      expect(chatApi.updateSession).toHaveBeenCalledWith("sess-new", { title: "renamed" });
      expect(hoisted.toastSuccess).toHaveBeenCalledWith("Session updated");
    });
  });
});
