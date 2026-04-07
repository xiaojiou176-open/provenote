import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useParams, useSearchParams } from "next/navigation";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useIsDesktop } from "@/lib/hooks/use-media-query";
import { useNotebook } from "@/lib/hooks/use-notebooks";
import { useNotes } from "@/lib/hooks/use-notes";
import { useNotebookSources } from "@/lib/hooks/use-sources";
import { useTranslation } from "@/lib/hooks/use-translation";
import { useNotebookColumnsStore } from "@/lib/stores/notebook-columns-store";
import NotebookPage from "./page";

vi.mock("next/navigation", () => ({
  useParams: vi.fn(),
  useSearchParams: vi.fn(),
}));

vi.mock("@/lib/hooks/use-media-query");
vi.mock("@/lib/hooks/use-notebooks");
vi.mock("@/lib/hooks/use-notes");
vi.mock("@/lib/hooks/use-sources");
vi.mock("@/lib/hooks/use-translation");
vi.mock("@/lib/stores/notebook-columns-store");

vi.mock("@/components/ui/tabs", async () => {
  const React = await import("react");
  const TabsContext = React.createContext<{
    value: string;
    onValueChange?: (value: string) => void;
  }>({
    value: "chat",
  });

  return {
    Tabs: ({
      children,
      value,
      onValueChange,
    }: {
      children: ReactNode;
      value: string;
      onValueChange?: (value: string) => void;
    }) => (
      <TabsContext.Provider value={{ value, onValueChange }}>
        <div>{children}</div>
      </TabsContext.Provider>
    ),
    TabsList: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    TabsTrigger: ({
      value,
      children,
    }: {
      value: "sources" | "notes" | "chat" | "drafts";
      children: ReactNode;
    }) => {
      const ctx = React.useContext(TabsContext);
      return (
        <button
          data-testid={`mobile-tab-${value}`}
          data-state={ctx.value === value ? "active" : "inactive"}
          onClick={() => ctx.onValueChange?.(value)}
          type="button"
        >
          {children}
        </button>
      );
    },
  };
});

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

vi.mock("@/components/layout/AppShell", () => ({
  AppShell: ({ children }: { children: ReactNode }) => (
    <div data-testid="app-shell">{children}</div>
  ),
}));

vi.mock("@/components/notebooks/NotebookDraftPanel", () => ({
  NotebookDraftPanel: ({
    notebookId,
    draftSeedThreadId,
  }: {
    notebookId: string;
    draftSeedThreadId?: string;
  }) => (
    <div
      data-testid="draft-panel"
      data-notebook-id={notebookId}
      data-draft-seed-thread-id={draftSeedThreadId ?? ""}
    />
  ),
}));

vi.mock("@/components/notebooks/NotebookOutcomeJourneyCard", () => ({
  NotebookOutcomeJourneyCard: ({
    notebookId,
    onOpenDraftLane,
    onOpenResearchThreadsLane,
    draftSeedThreadId,
  }: {
    notebookId: string;
    onOpenDraftLane?: () => void;
    onOpenResearchThreadsLane?: () => void;
    draftSeedThreadId?: string;
  }) => (
    <div
      data-testid="notebook-outcome-journey-card"
      data-notebook-id={notebookId}
      data-draft-seed-thread-id={draftSeedThreadId ?? ""}
    >
      <button onClick={() => onOpenDraftLane?.()} type="button">
        open-draft-lane
      </button>
      <button onClick={() => onOpenResearchThreadsLane?.()} type="button">
        open-research-threads-lane
      </button>
    </div>
  ),
}));

vi.mock("@/components/notebooks/ResearchThreadsPanel", () => ({
  ResearchThreadsPanel: ({
    notebookId,
    draftSeedThreadId,
  }: {
    notebookId: string;
    draftSeedThreadId?: string;
  }) => (
    <div
      data-testid="research-threads-panel"
      data-notebook-id={notebookId}
      data-draft-seed-thread-id={draftSeedThreadId ?? ""}
    />
  ),
}));

vi.mock("../components/NotebookHeader", () => ({
  NotebookHeader: ({ notebook }: { notebook: { name: string } }) => (
    <div data-testid="notebook-header">{notebook.name}</div>
  ),
}));

vi.mock("../components/SourcesColumn", () => ({
  SourcesColumn: ({
    notebookId,
    contextSelections,
    onContextModeChange,
  }: {
    notebookId: string;
    contextSelections?: Record<string, string>;
    onContextModeChange?: (id: string, mode: "off" | "insights" | "full") => void;
  }) => (
    <div data-testid="sources-column" data-notebook-id={notebookId}>
      <div data-testid="sources-context">{JSON.stringify(contextSelections ?? {})}</div>
      <button onClick={() => onContextModeChange?.("source-2", "off")} type="button">
        set-source-off
      </button>
    </div>
  ),
}));

vi.mock("../components/NotesColumn", () => ({
  NotesColumn: ({
    contextSelections,
    onContextModeChange,
  }: {
    contextSelections?: Record<string, string>;
    onContextModeChange?: (id: string, mode: "off" | "insights" | "full") => void;
  }) => (
    <div data-testid="notes-column">
      {JSON.stringify(contextSelections ?? {})}
      <button onClick={() => onContextModeChange?.("note-1", "off")} type="button">
        set-note-off
      </button>
    </div>
  ),
}));

vi.mock("../components/ChatColumn", () => ({
  ChatColumn: ({
    contextSelections,
  }: {
    contextSelections: Record<string, Record<string, string>>;
  }) => <div data-testid="chat-context">{JSON.stringify(contextSelections)}</div>,
}));

const notebookSourcesReturn = {
  sources: [],
  isLoading: false,
  refetch: vi.fn(),
  hasNextPage: false,
  isFetchingNextPage: false,
  fetchNextPage: vi.fn(),
  error: null,
};

describe("NotebookPage[id]", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        notebooks: {
          notFound: "Notebook Not Found",
          notFoundDesc: "Unable to load notebook",
          draftsTitle: "Drafts",
        },
        navigation: {
          sources: "Sources",
        },
        common: {
          notes: "Notes",
          chat: "Chat",
        },
      },
    } as unknown as ReturnType<typeof useTranslation>);

    vi.mocked(useParams).mockReturnValue({ id: "notebook%20123" } as ReturnType<typeof useParams>);
    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams() as unknown as ReturnType<typeof useSearchParams>,
    );

    vi.mocked(useNotebookColumnsStore).mockReturnValue({
      sourcesCollapsed: false,
      notesCollapsed: false,
    } as unknown as ReturnType<typeof useNotebookColumnsStore>);

    vi.mocked(useNotebookSources).mockReturnValue(
      notebookSourcesReturn as unknown as ReturnType<typeof useNotebookSources>,
    );

    vi.mocked(useNotes).mockReturnValue({
      data: [],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotes>);

    vi.mocked(useIsDesktop).mockReturnValue(true);
  });

  it("renders loading state while notebook is pending", () => {
    vi.mocked(useNotebook).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as unknown as ReturnType<typeof useNotebook>);

    render(<NotebookPage />);

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("renders not found state when notebook is missing", () => {
    vi.mocked(useNotebook).mockReturnValue({
      data: null,
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebook>);

    render(<NotebookPage />);

    expect(screen.getByText("Notebook Not Found")).toBeInTheDocument();
    expect(screen.getByText("Unable to load notebook")).toBeInTheDocument();
  });

  it("initializes context defaults and updates source mode via callback", async () => {
    vi.mocked(useNotebook).mockReturnValue({
      data: {
        id: "notebook:123",
        name: "Notebook A",
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebook>);

    vi.mocked(useNotebookSources).mockReturnValue({
      ...notebookSourcesReturn,
      sources: [
        { id: "source-1", insights_count: 2 },
        { id: "source-2", insights_count: 0 },
      ],
    } as unknown as ReturnType<typeof useNotebookSources>);

    vi.mocked(useNotes).mockReturnValue({
      data: [{ id: "note-1" }],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotes>);

    render(<NotebookPage />);

    await waitFor(() => {
      expect(screen.getAllByTestId("sources-column")[0]).toHaveAttribute(
        "data-notebook-id",
        "notebook 123",
      );
      expect(screen.getByTestId("draft-panel")).toHaveAttribute("data-notebook-id", "notebook 123");
      expect(screen.getByTestId("research-threads-panel")).toHaveAttribute(
        "data-notebook-id",
        "notebook 123",
      );
      expect(screen.getByTestId("chat-context")).toHaveTextContent('"source-1":"insights"');
      expect(screen.getByTestId("chat-context")).toHaveTextContent('"source-2":"full"');
      expect(screen.getByTestId("chat-context")).toHaveTextContent('"note-1":"full"');
    });

    fireEvent.click(screen.getByRole("button", { name: "set-source-off" }));

    await waitFor(() => {
      expect(screen.getByTestId("chat-context")).toHaveTextContent('"source-2":"off"');
    });
  });

  it("handles missing route params by decoding notebook id to empty string", async () => {
    vi.mocked(useParams).mockReturnValue({} as ReturnType<typeof useParams>);
    vi.mocked(useNotebook).mockReturnValue({
      data: {
        id: "notebook:empty",
        name: "Notebook Without Param",
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebook>);

    render(<NotebookPage />);

    await waitFor(() => {
      expect(screen.getAllByTestId("sources-column")[0]).toHaveAttribute("data-notebook-id", "");
    });
  });

  it("auto-upgrades source context and updates note context through callbacks", async () => {
    vi.mocked(useNotebook).mockReturnValue({
      data: { id: "notebook:123", name: "Notebook A" },
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebook>);
    vi.mocked(useIsDesktop).mockReturnValue(true);
    vi.mocked(useNotebookSources).mockReturnValue({
      ...notebookSourcesReturn,
      sources: [{ id: "source-1", insights_count: 0 }],
    } as unknown as ReturnType<typeof useNotebookSources>);
    vi.mocked(useNotes).mockReturnValue({
      data: [{ id: "note-1" }],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotes>);

    const { rerender } = render(<NotebookPage />);

    await waitFor(() => {
      expect(screen.getByTestId("chat-context")).toHaveTextContent('"source-1":"full"');
    });

    vi.mocked(useNotebookSources).mockReturnValue({
      ...notebookSourcesReturn,
      sources: [{ id: "source-1", insights_count: 2 }],
    } as unknown as ReturnType<typeof useNotebookSources>);
    rerender(<NotebookPage />);

    await waitFor(() => {
      expect(screen.getByTestId("chat-context")).toHaveTextContent('"source-1":"insights"');
    });

    fireEvent.click(screen.getByRole("button", { name: "set-note-off" }));

    await waitFor(() => {
      expect(screen.getByTestId("chat-context")).toHaveTextContent('"note-1":"off"');
    });

    fireEvent.click(screen.getByRole("button", { name: "set-source-off" }));
    await waitFor(() => {
      expect(screen.getByTestId("chat-context")).toHaveTextContent('"source-2":"off"');
    });

    vi.mocked(useNotebookSources).mockReturnValue({
      ...notebookSourcesReturn,
      sources: [{ id: "source-1", insights_count: 3 }],
    } as unknown as ReturnType<typeof useNotebookSources>);
    vi.mocked(useNotes).mockReturnValue({
      data: [{ id: "note-1" }],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotes>);
    rerender(<NotebookPage />);

    await waitFor(() => {
      expect(screen.getByTestId("chat-context")).toHaveTextContent('"source-1":"insights"');
      expect(screen.getByTestId("chat-context")).toHaveTextContent('"note-1":"off"');
    });
  });

  it("renders mobile tab views and switches between sources, notes and chat", async () => {
    vi.mocked(useNotebook).mockReturnValue({
      data: { id: "notebook:123", name: "Notebook Mobile" },
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebook>);
    vi.mocked(useNotebookSources).mockReturnValue({
      ...notebookSourcesReturn,
      sources: [{ id: "source-1", insights_count: 1 }],
    } as unknown as ReturnType<typeof useNotebookSources>);
    vi.mocked(useNotes).mockReturnValue({
      data: [{ id: "note-1" }],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotes>);
    vi.mocked(useIsDesktop).mockReturnValue(false);

    render(<NotebookPage />);

    expect(screen.getByTestId("mobile-tab-chat")).toHaveAttribute("data-state", "active");

    fireEvent.click(screen.getByTestId("mobile-tab-sources"));
    await waitFor(() => {
      expect(screen.getByTestId("mobile-tab-sources")).toHaveAttribute("data-state", "active");
      expect(screen.getAllByTestId("sources-column")).toHaveLength(2);
    });
    screen
      .getAllByRole("button", { name: "set-source-off" })
      .forEach((button) => fireEvent.click(button));
    await waitFor(() => {
      expect(screen.getAllByTestId("chat-context")[0]).toHaveTextContent('"source-2":"off"');
    });

    fireEvent.click(screen.getByTestId("mobile-tab-notes"));
    await waitFor(() => {
      expect(screen.getByTestId("mobile-tab-notes")).toHaveAttribute("data-state", "active");
      expect(screen.getAllByTestId("notes-column")).toHaveLength(2);
    });
    screen
      .getAllByRole("button", { name: "set-note-off" })
      .forEach((button) => fireEvent.click(button));
    await waitFor(() => {
      expect(screen.getAllByTestId("chat-context")[0]).toHaveTextContent('"note-1":"off"');
    });
  });

  it("switches to drafts tab when outcome card opens the draft lane on mobile", () => {
    vi.useFakeTimers();
    const scrollIntoView = vi.fn();
    const originalQuerySelector = document.querySelector.bind(document);
    vi.spyOn(document, "querySelector").mockImplementation((selector) => {
      if (selector === '[data-testid="notebook-drafts-panel"]') {
        return { scrollIntoView } as unknown as Element;
      }
      return originalQuerySelector(selector);
    });

    vi.mocked(useNotebook).mockReturnValue({
      data: { id: "notebook:123", name: "Notebook Mobile" },
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebook>);
    vi.mocked(useNotebookSources).mockReturnValue({
      ...notebookSourcesReturn,
      sources: [{ id: "source-1", insights_count: 1 }],
    } as unknown as ReturnType<typeof useNotebookSources>);
    vi.mocked(useNotes).mockReturnValue({
      data: [{ id: "note-1" }],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotes>);
    vi.mocked(useIsDesktop).mockReturnValue(false);

    render(<NotebookPage />);

    const mobileOutcomeCard = screen.getAllByTestId("notebook-outcome-journey-card")[0];
    fireEvent.click(within(mobileOutcomeCard).getByRole("button", { name: "open-draft-lane" }));
    vi.runAllTimers();

    expect(screen.getByTestId("mobile-tab-drafts")).toHaveAttribute("data-state", "active");
    vi.useRealTimers();
  });

  it("switches to drafts tab when outcome card opens the research thread lane on mobile", () => {
    vi.useFakeTimers();
    const scrollIntoView = vi.fn();
    const originalQuerySelector = document.querySelector.bind(document);
    vi.spyOn(document, "querySelector").mockImplementation((selector) => {
      if (selector === '[data-testid="research-threads-panel"]') {
        return { scrollIntoView } as unknown as Element;
      }
      return originalQuerySelector(selector);
    });

    vi.mocked(useNotebook).mockReturnValue({
      data: { id: "notebook:123", name: "Notebook Mobile" },
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebook>);
    vi.mocked(useNotebookSources).mockReturnValue({
      ...notebookSourcesReturn,
      sources: [{ id: "source-1", insights_count: 1 }],
    } as unknown as ReturnType<typeof useNotebookSources>);
    vi.mocked(useNotes).mockReturnValue({
      data: [{ id: "note-1" }],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotes>);
    vi.mocked(useIsDesktop).mockReturnValue(false);

    render(<NotebookPage />);

    const mobileOutcomeCard = screen.getAllByTestId("notebook-outcome-journey-card")[0];
    fireEvent.click(
      within(mobileOutcomeCard).getByRole("button", { name: "open-research-threads-lane" }),
    );
    vi.runAllTimers();

    expect(screen.getByTestId("mobile-tab-drafts")).toHaveAttribute("data-state", "active");
    vi.useRealTimers();
  });

  it("opens the drafts tab automatically when arriving with a draft seed thread on mobile", () => {
    vi.useFakeTimers();
    const scrollIntoView = vi.fn();
    const originalQuerySelector = document.querySelector.bind(document);
    vi.spyOn(document, "querySelector").mockImplementation((selector) => {
      if (selector === '[data-testid="research-threads-panel"]') {
        return { scrollIntoView } as unknown as Element;
      }
      return originalQuerySelector(selector);
    });

    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams("draftSeedThread=research_thread%3A1") as unknown as ReturnType<
        typeof useSearchParams
      >,
    );
    vi.mocked(useNotebook).mockReturnValue({
      data: { id: "notebook:123", name: "Notebook Mobile" },
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebook>);
    vi.mocked(useNotebookSources).mockReturnValue({
      ...notebookSourcesReturn,
      sources: [{ id: "source-1", insights_count: 1 }],
    } as unknown as ReturnType<typeof useNotebookSources>);
    vi.mocked(useNotes).mockReturnValue({
      data: [{ id: "note-1" }],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotes>);
    vi.mocked(useIsDesktop).mockReturnValue(false);

    render(<NotebookPage />);
    vi.runAllTimers();

    expect(screen.getByTestId("mobile-tab-drafts")).toHaveAttribute("data-state", "active");
    expect(screen.getAllByTestId("notebook-outcome-journey-card")[0]).toHaveAttribute(
      "data-draft-seed-thread-id",
      "research_thread:1",
    );
    expect(screen.getAllByTestId("research-threads-panel")[0]).toHaveAttribute(
      "data-draft-seed-thread-id",
      "research_thread:1",
    );
    expect(screen.getAllByTestId("draft-panel")[0]).toHaveAttribute(
      "data-draft-seed-thread-id",
      "research_thread:1",
    );
    vi.useRealTimers();
  });

  it("applies collapsed desktop classes when both columns are collapsed", async () => {
    vi.mocked(useNotebook).mockReturnValue({
      data: { id: "notebook:123", name: "Notebook Collapsed" },
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebook>);
    vi.mocked(useNotebookSources).mockReturnValue({
      ...notebookSourcesReturn,
      sources: [{ id: "source-1", insights_count: 1 }],
    } as unknown as ReturnType<typeof useNotebookSources>);
    vi.mocked(useNotes).mockReturnValue({
      data: [{ id: "note-1" }],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotes>);
    vi.mocked(useNotebookColumnsStore).mockReturnValue({
      sourcesCollapsed: true,
      notesCollapsed: true,
    } as unknown as ReturnType<typeof useNotebookColumnsStore>);
    vi.mocked(useIsDesktop).mockReturnValue(true);

    const { container } = render(<NotebookPage />);

    await waitFor(() => {
      expect(container.querySelectorAll(".w-12.flex-shrink-0").length).toBeGreaterThanOrEqual(2);
    });
  });
});
