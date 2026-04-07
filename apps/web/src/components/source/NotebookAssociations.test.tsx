import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useNotebooks } from "@/lib/hooks/use-notebooks";
import { useAddSourcesToNotebook, useRemoveSourceFromNotebook } from "@/lib/hooks/use-sources";
import { appLog } from "@/lib/log";
import { NotebookAssociations } from "./NotebookAssociations";

vi.mock("@/lib/hooks/use-notebooks");
vi.mock("@/lib/hooks/use-sources");
vi.mock("@/lib/log", () => ({
  appLog: {
    error: vi.fn(),
  },
}));

const notebooksFixture = [
  {
    id: "nb-1",
    name: "Notebook 1",
    description: "First notebook",
    archived: false,
  },
  {
    id: "nb-2",
    name: "Notebook 2",
    description: "Second notebook",
    archived: false,
  },
];

describe("NotebookAssociations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state", () => {
    vi.mocked(useNotebooks).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as unknown as ReturnType<typeof useNotebooks>);

    vi.mocked(useAddSourcesToNotebook).mockReturnValue({
      mutateAsync: vi.fn(),
    } as unknown as ReturnType<typeof useAddSourcesToNotebook>);

    vi.mocked(useRemoveSourceFromNotebook).mockReturnValue({
      mutateAsync: vi.fn(),
    } as unknown as ReturnType<typeof useRemoveSourceFromNotebook>);

    render(<NotebookAssociations sourceId="source:1" currentNotebookIds={[]} />);

    expect(screen.getByText("Manage Notebooks")).toBeInTheDocument();
    expect(screen.getByText(/Manage which notebooks/i)).toBeInTheDocument();
  });

  it("renders empty state when no notebooks are available", () => {
    vi.mocked(useNotebooks).mockReturnValue({
      data: [],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebooks>);

    vi.mocked(useAddSourcesToNotebook).mockReturnValue({
      mutateAsync: vi.fn(),
    } as unknown as ReturnType<typeof useAddSourcesToNotebook>);

    vi.mocked(useRemoveSourceFromNotebook).mockReturnValue({
      mutateAsync: vi.fn(),
    } as unknown as ReturnType<typeof useRemoveSourceFromNotebook>);

    render(<NotebookAssociations sourceId="source:1" currentNotebookIds={[]} />);

    expect(screen.getByText("No notebooks available")).toBeInTheDocument();
  });

  it("adds/removes associations and calls onSave", async () => {
    const addMutateAsync = vi.fn().mockResolvedValue(undefined);
    const removeMutateAsync = vi.fn().mockResolvedValue(undefined);
    const onSave = vi.fn();

    vi.mocked(useNotebooks).mockReturnValue({
      data: notebooksFixture,
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebooks>);

    vi.mocked(useAddSourcesToNotebook).mockReturnValue({
      mutateAsync: addMutateAsync,
    } as unknown as ReturnType<typeof useAddSourcesToNotebook>);

    vi.mocked(useRemoveSourceFromNotebook).mockReturnValue({
      mutateAsync: removeMutateAsync,
    } as unknown as ReturnType<typeof useRemoveSourceFromNotebook>);

    render(
      <NotebookAssociations sourceId="source:1" currentNotebookIds={["nb-1"]} onSave={onSave} />,
    );

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);

    fireEvent.click(screen.getByRole("button", { name: "Save Changes" }));

    await waitFor(() => {
      expect(addMutateAsync).toHaveBeenCalledWith({
        notebookId: "nb-2",
        sourceIds: ["source:1"],
      });
      expect(removeMutateAsync).toHaveBeenCalledWith({
        notebookId: "nb-1",
        sourceId: "source:1",
      });
      expect(onSave).toHaveBeenCalledTimes(1);
    });
  });

  it("disables actions while save is in progress", async () => {
    let resolveAdd: (() => void) | null = null;
    const addPendingPromise = new Promise<void>((resolve) => {
      resolveAdd = resolve;
    });
    const addMutateAsync = vi.fn(() => addPendingPromise);

    vi.mocked(useNotebooks).mockReturnValue({
      data: notebooksFixture,
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebooks>);

    vi.mocked(useAddSourcesToNotebook).mockReturnValue({
      mutateAsync: addMutateAsync,
    } as unknown as ReturnType<typeof useAddSourcesToNotebook>);

    vi.mocked(useRemoveSourceFromNotebook).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(undefined),
    } as unknown as ReturnType<typeof useRemoveSourceFromNotebook>);

    render(<NotebookAssociations sourceId="source:1" currentNotebookIds={["nb-1"]} />);

    fireEvent.click(screen.getAllByRole("checkbox")[1]);
    fireEvent.click(screen.getByRole("button", { name: "Save Changes" }));

    expect(screen.getByRole("button", { name: /Saving/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();

    resolveAdd?.();
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: /Saving/ })).not.toBeInTheDocument();
    });
  });

  it("reverts pending notebook selections when cancel is clicked", () => {
    vi.mocked(useNotebooks).mockReturnValue({
      data: notebooksFixture,
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebooks>);

    vi.mocked(useAddSourcesToNotebook).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(undefined),
    } as unknown as ReturnType<typeof useAddSourcesToNotebook>);

    vi.mocked(useRemoveSourceFromNotebook).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(undefined),
    } as unknown as ReturnType<typeof useRemoveSourceFromNotebook>);

    render(<NotebookAssociations sourceId="source:1" currentNotebookIds={["nb-1"]} />);

    fireEvent.click(screen.getAllByRole("checkbox")[1]);
    expect(screen.getByRole("button", { name: "Save Changes" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("button", { name: "Save Changes" })).not.toBeInTheDocument();
  });

  it("logs and exits save flow when mutation throws synchronously", async () => {
    const addMutateAsync = vi.fn(() => {
      throw new Error("sync failure");
    });

    vi.mocked(useNotebooks).mockReturnValue({
      data: notebooksFixture,
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebooks>);

    vi.mocked(useAddSourcesToNotebook).mockReturnValue({
      mutateAsync: addMutateAsync,
    } as unknown as ReturnType<typeof useAddSourcesToNotebook>);

    vi.mocked(useRemoveSourceFromNotebook).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(undefined),
    } as unknown as ReturnType<typeof useRemoveSourceFromNotebook>);

    render(<NotebookAssociations sourceId="source:1" currentNotebookIds={[]} />);

    fireEvent.click(screen.getAllByRole("checkbox")[0]);
    fireEvent.click(screen.getByRole("button", { name: "Save Changes" }));

    await waitFor(() => {
      expect(appLog.error).toHaveBeenCalledWith(
        "notebook-associations",
        "Failed to save notebook associations",
        expect.any(Error),
      );
      expect(screen.queryByRole("button", { name: /Saving/ })).not.toBeInTheDocument();
    });
  });
});
