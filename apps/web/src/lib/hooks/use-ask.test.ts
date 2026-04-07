import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  askKnowledgeBaseMock: vi.fn(),
  toastErrorMock: vi.fn(),
  getApiErrorMessageMock: vi.fn(),
}));

vi.mock("@/lib/api/search", () => ({
  searchApi: {
    askKnowledgeBase: hoisted.askKnowledgeBaseMock,
  },
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("@/lib/utils/error-handler", () => ({
  getApiErrorMessage: hoisted.getApiErrorMessageMock,
}));

vi.mock("sonner", () => ({
  toast: {
    error: hoisted.toastErrorMock,
  },
}));

import { useAsk } from "./use-ask";

const encoder = new TextEncoder();
let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function createStream(chunks: string[]): ReadableStream<Uint8Array> {
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
}

describe("useAsk", () => {
  const validModels = {
    strategy: "s",
    answer: "a",
    finalAnswer: "f",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    hoisted.getApiErrorMessageMock.mockImplementation(
      (message: string, translate?: (key: string) => string) =>
        `mapped:${message}:${translate ? translate("apiErrors.askFailed") : "no-map"}`,
    );
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("parses streamed strategy/answer/final events and deduplicates answers", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(
      createStream([
        'data: {"type":"strategy","reasoning":"R","searches":[]}\n\n',
        'data: {"type":"answer","content":"A1"}\n\n',
        'data: {"type":"answer","content":"A1"}\n\n',
        'data: {"type":"answer","content":""}\n\n',
        'data: {"type":"final_answer","content":"F"}\n\n',
        'data: {"type":"complete"}\n\n',
      ]),
    );

    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.strategy?.reasoning).toBe("R");
    expect(result.current.answers).toEqual(["A1"]);
    expect(result.current.finalAnswer).toBe("F");
    expect(result.current.isStreaming).toBe(false);
  });

  it("flushes EOF strategy event without trailing newline", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(
      createStream([
        'data: {"type":"strategy","reasoning":"Tail","searches":[{"term":"k","instructions":"i"}]}',
      ]),
    );

    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.strategy).toEqual({
      reasoning: "Tail",
      searches: [{ term: "k", instructions: "i" }],
    });
    expect(result.current.isStreaming).toBe(false);
  });

  it("flushes EOF complete event and stops streaming", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(createStream(['data: {"type":"complete"}']));

    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("handles EOF answer updates including duplicate suppression", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(
      createStream([
        'data: {"type":"answer","content":"EOF-A"}\n\n',
        'data: {"type":"answer","content":"EOF-A"}',
      ]),
    );

    const { result } = renderHook(() => useAsk());
    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.answers).toEqual(["EOF-A"]);
  });

  it("adds new EOF answer content when it is not a duplicate", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(
      createStream(['data: {"type":"answer","content":"EOF-NEW"}']),
    );

    const { result } = renderHook(() => useAsk());
    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.answers).toEqual(["EOF-NEW"]);
  });

  it("ignores EOF answer events when content is empty", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(
      createStream(['data: {"type":"answer","content":""}']),
    );

    const { result } = renderHook(() => useAsk());
    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.answers).toEqual([]);
  });

  it("flushes EOF final_answer event", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(
      createStream(['data: {"type":"final_answer","content":"EOF_FINAL"}']),
    );

    const { result } = renderHook(() => useAsk());
    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.finalAnswer).toBe("EOF_FINAL");
    expect(result.current.isStreaming).toBe(false);
  });

  it("ignores blank SSE payload blocks", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(
      createStream(["data:    \n\n", 'data: {"type":"final_answer","content":"Recovered"}\n\n']),
    );

    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.finalAnswer).toBe("Recovered");
    expect(result.current.error).toBeNull();
  });

  it("ignores non-data SSE lines without crashing", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(createStream(["event: ping\n\n"]));
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.error).toBeNull();
    expect(result.current.answers).toEqual([]);
  });

  it("applies default strategy fields for EOF strategy events", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(createStream(['data: {"type":"strategy"}']));
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.strategy).toEqual({ reasoning: "", searches: [] });
  });

  it("applies default strategy fields for non-EOF strategy events", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(createStream(['data: {"type":"strategy"}\n\n']));
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.strategy).toEqual({ reasoning: "", searches: [] });
  });

  it("applies default content for final_answer events", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(
      createStream(['data: {"type":"final_answer"}\n\n', 'data: {"type":"final_answer"}']),
    );
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.finalAnswer).toBe("");
    expect(result.current.isStreaming).toBe(false);
  });

  it("ignores unknown event types in both non-EOF and EOF parsing", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(
      createStream(['data: {"type":"noop"}\n\n', 'data: {"type":"noop"}']),
    );
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.error).toBeNull();
    expect(result.current.finalAnswer).toBeNull();
  });

  it("rejects empty questions and skips api call", async () => {
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("   ", validModels);
    });

    expect(hoisted.askKnowledgeBaseMock).not.toHaveBeenCalled();
    expect(hoisted.toastErrorMock).toHaveBeenCalledWith("apiErrors.pleaseEnterQuestion");
  });

  it("rejects incomplete model configuration", async () => {
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", {
        strategy: "",
        answer: "a",
        finalAnswer: "f",
      });
    });

    expect(hoisted.askKnowledgeBaseMock).not.toHaveBeenCalled();
    expect(hoisted.toastErrorMock).toHaveBeenCalledWith("apiErrors.pleaseConfigureModels");
  });

  it("maps request errors and stores error state", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(undefined);
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBe("No response body received from server");
    expect(hoisted.getApiErrorMessageMock).toHaveBeenCalledWith(
      "No response body received from server",
      expect.any(Function),
    );
    expect(hoisted.toastErrorMock).toHaveBeenCalledWith("apiErrors.askFailed", {
      description: "mapped:No response body received from server:apiErrors.askFailed",
    });
  });

  it("surfaces stream error events with fallback message", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(createStream(['data: {"type":"error"}']));
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.error).toBe("Stream error occurred");
    expect(result.current.isStreaming).toBe(false);
    expect(hoisted.toastErrorMock).toHaveBeenCalled();
  });

  it("handles non-EOF stream error events", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(
      createStream(['data: {"type":"error","message":"midstream boom"}\n\n']),
    );
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.error).toBe("midstream boom");
    expect(result.current.isStreaming).toBe(false);
  });

  it("uses default message for non-EOF stream errors without a message", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(createStream(['data: {"type":"error"}\n\n']));
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.error).toBe("Stream error occurred");
  });

  it("falls back to default catch message for unknown thrown values", async () => {
    hoisted.askKnowledgeBaseMock.mockRejectedValue({});
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.error).toBe("An unexpected error occurred");
    expect(hoisted.toastErrorMock).toHaveBeenCalled();
  });

  it("ignores malformed SSE payload and keeps valid events", async () => {
    hoisted.askKnowledgeBaseMock.mockResolvedValue(
      createStream([
        "data: {invalid-json\n\n",
        'data: {"type":"final_answer","content":"Recovered"}\n\n',
      ]),
    );

    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.finalAnswer).toBe("Recovered");
    expect(consoleErrorSpy).toHaveBeenCalled();
  });

  it("handles AbortError from request without surfacing toast", async () => {
    hoisted.askKnowledgeBaseMock.mockRejectedValue(new DOMException("aborted", "AbortError"));
    const { result } = renderHook(() => useAsk());

    await act(async () => {
      await result.current.sendAsk("question", validModels);
    });

    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBeNull();
    expect(hoisted.toastErrorMock).not.toHaveBeenCalled();
  });

  it("cancels stale reader when a newer request supersedes it", async () => {
    const firstResponse = createDeferred<{
      getReader: () => { read: () => Promise<any>; cancel: () => Promise<void> };
    }>();
    const staleReader = {
      read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
      cancel: vi.fn().mockResolvedValue(undefined),
    };

    hoisted.askKnowledgeBaseMock
      .mockReturnValueOnce(firstResponse.promise)
      .mockResolvedValueOnce(createStream(['data: {"type":"complete"}\n\n']));

    const { result } = renderHook(() => useAsk());

    act(() => {
      void result.current.sendAsk("first", validModels);
    });

    await act(async () => {
      await result.current.sendAsk("second", validModels);
    });

    await act(async () => {
      firstResponse.resolve({ getReader: () => staleReader });
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(staleReader.cancel).toHaveBeenCalledTimes(1);
    });
  });

  it("ignores stale non-EOF events after request supersession", async () => {
    const firstRead = createDeferred<{ done: boolean; value?: Uint8Array }>();
    const staleReader = {
      read: vi
        .fn()
        .mockImplementationOnce(() => firstRead.promise)
        .mockResolvedValueOnce({ done: true, value: undefined }),
      cancel: vi.fn().mockResolvedValue(undefined),
    };

    hoisted.askKnowledgeBaseMock
      .mockResolvedValueOnce({ getReader: () => staleReader })
      .mockResolvedValueOnce(createStream(['data: {"type":"complete"}\n\n']));

    const { result } = renderHook(() => useAsk());
    let firstPromise!: Promise<void>;
    act(() => {
      firstPromise = result.current.sendAsk("first", validModels);
    });

    await waitFor(() => {
      expect(staleReader.read).toHaveBeenCalledTimes(1);
    });

    await act(async () => {
      await result.current.sendAsk("second", validModels);
    });

    await act(async () => {
      firstRead.resolve({
        done: false,
        value: encoder.encode('data: {"type":"answer","content":"stale"}\n\n'),
      });
      await firstPromise;
    });

    expect(result.current.answers).toEqual([]);
  });

  it("ignores stale EOF events after request supersession", async () => {
    const secondRead = createDeferred<{ done: boolean; value?: Uint8Array }>();
    const staleReader = {
      read: vi
        .fn()
        .mockResolvedValueOnce({
          done: false,
          value: encoder.encode('data: {"type":"strategy","reasoning":"stale","searches":[]}'),
        })
        .mockImplementationOnce(() => secondRead.promise),
      cancel: vi.fn().mockResolvedValue(undefined),
    };

    hoisted.askKnowledgeBaseMock
      .mockResolvedValueOnce({ getReader: () => staleReader })
      .mockResolvedValueOnce(createStream(['data: {"type":"complete"}\n\n']));

    const { result } = renderHook(() => useAsk());
    let firstPromise!: Promise<void>;
    act(() => {
      firstPromise = result.current.sendAsk("first", validModels);
    });

    await waitFor(() => {
      expect(staleReader.read).toHaveBeenCalledTimes(2);
    });

    await act(async () => {
      await result.current.sendAsk("second", validModels);
    });

    await act(async () => {
      secondRead.resolve({ done: true, value: undefined });
      await firstPromise;
    });

    expect(result.current.strategy).toBeNull();
  });

  it("passes AbortSignal and cancel aborts an in-flight request", async () => {
    let capturedSignal: AbortSignal | undefined;
    hoisted.askKnowledgeBaseMock.mockImplementation(
      async (_payload, options?: { signal?: AbortSignal }) =>
        await new Promise((_, reject) => {
          capturedSignal = options?.signal;
          capturedSignal?.addEventListener("abort", () => {
            reject(new DOMException("aborted", "AbortError"));
          });
        }),
    );

    const { result } = renderHook(() => useAsk());
    let pendingRequest!: Promise<void>;
    act(() => {
      pendingRequest = result.current.sendAsk("question", validModels);
    });

    await waitFor(() => {
      expect(capturedSignal).not.toBeUndefined();
      expect(result.current.isStreaming).toBe(true);
      expect(capturedSignal?.aborted).toBe(false);
    });

    act(() => {
      result.current.cancel();
    });

    await act(async () => {
      await pendingRequest;
    });
    expect(capturedSignal?.aborted).toBe(true);
    expect(result.current.isStreaming).toBe(false);
  });

  it("keeps state stable when cancel is called without active request", () => {
    const { result } = renderHook(() => useAsk());
    act(() => {
      result.current.cancel();
    });
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("aborts in-flight request and resets state", async () => {
    let capturedSignal: AbortSignal | undefined;
    hoisted.askKnowledgeBaseMock.mockImplementation(
      async (_payload, options?: { signal?: AbortSignal }) =>
        await new Promise((_, reject) => {
          capturedSignal = options?.signal;
          capturedSignal?.addEventListener("abort", () => {
            reject(new DOMException("aborted", "AbortError"));
          });
        }),
    );

    const { result } = renderHook(() => useAsk());
    let pendingRequest!: Promise<void>;
    act(() => {
      pendingRequest = result.current.sendAsk("question", validModels);
    });

    await waitFor(() => {
      expect(capturedSignal).not.toBeUndefined();
      expect(result.current.isStreaming).toBe(true);
    });

    act(() => {
      result.current.reset();
    });

    await act(async () => {
      await pendingRequest;
    });
    expect(capturedSignal?.aborted).toBe(true);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.strategy).toBeNull();
    expect(result.current.answers).toEqual([]);
    expect(result.current.finalAnswer).toBeNull();
    expect(result.current.error).toBeNull();
  });
});
