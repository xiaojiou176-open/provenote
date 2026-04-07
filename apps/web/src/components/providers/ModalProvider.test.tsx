import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ModalProvider } from "./ModalProvider";

const hoisted = vi.hoisted(() => ({
  closeModalMock: vi.fn(),
  modalId: "item-1" as string | undefined,
  modalType: "source" as "source" | "note" | "insight" | undefined,
}));

vi.mock("@/lib/hooks/use-modal-manager", () => ({
  useModalManager: () => ({
    modalType: hoisted.modalType,
    modalId: hoisted.modalId,
    closeModal: hoisted.closeModalMock,
  }),
}));

vi.mock("@/components/source/SourceDialog", () => ({
  SourceDialog: ({
    open,
    sourceId,
    onOpenChange,
  }: {
    open: boolean;
    sourceId?: string;
    onOpenChange: (open: boolean) => void;
  }) => (
    <div data-open={String(open)} data-testid="source-dialog">
      <span>{sourceId ?? "no-source"}</span>
      <button onClick={() => onOpenChange(false)} type="button">
        close source
      </button>
      <button onClick={() => onOpenChange(true)} type="button">
        keep source open
      </button>
    </div>
  ),
}));

vi.mock("@/components/notebooks/NoteEditorDialog", () => ({
  NoteEditorDialog: ({
    open,
    note,
    onOpenChange,
  }: {
    open: boolean;
    note?: { id: string };
    onOpenChange: (open: boolean) => void;
  }) => (
    <div data-open={String(open)} data-testid="note-dialog">
      <span>{note?.id ?? "no-note"}</span>
      <button onClick={() => onOpenChange(false)} type="button">
        close note
      </button>
      <button onClick={() => onOpenChange(true)} type="button">
        keep note open
      </button>
    </div>
  ),
}));

vi.mock("@/components/source/SourceInsightDialog", () => ({
  SourceInsightDialog: ({
    open,
    insight,
    onOpenChange,
  }: {
    open: boolean;
    insight?: { id: string };
    onOpenChange: (open: boolean) => void;
  }) => (
    <div data-open={String(open)} data-testid="insight-dialog">
      <span>{insight?.id ?? "no-insight"}</span>
      <button onClick={() => onOpenChange(false)} type="button">
        close insight
      </button>
      <button onClick={() => onOpenChange(true)} type="button">
        keep insight open
      </button>
    </div>
  ),
}));

describe("ModalProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.modalId = "item-1";
    hoisted.modalType = "source";
  });

  it("opens the source dialog for source modal state and closes through manager", () => {
    render(<ModalProvider />);

    const sourceDialog = screen.getByTestId("source-dialog");
    expect(sourceDialog).toHaveAttribute("data-open", "true");
    expect(sourceDialog).toHaveTextContent("item-1");
    expect(screen.getByTestId("note-dialog")).toHaveAttribute("data-open", "false");

    fireEvent.click(screen.getByRole("button", { name: "close source" }));
    expect(hoisted.closeModalMock).toHaveBeenCalledTimes(1);
    expect(sourceDialog).toHaveAttribute("data-open", "false");
  });

  it("maps note modal state to NoteEditorDialog placeholder note payload", () => {
    hoisted.modalType = "note";
    hoisted.modalId = "note-7";

    render(<ModalProvider />);

    const noteDialog = screen.getByTestId("note-dialog");
    expect(noteDialog).toHaveAttribute("data-open", "true");
    expect(noteDialog).toHaveTextContent("note-7");
    expect(screen.getByTestId("source-dialog")).toHaveAttribute("data-open", "false");
  });

  it("maps insight modal state to SourceInsightDialog placeholder insight payload", () => {
    hoisted.modalType = "insight";
    hoisted.modalId = "insight-9";

    render(<ModalProvider />);

    const insightDialog = screen.getByTestId("insight-dialog");
    expect(insightDialog).toHaveAttribute("data-open", "true");
    expect(insightDialog).toHaveTextContent("insight-9");
  });

  it("falls back to undefined payloads and closes through note/insight onOpenChange", () => {
    hoisted.modalType = "note";
    hoisted.modalId = undefined;

    const { rerender } = render(<ModalProvider />);

    expect(screen.getByTestId("note-dialog")).toHaveTextContent("no-note");
    fireEvent.click(screen.getByRole("button", { name: "close note" }));
    expect(hoisted.closeModalMock).toHaveBeenCalledTimes(1);

    hoisted.modalType = "insight";
    rerender(<ModalProvider />);

    expect(screen.getByTestId("insight-dialog")).toHaveTextContent("no-insight");
    fireEvent.click(screen.getByRole("button", { name: "close insight" }));
    expect(hoisted.closeModalMock).toHaveBeenCalledTimes(2);
  });

  it("does not close modal manager when dialogs emit open=true", () => {
    render(<ModalProvider />);

    fireEvent.click(screen.getByRole("button", { name: "keep source open" }));
    fireEvent.click(screen.getByRole("button", { name: "keep note open" }));
    fireEvent.click(screen.getByRole("button", { name: "keep insight open" }));

    expect(hoisted.closeModalMock).not.toHaveBeenCalled();
  });
});
