import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Transformation } from "@/lib/types/transformations";
import { TransformationsList } from "./TransformationsList";

vi.mock("./TransformationEditorDialog", () => ({
  TransformationEditorDialog: ({
    open,
    transformation,
  }: {
    open: boolean;
    transformation?: Transformation;
  }) =>
    open ? <div data-testid="editor-dialog">editing:{transformation?.name ?? "new"}</div> : null,
}));

vi.mock("./TransformationCard", () => ({
  TransformationCard: ({
    transformation,
    onPlayground,
    onEdit,
  }: {
    transformation: Transformation;
    onPlayground?: () => void;
    onEdit?: () => void;
  }) => (
    <div data-testid={`transformation-card-${transformation.id}`}>
      <span>{transformation.name}</span>
      <button onClick={onPlayground} type="button">
        run-playground-{transformation.id}
      </button>
      <button onClick={onEdit} type="button">
        edit-{transformation.id}
      </button>
    </div>
  ),
}));

const sampleTransformations: Transformation[] = [
  {
    id: "tr-1",
    name: "summary",
    title: "Summary",
    description: "Summarize source",
    prompt: "Summarize",
    apply_default: false,
    created: "2026-01-01T00:00:00Z",
    updated: "2026-01-01T00:00:00Z",
  },
  {
    id: "tr-2",
    name: "key_points",
    title: "Key Points",
    description: "Extract key points",
    prompt: "Extract",
    apply_default: true,
    created: "2026-01-01T00:00:00Z",
    updated: "2026-01-01T00:00:00Z",
  },
];

describe("TransformationsList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading spinner while fetching", () => {
    render(<TransformationsList transformations={undefined} isLoading onPlayground={vi.fn()} />);

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("renders empty state with create action", () => {
    render(<TransformationsList transformations={[]} isLoading={false} onPlayground={vi.fn()} />);

    expect(screen.getByText("No transformations yet")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create New" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Create New" }));
    expect(screen.queryByTestId("editor-dialog")).not.toBeInTheDocument();
  });

  it("renders transformation cards and forwards playground action", () => {
    const onPlayground = vi.fn();

    render(
      <TransformationsList
        transformations={sampleTransformations}
        isLoading={false}
        onPlayground={onPlayground}
      />,
    );

    expect(screen.getByTestId("transformation-card-tr-1")).toBeInTheDocument();
    expect(screen.getByTestId("transformation-card-tr-2")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "run-playground-tr-1" }));
    expect(onPlayground).toHaveBeenCalledWith(sampleTransformations[0]);
  });

  it("opens edit dialog with selected transformation", async () => {
    render(
      <TransformationsList
        transformations={sampleTransformations}
        isLoading={false}
        onPlayground={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "edit-tr-2" }));

    await waitFor(() => {
      expect(screen.getByTestId("editor-dialog")).toHaveTextContent("editing:key_points");
    });
  });
});
