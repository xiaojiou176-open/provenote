import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QUERY_KEYS } from "@/lib/api/query-client";
import {
  useAddSourcesToNotebook,
  useCreateSource,
  useDeleteSource,
  useFileUpload,
  useNotebookSources,
  useRemoveSourceFromNotebook,
  useReprocessSource,
  useRetrySource,
  useSource,
  useSourceProcessingReport,
  useSourceStatus,
  useSources,
  useUpdateSource,
} from "./use-sources";

const hoisted = vi.hoisted(() => ({
  useQueryMock: vi.fn(),
  useInfiniteQueryMock: vi.fn(),
  useQueryClientMock: vi.fn(),
  useAppMutationMock: vi.fn(),
  getApiErrorMessageMock: vi.fn(),
  queryClient: {
    invalidateQueries: vi.fn(),
  },
  sourcesApiMock: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    upload: vi.fn(),
    status: vi.fn(),
    retry: vi.fn(),
    processingReport: vi.fn(),
    reprocess: vi.fn(),
  },
  notebooksApiAddSourceMock: vi.fn(),
  notebooksApiRemoveSourceMock: vi.fn(),
  t: Object.assign((key: string) => key, {
    common: {
      success: "Success",
      error: "Error",
      warning: "Warning",
    },
    sources: {
      sourceQueued: "Source queued",
      sourceQueuedDesc: "Queued description",
      sourceAddedSuccess: "Source added",
      sourceRequeued: "Source requeued",
      sourceRequeuedDesc: "Retry queued",
      failedToRetry: "Retry failed",
      failedToAddSource: "Add failed",
      sourceUpdatedSuccess: "Source updated",
      failedToUpdateSource: "Update failed",
      sourceDeletedSuccess: "Source deleted",
      failedToDeleteSource: "Delete failed",
      fileUploadedSuccess: "File uploaded",
      failedToUploadFile: "Upload failed",
      failedToAddSourcesToNotebook: "Add to notebook failed",
      sourcesAddedToNotebook: "Added {count} sources",
      partialAddSuccess: "Added {success}, failed {failed}",
      sourceRemovedFromNotebook: "Removed",
      failedToRemoveSourceFromNotebook: "Remove failed",
    },
  }),
}));

vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: hoisted.useQueryMock,
    useInfiniteQuery: hoisted.useInfiniteQueryMock,
    useQueryClient: hoisted.useQueryClientMock,
  };
});

vi.mock("@/lib/hooks/use-app-mutation", () => ({
  useAppMutation: hoisted.useAppMutationMock,
}));

vi.mock("@/lib/api/sources", () => ({
  sourcesApi: hoisted.sourcesApiMock,
}));

vi.mock("@/lib/api/notebooks", () => ({
  notebooksApi: {
    addSource: hoisted.notebooksApiAddSourceMock,
    removeSource: hoisted.notebooksApiRemoveSourceMock,
  },
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t: hoisted.t }),
}));

vi.mock("@/lib/utils/error-handler", () => ({
  getApiErrorMessage: hoisted.getApiErrorMessageMock,
}));

describe("useSources hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useQueryMock.mockImplementation((options: unknown) => options);
    hoisted.useInfiniteQueryMock.mockImplementation((options: unknown) => options);
    hoisted.useQueryClientMock.mockReturnValue(hoisted.queryClient);
    hoisted.useAppMutationMock.mockImplementation((options: unknown) => options);
    hoisted.getApiErrorMessageMock.mockImplementation((_error, translate, fallback) =>
      typeof translate === "function" ? translate("resolved-error-message") : fallback,
    );
  });

  it("configures notebook-scoped source query with short stale-time", () => {
    renderHook(() => useSources("nb-1"));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      enabled: boolean;
      staleTime: number;
      refetchOnWindowFocus: boolean;
    };

    expect(queryOptions.queryKey).toEqual(QUERY_KEYS.sources("nb-1"));
    expect(queryOptions.enabled).toBe(true);
    expect(queryOptions.staleTime).toBe(5000);
    expect(queryOptions.refetchOnWindowFocus).toBe(true);
  });

  it("disables sources query when notebook id is missing", () => {
    renderHook(() => useSources(undefined));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      enabled: boolean;
    };

    expect(queryOptions.queryKey).toEqual(QUERY_KEYS.sources(undefined));
    expect(queryOptions.enabled).toBe(false);
  });

  it("flattens infinite source pages and exposes manual refetch", () => {
    const fetchNextPage = vi.fn();
    hoisted.useInfiniteQueryMock.mockReturnValue({
      data: {
        pages: [
          { sources: [{ id: "source-1", title: "A" }] },
          { sources: [{ id: "source-2", title: "B" }] },
        ],
      },
      isLoading: false,
      isFetchingNextPage: true,
      hasNextPage: true,
      fetchNextPage,
      error: null,
    });

    const { result } = renderHook(() => useNotebookSources("nb-2"));

    expect(result.current.sources).toEqual([
      { id: "source-1", title: "A" },
      { id: "source-2", title: "B" },
    ]);
    expect(result.current.isFetchingNextPage).toBe(true);
    expect(result.current.hasNextPage).toBe(true);

    result.current.refetch();

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.sourcesInfinite("nb-2"),
    });
  });

  it("builds notebook source pagination offsets and handles short final page", async () => {
    renderHook(() => useNotebookSources("nb-paged"));
    const queryOptions = hoisted.useInfiniteQueryMock.mock.calls[0][0] as {
      enabled: boolean;
      queryFn: (params: {
        pageParam: number;
      }) => Promise<{ nextOffset?: number; sources: unknown[] }>;
      getNextPageParam: (lastPage: { nextOffset?: number }) => number | undefined;
    };

    hoisted.sourcesApiMock.list.mockResolvedValueOnce(new Array(30).fill({ id: "source-x" }));
    const firstPage = await queryOptions.queryFn({ pageParam: 0 });
    hoisted.sourcesApiMock.list.mockResolvedValueOnce([{ id: "source-only" }]);
    const secondPage = await queryOptions.queryFn({ pageParam: 30 });

    renderHook(() => useNotebookSources(""));
    const disabledOptions = hoisted.useInfiniteQueryMock.mock.calls[1][0] as { enabled: boolean };

    expect(queryOptions.enabled).toBe(true);
    expect(firstPage.nextOffset).toBe(30);
    expect(queryOptions.getNextPageParam(firstPage)).toBe(30);
    expect(secondPage.nextOffset).toBeUndefined();
    expect(disabledOptions.enabled).toBe(false);
    expect(hoisted.sourcesApiMock.list).toHaveBeenNthCalledWith(1, {
      notebook_id: "nb-paged",
      limit: 30,
      offset: 0,
      sort_by: "updated",
      sort_order: "desc",
    });
  });

  it("uses the default initial page offset when infinite query pageParam is omitted", async () => {
    renderHook(() => useNotebookSources("nb-default-page"));
    const queryOptions = hoisted.useInfiniteQueryMock.mock.calls[0][0] as {
      queryFn: (params: {
        pageParam?: number;
      }) => Promise<{ nextOffset?: number; sources: unknown[] }>;
    };

    hoisted.sourcesApiMock.list.mockResolvedValueOnce([{ id: "source-default" }]);
    await queryOptions.queryFn({});

    expect(hoisted.sourcesApiMock.list).toHaveBeenCalledWith({
      notebook_id: "nb-default-page",
      limit: 30,
      offset: 0,
      sort_by: "updated",
      sort_order: "desc",
    });
  });

  it("polls only processing statuses and stops retries on 404", () => {
    renderHook(() => useSourceStatus("src-1", true));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      refetchInterval: (query: { state: { data?: { status?: string } } }) => number | false;
      retry: (failureCount: number, error: unknown) => boolean;
    };

    expect(queryOptions.refetchInterval({ state: { data: { status: "running" } } })).toBe(2000);
    expect(queryOptions.refetchInterval({ state: { data: { status: "completed" } } })).toBe(false);

    expect(queryOptions.retry(0, { response: { status: 404 } })).toBe(false);
    expect(queryOptions.retry(2, { response: { status: 500 } })).toBe(true);
    expect(queryOptions.retry(3, { response: { status: 500 } })).toBe(false);
  });

  it("polls queued/new statuses and honors explicit disabled flag", () => {
    renderHook(() => useSourceStatus("src-queued", false));
    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      enabled: boolean;
      refetchInterval: (query: { state: { data?: { status?: string } } }) => number | false;
    };

    expect(queryOptions.enabled).toBe(false);
    expect(queryOptions.refetchInterval({ state: { data: { status: "queued" } } })).toBe(2000);
    expect(queryOptions.refetchInterval({ state: { data: { status: "new" } } })).toBe(2000);
  });

  it("configures source processing report query and respects enabled flag", async () => {
    renderHook(() => useSourceProcessingReport("src-report", true));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      enabled: boolean;
      staleTime: number;
      queryFn: () => Promise<unknown>;
    };

    await queryOptions.queryFn();

    expect(queryOptions.queryKey).toEqual(["sources", "src-report", "processing-report"]);
    expect(queryOptions.enabled).toBe(true);
    expect(queryOptions.staleTime).toBe(0);
    expect(hoisted.sourcesApiMock.processingReport).toHaveBeenCalledWith("src-report");

    renderHook(() => useSourceProcessingReport("", false));
    const disabledOptions = hoisted.useQueryMock.mock.calls[1][0] as { enabled: boolean };
    expect(disabledOptions.enabled).toBe(false);
  });

  it("enables the processing report query by default when the flag is omitted", () => {
    renderHook(() => useSourceProcessingReport("src-default-report"));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as { enabled: boolean };
    expect(queryOptions.enabled).toBe(true);
  });

  it("disables source status query when source id is empty", () => {
    renderHook(() => useSourceStatus("", true));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as { enabled: boolean };

    expect(queryOptions.enabled).toBe(false);
  });

  it("configures source detail query", () => {
    renderHook(() => useSource("src-detail"));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      enabled: boolean;
      staleTime: number;
      refetchOnWindowFocus: boolean;
    };

    expect(queryOptions.queryKey).toEqual(QUERY_KEYS.source("src-detail"));
    expect(queryOptions.enabled).toBe(true);
    expect(queryOptions.staleTime).toBe(30000);
    expect(queryOptions.refetchOnWindowFocus).toBe(true);
  });

  it("disables source detail query when id is empty", () => {
    renderHook(() => useSource(""));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as { enabled: boolean };
    expect(queryOptions.enabled).toBe(false);
  });

  it("invokes source/list/status queryFns and mutationFns for source lifecycle hooks", async () => {
    renderHook(() => useSources("nb-query"));
    const listQuery = hoisted.useQueryMock.mock.calls[0][0] as { queryFn: () => Promise<unknown> };
    await listQuery.queryFn();

    renderHook(() => useSource("src-query"));
    const sourceQuery = hoisted.useQueryMock.mock.calls[1][0] as {
      queryFn: () => Promise<unknown>;
    };
    await sourceQuery.queryFn();

    renderHook(() => useSourceStatus("src-status"));
    const statusQuery = hoisted.useQueryMock.mock.calls[2][0] as {
      queryFn: () => Promise<unknown>;
    };
    await statusQuery.queryFn();

    renderHook(() => useCreateSource());
    const createOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      mutationFn: (data: { notebook_id: string }) => Promise<unknown>;
    };
    await createOptions.mutationFn({ notebook_id: "nb-create" });

    renderHook(() => useUpdateSource());
    const updateOptions = hoisted.useAppMutationMock.mock.calls[1][0] as {
      mutationFn: (payload: { id: string; data: { title: string } }) => Promise<unknown>;
    };
    await updateOptions.mutationFn({ id: "src-update", data: { title: "updated" } });

    renderHook(() => useDeleteSource());
    const deleteOptions = hoisted.useAppMutationMock.mock.calls[2][0] as {
      mutationFn: (id: string) => Promise<unknown>;
    };
    await deleteOptions.mutationFn("src-delete");

    renderHook(() => useFileUpload());
    const fileUploadOptions = hoisted.useAppMutationMock.mock.calls[3][0] as {
      mutationFn: (payload: { file: File; notebookId: string }) => Promise<unknown>;
    };
    await fileUploadOptions.mutationFn({
      file: new File(["hello"], "sample.txt", { type: "text/plain" }),
      notebookId: "nb-upload",
    });

    renderHook(() => useRetrySource());
    const retryOptions = hoisted.useAppMutationMock.mock.calls[4][0] as {
      mutationFn: (id: string) => Promise<unknown>;
    };
    await retryOptions.mutationFn("src-retry");

    expect(hoisted.sourcesApiMock.list).toHaveBeenCalledWith({ notebook_id: "nb-query" });
    expect(hoisted.sourcesApiMock.get).toHaveBeenCalledWith("src-query");
    expect(hoisted.sourcesApiMock.status).toHaveBeenCalledWith("src-status");
    expect(hoisted.sourcesApiMock.create).toHaveBeenCalledWith({ notebook_id: "nb-create" });
    expect(hoisted.sourcesApiMock.update).toHaveBeenCalledWith("src-update", { title: "updated" });
    expect(hoisted.sourcesApiMock.delete).toHaveBeenCalledWith("src-delete");
    expect(hoisted.sourcesApiMock.upload).toHaveBeenCalled();
    expect(hoisted.sourcesApiMock.retry).toHaveBeenCalledWith("src-retry");
  });

  it("invalidates source caches after create and returns queued toast copy", () => {
    renderHook(() => useCreateSource());
    const mutationOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      onSuccess?: (
        result: unknown,
        variables: { notebook_id?: string; notebooks?: string[] },
      ) => void;
      successToast?: (
        result: unknown,
        variables: { async_processing?: boolean },
      ) => {
        title?: string;
        description?: string;
      };
    };

    mutationOptions.onSuccess?.({}, { notebook_id: "nb-1" });

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(1, {
      queryKey: QUERY_KEYS.sources(),
      refetchType: "active",
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(2, {
      queryKey: QUERY_KEYS.sources("nb-1"),
      refetchType: "active",
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(3, {
      queryKey: QUERY_KEYS.sourcesInfinite("nb-1"),
      refetchType: "active",
    });

    expect(mutationOptions.successToast?.({}, { async_processing: true })).toEqual({
      title: "Source queued",
      description: "Queued description",
    });
    expect(mutationOptions.successToast?.({}, { async_processing: false })).toEqual({
      title: "Success",
      description: "Source added",
    });
  });

  it("uses notebooks fallback id and resolves create-source error toast", () => {
    renderHook(() => useCreateSource());
    const mutationOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      onSuccess?: (
        result: unknown,
        variables: { notebook_id?: string; notebooks?: string[] },
      ) => void;
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };

    mutationOptions.onSuccess?.({}, { notebooks: ["nb-fallback"] });
    const errorToast = mutationOptions.errorToast?.(new Error("create failed"));

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.sources("nb-fallback"),
      refetchType: "active",
    });
    expect(errorToast?.description).toBe("resolved-error-message");
    expect(errorToast?.variant).toBe("destructive");
  });

  it("resolves translated error toasts for update, delete, upload, retry, reprocess, add, and remove mutations", () => {
    renderHook(() => useUpdateSource());
    const updateOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };
    expect(updateOptions.errorToast?.(new Error("update failed"))).toEqual({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });

    renderHook(() => useDeleteSource());
    const deleteOptions = hoisted.useAppMutationMock.mock.calls[1][0] as {
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };
    expect(deleteOptions.errorToast?.(new Error("delete failed"))).toEqual({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });

    renderHook(() => useFileUpload());
    const uploadOptions = hoisted.useAppMutationMock.mock.calls[2][0] as {
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };
    expect(uploadOptions.errorToast?.(new Error("upload failed"))).toEqual({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });

    renderHook(() => useRetrySource());
    const retryOptions = hoisted.useAppMutationMock.mock.calls[3][0] as {
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };
    expect(retryOptions.errorToast?.(new Error("retry failed"))).toEqual({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });

    renderHook(() => useReprocessSource());
    const reprocessOptions = hoisted.useAppMutationMock.mock.calls[4][0] as {
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };
    expect(reprocessOptions.errorToast?.(new Error("reprocess failed"))).toEqual({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });

    renderHook(() => useAddSourcesToNotebook());
    const addOptions = hoisted.useAppMutationMock.mock.calls[5][0] as {
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };
    expect(addOptions.errorToast?.(new Error("add failed"))).toEqual({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });

    renderHook(() => useRemoveSourceFromNotebook());
    const removeOptions = hoisted.useAppMutationMock.mock.calls[6][0] as {
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };
    expect(removeOptions.errorToast?.(new Error("remove failed"))).toEqual({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });
  });

  it("invalidates status and source caches after retry", () => {
    renderHook(() => useRetrySource());
    const mutationOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      onSuccess?: (result: unknown, sourceId: string) => void;
    };

    mutationOptions.onSuccess?.({}, "src-9");

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ["sources", "src-9", "status"],
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.sources(),
      refetchType: "active",
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.source("src-9"),
    });
  });

  it("invalidates processing report caches after reprocess and resolves error toast", () => {
    renderHook(() => useReprocessSource());
    const mutationOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      mutationFn: (sourceId: string) => Promise<unknown>;
      onSuccess?: (result: unknown, sourceId: string) => void;
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };

    mutationOptions.mutationFn("src-reprocess");
    mutationOptions.onSuccess?.({}, "src-reprocess");

    expect(hoisted.sourcesApiMock.reprocess).toHaveBeenCalledWith("src-reprocess");
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ["sources", "src-reprocess", "processing-report"],
    });
    expect(mutationOptions.errorToast?.(new Error("reprocess failed"))).toEqual({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });
  });

  it("invalidates list and detail queries after update source", () => {
    renderHook(() => useUpdateSource());
    const mutationOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      onSuccess?: (result: unknown, variables: { id: string }) => void;
      successToast?: { title?: string; description?: string };
    };

    mutationOptions.onSuccess?.({}, { id: "src-update" });

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.sources(),
      refetchType: "active",
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.source("src-update"),
    });
    expect(mutationOptions.successToast).toEqual({
      title: "Success",
      description: "Source updated",
    });
  });

  it("invalidates list and detail queries after delete source", () => {
    renderHook(() => useDeleteSource());
    const mutationOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      onSuccess?: (result: unknown, sourceId: string) => void;
      successToast?: { title?: string; description?: string };
    };

    mutationOptions.onSuccess?.({}, "src-delete");

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.sources(),
      refetchType: "active",
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.source("src-delete"),
    });
    expect(mutationOptions.successToast).toEqual({
      title: "Success",
      description: "Source deleted",
    });
  });

  it("invalidates notebook scoped caches after file upload", () => {
    renderHook(() => useFileUpload());
    const mutationOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      onSuccess?: (result: unknown, variables: { notebookId: string }) => void;
      successToast?: { title?: string; description?: string };
    };

    mutationOptions.onSuccess?.({}, { notebookId: "nb-upload" });

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.sources(),
      refetchType: "active",
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.sources("nb-upload"),
      refetchType: "active",
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.sourcesInfinite("nb-upload"),
      refetchType: "active",
    });
    expect(mutationOptions.successToast).toEqual({
      title: "Success",
      description: "File uploaded",
    });
  });

  it("returns proper toast messages for add-to-notebook success branches", () => {
    renderHook(() => useAddSourcesToNotebook());
    const mutationOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      successToast?: (result: { successes: number; failures: number; total: number }) => {
        title?: string;
        description?: string;
        variant?: "default" | "destructive";
      };
      onSuccess?: (
        result: { successes: number; failures: number; total: number },
        variables: { notebookId: string; sourceIds: string[] },
      ) => void;
    };

    expect(mutationOptions.successToast?.({ successes: 2, failures: 0, total: 2 })).toEqual({
      title: "Success",
      description: "Added 2 sources",
    });
    expect(mutationOptions.successToast?.({ successes: 0, failures: 2, total: 2 })).toEqual({
      title: "Error",
      description: "Add to notebook failed",
      variant: "destructive",
    });
    expect(mutationOptions.successToast?.({ successes: 1, failures: 1, total: 2 })).toEqual({
      title: "Success",
      description: "Added 1, failed 1",
      variant: "default",
    });

    mutationOptions.onSuccess?.(
      { successes: 2, failures: 0, total: 2 },
      { notebookId: "nb-add", sourceIds: ["s1", "s2"] },
    );

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.sources("nb-add"),
      refetchType: "active",
    });
  });

  it("returns destructive error toasts for add/remove notebook mutations", () => {
    renderHook(() => useAddSourcesToNotebook());
    const addOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };
    const addError = addOptions.errorToast?.(new Error("add failed"));

    renderHook(() => useRemoveSourceFromNotebook());
    const removeOptions = hoisted.useAppMutationMock.mock.calls[1][0] as {
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };
    const removeError = removeOptions.errorToast?.(new Error("remove failed"));

    expect(addError?.description).toBe("resolved-error-message");
    expect(addError?.variant).toBe("destructive");
    expect(removeError?.description).toBe("resolved-error-message");
    expect(removeError?.variant).toBe("destructive");
  });

  it("adds multiple sources with allSettled result counting", async () => {
    hoisted.notebooksApiAddSourceMock
      .mockResolvedValueOnce(undefined)
      .mockRejectedValueOnce(new Error("failed one"))
      .mockResolvedValueOnce(undefined);

    renderHook(() => useAddSourcesToNotebook());
    const mutationOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      mutationFn?: (variables: { notebookId: string; sourceIds: string[] }) => Promise<{
        successes: number;
        failures: number;
        total: number;
      }>;
    };

    const result = await mutationOptions.mutationFn?.({
      notebookId: "nb-multi",
      sourceIds: ["s1", "s2", "s3"],
    });

    expect(hoisted.notebooksApiAddSourceMock).toHaveBeenCalledTimes(3);
    expect(hoisted.notebooksApiAddSourceMock).toHaveBeenNthCalledWith(1, "nb-multi", "s1");
    expect(hoisted.notebooksApiAddSourceMock).toHaveBeenNthCalledWith(2, "nb-multi", "s2");
    expect(hoisted.notebooksApiAddSourceMock).toHaveBeenNthCalledWith(3, "nb-multi", "s3");
    expect(result).toEqual({ successes: 2, failures: 1, total: 3 });
  });

  it("invalidates notebook and source detail after remove-from-notebook", () => {
    renderHook(() => useRemoveSourceFromNotebook());
    const mutationOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      onSuccess?: (result: unknown, variables: { notebookId: string; sourceId: string }) => void;
    };

    mutationOptions.onSuccess?.({}, { notebookId: "nb-rm", sourceId: "src-rm" });

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.sources("nb-rm"),
      refetchType: "active",
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.source("src-rm"),
    });
  });

  it("removes source from notebook via notebooks api", async () => {
    hoisted.notebooksApiRemoveSourceMock.mockResolvedValue({ ok: true });

    renderHook(() => useRemoveSourceFromNotebook());
    const mutationOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      mutationFn?: (variables: { notebookId: string; sourceId: string }) => Promise<unknown>;
    };

    const result = await mutationOptions.mutationFn?.({
      notebookId: "nb-remove",
      sourceId: "src-remove",
    });

    expect(hoisted.notebooksApiRemoveSourceMock).toHaveBeenCalledWith("nb-remove", "src-remove");
    expect(result).toEqual({ ok: true });
  });
});
