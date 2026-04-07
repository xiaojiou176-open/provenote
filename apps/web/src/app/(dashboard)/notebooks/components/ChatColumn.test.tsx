import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useNotes } from "@/lib/hooks/use-notes";
import { useCreateResearchThread } from "@/lib/hooks/use-research-threads";
import { useNotebookChat } from "@/lib/hooks/useNotebookChat";
import { ChatColumn } from "./ChatColumn";

vi.mock("@/lib/hooks/use-notes");
vi.mock("@/lib/hooks/use-research-threads");
vi.mock("@/lib/hooks/useNotebookChat");
vi.mock("@/components/source/ChatPanel", () => ({
  ChatPanel: ({ notebookContextStats }: { notebookContextStats: unknown }) => (
    <div data-testid="chat-panel" data-context={JSON.stringify(notebookContextStats)} />
  ),
}));

function createNotesMock(
  overrides: { isLoading?: boolean; error?: unknown; refetch?: () => void } = {},
) {
  return {
    data: [],
    isLoading: overrides.isLoading ?? false,
    error: overrides.error,
    refetch: overrides.refetch ?? vi.fn(),
  } as unknown as ReturnType<typeof useNotes>;
}

function createChatMock() {
  return {
    messages: [],
    isSending: false,
    tokenCount: 42,
    charCount: 120,
    sessions: [],
    currentSessionId: null,
    sendMessage: vi.fn(),
    setModelOverride: vi.fn(),
    createSession: vi.fn(),
    switchSession: vi.fn(),
    updateSession: vi.fn(),
    deleteSession: vi.fn(),
    loadingSessions: false,
  } as unknown as ReturnType<typeof useNotebookChat>;
}

function createResearchThreadMock() {
  return {
    mutateAsync: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof useCreateResearchThread>;
}

describe("ChatColumn", () => {
  const baseProps = {
    notebookId: "test-notebook",
    contextSelections: {
      sources: {
        "source-1": "insights",
        "source-2": "full",
      },
      notes: {
        "note-1": "full",
      },
    },
    sources: [{ id: "source-1" }, { id: "source-2" }],
  };

  it("shows loading spinner when fetching data", () => {
    vi.mocked(useNotes).mockReturnValue(createNotesMock({ isLoading: true }));
    vi.mocked(useCreateResearchThread).mockReturnValue(createResearchThreadMock());
    vi.mocked(useNotebookChat).mockReturnValue(createChatMock());

    render(<ChatColumn {...baseProps} sourcesLoading />);

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("shows retry state when notes or sources fail to load", () => {
    const refetch = vi.fn();
    vi.mocked(useNotes).mockReturnValue(createNotesMock({ error: new Error("boom"), refetch }));
    vi.mocked(useCreateResearchThread).mockReturnValue(createResearchThreadMock());
    vi.mocked(useNotebookChat).mockReturnValue(createChatMock());

    render(<ChatColumn {...baseProps} sourcesLoading={false} />);

    expect(screen.getByText("Unable to load chat")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Try Again|Retry/i }));
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("renders chat panel with computed context stats", () => {
    vi.mocked(useNotes).mockReturnValue({
      ...createNotesMock(),
      data: [{ id: "note-1" }],
    } as unknown as ReturnType<typeof useNotes>);
    vi.mocked(useCreateResearchThread).mockReturnValue(createResearchThreadMock());
    vi.mocked(useNotebookChat).mockReturnValue(createChatMock());

    render(<ChatColumn {...baseProps} sourcesLoading={false} />);

    const stats = JSON.parse(screen.getByTestId("chat-panel").getAttribute("data-context") ?? "{}");
    expect(stats.sourcesInsights).toBe(1);
    expect(stats.sourcesFull).toBe(1);
    expect(stats.notesCount).toBe(1);
    expect(stats.tokenCount).toBe(42);
    expect(stats.charCount).toBe(120);
  });
});
