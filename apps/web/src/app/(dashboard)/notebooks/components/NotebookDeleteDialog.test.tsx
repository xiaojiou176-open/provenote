import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useDeleteNotebook, useNotebookDeletePreview } from "@/lib/hooks/use-notebooks";
import { NotebookDeleteDialog } from "./NotebookDeleteDialog";

const push = vi.fn();
const mutateAsync = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
}));

vi.mock("@/lib/hooks/use-notebooks", () => ({
  useNotebookDeletePreview: vi.fn(),
  useDeleteNotebook: vi.fn(),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      common: {
        error: "Error",
        refreshPage: "Please refresh",
        cancel: "Cancel",
        delete: "Delete",
        deleting: "Deleting",
      },
      notebooks: {
        deleteNotebook: "Delete notebook",
        deleteNotebookDesc: "Delete {name}?",
        deleteNotebookLoading: "Loading delete preview",
        deleteNotebookNotes: "Contains {count} notes",
        deleteNotebookNoNotes: "No notes in this notebook",
        deleteNotebookSharedSources: "Has {count} shared sources",
        deleteNotebookNoSources: "No sources linked",
        deleteNotebookExclusiveSources: "Contains {count} exclusive sources",
        deleteExclusiveSourcesLabel: "Delete exclusive sources",
        keepExclusiveSourcesLabel: "Keep exclusive sources",
      },
    },
  }),
}));

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: ({ className }: { className?: string }) => (
    <span data-testid="loading-spinner" className={className}>
      spinner
    </span>
  ),
}));

vi.mock("@/components/ui/alert-dialog", () => ({
  AlertDialog: ({ open, children }: { open: boolean; children: ReactNode }) =>
    open ? <div>{children}</div> : null,
  AlertDialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  AlertDialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  AlertDialogFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogCancel: ({
    children,
    ...props
  }: {
    children: ReactNode;
    disabled?: boolean;
    className?: string;
  }) => (
    <button type="button" {...props}>
      {children}
    </button>
  ),
  AlertDialogAction: ({
    children,
    onClick,
    ...props
  }: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    className?: string;
    "aria-busy"?: boolean;
  }) => (
    <button type="button" onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

vi.mock("@/components/ui/radio-group", () => ({
  RadioGroup: ({
    onValueChange,
    children,
    disabled,
  }: {
    value: string;
    onValueChange: (value: string) => void;
    disabled?: boolean;
    children: ReactNode;
  }) => (
    <div
      aria-disabled={disabled}
      onChange={(event) => onValueChange((event.target as HTMLInputElement).value)}
    >
      {children}
    </div>
  ),
  RadioGroupItem: ({ value, id, disabled }: { value: string; id: string; disabled?: boolean }) => (
    <input id={id} type="radio" name="source-action" value={value} disabled={disabled} />
  ),
}));

describe("NotebookDeleteDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useRouter).mockReturnValue({
      push,
    } as unknown as ReturnType<typeof useRouter>);

    vi.mocked(useDeleteNotebook).mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteNotebook>);

    vi.mocked(useNotebookDeletePreview).mockReturnValue({
      data: {
        note_count: 0,
        shared_source_count: 0,
        exclusive_source_count: 0,
      },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useNotebookDeletePreview>);
  });

  it("renders loading preview state and blocks confirm", () => {
    vi.mocked(useNotebookDeletePreview).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as unknown as ReturnType<typeof useNotebookDeletePreview>);

    render(
      <NotebookDeleteDialog open onOpenChange={vi.fn()} notebookId="nb-1" notebookName="Demo" />,
    );

    expect(screen.getByText("Loading delete preview")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete" })).toBeDisabled();
  });

  it("shows preview error", () => {
    vi.mocked(useNotebookDeletePreview).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("preview failed"),
    } as unknown as ReturnType<typeof useNotebookDeletePreview>);

    render(
      <NotebookDeleteDialog open onOpenChange={vi.fn()} notebookId="nb-1" notebookName="Demo" />,
    );

    expect(screen.getByText("Error: preview failed")).toBeInTheDocument();
  });

  it("renders no-notes/no-sources empty messages from preview", () => {
    render(
      <NotebookDeleteDialog open onOpenChange={vi.fn()} notebookId="nb-1" notebookName="Demo" />,
    );

    expect(screen.getByText("No notes in this notebook")).toBeInTheDocument();
    expect(screen.getByText("No sources linked")).toBeInTheDocument();
  });

  it("deletes notebook with exclusive source removal and redirects", async () => {
    const onOpenChange = vi.fn();
    mutateAsync.mockResolvedValue(undefined);

    vi.mocked(useNotebookDeletePreview).mockReturnValue({
      data: {
        note_count: 3,
        shared_source_count: 2,
        exclusive_source_count: 1,
      },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useNotebookDeletePreview>);

    render(
      <NotebookDeleteDialog
        open
        onOpenChange={onOpenChange}
        notebookId="nb-1"
        notebookName="Demo"
        redirectAfterDelete
      />,
    );

    fireEvent.click(screen.getByLabelText("Delete exclusive sources"));
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        id: "nb-1",
        deleteExclusiveSources: true,
      });
      expect(onOpenChange).toHaveBeenCalledWith(false);
      expect(push).toHaveBeenCalledWith("/notebooks");
    });
  });
});
