import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { notebooksApi } from "@/lib/api/notebooks";
import { QUERY_KEYS } from "@/lib/api/query-client";
import {
  useCreateNotebook,
  useDeleteNotebook,
  useNotebook,
  useNotebookDeletePreview,
  useNotebooks,
  useUpdateNotebook,
} from "./use-notebooks";

const hoisted = vi.hoisted(() => ({
  useQueryMock: vi.fn(),
  useQueryClientMock: vi.fn(),
  useAppMutationMock: vi.fn(),
  getApiErrorKeyMock: vi.fn(),
  queryClient: {
    invalidateQueries: vi.fn(),
  },
  t: Object.assign((key: string) => `translated:${key}`, {
    common: {
      success: "Success",
      error: "Error",
    },
    notebooks: {
      createSuccess: "Notebook created",
      updateSuccess: "Notebook updated",
      deleteSuccess: "Notebook deleted",
    },
  }),
}));

vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: hoisted.useQueryMock,
    useQueryClient: hoisted.useQueryClientMock,
  };
});

vi.mock("@/lib/hooks/use-app-mutation", () => ({
  useAppMutation: hoisted.useAppMutationMock,
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t: hoisted.t }),
}));

vi.mock("@/lib/utils/error-handler", () => ({
  getApiErrorKey: hoisted.getApiErrorKeyMock,
}));

vi.mock("@/lib/api/notebooks", () => ({
  notebooksApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    deletePreview: vi.fn(),
  },
}));

describe("useNotebooks hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useQueryMock.mockImplementation((options: unknown) => options);
    hoisted.useQueryClientMock.mockReturnValue(hoisted.queryClient);
    hoisted.useAppMutationMock.mockImplementation((options: unknown) => options);
    hoisted.getApiErrorKeyMock.mockReturnValue("services.api.error");
  });

  it("requests notebook list with archive filter and updated sort", async () => {
    renderHook(() => useNotebooks(true));
    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
    };

    await queryOptions.queryFn();

    expect(queryOptions.queryKey).toEqual([...QUERY_KEYS.notebooks, { archived: true }]);
    expect(notebooksApi.list).toHaveBeenCalledWith({ archived: true, order_by: "updated desc" });
  });

  it("disables notebook detail query when id is empty", () => {
    renderHook(() => useNotebook(""));
    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      enabled: boolean;
      queryKey: unknown[];
    };

    expect(queryOptions.queryKey).toEqual(QUERY_KEYS.notebook(""));
    expect(queryOptions.enabled).toBe(false);
  });

  it("configures notebook detail query when id exists", async () => {
    renderHook(() => useNotebook("nb-99"));
    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      enabled: boolean;
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
    };

    await queryOptions.queryFn();

    expect(queryOptions.queryKey).toEqual(QUERY_KEYS.notebook("nb-99"));
    expect(queryOptions.enabled).toBe(true);
    expect(notebooksApi.get).toHaveBeenCalledWith("nb-99");
  });

  it("configures notebook detail and delete-preview queries", async () => {
    renderHook(() => useNotebook("nb-42"));
    renderHook(() => useNotebookDeletePreview("nb-42", true));

    const detailOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      enabled: boolean;
      queryFn: () => Promise<unknown>;
    };
    const previewOptions = hoisted.useQueryMock.mock.calls[1][0] as {
      queryKey: unknown[];
      enabled: boolean;
      queryFn: () => Promise<unknown>;
    };

    await detailOptions.queryFn();
    await previewOptions.queryFn();

    expect(detailOptions.queryKey).toEqual(QUERY_KEYS.notebook("nb-42"));
    expect(detailOptions.enabled).toBe(true);
    expect(notebooksApi.get).toHaveBeenCalledWith("nb-42");

    expect(previewOptions.queryKey).toEqual([...QUERY_KEYS.notebook("nb-42"), "delete-preview"]);
    expect(previewOptions.enabled).toBe(true);
    expect(notebooksApi.deletePreview).toHaveBeenCalledWith("nb-42");
  });

  it("configures and executes notebook delete preview query", async () => {
    renderHook(() => useNotebookDeletePreview("nb-preview", true));
    const enabledOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      enabled: boolean;
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
    };

    await enabledOptions.queryFn();

    renderHook(() => useNotebookDeletePreview("nb-preview", false));
    const disabledOptions = hoisted.useQueryMock.mock.calls[1][0] as {
      enabled: boolean;
    };

    expect(enabledOptions.queryKey).toEqual([
      ...QUERY_KEYS.notebook("nb-preview"),
      "delete-preview",
    ]);
    expect(enabledOptions.enabled).toBe(true);
    expect(disabledOptions.enabled).toBe(false);
    expect(notebooksApi.deletePreview).toHaveBeenCalledWith("nb-preview");
  });

  it("invalidates notebook lists after create and update", () => {
    renderHook(() => useCreateNotebook());
    const createOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      onSuccess?: () => void;
      errorToast?: (error: unknown) => { description?: string };
    };

    createOptions.onSuccess?.();
    const createError = createOptions.errorToast?.(new Error("boom"));

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.notebooks,
    });
    expect(hoisted.getApiErrorKeyMock).toHaveBeenCalled();
    expect(createError?.description).toBe("translated:services.api.error");

    renderHook(() => useUpdateNotebook());
    const updateOptions = hoisted.useAppMutationMock.mock.calls[1][0] as {
      onSuccess?: (data: unknown, vars: { id: string }) => void;
    };

    updateOptions.onSuccess?.({}, { id: "nb-1" });

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.notebooks,
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.notebook("nb-1"),
    });
  });

  it("wires create/update mutation functions and translated toast descriptors", async () => {
    renderHook(() => useCreateNotebook());
    renderHook(() => useUpdateNotebook());

    const createOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      mutationFn: (payload: { title: string }) => Promise<unknown>;
      successToast?: { title?: string; description?: string };
    };
    const updateOptions = hoisted.useAppMutationMock.mock.calls[1][0] as {
      mutationFn: (payload: { id: string; data: { title: string } }) => Promise<unknown>;
      successToast?: { title?: string; description?: string };
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };

    await createOptions.mutationFn({ title: "Notebook One" });
    await updateOptions.mutationFn({ id: "nb-2", data: { title: "Notebook Two" } });

    expect(notebooksApi.create).toHaveBeenCalledWith({ title: "Notebook One" });
    expect(notebooksApi.update).toHaveBeenCalledWith("nb-2", { title: "Notebook Two" });
    expect(createOptions.successToast).toEqual({
      title: "Success",
      description: "Notebook created",
    });
    expect(updateOptions.successToast).toEqual({
      title: "Success",
      description: "Notebook updated",
    });
    expect(updateOptions.errorToast?.(new Error("boom"))).toEqual({
      title: "Error",
      description: "translated:services.api.error",
      variant: "destructive",
    });
  });

  it("wires create/update/delete mutation functions and error toasts", async () => {
    renderHook(() => useCreateNotebook());
    const createOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      mutationFn?: (data: { title: string }) => Promise<unknown>;
    };
    await createOptions.mutationFn?.({ title: "Notebook 1" });

    renderHook(() => useUpdateNotebook());
    const updateOptions = hoisted.useAppMutationMock.mock.calls[1][0] as {
      mutationFn?: (input: { id: string; data: { title: string } }) => Promise<unknown>;
      errorToast?: (error: unknown) => { description?: string };
    };
    await updateOptions.mutationFn?.({ id: "nb-2", data: { title: "Notebook 2" } });
    const updateError = updateOptions.errorToast?.(new Error("update failed"));

    renderHook(() => useDeleteNotebook());
    const deleteOptions = hoisted.useAppMutationMock.mock.calls[2][0] as {
      mutationFn?: (input: { id: string; deleteExclusiveSources?: boolean }) => Promise<unknown>;
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };
    await deleteOptions.mutationFn?.({ id: "nb-3" });
    await deleteOptions.mutationFn?.({ id: "nb-3", deleteExclusiveSources: true });
    const deleteError = deleteOptions.errorToast?.(new Error("delete failed"));

    expect(notebooksApi.create).toHaveBeenCalledWith({ title: "Notebook 1" });
    expect(notebooksApi.update).toHaveBeenCalledWith("nb-2", { title: "Notebook 2" });
    expect(notebooksApi.delete).toHaveBeenNthCalledWith(1, "nb-3", false);
    expect(notebooksApi.delete).toHaveBeenNthCalledWith(2, "nb-3", true);
    expect(updateError?.description).toBe("translated:services.api.error");
    expect(deleteError?.description).toBe("translated:services.api.error");
    expect(deleteError?.variant).toBe("destructive");
  });

  it("invalidates notebooks and sources after delete", () => {
    renderHook(() => useDeleteNotebook());
    const deleteOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      onSuccess?: () => void;
    };

    deleteOptions.onSuccess?.();

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(1, {
      queryKey: QUERY_KEYS.notebooks,
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(2, {
      queryKey: ["sources"],
    });
  });

  it("wires delete mutation function and destructive error toast", async () => {
    renderHook(() => useDeleteNotebook());

    const deleteOptions = hoisted.useAppMutationMock.mock.calls[0][0] as {
      mutationFn: (payload: { id: string; deleteExclusiveSources?: boolean }) => Promise<unknown>;
      errorToast?: (error: unknown) => { description?: string; variant?: string };
    };

    await deleteOptions.mutationFn({ id: "nb-7" });
    await deleteOptions.mutationFn({ id: "nb-7", deleteExclusiveSources: true });

    expect(notebooksApi.delete).toHaveBeenNthCalledWith(1, "nb-7", false);
    expect(notebooksApi.delete).toHaveBeenNthCalledWith(2, "nb-7", true);
    expect(deleteOptions.errorToast?.(new Error("boom"))).toEqual({
      title: "Error",
      description: "translated:services.api.error",
      variant: "destructive",
    });
  });
});
