import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { researchThreadsApi } from "@/lib/api/research-threads";
import {
  useAppendResearchThreadEntry,
  useCreateDraftFromResearchThread,
  useCreateResearchThread,
  useNotebookResearchThreads,
} from "./use-research-threads";

const hoisted = vi.hoisted(() => ({
  useQueryMock: vi.fn(),
  useMutationMock: vi.fn(),
  useQueryClientMock: vi.fn(),
  queryClient: {
    invalidateQueries: vi.fn(),
  },
  toastMock: vi.fn(),
  t: Object.assign((key: string) => key, {
    common: {
      success: "Success",
      error: "Error",
    },
    notebooks: {
      researchThreadSaved: "Research thread saved.",
      researchThreadDraftCreated: "Draft created from research thread.",
    },
  }),
  getApiErrorMessageMock: vi.fn((_error, translate, fallback) =>
    typeof translate === "function" ? translate("resolved-error") : fallback,
  ),
}));

vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: hoisted.useQueryMock,
    useMutation: hoisted.useMutationMock,
    useQueryClient: hoisted.useQueryClientMock,
  };
});

vi.mock("@/lib/api/research-threads", () => ({
  researchThreadsApi: {
    list: vi.fn(),
    create: vi.fn(),
    append: vi.fn(),
    createDraft: vi.fn(),
  },
}));

vi.mock("@/lib/hooks/use-toast", () => ({
  useToast: () => ({ toast: hoisted.toastMock }),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t: hoisted.t }),
}));

vi.mock("@/lib/utils/error-handler", () => ({
  getApiErrorMessage: hoisted.getApiErrorMessageMock,
}));

describe("useResearchThreads hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useQueryMock.mockImplementation((options: unknown) => options);
    hoisted.useMutationMock.mockImplementation((options: unknown) => options);
    hoisted.useQueryClientMock.mockReturnValue(hoisted.queryClient);
  });

  it("configures notebook research thread query", async () => {
    renderHook(() => useNotebookResearchThreads("nb-1"));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
      enabled: boolean;
    };

    await queryOptions.queryFn();

    expect(queryOptions.queryKey).toEqual(QUERY_KEYS.notebookResearchThreads("nb-1"));
    expect(queryOptions.enabled).toBe(true);
    expect(researchThreadsApi.list).toHaveBeenCalledWith("nb-1");
  });

  it("disables the notebook research thread query when notebook id is empty", () => {
    renderHook(() => useNotebookResearchThreads(""));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      enabled: boolean;
    };

    expect(queryOptions.enabled).toBe(false);
  });

  it("creates a research thread, invalidates queries, and shows success toast", async () => {
    renderHook(() => useCreateResearchThread());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      mutationFn: (args: { notebookId: string; payload: { title: string } }) => Promise<unknown>;
      onSuccess: (data: { notebook_id: string }) => void;
      onError: (error: unknown) => void;
    };

    await mutationOptions.mutationFn({
      notebookId: "nb-7",
      payload: { title: "Thread" },
    });
    mutationOptions.onSuccess({ notebook_id: "nb-7" });
    mutationOptions.onError(new Error("boom"));

    expect(researchThreadsApi.create).toHaveBeenCalledWith("nb-7", { title: "Thread" });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.notebookResearchThreads("nb-7"),
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Research thread saved.",
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-error",
      variant: "destructive",
    });
  });

  it("creates a draft from a research thread and invalidates both draft and thread queries", async () => {
    renderHook(() => useCreateDraftFromResearchThread("nb-9"));

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      mutationFn: (threadId: string) => Promise<unknown>;
      onSuccess: () => void;
      onError: (error: unknown) => void;
    };

    await mutationOptions.mutationFn("thread-9");
    mutationOptions.onSuccess();
    mutationOptions.onError(new Error("nope"));

    expect(researchThreadsApi.createDraft).toHaveBeenCalledWith("thread-9");
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.notebookDrafts("nb-9"),
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.notebookResearchThreads("nb-9"),
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Draft created from research thread.",
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-error",
      variant: "destructive",
    });
  });

  it("appends a research thread entry and invalidates thread queries", async () => {
    renderHook(() => useAppendResearchThreadEntry("nb-2"));

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      mutationFn: (args: {
        threadId: string;
        payload: { entry_type: string; content: string };
      }) => Promise<unknown>;
      onSuccess: () => void;
      onError: (error: unknown) => void;
    };

    await mutationOptions.mutationFn({
      threadId: "thread-2",
      payload: { entry_type: "answer_snapshot", content: "saved answer" },
    });
    mutationOptions.onSuccess();
    mutationOptions.onError(new Error("append failed"));

    expect(researchThreadsApi.append).toHaveBeenCalledWith("thread-2", {
      entry_type: "answer_snapshot",
      content: "saved answer",
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.notebookResearchThreads("nb-2"),
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-error",
      variant: "destructive",
    });
  });
});
