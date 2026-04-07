import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  MODEL_QUERY_KEYS,
  useAutoAssignDefaults,
  useCreateModel,
  useDeleteModel,
  useModel,
  useModelDefaults,
  useModels,
  useProviders,
  useTestModel,
  useUpdateModelDefaults,
} from "./use-models";

const hoisted = vi.hoisted(() => ({
  useQueryMock: vi.fn(),
  useMutationMock: vi.fn(),
  useQueryClientMock: vi.fn(),
  useAppMutationMock: vi.fn(),
  getApiErrorKeyMock: vi.fn(),
  toastMock: vi.fn(),
  listMock: vi.fn(),
  getMock: vi.fn(),
  createMock: vi.fn(),
  deleteMock: vi.fn(),
  getDefaultsMock: vi.fn(),
  updateDefaultsMock: vi.fn(),
  getProvidersMock: vi.fn(),
  autoAssignMock: vi.fn(),
  testModelMock: vi.fn(),
  queryClient: {
    invalidateQueries: vi.fn(),
  },
  t: Object.assign((key: string) => key, {
    common: {
      success: "Success",
      warning: "Warning",
      error: "Error",
    },
    models: {
      saveSuccess: "Saved",
      deleteSuccess: "Deleted",
      autoAssignSuccess: "Assigned {count} defaults",
      autoAssignNoModels: "No models available",
      autoAssignAlreadySet: "Already set",
    },
  }),
}));

vi.mock("@/lib/api/models", () => ({
  modelsApi: {
    list: hoisted.listMock,
    get: hoisted.getMock,
    create: hoisted.createMock,
    delete: hoisted.deleteMock,
    getDefaults: hoisted.getDefaultsMock,
    updateDefaults: hoisted.updateDefaultsMock,
    getProviders: hoisted.getProvidersMock,
    autoAssign: hoisted.autoAssignMock,
    testModel: hoisted.testModelMock,
  },
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

vi.mock("@/lib/hooks/use-app-mutation", () => ({
  useAppMutation: hoisted.useAppMutationMock,
}));

vi.mock("@/lib/hooks/use-toast", () => ({
  useToast: () => ({ toast: hoisted.toastMock }),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t: hoisted.t }),
}));

vi.mock("@/lib/utils/error-handler", () => ({
  getApiErrorKey: hoisted.getApiErrorKeyMock,
}));

describe("useModels hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useQueryMock.mockImplementation((options: unknown) => options);
    hoisted.useQueryClientMock.mockReturnValue(hoisted.queryClient);
    hoisted.useAppMutationMock.mockImplementation((options: unknown) => options);
    hoisted.useMutationMock.mockImplementation((options: unknown) => ({
      mutate: vi.fn(),
      isPending: false,
      ...options,
    }));
    hoisted.getApiErrorKeyMock.mockReturnValue("resolved-error");
  });

  it("executes model queries and honours enabled gating", async () => {
    hoisted.listMock.mockResolvedValue([]);
    hoisted.getMock.mockResolvedValue({ id: "m1" });
    hoisted.getDefaultsMock.mockResolvedValue({});
    hoisted.getProvidersMock.mockResolvedValue([]);

    const { result: models } = renderHook(() => useModels());
    expect(models.current.queryKey).toEqual(MODEL_QUERY_KEYS.models);
    await models.current.queryFn();
    expect(hoisted.listMock).toHaveBeenCalledTimes(1);

    const { result: model } = renderHook(() => useModel("m1"));
    expect(model.current.queryKey).toEqual(MODEL_QUERY_KEYS.model("m1"));
    expect(model.current.enabled).toBe(true);
    await model.current.queryFn();
    expect(hoisted.getMock).toHaveBeenCalledWith("m1");

    const { result: disabledModel } = renderHook(() => useModel(""));
    expect(disabledModel.current.enabled).toBe(false);

    const { result: defaults } = renderHook(() => useModelDefaults());
    await defaults.current.queryFn();
    expect(hoisted.getDefaultsMock).toHaveBeenCalledTimes(1);

    const { result: providers } = renderHook(() => useProviders());
    await providers.current.queryFn();
    expect(hoisted.getProvidersMock).toHaveBeenCalledTimes(1);
  });

  it("creates model and invalidates list", async () => {
    hoisted.createMock.mockResolvedValue({ id: "new-model" });
    const { result } = renderHook(() => useCreateModel());

    await result.current.mutationFn({ provider: "gemini", model_name: "3.1-pro" });
    result.current.onSuccess?.();
    result.current.errorToast?.(new Error("create failed"));

    expect(hoisted.createMock).toHaveBeenCalledWith({ provider: "gemini", model_name: "3.1-pro" });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: MODEL_QUERY_KEYS.models,
    });
    expect(result.current.successToast).toEqual({
      title: "Success",
      description: "Saved",
    });
    expect(hoisted.getApiErrorKeyMock).toHaveBeenCalledWith(expect.any(Error), "Error");
  });

  it("deletes model and invalidates dependent queries", async () => {
    hoisted.deleteMock.mockResolvedValue(undefined);
    const { result } = renderHook(() => useDeleteModel());

    await result.current.mutationFn("model-1");
    result.current.onSuccess?.();
    result.current.errorToast?.(new Error("delete failed"));

    expect(hoisted.deleteMock).toHaveBeenCalledWith("model-1");
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(1, {
      queryKey: MODEL_QUERY_KEYS.models,
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(2, {
      queryKey: MODEL_QUERY_KEYS.defaults,
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(3, {
      queryKey: ["credentials"],
    });
  });

  it("updates defaults and invalidates defaults query", async () => {
    hoisted.updateDefaultsMock.mockResolvedValue({ strategy_model: "m2" });
    const { result } = renderHook(() => useUpdateModelDefaults());

    await result.current.mutationFn({ strategy_model: "m2" });
    result.current.onSuccess?.();
    result.current.errorToast?.(new Error("update defaults failed"));

    expect(hoisted.updateDefaultsMock).toHaveBeenCalledWith({ strategy_model: "m2" });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: MODEL_QUERY_KEYS.defaults,
    });
  });

  it("toasts all auto-assign branches and handles errors", async () => {
    hoisted.autoAssignMock.mockResolvedValue({
      assigned: { chat: "model-1" },
      missing: [],
    });
    const { result } = renderHook(() => useAutoAssignDefaults());

    await result.current.mutationFn();
    expect(hoisted.autoAssignMock).toHaveBeenCalledTimes(1);

    result.current.onSuccess?.({ assigned: { chat: "model-1" }, missing: [] });
    result.current.onSuccess?.({ assigned: {}, missing: ["Embedding Model"] });
    result.current.onSuccess?.({ assigned: {}, missing: [] });

    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Assigned 1 defaults",
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Warning",
      description: "No models available",
      variant: "destructive",
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Already set",
    });

    result.current.onError?.(new Error("boom"));
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-error",
      variant: "destructive",
    });
  });

  it("tracks successful model test state and clearResult", () => {
    hoisted.useMutationMock.mockImplementation((options: unknown) => {
      const typed = options as {
        onSuccess?: (result: { success: boolean; message: string }) => void;
      };
      return {
        mutate: (modelId: string) => {
          if (modelId === "model-1") {
            typed.onSuccess?.({ success: true, message: "ok" });
          }
        },
        isPending: false,
      };
    });

    const { result } = renderHook(() => useTestModel());

    act(() => {
      result.current.testModel("model-1", "Gemini Pro");
    });

    expect(result.current.testedModelName).toBe("Gemini Pro");
    expect(result.current.testingModelId).toBeNull();
    expect(result.current.testResult).toEqual({ success: true, message: "ok" });

    act(() => {
      result.current.clearResult();
    });

    expect(result.current.testResult).toBeNull();
    expect(result.current.testedModelName).toBe("");
    expect(result.current.testingModelId).toBeNull();
  });

  it("stores failed model test result for non-Error values", () => {
    hoisted.useMutationMock.mockImplementation((options: unknown) => {
      const typed = options as {
        onError?: (error: unknown) => void;
      };
      return {
        mutate: () => {
          typed.onError?.({ code: "timeout" });
        },
        isPending: false,
      };
    });

    const { result } = renderHook(() => useTestModel());

    act(() => {
      result.current.testModel("model-2", "Gemini Flash");
    });

    expect(result.current.testResult).toEqual({
      success: false,
      message: "[object Object]",
    });
    expect(result.current.testingModelId).toBeNull();
  });

  it("executes testModel mutationFn and handles Error instances", async () => {
    hoisted.testModelMock.mockResolvedValue({ success: true, message: "ok" });
    const { result } = renderHook(() => useTestModel());

    const options = hoisted.useMutationMock.mock.calls[0][0] as {
      mutationFn: (id: string) => Promise<unknown>;
      onError?: (error: unknown) => void;
    };

    await options.mutationFn("model-x");
    expect(hoisted.testModelMock).toHaveBeenCalledWith("model-x");

    act(() => {
      options.onError?.(new Error("boom"));
    });

    expect(result.current.testResult).toEqual({ success: false, message: "boom" });
  });
});
