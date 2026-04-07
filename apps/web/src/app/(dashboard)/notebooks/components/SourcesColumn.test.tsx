import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useModalManager } from "@/lib/hooks/use-modal-manager";
import {
  useDeleteSource,
  useRemoveSourceFromNotebook,
  useRetrySource,
} from "@/lib/hooks/use-sources";
import { useTranslation } from "@/lib/hooks/use-translation";
import { appLog } from "@/lib/log";
import { useNotebookColumnsStore } from "@/lib/stores/notebook-columns-store";
import { SourcesColumn } from "./SourcesColumn";

const openModal = vi.fn();
const deleteMutateAsync = vi.fn();
const retryMutateAsync = vi.fn();
const removeMutateAsync = vi.fn();

vi.mock("@/lib/hooks/use-modal-manager");
vi.mock("@/lib/hooks/use-sources");
vi.mock("@/lib/log", () => ({
  appLog: {
    error: vi.fn(),
  },
}));
vi.mock("@/lib/hooks/use-translation");
vi.mock("@/lib/stores/notebook-columns-store");

vi.mock("@/components/notebooks/CollapsibleColumn", () => ({
  CollapsibleColumn: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  createCollapseButton: () => <button type="button">collapse-sources</button>,
}));

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

vi.mock("@/components/common/EmptyState", () => ({
  EmptyState: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock("@/components/common/ConfirmDialog", () => ({
  ConfirmDialog: ({
    open,
    title,
    onConfirm,
  }: {
    open: boolean;
    title: string;
    onConfirm: () => Promise<void> | void;
  }) =>
    open ? (
      <button onClick={() => void onConfirm()} type="button">
        confirm-{title}
      </button>
    ) : null,
}));

vi.mock("@/components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuItem: ({ children, onClick }: { children: ReactNode; onClick?: () => void }) => (
    <button onClick={onClick} type="button">
      {children}
    </button>
  ),
}));

vi.mock("@/components/sources/SourceCard", () => ({
  SourceCard: ({
    source,
    onClick,
    onDelete,
    onRetry,
    onRemoveFromNotebook,
    onContextModeChange,
  }: {
    source: { id: string };
    onClick: (id: string) => void;
    onDelete: (id: string) => void;
    onRetry: (id: string) => void;
    onRemoveFromNotebook: (id: string) => void;
    onContextModeChange?: (mode: "off" | "insights" | "full") => void;
  }) => (
    <div>
      <button onClick={() => onClick(source.id)} type="button">
        open-source
      </button>
      <button onClick={() => onDelete(source.id)} type="button">
        delete-source
      </button>
      <button onClick={() => onRetry(source.id)} type="button">
        retry-source
      </button>
      <button onClick={() => onRemoveFromNotebook(source.id)} type="button">
        remove-source
      </button>
      <button onClick={() => onContextModeChange?.("off")} type="button">
        set-source-context
      </button>
    </div>
  ),
}));

vi.mock("@/components/sources/AddSourceDialog", () => ({
  AddSourceDialog: ({ open }: { open: boolean }) => (
    <div data-testid="add-source">{String(open)}</div>
  ),
}));

vi.mock("@/components/sources/AddExistingSourceDialog", () => ({
  AddExistingSourceDialog: ({ open }: { open: boolean }) => (
    <div data-testid="add-existing-source">{String(open)}</div>
  ),
}));

describe("SourcesColumn", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        navigation: { sources: "Sources" },
        common: { delete: "Delete", remove: "Remove" },
        sources: {
          addSource: "Add Source",
          addExistingTitle: "Add Existing",
          noSourcesYet: "No sources",
          createFirstSource: "Create first source",
          delete: "Delete Source",
          deleteConfirm: "Delete source confirm",
          removeFromNotebook: "Remove from notebook",
          removeConfirm: "Remove source confirm",
        },
      },
    } as unknown as ReturnType<typeof useTranslation>);

    vi.mocked(useModalManager).mockReturnValue({
      openModal,
    } as unknown as ReturnType<typeof useModalManager>);

    vi.mocked(useNotebookColumnsStore).mockReturnValue({
      sourcesCollapsed: false,
      toggleSources: vi.fn(),
    } as unknown as ReturnType<typeof useNotebookColumnsStore>);

    vi.mocked(useDeleteSource).mockReturnValue({
      mutateAsync: deleteMutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteSource>);

    vi.mocked(useRetrySource).mockReturnValue({
      mutateAsync: retryMutateAsync,
    } as unknown as ReturnType<typeof useRetrySource>);

    vi.mocked(useRemoveSourceFromNotebook).mockReturnValue({
      mutateAsync: removeMutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useRemoveSourceFromNotebook>);
  });

  it("opens source details and retries source processing", async () => {
    retryMutateAsync.mockResolvedValue(undefined);

    render(
      <SourcesColumn
        sources={[
          {
            id: "source-1",
            title: "Source",
            asset: null,
            embedded: true,
            embedded_chunks: 0,
            insights_count: 0,
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
          },
        ]}
        isLoading={false}
        notebookId="nb-1"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "open-source" }));
    expect(openModal).toHaveBeenCalledWith("source", "source-1");

    fireEvent.click(screen.getByRole("button", { name: "retry-source" }));

    await waitFor(() => {
      expect(retryMutateAsync).toHaveBeenCalledWith("source-1");
    });
  });

  it("confirms delete and remove-from-notebook actions", async () => {
    const onRefresh = vi.fn();
    deleteMutateAsync.mockResolvedValue(undefined);
    removeMutateAsync.mockResolvedValue(undefined);

    render(
      <SourcesColumn
        sources={[
          {
            id: "source-1",
            title: "Source",
            asset: null,
            embedded: true,
            embedded_chunks: 0,
            insights_count: 0,
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
          },
        ]}
        isLoading={false}
        notebookId="nb-1"
        onRefresh={onRefresh}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "delete-source" }));
    fireEvent.click(screen.getByRole("button", { name: "confirm-Delete Source" }));

    await waitFor(() => {
      expect(deleteMutateAsync).toHaveBeenCalledWith("source-1");
      expect(onRefresh).toHaveBeenCalledTimes(1);
    });

    fireEvent.click(screen.getByRole("button", { name: "remove-source" }));
    fireEvent.click(screen.getByRole("button", { name: "confirm-Remove from notebook" }));

    await waitFor(() => {
      expect(removeMutateAsync).toHaveBeenCalledWith({
        notebookId: "nb-1",
        sourceId: "source-1",
      });
    });
  });

  it("renders loading and empty states", () => {
    const { rerender } = render(<SourcesColumn sources={[]} isLoading notebookId="nb-1" />);
    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();

    rerender(<SourcesColumn isLoading={false} notebookId="nb-1" />);
    expect(screen.getByText("No sources")).toBeInTheDocument();
  });

  it("opens add source dialogs and propagates context mode changes", () => {
    const onContextModeChange = vi.fn();

    render(
      <SourcesColumn
        sources={[
          {
            id: "source-1",
            title: "Source",
            asset: null,
            embedded: true,
            embedded_chunks: 0,
            insights_count: 0,
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
          },
        ]}
        isLoading={false}
        notebookId="nb-1"
        onContextModeChange={onContextModeChange}
      />,
    );

    const addSourceButtons = screen.getAllByRole("button", { name: "Add Source" });
    fireEvent.click(addSourceButtons[1]);
    expect(screen.getByTestId("add-source")).toHaveTextContent("true");

    fireEvent.click(screen.getByRole("button", { name: "Add Existing" }));
    expect(screen.getByTestId("add-existing-source")).toHaveTextContent("true");

    fireEvent.click(screen.getByRole("button", { name: "set-source-context" }));
    expect(onContextModeChange).toHaveBeenCalledWith("source-1", "off");
  });

  it("requests next page on near-bottom scroll and shows pagination loading indicator", () => {
    const fetchNextPage = vi.fn();
    const { container, rerender } = render(
      <SourcesColumn
        sources={[
          {
            id: "source-1",
            title: "Source",
            asset: null,
            embedded: true,
            embedded_chunks: 0,
            insights_count: 0,
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
          },
        ]}
        isLoading={false}
        notebookId="nb-1"
        hasNextPage
        isFetchingNextPage={false}
        fetchNextPage={fetchNextPage}
      />,
    );

    const scrollContainer = container.querySelector(".overflow-y-auto") as HTMLDivElement;
    Object.defineProperty(scrollContainer, "scrollHeight", { value: 1000, configurable: true });
    Object.defineProperty(scrollContainer, "clientHeight", { value: 400, configurable: true });
    Object.defineProperty(scrollContainer, "scrollTop", { value: 450, configurable: true });

    fireEvent.scroll(scrollContainer);
    expect(fetchNextPage).toHaveBeenCalledTimes(1);

    rerender(
      <SourcesColumn
        sources={[
          {
            id: "source-1",
            title: "Source",
            asset: null,
            embedded: true,
            embedded_chunks: 0,
            insights_count: 0,
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
          },
        ]}
        isLoading={false}
        notebookId="nb-1"
        hasNextPage
        isFetchingNextPage
        fetchNextPage={fetchNextPage}
      />,
    );
    expect(container.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("logs delete/remove/retry failures without crashing", async () => {
    const retryError = new Error("retry failed");
    const deleteError = new Error("delete failed");
    const removeError = new Error("remove failed");
    const onRefresh = vi.fn();

    retryMutateAsync.mockRejectedValueOnce(retryError);
    deleteMutateAsync.mockRejectedValueOnce(deleteError);
    removeMutateAsync.mockRejectedValueOnce(removeError);

    render(
      <SourcesColumn
        sources={[
          {
            id: "source-1",
            title: "Source",
            asset: null,
            embedded: true,
            embedded_chunks: 0,
            insights_count: 0,
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
          },
        ]}
        isLoading={false}
        notebookId="nb-1"
        onRefresh={onRefresh}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "retry-source" }));
    await waitFor(() => {
      expect(appLog.error).toHaveBeenCalledWith("sources-column", "Failed to retry source", {
        sourceId: "source-1",
        error: retryError,
      });
    });

    fireEvent.click(screen.getByRole("button", { name: "delete-source" }));
    fireEvent.click(screen.getByRole("button", { name: "confirm-Delete Source" }));
    await waitFor(() => {
      expect(appLog.error).toHaveBeenCalledWith("sources-column", "Failed to delete source", {
        sourceId: "source-1",
        error: deleteError,
      });
      expect(onRefresh).not.toHaveBeenCalled();
    });

    fireEvent.click(screen.getByRole("button", { name: "remove-source" }));
    fireEvent.click(screen.getByRole("button", { name: "confirm-Remove from notebook" }));
    await waitFor(() => {
      expect(appLog.error).toHaveBeenCalledWith(
        "sources-column",
        "Failed to remove source from notebook",
        {
          notebookId: "nb-1",
          sourceId: "source-1",
          error: removeError,
        },
      );
    });
  });
});
