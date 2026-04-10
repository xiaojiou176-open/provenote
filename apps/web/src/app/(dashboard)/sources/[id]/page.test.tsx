import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useNavigation } from "@/lib/hooks/use-navigation";
import { useSource } from "@/lib/hooks/use-sources";
import { useSourceChat } from "@/lib/hooks/useSourceChat";
import SourceDetailPage from "./page";

const mockPush = vi.fn();
const mockClearReturnTo = vi.fn();
const mockScrollIntoView = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useParams: () => ({ id: "source%20123" }),
}));

vi.mock("@/components/layout/AppShell", () => ({
  AppShell: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/source/AuditableMarkdownPanel", () => ({
  AuditableMarkdownPanel: ({
    sourceId,
    linkedNotebookIds,
    onUseInDraft,
  }: {
    sourceId: string;
    linkedNotebookIds?: string[];
    onUseInDraft?: (notebookId: string) => void;
  }) => (
    <div data-testid="auditable-panel" data-source-id={sourceId}>
      <span data-testid="linked-notebooks">{(linkedNotebookIds ?? []).join(",")}</span>
      <button onClick={() => onUseInDraft?.("notebook:1")} type="button">
        open-linked-draft
      </button>
    </div>
  ),
}));

vi.mock("@/components/source/SourceDetailContent", () => ({
  SourceDetailContent: ({ sourceId }: { sourceId: string }) => (
    <div data-testid="source-detail-content" data-source-id={sourceId} />
  ),
}));

vi.mock("@/components/source/ChatPanel", () => ({
  ChatPanel: ({
    currentSessionId,
    onModelChange,
    onSendMessage,
    onCreateSession,
    onSelectSession,
    onUpdateSession,
    onDeleteSession,
  }: {
    currentSessionId: string | null;
    onModelChange?: (model: string) => void;
    onSendMessage?: (message: string, model?: string) => void;
    onCreateSession?: (title: string) => void;
    onSelectSession?: (sessionId: string) => void;
    onUpdateSession?: (sessionId: string, title: string) => void;
    onDeleteSession?: (sessionId: string) => void;
  }) => (
    <>
      <div data-testid="chat-panel" data-current-session={currentSessionId ?? "none"} />
      <button onClick={() => onModelChange?.("gemini-3.0-pro")} type="button">
        trigger-model-change
      </button>
      <button onClick={() => onSendMessage?.("hello source", "gemini-3.0-flash")} type="button">
        trigger-send-message
      </button>
      <button onClick={() => onCreateSession?.("fresh lane")} type="button">
        trigger-create-session
      </button>
      <button onClick={() => onSelectSession?.("sess-2")} type="button">
        trigger-select-session
      </button>
      <button onClick={() => onUpdateSession?.("sess-2", "retitled lane")} type="button">
        trigger-update-session
      </button>
      <button onClick={() => onDeleteSession?.("sess-2")} type="button">
        trigger-delete-session
      </button>
    </>
  ),
}));

vi.mock("@/lib/hooks/use-navigation");
vi.mock("@/lib/hooks/useSourceChat");
vi.mock("@/lib/hooks/use-sources");

describe("SourceDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    HTMLElement.prototype.scrollIntoView = mockScrollIntoView;

    vi.mocked(useNavigation).mockReturnValue({
      getReturnPath: () => "/sources",
      getReturnLabel: () => "Back to sources",
      clearReturnTo: mockClearReturnTo,
      returnTo: null,
      setReturnTo: vi.fn(),
    } as unknown as ReturnType<typeof useNavigation>);

    vi.mocked(useSource).mockReturnValue({
      data: {
        id: "source 123",
        title: "Decoded Source",
        full_text: "Body",
        notebooks: ["notebook:1"],
        asset: null,
        embedded: true,
        embedded_chunks: 1,
        insights_count: 0,
        created: "",
        updated: "",
      },
    } as unknown as ReturnType<typeof useSource>);

    vi.mocked(useSourceChat).mockReturnValue({
      messages: [],
      isStreaming: false,
      contextIndicators: null,
      sendMessage: vi.fn(),
      currentSession: null,
      updateSession: vi.fn(),
      currentSessionId: null,
      sessions: [],
      createSession: vi.fn(),
      switchSession: vi.fn(),
      deleteSession: vi.fn(),
      loadingSessions: false,
      cancelStreaming: vi.fn(),
      refetchSessions: vi.fn(),
    } as unknown as ReturnType<typeof useSourceChat>);
  });

  it("passes decoded source id to page sections", () => {
    render(<SourceDetailPage />);

    expect(screen.getByTestId("auditable-panel")).toHaveAttribute("data-source-id", "source 123");
    expect(screen.getByTestId("source-detail-content")).toHaveAttribute(
      "data-source-id",
      "source 123",
    );
    expect(screen.getByTestId("chat-panel")).toBeInTheDocument();
  });

  it("renders source next-step content before the auditable panel", () => {
    render(<SourceDetailPage />);

    const sourceDetail = screen.getByTestId("source-detail-content");
    const auditablePanel = screen.getByTestId("auditable-panel");

    expect(sourceDetail.compareDocumentPosition(auditablePanel)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
  });

  it("navigates back and clears return target", () => {
    render(<SourceDetailPage />);

    fireEvent.click(screen.getByRole("button", { name: "Back to sources" }));

    expect(mockPush).toHaveBeenCalledWith("/sources");
    expect(mockClearReturnTo).toHaveBeenCalledTimes(1);
  });

  it("updates current chat session model override", () => {
    const updateSession = vi.fn();
    vi.mocked(useSourceChat).mockReturnValue({
      messages: [],
      isStreaming: false,
      contextIndicators: null,
      sendMessage: vi.fn(),
      currentSession: {
        id: "sess-1",
        source_id: "source 123",
        title: "session",
        model_override: null,
      },
      updateSession,
      currentSessionId: "sess-1",
      sessions: [],
      createSession: vi.fn(),
      switchSession: vi.fn(),
      deleteSession: vi.fn(),
      loadingSessions: false,
      cancelStreaming: vi.fn(),
      refetchSessions: vi.fn(),
    } as unknown as ReturnType<typeof useSourceChat>);

    render(<SourceDetailPage />);
    fireEvent.click(screen.getByRole("button", { name: "trigger-model-change" }));

    expect(updateSession).toHaveBeenCalledWith("sess-1", { model_override: "gemini-3.0-pro" });
  });

  it("routes next-step buttons to their matching sections", () => {
    render(<SourceDetailPage />);

    fireEvent.click(screen.getByRole("button", { name: "sources.detailPage.evidenceAction" }));
    fireEvent.click(screen.getByRole("button", { name: "sources.detailPage.auditAction" }));
    fireEvent.click(screen.getByRole("button", { name: "sources.detailPage.chatAction" }));

    expect(mockScrollIntoView).toHaveBeenCalledTimes(3);
  });

  it("passes linked notebooks into the auditable lane and opens the draft rail callback", () => {
    render(<SourceDetailPage />);

    expect(screen.getByTestId("linked-notebooks")).toHaveTextContent("notebook:1");

    fireEvent.click(screen.getByRole("button", { name: "open-linked-draft" }));

    expect(mockPush).toHaveBeenCalledWith("/notebooks/notebook%3A1");
  });

  it("wires source chat actions through to the chat hook", () => {
    const sendMessage = vi.fn();
    const createSession = vi.fn();
    const switchSession = vi.fn();
    const updateSession = vi.fn();
    const deleteSession = vi.fn();

    vi.mocked(useSourceChat).mockReturnValue({
      messages: [],
      isStreaming: false,
      contextIndicators: null,
      sendMessage,
      currentSession: {
        id: "sess-1",
        source_id: "source 123",
        title: "session",
        model_override: null,
      },
      updateSession,
      currentSessionId: "sess-1",
      sessions: [],
      createSession,
      switchSession,
      deleteSession,
      loadingSessions: false,
      cancelStreaming: vi.fn(),
      refetchSessions: vi.fn(),
    } as unknown as ReturnType<typeof useSourceChat>);

    render(<SourceDetailPage />);

    fireEvent.click(screen.getByRole("button", { name: "trigger-send-message" }));
    fireEvent.click(screen.getByRole("button", { name: "trigger-create-session" }));
    fireEvent.click(screen.getByRole("button", { name: "trigger-select-session" }));
    fireEvent.click(screen.getByRole("button", { name: "trigger-update-session" }));
    fireEvent.click(screen.getByRole("button", { name: "trigger-delete-session" }));

    expect(sendMessage).toHaveBeenCalledWith("hello source", "gemini-3.0-flash");
    expect(createSession).toHaveBeenCalledWith({ title: "fresh lane" });
    expect(switchSession).toHaveBeenCalledWith("sess-2");
    expect(updateSession).toHaveBeenCalledWith("sess-2", { title: "retitled lane" });
    expect(deleteSession).toHaveBeenCalledWith("sess-2");
  });
});
