import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  getRunMock: vi.fn(),
  listRunsMock: vi.fn(),
  repairClaimMock: vi.fn(),
  repairSectionMock: vi.fn(),
  startRunMock: vi.fn(),
  getApiErrorMessageMock: vi.fn(),
  invalidateQueriesMock: vi.fn(),
  toastMock: vi.fn(),
  useMutationMock: vi.fn(),
  useQueryClientMock: vi.fn(),
  useQueryMock: vi.fn(),
  t: Object.assign((key: string) => key, {
    common: {
      success: "Success",
      error: "Error",
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

vi.mock("@/lib/api/auditable", () => ({
  auditableApi: {
    listRuns: hoisted.listRunsMock,
    getRun: hoisted.getRunMock,
    repairClaim: hoisted.repairClaimMock,
    repairSection: hoisted.repairSectionMock,
    startRun: hoisted.startRunMock,
  },
}));

vi.mock("@/lib/hooks/use-toast", () => ({
  useToast: () => ({
    toast: hoisted.toastMock,
  }),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: hoisted.t,
  }),
}));

vi.mock("@/lib/utils/error-handler", () => ({
  getApiErrorMessage: hoisted.getApiErrorMessageMock,
}));

import {
  AUDITABLE_QUERY_KEYS,
  getLatestAuditableRun,
  useAuditableRuns,
  useStartAuditableRun,
} from "./use-auditable-runs";

describe("use-auditable-runs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useQueryMock.mockImplementation((options: unknown) => options);
    hoisted.useMutationMock.mockImplementation((options: unknown) => options);
    hoisted.useQueryClientMock.mockReturnValue({
      invalidateQueries: hoisted.invalidateQueriesMock,
    });
    hoisted.getApiErrorMessageMock.mockReturnValue("resolved-error-message");
  });

  it("sorts latest run by newest updated timestamp", () => {
    expect(
      getLatestAuditableRun([
        { id: "run-1", created: "2025-01-01T00:00:00Z", updated: "2025-01-01T00:00:00Z" },
        { id: "run-2", created: "2025-01-02T00:00:00Z", updated: "2025-01-03T00:00:00Z" },
      ] as never),
    ).toMatchObject({ id: "run-2" });
  });

  it("returns null for empty run list and handles invalid timestamps", () => {
    expect(getLatestAuditableRun([])).toBeNull();
    expect(
      getLatestAuditableRun([
        { id: "invalid-ts", created: "bad-date" },
        { id: "valid-ts", created: "2025-01-01T00:00:00Z" },
      ] as never),
    ).toMatchObject({ id: "valid-ts" });
  });

  it("builds disabled queries when source id is missing and exposes refetch intervals", () => {
    renderHook(() => useAuditableRuns(""));

    const runsQueryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      enabled: boolean;
      refetchInterval: (query: { state: { data?: unknown } }) => number | false;
    };
    const latestRunQueryOptions = hoisted.useQueryMock.mock.calls[1][0] as {
      enabled: boolean;
      refetchInterval: (query: { state: { data?: unknown } }) => number | false;
    };

    expect(runsQueryOptions.enabled).toBe(false);
    expect(latestRunQueryOptions.enabled).toBe(false);
    expect(
      runsQueryOptions.refetchInterval({
        state: { data: [{ id: "run-1", status: "running", updated: "2025-01-03T00:00:00Z" }] },
      }),
    ).toBe(2000);
    expect(
      runsQueryOptions.refetchInterval({
        state: { data: [{ id: "run-2", status: "completed", updated: "2025-01-04T00:00:00Z" }] },
      }),
    ).toBe(false);
    expect(
      latestRunQueryOptions.refetchInterval({ state: { data: { id: "run-3", status: "queued" } } }),
    ).toBe(2000);
    expect(
      latestRunQueryOptions.refetchInterval({
        state: { data: { id: "run-4", status: "failed" } },
      }),
    ).toBe(false);
  });

  it("builds runs and latest-run queries with active polling only for queued/running states", () => {
    hoisted.useQueryMock
      .mockReturnValueOnce({
        data: [{ id: "run-2", status: "queued", updated: "2025-01-03T00:00:00Z" }],
        isLoading: false,
        isFetching: false,
        error: null,
        refetch: vi.fn(),
      })
      .mockImplementationOnce((options: any) => options);

    const { result } = renderHook(() => useAuditableRuns("source-1"));

    expect(result.current.runs).toHaveLength(1);
    expect(result.current.latestRun).toMatchObject({ id: "run-2", status: "queued" });
    expect(AUDITABLE_QUERY_KEYS.runs("source-1")).toEqual([
      "sources",
      "source-1",
      "auditable-runs",
    ]);
    expect(AUDITABLE_QUERY_KEYS.run("source-1", "run-2")).toEqual([
      "sources",
      "source-1",
      "auditable-runs",
      "run-2",
    ]);
  });

  it("starts a run, invalidates queries, and shows success toast", async () => {
    hoisted.startRunMock.mockResolvedValue({ id: "run-9" });

    const mutation = useStartAuditableRun("source-9");
    await mutation.mutationFn({ language: "en" });
    mutation.onSuccess({ id: "run-9" });

    expect(hoisted.startRunMock).toHaveBeenCalledWith("source-9", { language: "en" });
    expect(hoisted.invalidateQueriesMock).toHaveBeenCalledTimes(2);
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Auditable markdown run started.",
    });
  });

  it("uses empty payload fallback and prefers latest-run query data over listed run", async () => {
    hoisted.useQueryMock
      .mockReturnValueOnce({
        data: [{ id: "run-old", status: "queued", updated: "2025-01-01T00:00:00Z" }],
        isLoading: false,
        isFetching: false,
        error: null,
        refetch: vi.fn(),
      })
      .mockReturnValueOnce({
        data: { id: "run-fresh", status: "running" },
        isLoading: false,
        isFetching: false,
        error: null,
      });

    const { result } = renderHook(() => useAuditableRuns("source-2"));
    expect(result.current.latestRun).toMatchObject({ id: "run-fresh" });

    const mutation = useStartAuditableRun("source-2");
    await mutation.mutationFn();

    expect(hoisted.startRunMock).toHaveBeenCalledWith("source-2", {});
  });

  it("prefers runsQuery error over latestRunQuery error in returned state", () => {
    const refetchMock = vi.fn();
    hoisted.useQueryMock
      .mockReturnValueOnce({
        data: [],
        isLoading: false,
        isFetching: false,
        error: new Error("runs-error"),
        refetch: refetchMock,
      })
      .mockReturnValueOnce({
        data: null,
        isLoading: false,
        isFetching: false,
        error: new Error("latest-error"),
      });

    const { result } = renderHook(() => useAuditableRuns("source-3"));

    expect(result.current.error).toBeInstanceOf(Error);
    expect((result.current.error as Error)?.message).toBe("runs-error");
    expect(result.current.refetchRuns).toBe(refetchMock);
  });

  it("throws for missing source id and emits destructive toast on error", () => {
    const mutation = useStartAuditableRun("");

    expect(() => mutation.mutationFn()).toThrow(
      "Source id is required to start auditable markdown run",
    );

    mutation.onError(new Error("boom"));
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });
  });

  it("repairs a claim, invalidates both queries, and emits a success toast", async () => {
    hoisted.useQueryMock
      .mockReturnValueOnce({
        data: [{ id: "run-1", status: "completed", updated: "2025-01-01T00:00:00Z" }],
        isLoading: false,
        isFetching: false,
        error: null,
        refetch: vi.fn(),
      })
      .mockReturnValueOnce({
        data: { id: "run-1", status: "completed" },
        isLoading: false,
        isFetching: false,
        error: null,
      });
    hoisted.repairClaimMock.mockResolvedValue({ id: "run-claim" });

    const { result } = renderHook(() => useAuditableRuns("source-4"));

    await result.current.repairClaim.mutationFn({ runId: "run-1", targetIndex: 3 });
    result.current.repairClaim.onSuccess({ id: "run-claim" });

    expect(hoisted.repairClaimMock).toHaveBeenCalledWith("run-1", { target_index: 3 });
    expect(hoisted.invalidateQueriesMock).toHaveBeenNthCalledWith(1, {
      queryKey: AUDITABLE_QUERY_KEYS.runs("source-4"),
    });
    expect(hoisted.invalidateQueriesMock).toHaveBeenNthCalledWith(2, {
      queryKey: AUDITABLE_QUERY_KEYS.run("source-4", "run-claim"),
    });
    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Claim repaired into a new auditable run.",
    });
  });

  it("repairs a section and emits destructive toast when repair mutations fail", async () => {
    hoisted.useQueryMock
      .mockReturnValueOnce({
        data: [{ id: "run-2", status: "completed", updated: "2025-01-02T00:00:00Z" }],
        isLoading: false,
        isFetching: false,
        error: null,
        refetch: vi.fn(),
      })
      .mockReturnValueOnce({
        data: { id: "run-2", status: "completed" },
        isLoading: false,
        isFetching: false,
        error: null,
      });
    hoisted.repairSectionMock.mockResolvedValue({ id: "run-section" });

    const { result } = renderHook(() => useAuditableRuns("source-5"));

    await result.current.repairSection.mutationFn({ runId: "run-2", targetIndex: 5 });
    result.current.repairSection.onSuccess({ id: "run-section" });
    result.current.repairClaim.onError(new Error("claim-fail"));
    result.current.repairSection.onError(new Error("section-fail"));

    expect(hoisted.repairSectionMock).toHaveBeenCalledWith("run-2", { target_index: 5 });
    expect(hoisted.invalidateQueriesMock).toHaveBeenNthCalledWith(1, {
      queryKey: AUDITABLE_QUERY_KEYS.runs("source-5"),
    });
    expect(hoisted.invalidateQueriesMock).toHaveBeenNthCalledWith(2, {
      queryKey: AUDITABLE_QUERY_KEYS.run("source-5", "run-section"),
    });
    expect(hoisted.toastMock).toHaveBeenNthCalledWith(1, {
      title: "Success",
      description: "Section repaired into a new auditable run.",
    });
    expect(hoisted.toastMock).toHaveBeenNthCalledWith(2, {
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });
    expect(hoisted.toastMock).toHaveBeenNthCalledWith(3, {
      title: "Error",
      description: "resolved-error-message",
      variant: "destructive",
    });
  });
});
