import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QUERY_KEYS } from "@/lib/api/query-client";

const hoisted = vi.hoisted(() => ({
  getApiErrorKeyMock: vi.fn(),
  invalidateQueriesMock: vi.fn(),
  toastMock: vi.fn(),
  updateMock: vi.fn(),
  useMutationMock: vi.fn(),
  useQueryClientMock: vi.fn(),
  useQueryMock: vi.fn(),
  t: {
    common: {
      error: "Error",
      saveSuccess: "Saved",
      success: "Success",
    },
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

vi.mock("@/lib/api/settings", () => ({
  settingsApi: {
    get: vi.fn(),
    update: hoisted.updateMock,
  },
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

import { useSettings, useUpdateSettings } from "./use-settings";

describe("useSettings hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useQueryMock.mockImplementation((options: unknown) => options);
    hoisted.useMutationMock.mockImplementation((options: unknown) => options);
    hoisted.useQueryClientMock.mockReturnValue({
      invalidateQueries: hoisted.invalidateQueriesMock,
    });
    hoisted.getApiErrorKeyMock.mockReturnValue("resolved-api-error");
  });

  it("queries settings using the shared query key", () => {
    const { result } = renderHook(() => useSettings());
    const query = result.current;

    expect(query.queryKey).toEqual(QUERY_KEYS.settings);
    expect(query.queryFn).toBeTypeOf("function");
  });

  it("calls settingsApi.get from queryFn", async () => {
    hoisted.updateMock.mockResolvedValue(undefined);
    const getMock = vi.fn().mockResolvedValue({ theme: "dark" });
    const { settingsApi } = await import("@/lib/api/settings");
    vi.mocked(settingsApi.get).mockImplementation(getMock);

    const { result } = renderHook(() => useSettings());
    await result.current.queryFn();

    expect(getMock).toHaveBeenCalledTimes(1);
  });

  it("invalidates settings and shows success toast on update success", () => {
    const { result } = renderHook(() => useUpdateSettings());
    result.current.onSuccess();

    expect(hoisted.invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.settings,
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Saved",
    });
  });

  it("shows destructive toast on update failure", () => {
    const { result } = renderHook(() => useUpdateSettings());
    const boom = new Error("boom");
    result.current.onError(boom);

    expect(hoisted.getApiErrorKeyMock).toHaveBeenCalledWith(boom, "Error");
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-api-error",
      variant: "destructive",
    });
  });

  it("calls settingsApi.update through mutationFn", async () => {
    hoisted.updateMock.mockResolvedValue({ ok: true });
    const payload = { language: "zh-CN" };
    const { result } = renderHook(() => useUpdateSettings());

    await result.current.mutationFn(payload);

    expect(hoisted.updateMock).toHaveBeenCalledWith(payload);
  });
});
