import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AddExistingSourceDialog } from "./AddExistingSourceDialog";

const listMock = vi.fn();
const searchMock = vi.fn();
const mutateAsyncMock = vi.fn();
const useSourcesMock = vi.fn();
let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

const t = {
  sources: {
    addExistingTitle: "Add existing source",
    addExistingDesc: "Link sources into notebook",
    searchPlaceholder: "Search sources",
    noNotebooksFound: "No sources",
    added: "Added {date}",
    showingFirst100: "Showing first 100",
    selectedCount: "Selected {count}",
    untitledSource: "Untitled source",
  },
  common: {
    loading: "Loading",
    linked: "Linked",
    cancel: "Cancel",
    addSelected: "Add selected",
    adding: "Adding",
  },
};

vi.mock("use-debounce", () => ({
  useDebounce: (value: string) => [value],
}));

vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({ open, children }: { open: boolean; children: ReactNode }) =>
    open ? <div>{children}</div> : null,
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  DialogFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/scroll-area", () => ({
  ScrollArea: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t }),
}));

vi.mock("@/lib/api/sources", () => ({
  sourcesApi: {
    list: (...args: unknown[]) => listMock(...args),
  },
}));

vi.mock("@/lib/api/search", () => ({
  searchApi: {
    search: (...args: unknown[]) => searchMock(...args),
  },
}));

vi.mock("@/lib/hooks/use-sources", () => ({
  useSources: (...args: unknown[]) => useSourcesMock(...args),
  useAddSourcesToNotebook: () => ({
    mutateAsync: (...args: unknown[]) => mutateAsyncMock(...args),
    isPending: false,
  }),
}));

describe("AddExistingSourceDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    useSourcesMock.mockReturnValue({
      data: [
        {
          id: "source-1",
          title: "Already linked",
          asset: null,
          embedded: false,
          embedded_chunks: 0,
          insights_count: 0,
          created: "2026-01-01T00:00:00.000Z",
          updated: "2026-01-01T00:00:00.000Z",
        },
      ],
    });
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("loads all sources, disables linked source, and adds selected source", async () => {
    listMock.mockResolvedValue([
      {
        id: "source-1",
        title: "Already linked",
        asset: null,
        embedded: false,
        embedded_chunks: 0,
        insights_count: 0,
        created: "2026-01-01T00:00:00.000Z",
        updated: "2026-01-01T00:00:00.000Z",
      },
      {
        id: "source-2",
        title: "Add me",
        asset: { url: "https://example.com" },
        embedded: false,
        embedded_chunks: 0,
        insights_count: 0,
        created: "2026-01-02T00:00:00.000Z",
        updated: "2026-01-02T00:00:00.000Z",
      },
    ]);
    mutateAsyncMock.mockResolvedValue(undefined);

    const onOpenChange = vi.fn();
    const onSuccess = vi.fn();

    render(
      <AddExistingSourceDialog
        open
        onOpenChange={onOpenChange}
        notebookId="nb-1"
        onSuccess={onSuccess}
      />,
    );

    await screen.findByText("Already linked");

    expect(listMock).toHaveBeenCalledWith({
      limit: 100,
      offset: 0,
      sort_by: "created",
      sort_order: "desc",
    });
    expect(screen.getByText("Linked")).toBeInTheDocument();

    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes[0]).toBeDisabled();

    fireEvent.click(checkboxes[1]);
    fireEvent.click(screen.getByRole("button", { name: "Add selected" }));

    await waitFor(() => {
      expect(mutateAsyncMock).toHaveBeenCalledWith({ notebookId: "nb-1", sourceIds: ["source-2"] });
      expect(onOpenChange).toHaveBeenCalledWith(false);
      expect(onSuccess).toHaveBeenCalledTimes(1);
    });
  });

  it("searches sources with debounced input and shows search results", async () => {
    listMock.mockResolvedValue([]);
    searchMock.mockResolvedValue({
      results: [
        {
          parent_id: "source-search-1",
          title: "Search hit",
          created: "2026-01-03T00:00:00.000Z",
          updated: "2026-01-03T00:00:00.000Z",
        },
      ],
    });

    render(<AddExistingSourceDialog open onOpenChange={vi.fn()} notebookId="nb-1" />);

    fireEvent.change(screen.getByPlaceholderText("Search sources"), {
      target: { value: "context" },
    });

    await waitFor(() => {
      expect(searchMock).toHaveBeenCalledWith({
        query: "context",
        type: "text",
        search_sources: true,
        search_notes: false,
        limit: 100,
        minimum_score: 0.01,
      });
    });

    expect(await screen.findByText("Search hit")).toBeInTheDocument();
  });

  it("falls back to all sources when search fails", async () => {
    listMock.mockResolvedValue([
      {
        id: "source-1",
        title: "Fallback source",
        asset: null,
        embedded: false,
        embedded_chunks: 0,
        insights_count: 0,
        created: "2026-01-01T00:00:00.000Z",
        updated: "2026-01-01T00:00:00.000Z",
      },
    ]);
    searchMock.mockRejectedValue(new Error("search failed"));

    render(<AddExistingSourceDialog open onOpenChange={vi.fn()} notebookId="nb-1" />);

    await screen.findByText("Fallback source");

    fireEvent.change(screen.getByPlaceholderText("Search sources"), {
      target: { value: "boom" },
    });

    await waitFor(() => {
      expect(searchMock).toHaveBeenCalledTimes(1);
      expect(screen.getByText("Fallback source")).toBeInTheDocument();
    });
  });

  it("keeps dialog open when add operation fails", async () => {
    listMock.mockResolvedValue([
      {
        id: "source-2",
        title: "Cannot add",
        asset: null,
        embedded: false,
        embedded_chunks: 0,
        insights_count: 0,
        created: "2026-01-01T00:00:00.000Z",
        updated: "2026-01-01T00:00:00.000Z",
      },
    ]);
    mutateAsyncMock.mockRejectedValue(new Error("add failed"));

    const onOpenChange = vi.fn();

    render(<AddExistingSourceDialog open onOpenChange={onOpenChange} notebookId="nb-1" />);

    await screen.findByText("Cannot add");

    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Add selected" }));

    await waitFor(() => {
      expect(mutateAsyncMock).toHaveBeenCalledTimes(1);
    });
    expect(onOpenChange).not.toHaveBeenCalledWith(false);
  });
});
