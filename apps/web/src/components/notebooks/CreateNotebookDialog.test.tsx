import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CreateNotebookDialog } from "./CreateNotebookDialog";

const hoisted = vi.hoisted(() => ({
  mutateAsyncMock: vi.fn(),
  isPending: false,
}));

vi.mock("@/lib/hooks/use-notebooks", () => ({
  useCreateNotebook: () => ({
    mutateAsync: hoisted.mutateAsyncMock,
    isPending: hoisted.isPending,
  }),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      notebooks: {
        createNew: "Create notebook",
        createNewDesc: "Create a new notebook",
        namePlaceholder: "Notebook name",
        descPlaceholder: "Describe notebook",
      },
      common: {
        name: "Name",
        description: "Description",
        cancel: "Cancel",
        creating: "Creating",
      },
    },
  }),
}));

describe("CreateNotebookDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.isPending = false;
  });

  it("keeps submit disabled until name is valid and submits payload", async () => {
    const onOpenChange = vi.fn();
    hoisted.mutateAsyncMock.mockResolvedValue({ id: "nb-1" });

    render(<CreateNotebookDialog open onOpenChange={onOpenChange} />);

    const submit = screen.getByRole("button", { name: "Create notebook" });
    expect(submit).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Name *"), {
      target: { value: "Research notebook" },
    });
    fireEvent.change(screen.getByLabelText("Description"), {
      target: { value: "Collects sources" },
    });

    await waitFor(() => {
      expect(submit).not.toBeDisabled();
    });

    fireEvent.click(submit);

    await waitFor(() => {
      expect(hoisted.mutateAsyncMock).toHaveBeenCalledWith({
        name: "Research notebook",
        description: "Collects sources",
      });
    });
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("resets fields when dialog closes and reopens", async () => {
    const onOpenChange = vi.fn();
    const { rerender } = render(<CreateNotebookDialog open onOpenChange={onOpenChange} />);

    const nameInput = screen.getByLabelText("Name *");
    fireEvent.change(nameInput, { target: { value: "Scratch" } });

    rerender(<CreateNotebookDialog open={false} onOpenChange={onOpenChange} />);
    rerender(<CreateNotebookDialog open onOpenChange={onOpenChange} />);

    await waitFor(() => {
      expect(screen.getByLabelText("Name *")).toHaveValue("");
    });
  });
});
