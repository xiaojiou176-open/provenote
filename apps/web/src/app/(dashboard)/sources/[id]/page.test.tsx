import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useNavigation } from "@/lib/hooks/use-navigation";
import { useSource } from "@/lib/hooks/use-sources";
import { useSourceChat } from "@/lib/hooks/useSourceChat";
import SourceDetailPage from "./page";

const mockPush = vi.fn();
const mockClearReturnTo = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useParams: () => ({ id: "source%20123" }),
}));

vi.mock("@/components/layout/AppShell", () => ({
  AppShell: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/source/AuditableMarkdownPanel", () => ({
  AuditableMarkdownPanel: ({ sourceId }: { sourceId: string }) => (
    <div data-testid="auditable-panel" data-source-id={sourceId} />
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
  }: {
    currentSessionId: string | null;
    onModelChange?: (model: string) => void;
  }) => (
    <>
      <div data-testid="chat-panel" data-current-session={currentSessionId ?? "none"} />
      <button onClick={() => onModelChange?.("gemini-3.0-pro")} type="button">
        trigger-model-change
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
});
