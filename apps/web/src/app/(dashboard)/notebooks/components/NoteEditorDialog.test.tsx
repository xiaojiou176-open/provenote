import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { useCreateNote, useNote, useUpdateNote } from "@/lib/hooks/use-notes";
import { useTranslation } from "@/lib/hooks/use-translation";
import { appLog } from "@/lib/log";
import { NoteEditorDialog } from "./NoteEditorDialog";

const invalidateQueries = vi.fn();

vi.mock("@tanstack/react-query", async () => {
  const actual =
    await vi.importActual<typeof import("@tanstack/react-query")>("@tanstack/react-query");
  return {
    ...actual,
    useQueryClient: () => ({ invalidateQueries }),
  };
});

vi.mock("@/lib/hooks/use-notes");
vi.mock("@/lib/log", () => ({
  appLog: {
    error: vi.fn(),
  },
}));
vi.mock("@/lib/hooks/use-translation");

vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({ open, children }: { open: boolean; children: ReactNode }) =>
    open ? <div data-testid="dialog-root">{children}</div> : null,
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
}));

vi.mock("@/components/common/InlineEdit", () => ({
  InlineEdit: ({ onSave, value }: { onSave: (value: string) => void; value: string }) => (
    <button onClick={() => onSave(value ? `${value}-edited` : "note-title")} type="button">
      edit-title
    </button>
  ),
}));

vi.mock("@/components/ui/markdown-editor", () => ({
  MarkdownEditor: ({
    value,
    onChange,
    placeholder,
  }: {
    value: string;
    onChange: (value: string) => void;
    placeholder: string;
  }) => (
    <textarea
      aria-label={placeholder}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  ),
}));

describe("NoteEditorDialog", () => {
  const createMutateAsync = vi.fn();
  const updateMutateAsync = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        common: {
          cancel: "Cancel",
          saving: "Saving",
          creating: "Creating",
          loading: "Loading",
        },
        sources: {
          editNote: "Edit Note",
          createNote: "Create Note",
          addTitle: "Add title",
          untitledNote: "Untitled",
          writeNotePlaceholder: "Write note",
          saveNote: "Save Note",
          createNoteBtn: "Create Note",
        },
      },
    } as unknown as ReturnType<typeof useTranslation>);

    vi.mocked(useCreateNote).mockReturnValue({
      mutateAsync: createMutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateNote>);

    vi.mocked(useUpdateNote).mockReturnValue({
      mutateAsync: updateMutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateNote>);

    vi.mocked(useNote).mockReturnValue({
      data: undefined,
      isLoading: false,
    } as unknown as ReturnType<typeof useNote>);
  });

  it("blocks create when notebook id is missing", async () => {
    const onOpenChange = vi.fn();

    render(<NoteEditorDialog open onOpenChange={onOpenChange} notebookId="" note={undefined} />);

    fireEvent.change(screen.getByRole("textbox", { name: "Write note" }), {
      target: { value: "new content" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create Note" }));

    await waitFor(() => {
      expect(appLog.error).toHaveBeenCalledWith(
        "note-editor-dialog",
        "Cannot create note without notebook_id",
      );
      expect(createMutateAsync).not.toHaveBeenCalled();
      expect(onOpenChange).not.toHaveBeenCalled();
    });
  });

  it("updates existing note with prefixed id and invalidates notebook notes", async () => {
    const onOpenChange = vi.fn();
    updateMutateAsync.mockResolvedValue(undefined);

    render(
      <NoteEditorDialog
        open
        onOpenChange={onOpenChange}
        notebookId="nb-1"
        note={{ id: "123", title: "old", content: "old content" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "edit-title" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Write note" }), {
      target: { value: "updated content" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save Note" }));

    await waitFor(() => {
      expect(updateMutateAsync).toHaveBeenCalledWith({
        id: "note:123",
        data: {
          title: "old-edited",
          content: "updated content",
        },
      });
      expect(invalidateQueries).toHaveBeenCalledWith({
        queryKey: QUERY_KEYS.notes("nb-1"),
      });
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it("creates a note when notebook id is present and closes from cancel action", async () => {
    const onOpenChange = vi.fn();
    createMutateAsync.mockResolvedValue(undefined);

    render(
      <NoteEditorDialog open onOpenChange={onOpenChange} notebookId="nb-create" note={undefined} />,
    );

    fireEvent.change(screen.getByRole("textbox", { name: "Write note" }), {
      target: { value: "draft body" },
    });
    fireEvent.submit(screen.getByRole("button", { name: "Create Note" }).closest("form")!);

    await waitFor(() => {
      expect(createMutateAsync).toHaveBeenCalledWith({
        title: undefined,
        content: "draft body",
        note_type: "human",
        notebook_id: "nb-create",
      });
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("resets quietly when dialog is closed and handles fullscreen observer callback", async () => {
    const mutationObserverCallback = vi.fn();
    const observe = vi.fn();
    const disconnect = vi.fn();
    class MutationObserverMock {
      constructor(cb: MutationCallback) {
        mutationObserverCallback.mockImplementation(cb);
      }
      observe = observe;
      disconnect = disconnect;
    }
    vi.stubGlobal("MutationObserver", MutationObserverMock as unknown as typeof MutationObserver);

    const { rerender } = render(
      <NoteEditorDialog
        open={false}
        onOpenChange={vi.fn()}
        notebookId="nb-observer"
        note={undefined}
      />,
    );

    act(() => {
      rerender(
        <NoteEditorDialog open onOpenChange={vi.fn()} notebookId="nb-observer" note={undefined} />,
      );
    });

    act(() => {
      mutationObserverCallback([], {} as MutationObserver);
    });
    await waitFor(() => {
      expect(observe).toHaveBeenCalled();
    });
    expect(disconnect).toHaveBeenCalledTimes(1);
  });
});
