import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  useMutationMock: vi.fn(),
  useToastMock: vi.fn(),
  toastMock: vi.fn(),
}));

vi.mock("@tanstack/react-query", () => ({
  useMutation: hoisted.useMutationMock,
}));

vi.mock("@/lib/hooks/use-toast", () => ({
  useToast: hoisted.useToastMock,
}));

import { useAppMutation } from "./use-app-mutation";

type SuccessHandler = (
  data: string,
  variables: { id: string },
  mutationContext: unknown,
) => Promise<void>;

type ErrorHandler = (
  error: unknown,
  variables: { id: string },
  mutationContext: unknown,
) => Promise<void>;

describe("useAppMutation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useToastMock.mockReturnValue({ toast: hoisted.toastMock });
    hoisted.useMutationMock.mockImplementation((options: unknown) => options);
  });

  it("runs onSuccess and success toast payload", async () => {
    const onSuccess = vi.fn().mockResolvedValue(undefined);
    renderHook(() =>
      useAppMutation<string, { id: string }>({
        mutationFn: async () => "ok",
        onSuccess,
        successToast: (data, variables) => ({
          title: `Saved ${variables.id}`,
          description: data,
        }),
      }),
    );

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onSuccess: SuccessHandler;
    };
    await mutationOptions.onSuccess("done", { id: "42" }, undefined);

    expect(onSuccess).toHaveBeenCalledWith("done", { id: "42" }, undefined);
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Saved 42",
      description: "done",
    });
  });

  it("runs onError and error toast payload", async () => {
    const onError = vi.fn().mockResolvedValue(undefined);
    renderHook(() =>
      useAppMutation<string, { id: string }>({
        mutationFn: async () => "ok",
        onError,
        errorToast: (error, variables) => ({
          title: `Failed ${variables.id}`,
          description: String(error),
          variant: "destructive",
        }),
      }),
    );

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onError: ErrorHandler;
    };
    await mutationOptions.onError(new Error("boom"), { id: "99" }, undefined);

    expect(onError).toHaveBeenCalled();
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Failed 99",
      description: "Error: boom",
      variant: "destructive",
    });
  });

  it("skips toast when factory returns null and keeps mutation options", async () => {
    renderHook(() =>
      useAppMutation<string, { id: string }>({
        mutationFn: async () => "ok",
        mutationKey: ["save-item"],
        successToast: () => null,
      }),
    );

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      mutationKey: string[];
      onSuccess: SuccessHandler;
    };
    expect(mutationOptions.mutationKey).toEqual(["save-item"]);

    await mutationOptions.onSuccess("done", { id: "7" }, undefined);
    expect(hoisted.toastMock).not.toHaveBeenCalled();
  });

  it("supports static success toast config object", async () => {
    renderHook(() =>
      useAppMutation<string, { id: string }>({
        mutationFn: async () => "ok",
        successToast: {
          title: "Saved",
          description: "static",
        },
      }),
    );

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onSuccess: SuccessHandler;
    };
    await mutationOptions.onSuccess("done", { id: "100" }, undefined);

    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Saved",
      description: "static",
    });
  });

  it("does not toast on error when errorToast is not configured", async () => {
    renderHook(() =>
      useAppMutation<string, { id: string }>({
        mutationFn: async () => "ok",
      }),
    );

    const mutationOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onError: ErrorHandler;
    };
    await mutationOptions.onError(new Error("boom"), { id: "404" }, undefined);

    expect(hoisted.toastMock).not.toHaveBeenCalled();
  });
});
