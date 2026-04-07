import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { toast } from "sonner";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useNotebooks } from "@/lib/hooks/use-notebooks";
import { useCreateNote } from "@/lib/hooks/use-notes";
import { useTranslation } from "@/lib/hooks/use-translation";
import { SaveToNotebooksDialog } from "./SaveToNotebooksDialog";

const mutateAsync = vi.fn();

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/lib/hooks/use-notebooks");
vi.mock("@/lib/hooks/use-notes");
vi.mock("@/lib/hooks/use-translation");

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({
    children,
    onClick,
    type = "button",
    disabled,
    ...props
  }: {
    children: ReactNode;
    onClick?: () => void;
    type?: "button" | "submit" | "reset";
    disabled?: boolean;
    "aria-busy"?: boolean;
    className?: string;
  }) => (
    <button data-disabled={disabled ? "true" : "false"} onClick={onClick} type={type} {...props}>
      {children}
    </button>
  ),
}));

vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({ open, children }: { open: boolean; children: ReactNode }) =>
    open ? <div>{children}</div> : null,
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  DialogFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/checkbox-list", () => ({
  CheckboxList: ({
    items,
    selectedIds,
    onToggle,
    emptyMessage,
  }: {
    items: Array<{ id: string; title: string }>;
    selectedIds: string[];
    onToggle: (id: string) => void;
    emptyMessage?: string;
  }) => (
    <div>
      {items.length === 0 ? (
        <span>{emptyMessage ?? "empty"}</span>
      ) : (
        items.map((item) => (
          <button key={item.id} onClick={() => onToggle(item.id)} type="button">
            {item.title}:{selectedIds.includes(item.id) ? "on" : "off"}
          </button>
        ))
      )}
    </div>
  ),
}));

describe("SaveToNotebooksDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        searchPage: {
          saveToNotebooks: "Save to notebooks",
          selectNotebook: "Select notebook",
          saveSuccess: "Saved",
          saveError: "Save failed",
          saveToNotebook: "Save",
          saving: "Saving",
        },
        sources: {
          noNotebooksFound: "No notebooks",
        },
        common: {
          cancel: "Cancel",
        },
      },
    } as unknown as ReturnType<typeof useTranslation>);

    vi.mocked(useCreateNote).mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateNote>);

    vi.mocked(useNotebooks).mockReturnValue({
      data: [
        { id: "nb-1", name: "Notebook A", description: "A" },
        { id: "nb-2", name: "Notebook B", description: "B" },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebooks>);
  });

  it("saves answer to all selected notebooks", async () => {
    const onOpenChange = vi.fn();
    mutateAsync.mockResolvedValue(undefined);

    render(
      <SaveToNotebooksDialog
        open
        onOpenChange={onOpenChange}
        question="What is context?"
        answer="Context answer"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Notebook A:off" }));
    fireEvent.click(screen.getByRole("button", { name: "Notebook B:off" }));
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(2);
      expect(mutateAsync).toHaveBeenNthCalledWith(1, {
        title: "What is context?",
        content: "Context answer",
        note_type: "ai",
        notebook_id: "nb-1",
      });
      expect(mutateAsync).toHaveBeenNthCalledWith(2, {
        title: "What is context?",
        content: "Context answer",
        note_type: "ai",
        notebook_id: "nb-2",
      });
      expect(toast.success).toHaveBeenCalledWith("Saved");
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it("shows error toast when save fails", async () => {
    mutateAsync.mockRejectedValue(new Error("save failed"));

    render(<SaveToNotebooksDialog open onOpenChange={vi.fn()} question="Q" answer="A" />);

    fireEvent.click(screen.getByRole("button", { name: "Notebook A:off" }));
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Save failed");
    });
  });

  it("shows select-notebook toast when nothing is selected and allows cancel", () => {
    const onOpenChange = vi.fn();
    render(<SaveToNotebooksDialog open onOpenChange={onOpenChange} question="Q" answer="A" />);

    expect(screen.getByRole("button", { name: "Save" })).toHaveAttribute("data-disabled", "true");
    expect(toast.error).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("lets a user deselect notebooks and still guards save when selection becomes empty", () => {
    render(<SaveToNotebooksDialog open onOpenChange={vi.fn()} question="Q" answer="A" />);

    fireEvent.click(screen.getByRole("button", { name: "Notebook A:off" }));
    fireEvent.click(screen.getByRole("button", { name: "Notebook A:on" }));
    expect(screen.getByRole("button", { name: "Notebook A:off" })).toBeInTheDocument();

    const saveButton = screen.getByRole("button", { name: "Save" });
    expect(saveButton).toHaveAttribute("data-disabled", "true");
    fireEvent.click(saveButton);

    expect(toast.error).toHaveBeenCalledWith("Select notebook");
  });

  it("renders loading state and then empty notebook message", () => {
    vi.mocked(useNotebooks).mockReturnValue({
      data: [],
      isLoading: true,
    } as unknown as ReturnType<typeof useNotebooks>);

    const { rerender } = render(
      <SaveToNotebooksDialog open onOpenChange={vi.fn()} question="Q" answer="A" />,
    );
    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();

    vi.mocked(useNotebooks).mockReturnValue({
      data: [],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebooks>);
    rerender(<SaveToNotebooksDialog open onOpenChange={vi.fn()} question="Q" answer="A" />);

    expect(screen.getByText("No notebooks")).toBeInTheDocument();
  });

  it("shows saving copy and busy attributes while mutation is pending", () => {
    vi.mocked(useCreateNote).mockReturnValue({
      mutateAsync,
      isPending: true,
    } as unknown as ReturnType<typeof useCreateNote>);

    render(<SaveToNotebooksDialog open onOpenChange={vi.fn()} question="Q" answer="A" />);

    const saveButton = screen.getByRole("button", { name: "Saving" });
    expect(saveButton).toHaveAttribute("data-disabled", "true");
    expect(saveButton).toHaveAttribute("aria-busy", "true");
  });
});
