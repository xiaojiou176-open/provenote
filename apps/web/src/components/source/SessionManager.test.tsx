import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useModels } from "@/lib/hooks/use-models";
import { useTranslation } from "@/lib/hooks/use-translation";
import { SessionManager } from "./SessionManager";

vi.mock("date-fns", () => ({
  formatDistanceToNow: vi.fn(() => "moments ago"),
}));

vi.mock("@/lib/hooks/use-models");
vi.mock("@/lib/hooks/use-translation");

vi.mock("@/components/ui/alert-dialog", () => ({
  AlertDialog: ({
    open,
    children,
    onOpenChange,
  }: {
    open: boolean;
    children: ReactNode;
    onOpenChange?: (open: boolean) => void;
  }) =>
    open ? (
      <div>
        {children}
        <button onClick={() => onOpenChange?.(false)} type="button">
          close-delete-dialog
        </button>
      </div>
    ) : null,
  AlertDialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  AlertDialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  AlertDialogFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogCancel: ({ children }: { children: ReactNode }) => (
    <button type="button">{children}</button>
  ),
  AlertDialogAction: ({ children, onClick }: { children: ReactNode; onClick?: () => void }) => (
    <button onClick={onClick} type="button">
      {children}
    </button>
  ),
}));

vi.mock("@/components/ui/scroll-area", () => ({
  ScrollArea: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

describe("SessionManager", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        common: {
          create: "Create",
          cancel: "Cancel",
          edit: "Edit",
          delete: "Delete",
          customModel: "Custom model",
          loading: "Loading",
        },
        chat: {
          sessions: "Sessions",
          sessionTitlePlaceholder: "Session title",
          noSessions: "No sessions",
          createToStart: "Create to start",
          messagesCount: "{count} messages",
          deleteSession: "Delete session",
          deleteSessionDesc: "Delete this session?",
        },
      },
      language: "en",
    } as unknown as ReturnType<typeof useTranslation>);

    vi.mocked(useModels).mockReturnValue({
      data: [{ id: "m-1", name: "Gemini Fast" }],
    } as unknown as ReturnType<typeof useModels>);
  });

  it("creates a new session via Enter key", () => {
    const onCreateSession = vi.fn();

    render(
      <SessionManager
        sessions={[]}
        currentSessionId={null}
        onCreateSession={onCreateSession}
        onSelectSession={vi.fn()}
        onUpdateSession={vi.fn()}
        onDeleteSession={vi.fn()}
        loadingSessions={false}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Create" }));
    fireEvent.change(screen.getByPlaceholderText("Session title"), {
      target: { value: "  New Session  " },
    });
    fireEvent.keyDown(screen.getByPlaceholderText("Session title"), { key: "Enter" });

    expect(onCreateSession).toHaveBeenCalledWith("New Session");
  });

  it("edits and deletes an existing session", () => {
    const onUpdateSession = vi.fn();
    const onDeleteSession = vi.fn();

    render(
      <SessionManager
        sessions={[
          {
            id: "sess-1",
            title: "Old title",
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
            message_count: 2,
            model_override: "m-1",
          },
        ]}
        currentSessionId={"sess-1"}
        onCreateSession={vi.fn()}
        onSelectSession={vi.fn()}
        onUpdateSession={onUpdateSession}
        onDeleteSession={onDeleteSession}
        loadingSessions={false}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    fireEvent.change(screen.getByDisplayValue("Old title"), { target: { value: "Renamed" } });
    fireEvent.keyDown(screen.getByDisplayValue("Renamed"), { key: "Enter" });

    expect(onUpdateSession).toHaveBeenCalledWith("sess-1", "Renamed");

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    fireEvent.click(screen.getAllByRole("button", { name: "Delete" })[1]);

    expect(onDeleteSession).toHaveBeenCalledWith("sess-1");
  });

  it("renders loading and empty states", () => {
    const { rerender } = render(
      <SessionManager
        sessions={[]}
        currentSessionId={null}
        onCreateSession={vi.fn()}
        onSelectSession={vi.fn()}
        onUpdateSession={vi.fn()}
        onDeleteSession={vi.fn()}
        loadingSessions
      />,
    );

    expect(screen.getByText("Loading")).toBeInTheDocument();

    rerender(
      <SessionManager
        sessions={[]}
        currentSessionId={null}
        onCreateSession={vi.fn()}
        onSelectSession={vi.fn()}
        onUpdateSession={vi.fn()}
        onDeleteSession={vi.fn()}
        loadingSessions={false}
      />,
    );

    expect(screen.getByText("No sessions")).toBeInTheDocument();
    expect(screen.getByText("Create to start")).toBeInTheDocument();
  });

  it("ignores empty create, supports escape cancel, and selects session from both click targets", () => {
    const onCreateSession = vi.fn();
    const onSelectSession = vi.fn();
    const onUpdateSession = vi.fn();

    render(
      <SessionManager
        sessions={[
          {
            id: "sess-2",
            title: "Session Two",
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
            message_count: 0,
            model_override: "unknown-model",
          },
        ]}
        currentSessionId={null}
        onCreateSession={onCreateSession}
        onSelectSession={onSelectSession}
        onUpdateSession={onUpdateSession}
        onDeleteSession={vi.fn()}
        loadingSessions={false}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Create" }));
    fireEvent.change(screen.getByPlaceholderText("Session title"), {
      target: { value: "   " },
    });
    fireEvent.keyDown(screen.getByPlaceholderText("Session title"), { key: "Enter" });
    expect(onCreateSession).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    fireEvent.change(screen.getByDisplayValue("Session Two"), { target: { value: "Changed" } });
    fireEvent.keyDown(screen.getByDisplayValue("Changed"), { key: "Escape" });
    expect(onUpdateSession).not.toHaveBeenCalled();

    const sessionButtons = screen.getAllByRole("button", { name: "Sessions: Session Two" });
    fireEvent.click(sessionButtons[0]);
    fireEvent.click(sessionButtons[1]);
    expect(onSelectSession).toHaveBeenCalledTimes(2);
    expect(onSelectSession).toHaveBeenNthCalledWith(1, "sess-2");
    expect(onSelectSession).toHaveBeenNthCalledWith(2, "sess-2");
    expect(screen.getByText("Custom model")).toBeInTheDocument();
  });

  it("ignores non-enter create key, clears create input on cancel, and skips blank save", () => {
    const onCreateSession = vi.fn();
    const onUpdateSession = vi.fn();
    const onDeleteSession = vi.fn();

    render(
      <SessionManager
        sessions={[
          {
            id: "sess-3",
            title: "Session Three",
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
            message_count: 1,
            model_override: "m-1",
          },
        ]}
        currentSessionId={null}
        onCreateSession={onCreateSession}
        onSelectSession={vi.fn()}
        onUpdateSession={onUpdateSession}
        onDeleteSession={onDeleteSession}
        loadingSessions={false}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Create" }));
    const createInput = screen.getByPlaceholderText("Session title");
    fireEvent.change(createInput, { target: { value: "New value" } });
    fireEvent.keyDown(createInput, { key: "A" });
    expect(onCreateSession).toHaveBeenCalledTimes(0);

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByPlaceholderText("Session title")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    const editInput = screen.getByDisplayValue("Session Three");
    fireEvent.change(editInput, { target: { value: "   " } });
    fireEvent.keyDown(editInput, { key: "Enter" });
    expect(onUpdateSession).toHaveBeenCalledTimes(0);
    fireEvent.keyDown(editInput, { key: "Escape" });

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    fireEvent.click(screen.getByRole("button", { name: "close-delete-dialog" }));
    expect(screen.queryByText("Delete this session?")).not.toBeInTheDocument();
    expect(onDeleteSession).toHaveBeenCalledTimes(0);
  });
});
