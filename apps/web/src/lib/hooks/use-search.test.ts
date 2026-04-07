import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  errorMock: vi.fn(),
  searchMock: vi.fn(),
  useMutationMock: vi.fn(),
  t: Object.assign((key: string) => key, {
    apiErrors: {
      searchFailed: "Search failed",
    },
  }),
}));

vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useMutation: hoisted.useMutationMock,
  };
});

vi.mock("sonner", () => ({
  toast: {
    error: hoisted.errorMock,
  },
}));

vi.mock("@/lib/api/search", () => ({
  searchApi: {
    search: hoisted.searchMock,
  },
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: hoisted.t,
  }),
}));

import { useSearch } from "./use-search";

describe("useSearch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useMutationMock.mockImplementation((options: unknown) => options);
  });

  it("sorts search results by final score descending", async () => {
    hoisted.searchMock.mockResolvedValue({
      results: [
        { id: "a", similarity: 0.3 },
        { id: "b", relevance: 0.9 },
        { id: "c", score: 0.5 },
      ],
      total_count: 3,
    });

    const mutation = useSearch();
    const result = await mutation.mutationFn({
      query: "hello",
      type: "text",
      search_sources: true,
      search_notes: false,
    });

    expect(result.results.map((item) => item.id)).toEqual(["b", "c", "a"]);
    expect(result.results[0].final_score).toBe(0.9);
  });

  it("shows mapped error toast when request fails", () => {
    const mutation = useSearch();
    mutation.onError(new Error("Source not found"));

    expect(hoisted.errorMock).toHaveBeenCalledWith("apiErrors.searchFailed", {
      description: "apiErrors.sourceNotFound",
    });
  });
});
