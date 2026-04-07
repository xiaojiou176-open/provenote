import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useUpdateNotebook } from "@/lib/hooks/use-notebooks";
import { useTranslation } from "@/lib/hooks/use-translation";
import { NotebookHeader } from "./NotebookHeader";

const mutate = vi.fn();
const mutateAsync = vi.fn();

vi.mock("date-fns", () => ({
  formatDistanceToNow: vi.fn(() => "1 day ago"),
}));

vi.mock("@/lib/hooks/use-notebooks");
vi.mock("@/lib/hooks/use-translation");

vi.mock("@/components/common/InlineEdit", () => ({
  InlineEdit: ({
    name,
    onSave,
  }: {
    name: string;
    onSave: (value: string) => Promise<void> | void;
  }) => (
    <button
      onClick={() => void onSave(name === "notebook-name" ? "Renamed Notebook" : "New description")}
      type="button"
    >
      save-{name}
    </button>
  ),
}));

vi.mock("./NotebookDeleteDialog", () => ({
  NotebookDeleteDialog: ({ open }: { open: boolean }) => (
    <div data-testid="delete-dialog">open:{String(open)}</div>
  ),
}));

describe("NotebookHeader", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        notebooks: {
          namePlaceholder: "Notebook name",
          archived: "Archived",
          unarchive: "Unarchive",
          archive: "Archive",
          addDescription: "Add description",
        },
        common: {
          delete: "Delete",
          created: "Created {time}",
          updated: "Updated {time}",
        },
      },
      language: "en",
    } as unknown as ReturnType<typeof useTranslation>);

    vi.mocked(useUpdateNotebook).mockReturnValue({
      mutate,
      mutateAsync,
    } as unknown as ReturnType<typeof useUpdateNotebook>);
  });

  it("updates notebook name and description through inline edits", async () => {
    mutateAsync.mockResolvedValue(undefined);

    render(
      <NotebookHeader
        notebook={{
          id: "nb-1",
          name: "Old notebook",
          description: "Old description",
          archived: false,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-02T00:00:00Z",
          source_count: 0,
          note_count: 0,
        }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "save-notebook-name" }));
    fireEvent.click(screen.getByRole("button", { name: "save-notebook-description" }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        id: "nb-1",
        data: { name: "Renamed Notebook" },
      });
      expect(mutateAsync).toHaveBeenCalledWith({
        id: "nb-1",
        data: { description: "New description" },
      });
    });
  });

  it("archives notebook and opens delete confirmation", () => {
    render(
      <NotebookHeader
        notebook={{
          id: "nb-1",
          name: "Notebook",
          description: "",
          archived: false,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-02T00:00:00Z",
          source_count: 0,
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
