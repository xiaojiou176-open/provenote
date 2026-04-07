import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NotebooksStep } from "./NotebooksStep";

const checkboxListMock = vi.fn();

const t = {
  notebooks: {
    title: "Notebooks",
  },
  common: {
    optional: "optional",
  },
  sources: {
    addExistingDesc: "Pick notebooks for this source",
    noNotebooksFound: "No notebooks found",
  },
};

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t }),
}));

vi.mock("@/components/ui/checkbox-list", () => ({
  CheckboxList: (props: {
    items: Array<{ id: string; title: string; description?: string }>;
    selectedIds: string[];
    onToggle: (id: string) => void;
    loading?: boolean;
    emptyMessage: string;
  }) => {
    checkboxListMock(props);
    return (
      <div>
        <div data-testid="items-size">{props.items.length}</div>
        <div data-testid="selected-size">{props.selectedIds.length}</div>
        <div data-testid="loading-state">{String(Boolean(props.loading))}</div>
        <div>{props.emptyMessage}</div>
        {props.items.map((item) => (
          <button key={item.id} onClick={() => props.onToggle(item.id)} type="button">
            {item.title}
          </button>
        ))}
      </div>
    );
  },
}));

describe("NotebookSelectionStep (NotebooksStep)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("maps notebooks to checkbox list items", () => {
    render(
      <NotebooksStep
        notebooks={[
          { id: "nb-1", name: "Notebook One", description: "Desc one" },
          { id: "nb-2", name: "Notebook Two", description: null },
        ]}
        selectedNotebooks={["nb-1"]}
        onToggleNotebook={vi.fn()}
      />,
    );

    expect(screen.getByText("Notebooks (optional)")).toBeInTheDocument();
    expect(screen.getByText("Pick notebooks for this source")).toBeInTheDocument();
    expect(screen.getByTestId("items-size")).toHaveTextContent("2");
    expect(screen.getByTestId("selected-size")).toHaveTextContent("1");

    expect(checkboxListMock).toHaveBeenCalledWith(
      expect.objectContaining({
        items: [
          { id: "nb-1", title: "Notebook One", description: "Desc one" },
          { id: "nb-2", title: "Notebook Two", description: undefined },
        ],
        emptyMessage: "No notebooks found",
      }),
    );
  });

  it("passes loading state and propagates toggle callback", () => {
    const onToggleNotebook = vi.fn();

    render(
      <NotebooksStep
        notebooks={[{ id: "nb-1", name: "Notebook One", description: null }]}
        selectedNotebooks={[]}
        onToggleNotebook={onToggleNotebook}
        loading
      />,
    );

    expect(screen.getByTestId("loading-state")).toHaveTextContent("true");

    fireEvent.click(screen.getByRole("button", { name: "Notebook One" }));
    expect(onToggleNotebook).toHaveBeenCalledWith("nb-1");
  });
});
