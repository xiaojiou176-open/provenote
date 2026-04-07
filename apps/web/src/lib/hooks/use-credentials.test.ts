import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MODEL_QUERY_KEYS } from "@/lib/hooks/use-models";
import {
  CREDENTIAL_QUERY_KEYS,
  useCreateCredential,
  useCredential,
  useCredentialStatus,
  useCredentials,
  useCredentialsByProvider,
  useDeleteCredential,
  useDiscoverModels,
  useRegisterModels,
  useTestCredential,
  useUpdateCredential,
} from "./use-credentials";

const hoisted = vi.hoisted(() => ({
  getStatusMock: vi.fn(),
  listMock: vi.fn(),
  getMock: vi.fn(),
  createMock: vi.fn(),
  updateMock: vi.fn(),
  deleteMock: vi.fn(),
  testMock: vi.fn(),
  discoverMock: vi.fn(),
  registerModelsMock: vi.fn(),
  useQueryMock: vi.fn(),
  useMutationMock: vi.fn(),
  useQueryClientMock: vi.fn(),
  getApiErrorKeyMock: vi.fn(),
  toastMock: vi.fn(),
  queryClient: {
    invalidateQueries: vi.fn(),
  },
  t: Object.assign((key: string) => key, {
    common: {
      success: "Success",
      error: "Error",
    },
    apiKeys: {
      configSaveSuccess: "Saved",
      configUpdateSuccess: "Updated",
      configDeleteSuccess: "Deleted",
      testSuccess: "Connection ok",
      testFailed: "Connection failed",
      syncFailed: "Sync failed",
      syncSuccess: "Sync success",
      syncNoNew: "No new {count}",
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
  getApiErrorKey: hoisted.getApiErrorKeyMock,
}));

vi.mock("@/lib/api/credentials", () => ({
  credentialsApi: {
    getStatus: hoisted.getStatusMock,
    list: hoisted.listMock,
    get: hoisted.getMock,
    create: hoisted.createMock,
    update: hoisted.updateMock,
    delete: hoisted.deleteMock,
    test: hoisted.testMock,
    discover: hoisted.discoverMock,
    registerModels: hoisted.registerModelsMock,
  },
}));

describe("useCredentials hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useQueryMock.mockImplementation((options: unknown) => options);
    hoisted.useMutationMock.mockImplementation((options: unknown) => ({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      ...options,
    }));
    hoisted.useQueryClientMock.mockReturnValue(hoisted.queryClient);
    hoisted.getApiErrorKeyMock.mockReturnValue("resolved-api-error");
  });

  it("exposes status/list/detail queryFns backed by credentialsApi", async () => {
    hoisted.getStatusMock.mockResolvedValue({ encryption_configured: true });
    hoisted.listMock.mockResolvedValue([{ id: "cred-1" }]);
    hoisted.getMock.mockResolvedValue({ id: "cred-1" });

    renderHook(() => useCredentialStatus());
    renderHook(() => useCredentials("google"));
    renderHook(() => useCredential("cred-1"));

    const statusQuery = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
    };
    const listQuery = hoisted.useQueryMock.mock.calls[1][0] as {
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
    };
    const detailQuery = hoisted.useQueryMock.mock.calls[2][0] as {
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
    };

    expect(statusQuery.queryKey).toEqual(CREDENTIAL_QUERY_KEYS.status);
    await expect(statusQuery.queryFn()).resolves.toEqual({ encryption_configured: true });
    expect(hoisted.getStatusMock).toHaveBeenCalledTimes(1);

    expect(listQuery.queryKey).toEqual(CREDENTIAL_QUERY_KEYS.byProvider("google"));
    await expect(listQuery.queryFn()).resolves.toEqual([{ id: "cred-1" }]);
    expect(hoisted.listMock).toHaveBeenCalledWith("google");

    expect(detailQuery.queryKey).toEqual(CREDENTIAL_QUERY_KEYS.detail("cred-1"));
    await expect(detailQuery.queryFn()).resolves.toEqual({ id: "cred-1" });
    expect(hoisted.getMock).toHaveBeenCalledWith("cred-1");
  });

  it("uses provider-aware query keys for credential listing", () => {
    renderHook(() => useCredentials());
    renderHook(() => useCredentials("google"));

    const firstQuery = hoisted.useQueryMock.mock.calls[0][0] as { queryKey: unknown[] };
    const secondQuery = hoisted.useQueryMock.mock.calls[1][0] as { queryKey: unknown[] };

    expect(firstQuery.queryKey).toEqual(CREDENTIAL_QUERY_KEYS.all);
    expect(secondQuery.queryKey).toEqual(CREDENTIAL_QUERY_KEYS.byProvider("google"));
  });

  it("exposes status/list/detail queryFns backed by credentialsApi", async () => {
    hoisted.getStatusMock.mockResolvedValue({ encryption_configured: true });
    hoisted.listMock.mockResolvedValue([{ id: "cred-1" }]);
    hoisted.getMock.mockResolvedValue({ id: "cred-1" });

    renderHook(() => useCredentialStatus());
    renderHook(() => useCredentials("google"));
    renderHook(() => useCredential("cred-1"));

    const statusQuery = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
    };
    const listQuery = hoisted.useQueryMock.mock.calls[1][0] as {
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
    };
    const detailQuery = hoisted.useQueryMock.mock.calls[2][0] as {
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
    };

    expect(statusQuery.queryKey).toEqual(CREDENTIAL_QUERY_KEYS.status);
    await expect(statusQuery.queryFn()).resolves.toEqual({ encryption_configured: true });
    expect(hoisted.getStatusMock).toHaveBeenCalledTimes(1);

    expect(listQuery.queryKey).toEqual(CREDENTIAL_QUERY_KEYS.byProvider("google"));
    await expect(listQuery.queryFn()).resolves.toEqual([{ id: "cred-1" }]);
    expect(hoisted.listMock).toHaveBeenCalledWith("google");

    expect(detailQuery.queryKey).toEqual(CREDENTIAL_QUERY_KEYS.detail("cred-1"));
    await expect(detailQuery.queryFn()).resolves.toEqual({ id: "cred-1" });
    expect(hoisted.getMock).toHaveBeenCalledWith("cred-1");
  });

  it("disables provider/detail queries when identifiers are empty", () => {
    renderHook(() => useCredentialsByProvider(""));
    renderHook(() => useCredential(""));

    const providerQuery = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      enabled: boolean;
    };
    const detailQuery = hoisted.useQueryMock.mock.calls[1][0] as {
      queryKey: unknown[];
      enabled: boolean;
    };

    expect(providerQuery.queryKey).toEqual(CREDENTIAL_QUERY_KEYS.byProvider(""));
    expect(providerQuery.enabled).toBe(false);
    expect(detailQuery.queryKey).toEqual(CREDENTIAL_QUERY_KEYS.detail(""));
    expect(detailQuery.enabled).toBe(false);
  });

  it("runs provider-filter queryFn when provider exists", async () => {
    hoisted.listMock.mockResolvedValue([{ id: "cred-provider" }]);
    renderHook(() => useCredentialsByProvider("openai"));

    const providerQuery = hoisted.useQueryMock.mock.calls[0][0] as {
      queryFn: () => Promise<unknown>;
      enabled: boolean;
    };
    await expect(providerQuery.queryFn()).resolves.toEqual([{ id: "cred-provider" }]);
    expect(providerQuery.enabled).toBe(true);
    expect(hoisted.listMock).toHaveBeenCalledWith("openai");
  });

  it("invalidates credentials and providers after creating credential", () => {
    renderHook(() => useCreateCredential());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onSuccess?: () => void;
    };

    mutationOptions.onSuccess?.();

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(1, {
      queryKey: CREDENTIAL_QUERY_KEYS.all,
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(2, {
      queryKey: MODEL_QUERY_KEYS.providers,
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Saved",
    });
  });

  it("shows destructive toast when updating credential fails", () => {
    renderHook(() => useUpdateCredential());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onError?: (error: unknown) => void;
    };

    mutationOptions.onError?.(new Error("boom"));

    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-api-error",
      variant: "destructive",
    });
  });

  it("executes create/update/delete mutationFns and success handlers", async () => {
    renderHook(() => useCreateCredential());
    const createOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      mutationFn: (payload: { provider: string }) => Promise<unknown>;
      onError?: (error: unknown) => void;
    };
    await createOptions.mutationFn({ provider: "openai" });
    createOptions.onError?.(new Error("create failed"));

    renderHook(() => useUpdateCredential());
    const updateOptions = hoisted.useMutationMock.mock.calls[1][0] as {
      mutationFn: (payload: {
        credentialId: string;
        data: { api_key: string };
      }) => Promise<unknown>;
      onSuccess?: () => void;
    };
    await updateOptions.mutationFn({ credentialId: "cred-1", data: { api_key: "x" } });
    updateOptions.onSuccess?.();

    renderHook(() => useDeleteCredential());
    const deleteOptions = hoisted.useMutationMock.mock.calls[2][0] as {
      mutationFn: (payload: {
        credentialId: string;
        options?: { delete_models?: boolean; migrate_to?: string };
      }) => Promise<unknown>;
    };
    await deleteOptions.mutationFn({
      credentialId: "cred-2",
      options: { delete_models: true, migrate_to: "other" },
    });

    expect(hoisted.createMock).toHaveBeenCalledWith({ provider: "openai" });
    expect(hoisted.updateMock).toHaveBeenCalledWith("cred-1", { api_key: "x" });
    expect(hoisted.deleteMock).toHaveBeenCalledWith("cred-2", {
      delete_models: true,
      migrate_to: "other",
    });
  });

  it("invalidates credentials/models/providers after deleting credential", () => {
    renderHook(() => useDeleteCredential());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onSuccess?: () => void;
    };

    mutationOptions.onSuccess?.();

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(1, {
      queryKey: CREDENTIAL_QUERY_KEYS.all,
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(2, {
      queryKey: MODEL_QUERY_KEYS.models,
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(3, {
      queryKey: MODEL_QUERY_KEYS.providers,
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Deleted",
    });
  });

  it("shows destructive toast when deleting credential fails", () => {
    renderHook(() => useDeleteCredential());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onError?: (error: unknown) => void;
    };

    mutationOptions.onError?.(new Error("delete failed"));

    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-api-error",
      variant: "destructive",
    });
  });

  it("tracks credential test results, supports clearResult, and handles failures", () => {
    hoisted.useMutationMock.mockImplementation((options: unknown) => {
      const typed = options as {
        onSuccess?: (
          result: { success: boolean; message?: string; provider: string },
          credentialId: string,
        ) => void;
        onError?: (error: unknown) => void;
      };

      return {
        mutate: (credentialId: string) => {
          if (credentialId === "cred-success") {
            typed.onSuccess?.({ provider: "google", success: true, message: "ok" }, credentialId);
            return;
          }
          if (credentialId === "cred-fail") {
            typed.onSuccess?.(
              { provider: "google", success: false, message: "provider rejected" },
              credentialId,
            );
            return;
          }
          typed.onError?.(new Error("network down"));
        },
        mutateAsync: vi.fn(),
        isPending: false,
      };
    });

    const { result } = renderHook(() => useTestCredential());

    act(() => {
      result.current.testCredential("cred-success");
    });

    expect(result.current.testResults["cred-success"]).toEqual({
      provider: "google",
      success: true,
      message: "ok",
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Connection ok",
    });

    act(() => {
      result.current.testCredential("cred-fail");
    });

    expect(result.current.testResults["cred-fail"]?.success).toBe(false);
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "provider rejected",
      variant: "destructive",
    });

    act(() => {
      result.current.clearResult("cred-fail");
    });

    expect(result.current.testResults["cred-fail"]).toBeUndefined();

    act(() => {
      result.current.testCredential("cred-error");
    });

    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-api-error",
      variant: "destructive",
    });
  });

  it("exposes credential test mutationFn and pending async passthrough", async () => {
    hoisted.testMock.mockResolvedValue({ provider: "google", success: true, message: "ok" });
    const mutateAsync = vi.fn();
    hoisted.useMutationMock.mockImplementation((options: unknown) => ({
      mutate: vi.fn(),
      mutateAsync,
      isPending: true,
      ...options,
    }));

    const { result } = renderHook(() => useTestCredential());
    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      mutationFn: (credentialId: string) => Promise<unknown>;
    };

    await expect(mutationOptions.mutationFn("cred-async")).resolves.toEqual({
      provider: "google",
      success: true,
      message: "ok",
    });
    expect(hoisted.testMock).toHaveBeenCalledWith("cred-async");
    expect(result.current.testCredentialAsync).toBe(mutateAsync);
    expect(result.current.isPending).toBe(true);
  });

  it("shows sync failure toast when model discovery fails", () => {
    renderHook(() => useDiscoverModels());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onError?: (error: unknown) => void;
    };

    mutationOptions.onError?.(new Error("discover failed"));

    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-api-error",
      variant: "destructive",
    });
  });

  it("executes discover/register mutationFns", async () => {
    renderHook(() => useDiscoverModels());
    const discoverOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      mutationFn: (credentialId: string) => Promise<unknown>;
    };
    await discoverOptions.mutationFn("cred-discover");

    renderHook(() => useRegisterModels());
    const registerOptions = hoisted.useMutationMock.mock.calls[1][0] as {
      mutationFn: (payload: {
        credentialId: string;
        models: Array<{ model_id: string; provider: string }>;
      }) => Promise<unknown>;
    };
    await registerOptions.mutationFn({
      credentialId: "cred-register",
      models: [{ model_id: "gemini-3.1-pro", provider: "google" }],
    });

    expect(hoisted.discoverMock).toHaveBeenCalledWith("cred-discover");
    expect(hoisted.registerModelsMock).toHaveBeenCalledWith("cred-register", {
      models: [{ model_id: "gemini-3.1-pro", provider: "google" }],
    });
  });

  it("invalidates caches and shows sync success when register creates models", () => {
    renderHook(() => useRegisterModels());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onSuccess?: (result: { created: number; existing: number }) => void;
    };

    mutationOptions.onSuccess?.({ created: 2, existing: 3 });

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(1, {
      queryKey: MODEL_QUERY_KEYS.models,
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(2, {
      queryKey: CREDENTIAL_QUERY_KEYS.all,
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Sync success",
    });
  });

  it("shows no-new sync toast and sync error fallback for register models", () => {
    renderHook(() => useRegisterModels());

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onSuccess?: (result: { created: number; existing: number }) => void;
      onError?: (error: unknown) => void;
    };

    mutationOptions.onSuccess?.({ created: 0, existing: 4 });
    mutationOptions.onError?.(new Error("register failed"));

    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "No new 4",
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-api-error",
      variant: "destructive",
    });
  });
});
