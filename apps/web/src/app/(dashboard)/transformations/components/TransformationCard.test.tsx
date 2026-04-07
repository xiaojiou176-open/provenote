import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useDeleteTransformation } from "@/lib/hooks/use-transformations";
import type { Transformation } from "@/lib/types/transformations";
import { TransformationCard } from "./TransformationCard";

vi.mock("@/lib/hooks/use-transformations");
vi.mock("@/components/common/ConfirmDialog", () => ({
  ConfirmDialog: ({
    open,
    onConfirm,
    isLoading,
  }: {
    open: boolean;
    onConfirm: () => void;
    isLoading?: boolean;
  }) =>
    open ? (
      <button
        data-testid="confirm-delete"
        disabled={Boolean(isLoading)}
        onClick={onConfirm}
        type="button"
      >
        confirm
      </button>
    ) : null,
}));

const transformation: Transformation = {
  id: "tr-1",
  name: "summary",
  title: "Summary title",
  description: "Summarize source text",
  prompt: "Return a concise summary.",
  apply_default: true,
  created: "2026-01-01T00:00:00Z",
  updated: "2026-01-01T00:00:00Z",
};

describe("TransformationCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useDeleteTransformation).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteTransformation>);
  });

  it("expands/collapses details and triggers playground/edit handlers", () => {
    const onPlayground = vi.fn();
    const onEdit = vi.fn();

    render(
      <TransformationCard
        transformation={transformation}
        onPlayground={onPlayground}
        onEdit={onEdit}
      />,
    );

    expect(screen.queryByText("Return a concise summary.")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("summary"));
    expect(screen.getByText("Return a concise summary.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Playground" }));
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));

    expect(onPlayground).toHaveBeenCalledTimes(1);
    expect(onEdit).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText("summary"));
    expect(screen.queryByText("Return a concise summary.")).not.toBeInTheDocument();
  });

  it("opens delete dialog and deletes transformation when confirmed", () => {
    const mutate = vi.fn();
    vi.mocked(useDeleteTransformation).mockReturnValue({
      mutate,
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteTransformation>);

    render(<TransformationCard transformation={transformation} />);

    fireEvent.click(screen.getByRole("button", { name: "Delete Source" }));
    fireEvent.click(screen.getByTestId("confirm-delete"));

    expect(mutate).toHaveBeenCalledWith("tr-1");
  });
});
