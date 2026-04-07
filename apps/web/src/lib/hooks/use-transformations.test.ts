import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  TRANSFORMATION_QUERY_KEYS,
  useCreateTransformation,
  useDefaultPrompt,
  useDeleteTransformation,
  useExecuteTransformation,
  useTransformation,
  useTransformations,
  useUpdateDefaultPrompt,
  useUpdateTransformation,
} from "./use-transformations";

const hoisted = vi.hoisted(() => ({
  useQueryMock: vi.fn(),
  useMutationMock: vi.fn(),
  useQueryClientMock: vi.fn(),
  getApiErrorMessageMock: vi.fn(),
  queryClient: {
    invalidateQueries: vi.fn(),
  },
  transformationsApiMock: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    execute: vi.fn(),
    getDefaultPrompt: vi.fn(),
    updateDefaultPrompt: vi.fn(),
  },
  toastMock: vi.fn(),
  t: Object.assign((key: string) => key, {
    common: {
      success: "Success",
      error: "Error",
    },
    transformations: {
      createSuccess: "Created",
      updateSuccess: "Updated",
      deleteSuccess: "Deleted",
    },
  }),
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

vi.mock("@/lib/hooks/use-toast", () => ({
  useToast: () => ({ toast: hoisted.toastMock }),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t: hoisted.t }),
}));

vi.mock("@/lib/utils/error-handler", () => ({
  getApiErrorMessage: hoisted.getApiErrorMessageMock,
}));

vi.mock("@/lib/api/transformations", () => ({
  transformationsApi: hoisted.transformationsApiMock,
}));

describe("useTransformations hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useQueryMock.mockImplementation((options: unknown) => options);
    hoisted.useMutationMock.mockImplementation((options: unknown) => options);
    hoisted.useQueryClientMock.mockReturnValue(hoisted.queryClient);
    hoisted.getApiErrorMessageMock.mockReturnValue("resolved-error-message");
  });

  it("builds list and default prompt queries and calls their queryFns", async () => {
    renderHook(() => useTransformations());
    const listQueryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
    };
    await listQueryOptions.queryFn();

    renderHook(() => useDefaultPrompt());
    const defaultPromptQueryOptions = hoisted.useQueryMock.mock.calls[1][0] as {
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
    };
    await defaultPromptQueryOptions.queryFn();

    expect(listQueryOptions.queryKey).toEqual(TRANSFORMATION_QUERY_KEYS.transformations);
    expect(defaultPromptQueryOptions.queryKey).toEqual(TRANSFORMATION_QUERY_KEYS.defaultPrompt);
    expect(hoisted.transformationsApiMock.list).toHaveBeenCalledTimes(1);
    expect(hoisted.transformationsApiMock.getDefaultPrompt).toHaveBeenCalledTimes(1);
  });

  it("disables transformation query when id is missing", () => {
    renderHook(() => useTransformation(undefined));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      enabled: boolean;
    };

    expect(queryOptions.queryKey).toEqual(TRANSFORMATION_QUERY_KEYS.transformation(""));
    expect(queryOptions.enabled).toBe(false);
  });

  it("respects explicit enabled flag for transformation query", () => {
    renderHook(() => useTransformation("tr-1", { enabled: false }));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      enabled: boolean;
    };

    expect(queryOptions.queryKey).toEqual(TRANSFORMATION_QUERY_KEYS.transformation("tr-1"));
    expect(queryOptions.enabled).toBe(false);
  });

  it("calls detail query function with transformation id when enabled", async () => {
    renderHook(() => useTransformation("tr-2"));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      enabled: boolean;
      queryFn: () => Promise<unknown>;
    };

    await queryOptions.queryFn();

    expect(queryOptions.enabled).toBe(true);
    expect(hoisted.transformationsApiMock.get).toHaveBeenCalledWith("tr-2");
  });

  it("invalidates list and toasts after create success", () => {
    renderHook(() => useCreateTransformation());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onSuccess?: () => void;
    };

    mutationOptions.onSuccess?.();

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: TRANSFORMATION_QUERY_KEYS.transformations,
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Created",
    });
  });

  it("shows destructive toast when create fails", () => {
    renderHook(() => useCreateTransformation());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onError?: (error: unknown) => void;
    };

    mutationOptions.onError?.(new Error("create failed"));

    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });
  });

  it("wires mutation functions to transformation api calls", async () => {
    renderHook(() => useCreateTransformation());
    const createOptions = hoisted.useMutationMock.mock.calls.at(-1)?.[0] as {
      mutationFn: (data: { name: string }) => Promise<unknown>;
    };
    await createOptions.mutationFn({ name: "transform-a" });

    renderHook(() => useUpdateTransformation());
    const updateOptions = hoisted.useMutationMock.mock.calls.at(-1)?.[0] as {
      mutationFn: (data: { id: string; data: { name: string } }) => Promise<unknown>;
      onError?: (error: unknown) => void;
    };
    await updateOptions.mutationFn({ id: "tr-1", data: { name: "transform-b" } });
    updateOptions.onError?.(new Error("update failed"));

    renderHook(() => useDeleteTransformation());
    const deleteOptions = hoisted.useMutationMock.mock.calls.at(-1)?.[0] as {
      mutationFn: (id: string) => Promise<unknown>;
    };
    await deleteOptions.mutationFn("tr-7");

    renderHook(() => useExecuteTransformation());
    const executeOptions = hoisted.useMutationMock.mock.calls.at(-1)?.[0] as {
      mutationFn: (payload: { source_id: string }) => Promise<unknown>;
    };
    await executeOptions.mutationFn({ source_id: "src-1" });

    renderHook(() => useUpdateDefaultPrompt());
    const updateDefaultPromptOptions = hoisted.useMutationMock.mock.calls.at(-1)?.[0] as {
      mutationFn: (payload: { transformation_instructions: string }) => Promise<unknown>;
    };
    await updateDefaultPromptOptions.mutationFn({ transformation_instructions: "New prompt" });

    expect(hoisted.transformationsApiMock.create).toHaveBeenCalledWith({ name: "transform-a" });
    expect(hoisted.transformationsApiMock.update).toHaveBeenCalledWith("tr-1", {
      name: "transform-b",
    });
    expect(hoisted.transformationsApiMock.delete).toHaveBeenCalledWith("tr-7");
    expect(hoisted.transformationsApiMock.execute).toHaveBeenCalledWith({ source_id: "src-1" });
    expect(hoisted.transformationsApiMock.updateDefaultPrompt).toHaveBeenCalledWith({
      transformation_instructions: "New prompt",
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });
  });

  it("invalidates list and detail after update success", () => {
    renderHook(() => useUpdateTransformation());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onSuccess?: (result: unknown, variables: { id: string }) => void;
    };

    mutationOptions.onSuccess?.({}, { id: "tr-9" });

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(1, {
      queryKey: TRANSFORMATION_QUERY_KEYS.transformations,
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(2, {
      queryKey: TRANSFORMATION_QUERY_KEYS.transformation("tr-9"),
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Updated",
    });
  });

  it("shows destructive toast when delete fails", () => {
    renderHook(() => useDeleteTransformation());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onError?: (error: unknown) => void;
    };

    mutationOptions.onError?.(new Error("cannot delete"));

    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });
  });

  it("invalidates list and toasts after delete success", () => {
    renderHook(() => useDeleteTransformation());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onSuccess?: () => void;
    };

    mutationOptions.onSuccess?.();

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: TRANSFORMATION_QUERY_KEYS.transformations,
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Deleted",
    });
  });

  it("shows destructive toast when execution fails", () => {
    renderHook(() => useExecuteTransformation());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onError?: (error: unknown) => void;
    };

    mutationOptions.onError?.(new Error("execution failed"));

    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });
  });

  it("invalidates default prompt and toasts after update", () => {
    renderHook(() => useUpdateDefaultPrompt());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onSuccess?: () => void;
      onError?: (error: unknown) => void;
    };

    mutationOptions.onSuccess?.();

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: TRANSFORMATION_QUERY_KEYS.defaultPrompt,
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Updated",
    });

    mutationOptions.onError?.(new Error("boom"));

    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });
  });
});
