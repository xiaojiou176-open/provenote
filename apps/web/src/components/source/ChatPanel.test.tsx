import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { toast } from "sonner";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ChatPanel } from "./ChatPanel";

const hoisted = vi.hoisted(() => ({
  openModalMock: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn() },
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      chat: {
        chatWith: "Chat with {name}",
        sessions: "Sessions",
        sessionsTitle: "Sessions",
        startConversation: "Start a conversation about this {type}",
        askQuestions: "Ask follow-up questions",
        model: "Model",
        sendPlaceholder: "Ask anything about your sources...",
        pressToSend: "Press {key} to send",
      },
      common: {
        notebook: "Notebook",
        insight: "Insight",
        insights: "Insights",
        note: "Note",
        notes: "Notes",
        noResults: "No results",
        references: "References",
      },
      navigation: {
        sources: "Sources",
      },
    },
  }),
}));

vi.mock("@/lib/hooks/use-modal-manager", () => ({
  useModalManager: () => ({
    openModal: hoisted.openModalMock,
  }),
}));

vi.mock("@/components/common/ContextIndicator", () => ({
  ContextIndicator: () => <div data-testid="context-indicator" />,
}));

vi.mock("@/components/source/MessageActions", () => ({
  MessageActions: () => <div data-testid="message-actions" />,
}));

vi.mock("@/components/source/SessionManager", () => ({
  SessionManager: ({
    onCreateSession,
    onSelectSession,
    onUpdateSession,
    onDeleteSession,
  }: {
    onCreateSession?: (title: string) => void;
    onSelectSession?: (sessionId: string) => void;
    onUpdateSession?: (sessionId: string, title: string) => void;
    onDeleteSession?: (sessionId: string) => void;
  }) => (
    <div>
      <button
        data-testid="session-manager-select"
        onClick={() => onSelectSession?.("session-2")}
        type="button"
      >
        session-manager-select
      </button>
      <button
        data-testid="session-manager-create"
        onClick={() => onCreateSession?.("new session")}
        type="button"
      >
        session-manager-create
      </button>
      <button
        data-testid="session-manager-update"
        onClick={() => onUpdateSession?.("session-1", "renamed")}
        type="button"
      >
        session-manager-update
      </button>
      <button
        data-testid="session-manager-delete"
        onClick={() => onDeleteSession?.("session-1")}
        type="button"
      >
        session-manager-delete
      </button>
    </div>
  ),
}));

vi.mock("./ModelSelector", () => ({
  ModelSelector: ({ disabled }: { disabled?: boolean }) => (
    <button data-testid="model-selector" disabled={disabled} type="button">
      model-selector
    </button>
  ),
}));

vi.mock("@/lib/utils/source-references", () => ({
  convertReferencesToCompactMarkdown: (content: string) =>
    content.replace(/\[source:[^\]]+\]/g, "[Reference](source:1)"),
  createCompactReferenceLinkComponent:
    (onReferenceClick: (type: string, id: string) => void) =>
    ({ children }: { children: ReactNode }) => (
      <button onClick={() => onReferenceClick("source", "source-99")} type="button">
        {children}
      </button>
    ),
}));

const baseProps = {
  messages: [],
  isStreaming: false,
  contextIndicators: null,
  onSendMessage: vi.fn(),
};

describe("ChatPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(window.HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: vi.fn(),
    });
  });

  it("renders empty state and keeps send disabled with blank input", () => {
    render(<ChatPanel {...baseProps} />);

    expect(screen.getByText("Start a conversation about this Sources")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Ask anything about your sources..." }),
    ).toBeDisabled();
  });

  it("submits message via keyboard shortcut", () => {
    const onSendMessage = vi.fn();
    render(<ChatPanel {...baseProps} onSendMessage={onSendMessage} />);

    const input = screen.getByPlaceholderText(/Ask anything about your sources/i);

    fireEvent.change(input, { target: { value: "hello context" } });
    fireEvent.keyDown(input, { key: "Enter", ctrlKey: true });

    expect(onSendMessage).toHaveBeenCalledWith("hello context", undefined);
    expect(input).toHaveValue("");
  });

  it("shows busy/disabled state while streaming", () => {
    render(
      <ChatPanel
        {...baseProps}
        isStreaming
        onModelChange={vi.fn()}
        modelOverride="gemini-3.1-pro"
      />,
    );

    const input = screen.getByPlaceholderText(/Ask anything about your sources/i);

    expect(input).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Ask anything about your sources..." }),
    ).toBeDisabled();
    expect(screen.getByTestId("model-selector")).toBeDisabled();
  });

  it("renders ai message actions, context badges, and notebook context indicator", () => {
    render(
      <ChatPanel
        {...baseProps}
        messages={[
          {
            id: "ai-1",
            type: "ai",
            content: "[source:abc] answer",
          },
        ]}
        contextIndicators={{
          sources: ["source-1", "source-2"],
          insights: ["insight-1"],
          notes: ["note-1"],
        }}
        notebookContextStats={{
          sourcesInsights: 1,
          sourcesFull: 2,
          notesCount: 3,
        }}
      />,
    );

    expect(screen.getByTestId("message-actions")).toBeInTheDocument();
    expect(screen.getByText(/2 Sources/)).toBeInTheDocument();
    expect(screen.getByText(/1 Insight/)).toBeInTheDocument();
    expect(screen.getByText(/1 Note/)).toBeInTheDocument();
    expect(screen.getByTestId("context-indicator")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reference" }));
    expect(hoisted.openModalMock).toHaveBeenCalledWith("source", "source-99");
  });

  it("opens session manager and selects an existing session", () => {
    const onCreateSession = vi.fn();
    const onSelectSession = vi.fn();
    const onUpdateSession = vi.fn();
    const onDeleteSession = vi.fn();

    render(
      <ChatPanel
        {...baseProps}
        sessions={[{ id: "session-1", title: "Current session" }]}
        currentSessionId="session-1"
        onCreateSession={onCreateSession}
        onSelectSession={onSelectSession}
        onDeleteSession={onDeleteSession}
        onUpdateSession={onUpdateSession}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /sessions/i }));
    fireEvent.click(screen.getByTestId("session-manager-create"));
    fireEvent.click(screen.getByTestId("session-manager-update"));
    fireEvent.click(screen.getByTestId("session-manager-delete"));
    fireEvent.click(screen.getByTestId("session-manager-select"));

    expect(onSelectSession).toHaveBeenCalledWith("session-2");
    expect(onCreateSession).toHaveBeenCalledWith("new session");
    expect(onUpdateSession).toHaveBeenCalledWith("session-1", "renamed");
    expect(onDeleteSession).toHaveBeenCalledWith("session-1");
  });

  it("renders human messages alongside markdown answers", () => {
    render(
      <ChatPanel
        {...baseProps}
        messages={[
          {
            id: "human-1",
            type: "human",
            content: "my question",
          },
          {
            id: "ai-2",
            type: "ai",
            content: "## Summary\n\n- item one\n\n| A | B |\n| --- | --- |\n| 1 | 2 |",
          },
        ]}
      />,
    );

    expect(screen.getByText("my question")).toBeInTheDocument();
    expect(screen.getByText("Summary")).toBeInTheDocument();
    expect(screen.getByText("item one")).toBeInTheDocument();
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getAllByTestId("message-actions")).toHaveLength(1);
  });

  it("shows all heading levels + ordered list markdown and handles modal-open failures", () => {
    hoisted.openModalMock.mockImplementationOnce(() => {
      throw new Error("modal-failed");
    });

    render(
      <ChatPanel
        {...baseProps}
        messages={[
          {
            id: "ai-3",
            type: "ai",
            content:
              "# H1\n## H2\n### H3\n#### H4\n##### H5\n###### H6\n1. first\n2. second\n[source:broken]",
          },
        ]}
      />,
    );

    expect(screen.getByText("H1")).toBeInTheDocument();
    expect(screen.getByText("H2")).toBeInTheDocument();
    expect(screen.getByText("H3")).toBeInTheDocument();
    expect(screen.getByText("H4")).toBeInTheDocument();
    expect(screen.getByText("H5")).toBeInTheDocument();
    expect(screen.getByText("H6")).toBeInTheDocument();
    expect(screen.getByRole("list")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reference" }));
    expect(toast.error).toHaveBeenCalledWith("No results");
  });
});
