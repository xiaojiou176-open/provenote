import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useUpdateNotebook } from "@/lib/hooks/use-notebooks";
import { useTranslation } from "@/lib/hooks/use-translation";
import { NotebookCard } from "./NotebookCard";

const push = vi.fn();
const mutate = vi.fn();

vi.mock("date-fns", () => ({
  formatDistanceToNow: vi.fn(() => "2 days ago"),
}));

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
}));

vi.mock("@/lib/hooks/use-notebooks");
vi.mock("@/lib/hooks/use-translation");

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

vi.mock("./NotebookDeleteDialog", () => ({
  NotebookDeleteDialog: ({ open }: { open: boolean }) => (
    <div data-testid="delete-dialog">open:{String(open)}</div>
  ),
}));

describe("NotebookCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useRouter).mockReturnValue({ push } as unknown as ReturnType<typeof useRouter>);

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        notebooks: {
          archived: "Archived",
          archive: "Archive",
          unarchive: "Unarchive",
        },
        chat: {
          noDescription: "No description",
        },
        common: {
          actions: "Actions",
          delete: "Delete",
          updated: "Updated {time}",
          processing: "Processing",
        },
      },
      language: "en",
    } as unknown as ReturnType<typeof useTranslation>);

    vi.mocked(useUpdateNotebook).mockReturnValue({
      mutate,
    } as unknown as ReturnType<typeof useUpdateNotebook>);
  });

  it("navigates to encoded notebook route and marks card as opening", async () => {
    render(
      <NotebookCard
        notebook={{
          id: "notebook/id",
          name: "My Notebook",
          description: "desc",
          archived: false,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-02T00:00:00Z",
          source_count: 4,
          note_count: 2,
        }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open notebook My Notebook" }));

    await waitFor(() => {
      expect(push).toHaveBeenCalledWith("/notebooks/notebook%2Fid");
      expect(screen.getByTestId("notebook-card-notebook/id")).toHaveAttribute("aria-busy", "true");
      expect(screen.getByText("Processing")).toBeInTheDocument();
    });
  });

  it("archives notebook and opens delete dialog", async () => {
    render(
      <NotebookCard
        notebook={{
          id: "nb-1",
          name: "My Notebook",
          description: "",
          archived: false,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-02T00:00:00Z",
          source_count: 1,
          note_count: 0,
        }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Archive" }));

    expect(mutate).toHaveBeenCalledWith({
      id: "nb-1",
      data: { archived: true },
    });

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    expect(screen.getByTestId("delete-dialog")).toHaveTextContent("open:true");
  });
});
