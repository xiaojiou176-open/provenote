import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useNotebooks } from "@/lib/hooks/use-notebooks";
import NotebooksPage from "./page";

vi.mock("@/lib/hooks/use-notebooks");

vi.mock("@/components/layout/AppShell", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-shell">{children}</div>
  ),
}));

vi.mock("@/components/notebooks/CreateNotebookDialog", () => ({
  CreateNotebookDialog: ({ open }: { open: boolean }) => (
    <div data-testid="create-notebook-dialog">open:{String(open)}</div>
  ),
}));

vi.mock("./components/NotebookList", () => ({
  NotebookList: ({
    title,
    notebooks,
    isLoading,
    onAction,
  }: {
    title: string;
    notebooks?: Array<{ id: string; name: string }>;
    isLoading: boolean;
    onAction?: () => void;
  }) => (
    <div data-testid="notebook-list">
      <div>{title}</div>
      <div>count:{notebooks?.length ?? 0}</div>
      <div>loading:{String(isLoading)}</div>
      <div>has-action:{String(Boolean(onAction))}</div>
      {onAction && (
        <button onClick={onAction} type="button">
          list-action
        </button>
      )}
    </div>
  ),
}));

describe("NotebooksPage", () => {
  const refetch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    refetch.mockReset();
  });

  it("renders loading state and opens create dialog from action button", () => {
    vi.mocked(useNotebooks).mockImplementation((archived?: boolean) => {
      if (archived) {
        return { data: [], isLoading: false } as unknown as ReturnType<typeof useNotebooks>;
      }
      return {
        data: undefined,
        isLoading: true,
        refetch,
      } as unknown as ReturnType<typeof useNotebooks>;
    });

    render(<NotebooksPage />);

    expect(screen.getByText("loading:true")).toBeInTheDocument();
    expect(screen.getByTestId("create-notebook-dialog")).toHaveTextContent("open:false");

    fireEvent.click(screen.getByRole("button", { name: "New Notebook" }));
    expect(screen.getByTestId("create-notebook-dialog")).toHaveTextContent("open:true");
  });

  it("refreshes notebooks when refresh button is clicked", () => {
    vi.mocked(useNotebooks).mockImplementation((archived?: boolean) => {
      if (archived) {
        return { data: [], isLoading: false } as unknown as ReturnType<typeof useNotebooks>;
      }
      return {
        data: [],
        isLoading: false,
        refetch,
      } as unknown as ReturnType<typeof useNotebooks>;
    });

    render(<NotebooksPage />);
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));

    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("filters active and archived notebooks while searching", () => {
    vi.mocked(useNotebooks).mockImplementation((archived?: boolean) => {
      if (archived) {
        return {
          data: [
            { id: "nb-arch-1", name: "Archived Alpha" },
            { id: "nb-arch-2", name: "Old Book" },
          ],
          isLoading: false,
        } as unknown as ReturnType<typeof useNotebooks>;
      }

      return {
        data: [
          { id: "nb-1", name: "Alpha Notebook" },
          { id: "nb-2", name: "Beta Notebook" },
        ],
        isLoading: false,
        refetch,
      } as unknown as ReturnType<typeof useNotebooks>;
    });

    render(<NotebooksPage />);

    expect(screen.getAllByText("has-action:true")).toHaveLength(1);

    fireEvent.change(screen.getByRole("textbox", { name: "Search notebooks" }), {
      target: { value: "alpha" },
    });

    const lists = screen.getAllByTestId("notebook-list");
    expect(lists[0]).toHaveTextContent("count:1");
    expect(lists[0]).toHaveTextContent("has-action:false");
    expect(lists[1]).toHaveTextContent("count:1");
  });

  it("hides archived section when no archived notebooks exist", () => {
    vi.mocked(useNotebooks).mockImplementation((archived?: boolean) => {
      if (archived) {
        return {
          data: [],
          isLoading: false,
        } as unknown as ReturnType<typeof useNotebooks>;
      }

      return {
        data: [{ id: "nb-1", name: "Alpha" }],
        isLoading: false,
        refetch,
      } as unknown as ReturnType<typeof useNotebooks>;
    });

    render(<NotebooksPage />);

    expect(screen.getAllByTestId("notebook-list")).toHaveLength(1);
  });

  it("falls back cleanly when archived notebooks are undefined", () => {
    vi.mocked(useNotebooks).mockImplementation((archived?: boolean) => {
      if (archived) {
        return {
          data: undefined,
          isLoading: false,
        } as unknown as ReturnType<typeof useNotebooks>;
      }

      return {
        data: [{ id: "nb-1", name: "Alpha" }],
        isLoading: false,
        refetch,
      } as unknown as ReturnType<typeof useNotebooks>;
    });

    render(<NotebooksPage />);

    expect(screen.getAllByTestId("notebook-list")).toHaveLength(1);
  });

  it("opens create dialog from NotebookList action when not searching", () => {
    vi.mocked(useNotebooks).mockImplementation((archived?: boolean) => {
      if (archived) {
        return {
          data: [],
          isLoading: false,
        } as unknown as ReturnType<typeof useNotebooks>;
      }

      return {
        data: [{ id: "nb-1", name: "Alpha" }],
        isLoading: false,
        refetch,
      } as unknown as ReturnType<typeof useNotebooks>;
    });

    render(<NotebooksPage />);
    fireEvent.click(screen.getByRole("button", { name: "list-action" }));

    expect(screen.getByTestId("create-notebook-dialog")).toHaveTextContent("open:true");
  });
});
