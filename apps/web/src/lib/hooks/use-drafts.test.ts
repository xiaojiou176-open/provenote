import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { draftsApi } from "@/lib/api/drafts";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { useNotebookDrafts } from "./use-drafts";

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
      draftCreateSuccess: "Draft created",
      draftRerunSuccess: "Draft rerun created",
      draftVerifySuccess: "Draft verified",
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

vi.mock("@/lib/api/drafts", () => ({
  draftsApi: {
    list: vi.fn(),
    create: vi.fn(),
    rerun: vi.fn(),
    verify: vi.fn(),
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

describe("useNotebookDrafts", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useQueryMock.mockImplementation((options: unknown) => options);
    hoisted.useMutationMock.mockImplementation((options: unknown) => options);
    hoisted.useQueryClientMock.mockReturnValue(hoisted.queryClient);
  });

  it("configures draft listing query with notebook key", async () => {
    renderHook(() => useNotebookDrafts("nb-1"));
    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      queryKey: unknown[];
      queryFn: () => Promise<unknown>;
    };

    await queryOptions.queryFn();

    expect(queryOptions.queryKey).toEqual(QUERY_KEYS.notebookDrafts("nb-1"));
    expect(draftsApi.list).toHaveBeenCalledWith("nb-1");
  });

  it("invalidates draft queries and shows translated toasts after create and rerun", async () => {
    renderHook(() => useNotebookDrafts("nb-2"));

    const createOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      mutationFn: (payload: { source_ids: string[] }) => Promise<unknown>;
      onSuccess: (data: { id: string }) => void;
    };
    const rerunOptions = hoisted.useMutationMock.mock.calls[1][0] as {
      mutationFn: (payload: {
        draftId: string;
        payload?: { language: string };
      }) => Promise<unknown>;
      onSuccess: (data: { id: string }) => void;
    };
    const verifyOptions = hoisted.useMutationMock.mock.calls[2][0] as {
      mutationFn: (draftId: string) => Promise<unknown>;
      onSuccess: (data: { id: string }) => void;
    };

    await createOptions.mutationFn({ source_ids: ["source:1"] });
    createOptions.onSuccess({ id: "draft-1" });

    await rerunOptions.mutationFn({ draftId: "draft-1", payload: { language: "en-US" } });
    rerunOptions.onSuccess({ id: "draft-2" });

    await verifyOptions.mutationFn("draft-2");
    verifyOptions.onSuccess({ id: "draft-2" });

    expect(draftsApi.create).toHaveBeenCalledWith("nb-2", { source_ids: ["source:1"] });
    expect(draftsApi.rerun).toHaveBeenCalledWith("draft-1", { language: "en-US" });
    expect(draftsApi.verify).toHaveBeenCalledWith("draft-2");
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.notebookDrafts("nb-2"),
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Draft created",
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Draft rerun created",
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Draft verified",
    });
  });

  it("refetches while a draft is active and stops polling when drafts are idle", () => {
    renderHook(() => useNotebookDrafts("nb-3"));

    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      refetchInterval: (query: { state: { data?: Array<{ status?: string }> } }) => number | false;
    };

    expect(
      queryOptions.refetchInterval({
        state: {
          data: [{ status: "queued" }],
        },
      }),
    ).toBe(2000);
    expect(
      queryOptions.refetchInterval({
        state: {
          data: [{ status: "completed" }],
        },
      }),
    ).toBe(false);
    expect(
      queryOptions.refetchInterval({
        state: {},
      }),
    ).toBe(false);
  });

  it("surfaces translated errors for create, rerun, and verify mutations", () => {
    renderHook(() => useNotebookDrafts("nb-4"));

    const createOptions = hoisted.useMutationMock.mock.calls[0][0] as {
      onError: (error: unknown) => void;
    };
    const rerunOptions = hoisted.useMutationMock.mock.calls[1][0] as {
      onError: (error: unknown) => void;
    };
    const verifyOptions = hoisted.useMutationMock.mock.calls[2][0] as {
      onError: (error: unknown) => void;
    };

    createOptions.onError(new Error("create failed"));
    rerunOptions.onError(new Error("rerun failed"));
    verifyOptions.onError(new Error("verify failed"));

    expect(hoisted.toastMock).toHaveBeenCalledTimes(3);
    expect(hoisted.toastMock).toHaveBeenNthCalledWith(1, {
      title: "Error",
      description: "resolved-error",
      variant: "destructive",
    });
    expect(hoisted.toastMock).toHaveBeenNthCalledWith(2, {
      title: "Error",
      description: "resolved-error",
      variant: "destructive",
    });
    expect(hoisted.toastMock).toHaveBeenNthCalledWith(3, {
      title: "Error",
      description: "resolved-error",
      variant: "destructive",
    });
  });
});
