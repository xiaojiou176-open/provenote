import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { NotebookResponse } from "@/lib/types/api";
import { NotebookList } from "./NotebookList";

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      common: {
        loading: "Loading",
        noResults: "No results",
      },
      chat: {
        startByCreating: "Start by creating one",
      },
    },
  }),
}));

vi.mock("./NotebookCard", () => ({
  NotebookCard: ({ notebook }: { notebook: NotebookResponse }) => (
    <div data-testid={`notebook-card-${notebook.id}`}>{notebook.name}</div>
  ),
}));

describe("NotebookList", () => {
  const notebooks: NotebookResponse[] = [
    {
      id: "nb-1",
      name: "Notebook A",
      description: "desc",
      archived: false,
      source_count: 2,
      note_count: 1,
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-02T00:00:00Z",
    },
    {
      id: "nb-2",
      name: "Notebook B",
      description: "desc",
      archived: false,
      source_count: 0,
      note_count: 0,
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-02T00:00:00Z",
    },
  ];

  it("renders loading skeleton grid", () => {
    render(<NotebookList notebooks={undefined} isLoading title="All notebooks" />);

    expect(screen.getByRole("status", { name: "Loading" })).toBeInTheDocument();
  });

  it("renders empty state and action callback", () => {
    const onAction = vi.fn();

    render(
      <NotebookList
        notebooks={[]}
        isLoading={false}
        title="All notebooks"
        actionLabel="Create notebook"
        onAction={onAction}
      />,
    );

    expect(screen.getByText("No results")).toBeInTheDocument();
    expect(screen.getByText("Start by creating one")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Create notebook" }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it("keeps collapsible panel closed by default and toggles open", () => {
    render(
      <NotebookList
        notebooks={notebooks}
        isLoading={false}
        title="Archived notebooks"
        collapsible
      />,
    );

    const panel = document.getElementById("archived-notebooks-panel");
    expect(panel).toHaveAttribute("data-state", "closed");
    expect(panel).toHaveAttribute("aria-hidden", "true");

    fireEvent.click(screen.getByRole("button", { name: "Archived notebooks" }));

    expect(panel).toHaveAttribute("data-state", "open");
    expect(panel).toHaveAttribute("aria-hidden", "false");
    expect(screen.getByTestId("notebook-card-nb-1")).toBeInTheDocument();
    expect(screen.getByTestId("notebook-card-nb-2")).toBeInTheDocument();
  });
});
