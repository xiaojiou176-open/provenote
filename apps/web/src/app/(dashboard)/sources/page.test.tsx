import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import SourcesPage from "./page";

const SLOW_TEST_TIMEOUT_MS = 15_000;

const pushMock = vi.fn();
const listMock = vi.fn();
const deleteMock = vi.fn();
const toastErrorMock = vi.fn();
const toastSuccessMock = vi.fn();
const openSourceDialogMock = vi.fn();
let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

function buildSource(id: string, overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id,
    title: `Source ${id}`,
    asset: null,
    embedded: false,
    embedded_chunks: 0,
    insights_count: 0,
    created: "2026-01-01T00:00:00.000Z",
    updated: "2026-01-02T00:00:00.000Z",
    ...overrides,
  };
}

function buildPage(size: number, prefix = "source") {
  return Array.from({ length: size }, (_, index) =>
    buildSource(`${prefix}-${index + 1}`, { title: `Source ${index + 1}` }),
  );
}

function createDeferred<T>() {
  let resolvePromise!: (value: T) => void;
  const promise = new Promise<T>((resolve) => {
    resolvePromise = resolve;
  });
  return { promise, resolve: resolvePromise };
}

const t = Object.assign((key: string) => `translated:${key}`, {
  common: {
    retry: "Retry",
    type: "Type",
    title: "Title",
    created_label: "Created",
    actions: "Actions",
    delete: "Delete",
    processing: "Processing",
  },
  sources: {
    failedToLoad: "Failed to load",
    deleteSuccess: "Delete success",
    delete: "Delete source",
    deleteConfirmWithTitle: "Delete {title}?",
    untitledSource: "Untitled source",
    noSourcesYet: "No sources yet",
    allSourcesDescShort: "Add your first source",
    allSources: "All sources",
    allSourcesDesc: "All sources description",
    outcomePathTitle: "Outcome path",
    outcomePathDescription: "Outcome path description",
    outcomeNotebookDraft: "Notebook draft",
    outcomeCreateDraftDescription: "Draft description",
    processDescription: "Process description",
    insightsDesc: "Insights description",
    viewSource: "View Source",
    notEmbedded: "Not Embedded",
    insightsCount: "{count} insights",
    addSource: "Add Source",
    createFirstSource: "Create first source",
    loadingMore: "Loading more",
    insights: "Insights",
    embedded: "Embedded",
    yes: "Yes",
    no: "No",
    type: {
      link: "Link",
      file: "File",
      text: "Text",
    },
  },
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock("date-fns", () => ({
  formatDistanceToNow: vi.fn(() => "moments ago"),
}));

vi.mock("@/components/layout/AppShell", () => ({
  AppShell: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/providers/CreateDialogsProvider", () => ({
  useCreateDialogs: () => ({
    openSourceDialog: openSourceDialogMock,
    openNotebookDialog: vi.fn(),
    openPodcastDialog: vi.fn(),
  }),
}));

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

vi.mock("@/components/common/EmptyState", () => ({
  EmptyState: ({ title }: { title: string }) => <div data-testid="empty-state">{title}</div>,
}));

vi.mock("@/components/common/ConfirmDialog", () => ({
  ConfirmDialog: ({
    open,
    title,
    description,
    onConfirm,
    onOpenChange,
  }: {
    open: boolean;
    title: string;
    description: string;
    onConfirm: () => Promise<void>;
    onOpenChange: (open: boolean) => void;
  }) =>
    open ? (
      <div data-testid="confirm-dialog">
        <p>{title}</p>
        <p>{description}</p>
        <button onClick={() => void onConfirm()} type="button">
          confirm-delete
        </button>
        <button onClick={() => onOpenChange(false)} type="button">
          cancel-delete
        </button>
        <button onClick={() => void onConfirm()} type="button">
          force-confirm
        </button>
      </div>
    ) : (
      <button onClick={() => void onConfirm()} type="button">
        force-confirm
      </button>
    ),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t,
    language: "en-US",
  }),
}));

vi.mock("@/lib/utils/date-locale", () => ({
  getDateLocale: vi.fn(() => undefined),
}));

vi.mock("@/lib/utils/error-handler", () => ({
  getApiErrorKey: vi.fn(() => "services.api.errors.generic"),
}));

vi.mock("@/lib/api/sources", () => ({
  sourcesApi: {
    list: (...args: unknown[]) => listMock(...args),
    delete: (...args: unknown[]) => deleteMock(...args),
  },
}));

vi.mock("sonner", () => ({
  toast: {
    error: (...args: unknown[]) => toastErrorMock(...args),
    success: (...args: unknown[]) => toastSuccessMock(...args),
  },
}));

describe("SourcesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    listMock.mockReset();
    deleteMock.mockReset();
    pushMock.mockReset();
    toastErrorMock.mockReset();
    toastSuccessMock.mockReset();
    openSourceDialogMock.mockReset();
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    vi.useRealTimers();
  });

  it(
    "renders list, supports keyboard navigation, and opens selected source",
    { timeout: SLOW_TEST_TIMEOUT_MS },
    async () => {
      listMock.mockResolvedValue([
        {
          id: "source-1",
          title: "Source One",
          asset: null,
          embedded: true,
          embedded_chunks: 0,
          insights_count: 1,
          created: "2026-01-01T00:00:00.000Z",
          updated: "2026-01-02T00:00:00.000Z",
        },
        {
          id: "source-2",
          title: "Source Two",
          asset: { url: "https://example.com" },
          embedded: false,
          embedded_chunks: 0,
          insights_count: 0,
          created: "2026-01-03T00:00:00.000Z",
          updated: "2026-01-04T00:00:00.000Z",
        },
      ]);

      render(<SourcesPage />);

      await screen.findByTestId("source-row-source-1");

      const tableRegion = screen.getByRole("region", { name: "All sources" });
      tableRegion.focus();

      fireEvent.keyDown(tableRegion, { key: "ArrowDown" });
      fireEvent.keyDown(tableRegion, { key: "Enter" });

      expect(pushMock).toHaveBeenCalledWith("/sources/source-2");
    },
  );

  it("toggles created sort order and refetches", { timeout: SLOW_TEST_TIMEOUT_MS }, async () => {
    listMock.mockResolvedValue([
      {
        id: "source-1",
        title: "Sortable",
        asset: null,
        embedded: false,
        embedded_chunks: 0,
        insights_count: 0,
        created: "2026-01-01T00:00:00.000Z",
        updated: "2026-01-02T00:00:00.000Z",
      },
    ]);

    render(<SourcesPage />);

    await screen.findByTestId("source-row-source-1");

    const createdButton = screen.getByRole("button", { name: /Created/ });

    fireEvent.click(createdButton);
    await waitFor(() => {
      expect(document.querySelector("th[aria-sort]")).toHaveAttribute("aria-sort", "descending");
    });

    fireEvent.click(screen.getByRole("button", { name: /Created/ }));
    await waitFor(() => {
      expect(document.querySelector("th[aria-sort]")).toHaveAttribute("aria-sort", "ascending");
    });

    fireEvent.click(screen.getByRole("button", { name: /Created/ }));
    await waitFor(() => {
      expect(document.querySelector("th[aria-sort]")).toHaveAttribute("aria-sort", "descending");
    });
  });

  it("deletes source on confirm and removes row", async () => {
    listMock.mockResolvedValue([
      {
        id: "source-1",
        title: "Delete Me",
        asset: null,
        embedded: false,
        embedded_chunks: 0,
        insights_count: 0,
        created: "2026-01-01T00:00:00.000Z",
        updated: "2026-01-02T00:00:00.000Z",
      },
    ]);
    deleteMock.mockResolvedValue(undefined);

    render(<SourcesPage />);

    await screen.findByTestId("source-row-source-1");

    fireEvent.click(screen.getByRole("button", { name: "Delete: Delete Me" }));
    fireEvent.click(screen.getByRole("button", { name: "confirm-delete" }));

    await waitFor(() => {
      expect(deleteMock).toHaveBeenCalledWith("source-1");
      expect(screen.queryByTestId("source-row-source-1")).not.toBeInTheDocument();
    });

    expect(toastSuccessMock).toHaveBeenCalledWith("Delete success");
  });

  it("shows error state and retries fetch", async () => {
    listMock.mockRejectedValueOnce(new Error("network")).mockResolvedValueOnce([]);

    render(<SourcesPage />);

    await screen.findByText("Failed to load");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() => {
      expect(listMock).toHaveBeenCalledTimes(2);
      expect(screen.getByTestId("empty-state")).toHaveTextContent("No sources yet");
    });

    expect(toastErrorMock).toHaveBeenCalledWith("Failed to load");
  });

  it("opens the add-source dialog from the first-success shell", async () => {
    listMock.mockResolvedValue([buildSource("source-1", { title: "Shell source" })]);

    render(<SourcesPage />);

    await screen.findByTestId("source-row-source-1");
    fireEvent.click(screen.getByRole("button", { name: "Add Source" }));

    expect(openSourceDialogMock).toHaveBeenCalledTimes(1);
  });

  it("opens the latest updated source from the first-success shell", async () => {
    listMock.mockResolvedValue([
      buildSource("source-1", {
        title: "Older source",
        updated: "2026-01-02T00:00:00.000Z",
      }),
      buildSource("source-2", {
        title: "Latest source",
        updated: "2026-01-05T00:00:00.000Z",
      }),
    ]);

    render(<SourcesPage />);

    await screen.findByTestId("source-row-source-1");
    fireEvent.click(screen.getByRole("button", { name: "View Source: Latest source" }));

    expect(pushMock).toHaveBeenCalledWith("/sources/source-2");
  });

  it("reports delete errors via translated api key", async () => {
    listMock.mockResolvedValue([
      {
        id: "source-1",
        title: "Fail Delete",
        asset: null,
        embedded: false,
        embedded_chunks: 0,
        insights_count: 0,
        created: "2026-01-01T00:00:00.000Z",
        updated: "2026-01-02T00:00:00.000Z",
      },
    ]);
    deleteMock.mockRejectedValue({ response: { data: { detail: "boom" } } });

    render(<SourcesPage />);

    await screen.findByTestId("source-row-source-1");
    fireEvent.click(screen.getByRole("button", { name: "Delete: Fail Delete" }));
    fireEvent.click(screen.getByRole("button", { name: "confirm-delete" }));

    await waitFor(() => {
      expect(toastErrorMock).toHaveBeenCalledWith("translated:services.api.errors.generic");
    });
  });

  it("opens delete dialog and keeps row when delete is cancelled", async () => {
    listMock.mockResolvedValue([buildSource("source-1", { title: "Keep Me" })]);

    render(<SourcesPage />);

    await screen.findByTestId("source-row-source-1");
    fireEvent.click(screen.getByRole("button", { name: "Delete: Keep Me" }));

    expect(screen.getByTestId("confirm-dialog")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "cancel-delete" }));

    expect(screen.queryByTestId("confirm-dialog")).not.toBeInTheDocument();
    expect(screen.getByTestId("source-row-source-1")).toBeInTheDocument();
    expect(deleteMock).not.toHaveBeenCalled();
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("does not navigate when keyboard interaction starts from action button", async () => {
    listMock.mockResolvedValue([buildSource("source-1", { title: "Keyboard Safe" })]);

    render(<SourcesPage />);

    const deleteButton = await screen.findByRole("button", { name: "Delete: Keyboard Safe" });
    fireEvent.keyDown(deleteButton, { key: "Enter" });

    expect(pushMock).not.toHaveBeenCalled();
    expect(deleteMock).not.toHaveBeenCalled();
  });

  it("shows source types and marks the clicked row as opening", async () => {
    listMock.mockResolvedValue([
      buildSource("source-1", {
        title: "Text source",
        asset: null,
      }),
      buildSource("source-2", {
        title: "Link source",
        asset: { url: "https://example.com" },
      }),
      buildSource("source-3", {
        title: "File source",
        asset: { file_path: "/tmp/file.pdf" },
      }),
    ]);

    render(<SourcesPage />);

    const openingRow = await screen.findByTestId("source-row-source-2");
    expect(screen.getByText("Text")).toBeInTheDocument();
    expect(screen.getByText("Link")).toBeInTheDocument();
    expect(screen.getByText("File")).toBeInTheDocument();

    fireEvent.click(openingRow);

    expect(pushMock).toHaveBeenCalledWith("/sources/source-2");
    expect(openingRow).toHaveAttribute("aria-busy", "true");
    expect(screen.getByText("Processing")).toBeInTheDocument();
  });

  it("supports Home and End keyboard shortcuts on table region", async () => {
    listMock.mockResolvedValue([
      buildSource("source-1", { title: "First" }),
      buildSource("source-2", { title: "Middle" }),
      buildSource("source-3", { title: "Last" }),
    ]);

    render(<SourcesPage />);
    const tableRegion = await screen.findByRole("region", { name: "All sources" });

    tableRegion.focus();
    fireEvent.keyDown(tableRegion, { key: "ArrowDown" });
    fireEvent.keyDown(tableRegion, { key: "Home" });
    fireEvent.keyDown(tableRegion, { key: "Enter" });

    fireEvent.keyDown(tableRegion, { key: "End" });
    fireEvent.keyDown(tableRegion, { key: "Enter" });

    expect(pushMock).toHaveBeenNthCalledWith(1, "/sources/source-1");
    expect(pushMock).toHaveBeenNthCalledWith(2, "/sources/source-3");
  });

  it("opens row on Space key press", async () => {
    listMock.mockResolvedValue([buildSource("source-space", { title: "Space opener" })]);

    render(<SourcesPage />);
    const row = await screen.findByTestId("source-row-source-space");
    fireEvent.keyDown(row, { key: " " });

    expect(pushMock).toHaveBeenCalledWith("/sources/source-space");
  });

  it(
    "loads more rows when scrolled near bottom and stops when no more pages",
    { timeout: SLOW_TEST_TIMEOUT_MS },
    async () => {
      const loadMorePage = createDeferred<ReturnType<typeof buildPage>>();
      listMock
        .mockResolvedValueOnce(buildPage(30))
        .mockResolvedValueOnce(buildPage(30, "sorted"))
        .mockImplementationOnce(() => loadMorePage.promise);

      const scrollTopSpy = vi.spyOn(HTMLElement.prototype, "scrollTop", "get").mockReturnValue(850);
      const scrollHeightSpy = vi
        .spyOn(HTMLElement.prototype, "scrollHeight", "get")
        .mockReturnValue(1000);
      const clientHeightSpy = vi
        .spyOn(HTMLElement.prototype, "clientHeight", "get")
        .mockReturnValue(100);

      render(<SourcesPage />);

      await screen.findByTestId("source-row-source-1");

      fireEvent.click(screen.getByRole("button", { name: /Created/ }));
      await screen.findByTestId("source-row-sorted-1");

      try {
        const region = screen.getByRole("region", { name: "All sources" });
        vi.useFakeTimers();
        fireEvent.scroll(region);
        await vi.advanceTimersByTimeAsync(150);

        expect(listMock).toHaveBeenCalledTimes(3);

        fireEvent.scroll(region);

        vi.useRealTimers();
        loadMorePage.resolve(buildPage(1, "tail"));

        expect(await screen.findByTestId("source-row-tail-1")).toBeInTheDocument();

        const callsBefore = listMock.mock.calls.length;
        fireEvent.scroll(region);

        await new Promise((resolve) => setTimeout(resolve, 150));
        expect(listMock).toHaveBeenCalledTimes(callsBefore);
      } finally {
        scrollTopSpy.mockRestore();
        scrollHeightSpy.mockRestore();
        clientHeightSpy.mockRestore();
      }
    },
  );

  it("ignores container keyboard shortcuts when event target is interactive", async () => {
    listMock.mockResolvedValue([buildSource("source-safe", { title: "Safe source" })]);

    render(<SourcesPage />);

    const deleteButton = await screen.findByRole("button", { name: "Delete: Safe source" });
    fireEvent.keyDown(deleteButton, { key: "ArrowDown" });

    expect(pushMock).not.toHaveBeenCalled();
  });

  it("scrolls selected rows into view for both upward and downward keyboard navigation", async () => {
    listMock.mockResolvedValue([
      buildSource("source-1", { title: "Top row" }),
      buildSource("source-2", { title: "Bottom row" }),
    ]);

    const rafSpy = vi
      .spyOn(window, "requestAnimationFrame")
      .mockImplementation((callback: FrameRequestCallback) => {
        callback(0);
        return 1;
      });
    const matchMediaSpy = vi.spyOn(window, "matchMedia").mockImplementation(
      () =>
        ({
          matches: false,
          media: "(prefers-reduced-motion: reduce)",
          addListener: () => undefined,
          removeListener: () => undefined,
          addEventListener: () => undefined,
          removeEventListener: () => undefined,
          dispatchEvent: () => false,
          onchange: null,
        }) as MediaQueryList,
    );

    render(<SourcesPage />);

    const region = await screen.findByRole("region", { name: "All sources" });
    const rows = region.querySelectorAll("tbody tr");
    const firstRow = rows[0] as HTMLElement;
    const secondRow = rows[1] as HTMLElement;
    const firstRowScrollSpy = vi.fn();
    const secondRowScrollSpy = vi.fn();

    firstRow.scrollIntoView = firstRowScrollSpy;
    secondRow.scrollIntoView = secondRowScrollSpy;

    vi.spyOn(region, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 0,
      top: 0,
      left: 0,
      right: 200,
      bottom: 80,
      width: 200,
      height: 80,
      toJSON: () => ({}),
    });
    vi.spyOn(firstRow, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: -20,
      top: -20,
      left: 0,
      right: 200,
      bottom: 20,
      width: 200,
      height: 40,
      toJSON: () => ({}),
    });
    vi.spyOn(secondRow, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 90,
      top: 90,
      left: 0,
      right: 200,
      bottom: 130,
      width: 200,
      height: 40,
      toJSON: () => ({}),
    });

    region.focus();
    fireEvent.keyDown(region, { key: "ArrowDown" });
    fireEvent.keyDown(region, { key: "ArrowUp" });

    expect(secondRowScrollSpy).toHaveBeenCalledWith({ behavior: "smooth", block: "end" });
    expect(firstRowScrollSpy).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });

    rafSpy.mockRestore();
    matchMediaSpy.mockRestore();
  });

  it("falls back to untitled labels and ignores delete confirm when no source is selected", async () => {
    listMock.mockResolvedValue([buildSource("untitled", { title: "" })]);
    render(<SourcesPage />);

    const row = await screen.findByTestId("source-row-untitled");
    expect(row).toHaveAttribute("aria-label", "Untitled source");
    expect(screen.getByRole("button", { name: "Delete: Untitled source" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "force-confirm" }));
    expect(deleteMock).not.toHaveBeenCalled();
  });

  it("reports delete errors using message fallback when API detail is absent", async () => {
    listMock.mockResolvedValue([buildSource("source-1", { title: "Fallback error" })]);
    deleteMock.mockRejectedValue({ message: "fallback-error-message" });

    render(<SourcesPage />);

    await screen.findByTestId("source-row-source-1");
    fireEvent.click(screen.getByRole("button", { name: "Delete: Fallback error" }));
    fireEvent.click(screen.getByRole("button", { name: "confirm-delete" }));

    await waitFor(() => {
      expect(toastErrorMock).toHaveBeenCalledWith("translated:services.api.errors.generic");
    });
  });

  it("highlights hovered rows and ignores non-activation row keyboard keys", async () => {
    listMock.mockResolvedValue([
      buildSource("source-1", { title: "Hover one" }),
      buildSource("source-2", { title: "Hover two" }),
    ]);
    render(<SourcesPage />);

    const secondRow = await screen.findByTestId("source-row-source-2");
    fireEvent.mouseEnter(secondRow);
    fireEvent.keyDown(secondRow, { key: "Escape" });

    expect(secondRow).toHaveClass("bg-accent");
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("does not navigate when selected index points to a deleted source", async () => {
    listMock.mockResolvedValue([
      buildSource("source-1", { title: "Keep" }),
      buildSource("source-2", { title: "Remove me" }),
    ]);
    deleteMock.mockResolvedValue(undefined);

    render(<SourcesPage />);
    await screen.findByTestId("source-row-source-2");

    fireEvent.click(screen.getByTestId("source-row-source-2"));
    pushMock.mockClear();

    fireEvent.click(screen.getByRole("button", { name: "Delete: Remove me" }));
    fireEvent.click(screen.getByRole("button", { name: "confirm-delete" }));

    await waitFor(() => {
      expect(screen.queryByTestId("source-row-source-2")).not.toBeInTheDocument();
    });

    const region = screen.getByRole("region", { name: "All sources" });
    region.focus();
    fireEvent.keyDown(region, { key: "Enter" });
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("uses reduced-motion behavior and keeps in-view rows from scrolling", async () => {
    listMock.mockResolvedValue([buildSource("source-1", { title: "Still row" })]);

    const rafSpy = vi
      .spyOn(window, "requestAnimationFrame")
      .mockImplementation((callback: FrameRequestCallback) => {
        callback(0);
        return 1;
      });
    const matchMediaSpy = vi.spyOn(window, "matchMedia").mockImplementation(
      () =>
        ({
          matches: true,
          media: "(prefers-reduced-motion: reduce)",
          addListener: () => undefined,
          removeListener: () => undefined,
          addEventListener: () => undefined,
          removeEventListener: () => undefined,
          dispatchEvent: () => false,
          onchange: null,
        }) as MediaQueryList,
    );

    render(<SourcesPage />);
    const region = await screen.findByRole("region", { name: "All sources" });
    const firstRow = region.querySelector("tbody tr") as HTMLElement;
    const scrollIntoViewSpy = vi.fn();
    firstRow.scrollIntoView = scrollIntoViewSpy;

    vi.spyOn(region, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 0,
      top: 0,
      left: 0,
      right: 200,
      bottom: 80,
      width: 200,
      height: 80,
      toJSON: () => ({}),
    });
    vi.spyOn(firstRow, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 10,
      top: 10,
      left: 0,
      right: 200,
      bottom: 40,
      width: 200,
      height: 30,
      toJSON: () => ({}),
    });

    region.focus();
    fireEvent.keyDown(region, { key: "ArrowDown" });

    expect(scrollIntoViewSpy).not.toHaveBeenCalled();

    rafSpy.mockRestore();
    matchMediaSpy.mockRestore();
  });

  it(
    "skips load-more far from bottom and clears pending scroll timeout on unmount",
    { timeout: SLOW_TEST_TIMEOUT_MS },
    async () => {
      listMock.mockResolvedValueOnce(buildPage(30)).mockResolvedValueOnce(buildPage(30, "sorted"));

      const scrollTopSpy = vi.spyOn(HTMLElement.prototype, "scrollTop", "get").mockReturnValue(0);
      const scrollHeightSpy = vi
        .spyOn(HTMLElement.prototype, "scrollHeight", "get")
        .mockReturnValue(1000);
      const clientHeightSpy = vi
        .spyOn(HTMLElement.prototype, "clientHeight", "get")
        .mockReturnValue(100);

      const { unmount } = render(<SourcesPage />);
      await screen.findByTestId("source-row-source-1");

      fireEvent.click(screen.getByRole("button", { name: /Created/ }));
      await screen.findByTestId("source-row-sorted-1");

      try {
        const region = screen.getByRole("region", { name: "All sources" });
        vi.useFakeTimers();
        fireEvent.scroll(region);
        fireEvent.scroll(region);
        unmount();

        await vi.advanceTimersByTimeAsync(150);
        expect(listMock).toHaveBeenCalledTimes(2);
      } finally {
        scrollTopSpy.mockRestore();
        scrollHeightSpy.mockRestore();
        clientHeightSpy.mockRestore();
      }
    },
  );
});
