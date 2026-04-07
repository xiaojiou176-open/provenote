import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  getMock: vi.fn(),
  useQueryMock: vi.fn(),
  invalidateQueries: vi.fn(),
  useAppMutationMock: vi.fn(),
}));

vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: hoisted.useQueryMock,
    useQueryClient: () => ({ invalidateQueries: hoisted.invalidateQueries }),
  };
});

vi.mock("@/lib/api/insights", () => ({
  insightsApi: {
    get: hoisted.getMock,
    saveAsNote: vi.fn(),
  },
}));

vi.mock("@/lib/hooks/use-app-mutation", () => ({
  useAppMutation: hoisted.useAppMutationMock,
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      common: { success: "Success", error: "Error" },
      sources: {
        saveInsightAsNoteSuccess: "Saved",
        saveInsightAsNoteFailed: "Failed",
      },
    },
  }),
}));

import { insightsApi } from "@/lib/api/insights";
import { useInsight, useSaveInsightAsNote } from "./use-insights";

describe("useInsight", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useQueryMock.mockImplementation((options: unknown) => options);
    hoisted.useAppMutationMock.mockImplementation((options: unknown) => options);
  });

  it("builds enabled query for a valid insight id", async () => {
    hoisted.getMock.mockResolvedValue({ id: "insight-1" });
    const query = useInsight("insight-1");

    expect(query.queryKey).toEqual(["insights", "insight-1"]);
    expect(query.enabled).toBe(true);
    await expect(query.queryFn()).resolves.toEqual({ id: "insight-1" });
    expect(hoisted.getMock).toHaveBeenCalledWith("insight-1");
  });

  it("disables query when id is empty or explicitly disabled", () => {
    const emptyQuery = useInsight("");
    const disabledQuery = useInsight("insight-2", { enabled: false });

    expect(emptyQuery.enabled).toBe(false);
    expect(disabledQuery.enabled).toBe(false);
  });

  it("builds save-as-note mutation with notebook invalidation and toasts", async () => {
    vi.mocked(insightsApi.saveAsNote).mockResolvedValue({
      id: "note:1",
    } as never);
    const mutation = useSaveInsightAsNote();

    await expect(
      mutation.mutationFn({
        insightId: "source_insight:1",
        notebookId: "notebook:1",
      }),
    ).resolves.toEqual({ id: "note:1" });

    await mutation.onSuccess?.(
      { id: "note:1" },
      { insightId: "source_insight:1", notebookId: "notebook:1" },
      undefined,
    );

    expect(insightsApi.saveAsNote).toHaveBeenCalledWith("source_insight:1", {
      notebook_id: "notebook:1",
    });
    expect(hoisted.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ["notes", "notebook:1"],
    });
    expect(mutation.successToast).toEqual({
      title: "Success",
      description: "Saved",
    });
  });
});
