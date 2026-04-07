import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useDeleteNote } from "@/lib/hooks/use-notes";
import { useTranslation } from "@/lib/hooks/use-translation";
import { useNotebookColumnsStore } from "@/lib/stores/notebook-columns-store";
import { NotesColumn } from "./NotesColumn";

const mutateAsync = vi.fn();

vi.mock("@/lib/hooks/use-notes");
vi.mock("@/lib/hooks/use-translation");
vi.mock("@/lib/stores/notebook-columns-store");

vi.mock("@/components/notebooks/CollapsibleColumn", () => ({
  CollapsibleColumn: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  createCollapseButton: () => <button type="button">collapse-notes</button>,
}));

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

vi.mock("@/components/common/EmptyState", () => ({
  EmptyState: ({ title, description }: { title: string; description: string }) => (
    <div>
      <p>{title}</p>
      <p>{description}</p>
    </div>
  ),
}));

vi.mock("@/components/common/ContextToggle", () => ({
  ContextToggle: ({ onChange }: { onChange: (mode: "off" | "full" | "insights") => void }) => (
    <button onClick={() => onChange("off")} type="button">
      context-toggle
    </button>
  ),
}));

vi.mock("@/components/common/ConfirmDialog", () => ({
  ConfirmDialog: ({
    open,
    onConfirm,
  }: {
    open: boolean;
    onConfirm: () => Promise<void> | void;
  }) => (
    <button
      data-open={String(open)}
      data-testid="confirm-delete"
      onClick={() => void onConfirm()}
      type="button"
    >
      confirm-delete
    </button>
  ),
}));

vi.mock("@/components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuItem: ({
    children,
    onClick,
  }: {
    children: ReactNode;
    onClick?: (event: React.MouseEvent) => void;
  }) => (
    <button onClick={(event) => onClick?.(event)} type="button">
      {children}
    </button>
  ),
}));

vi.mock("./NoteEditorDialog", () => ({
  NoteEditorDialog: ({
    open,
    note,
    onOpenChange,
  }: {
    open: boolean;
    note?: { id: string };
    onOpenChange: (open: boolean) => void;
  }) => (
    <div data-testid="note-editor">
      <span>open:{String(open)}</span>
      <span>note:{note?.id ?? "none"}</span>
      <button onClick={() => onOpenChange(true)} type="button">
        editor-open
      </button>
      <button onClick={() => onOpenChange(false)} type="button">
        editor-close
      </button>
    </div>
  ),
}));

describe("NotesColumn", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useDeleteNote).mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteNote>);

    vi.mocked(useNotebookColumnsStore).mockReturnValue({
      notesCollapsed: false,
      toggleNotes: vi.fn(),
    } as unknown as ReturnType<typeof useNotebookColumnsStore>);

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        common: {
          notes: "Notes",
          writeNote: "Write Note",
          actions: "Actions",
          delete: "Delete",
          aiGenerated: "AI",
          human: "Human",
        },
        notebooks: {
          noNotesYet: "No notes yet",
          deleteNote: "Delete Note",
          deleteNoteConfirm: "Delete this note?",
        },
        sources: {
          createFirstNote: "Create your first note",
        },
      },
      language: "en",
    } as unknown as ReturnType<typeof useTranslation>);
  });

  it("shows empty state and opens note editor when create button is clicked", () => {
    render(<NotesColumn notes={[]} isLoading={false} notebookId="nb-1" />);

    expect(screen.getByText("No notes yet")).toBeInTheDocument();
    expect(screen.getByText("Create your first note")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Write Note" }));

    expect(screen.getByTestId("note-editor")).toHaveTextContent("open:true");
  });

  it("propagates context mode changes and deletes notes through confirmation", async () => {
    const onContextModeChange = vi.fn();
    mutateAsync.mockResolvedValue(undefined);

    render(
      <NotesColumn
        notes={[
          {
            id: "note-1",
            title: "My note",
            content: "Body",
            note_type: "human",
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
          },
        ]}
        isLoading={false}
        notebookId="nb-1"
        contextSelections={{ "note-1": "full" }}
        onContextModeChange={onContextModeChange}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "context-toggle" }));
    expect(onContextModeChange).toHaveBeenCalledWith("note-1", "off");

    fireEvent.click(screen.getByRole("button", { name: "Delete Note" }));
    fireEvent.click(screen.getByTestId("confirm-delete"));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith("note-1");
    });
  });

  it("returns early when no note is selected for deletion and logs delete failures", async () => {
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    mutateAsync.mockRejectedValueOnce(new Error("delete failed"));

    render(
      <NotesColumn
        notes={[
          {
            id: "note-2",
            title: "Second note",
            content: "Body",
            note_type: "ai",
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
          },
        ]}
        isLoading={false}
        notebookId="nb-2"
      />,
    );

    fireEvent.click(screen.getByTestId("confirm-delete"));
    expect(mutateAsync).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Delete Note" }));
    fireEvent.click(screen.getByTestId("confirm-delete"));

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalled();
    });
  });

  it("opens editor from note actions/content and handles dialog open-state callbacks", () => {
    render(
      <NotesColumn
        notes={[
          {
            id: "note-3",
            title: "Editable note",
            content: "Body",
            note_type: "human",
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
          },
        ]}
        isLoading={false}
        notebookId="nb-3"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Actions" }));
    fireEvent.click(screen.getAllByRole("button", { name: "Editable note" })[0]);
    expect(screen.getByTestId("note-editor")).toHaveTextContent("note:note-3");

    fireEvent.click(screen.getByRole("button", { name: "editor-open" }));
    expect(screen.getByTestId("note-editor")).toHaveTextContent("open:true");

    fireEvent.click(screen.getByRole("button", { name: "editor-close" }));
    expect(screen.getByTestId("note-editor")).toHaveTextContent("open:false");

    fireEvent.click(screen.getAllByRole("button", { name: "Editable note" })[1]);
    expect(screen.getByTestId("note-editor")).toHaveTextContent("note:note-3");
  });

  it("renders loading state while notes are fetching", () => {
    render(<NotesColumn notes={undefined} isLoading notebookId="nb-loading" />);

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });
});
