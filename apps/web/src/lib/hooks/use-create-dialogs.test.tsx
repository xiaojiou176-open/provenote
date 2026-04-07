import { fireEvent, render, renderHook, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

vi.unmock("@/lib/hooks/use-create-dialogs");

import { CreateDialogsProvider, useCreateDialogs } from "@/lib/hooks/use-create-dialogs";

vi.mock("@/components/sources/AddSourceDialog", () => ({
  AddSourceDialog: ({ open }: { open: boolean }) => (
    <div data-testid="source-dialog">{String(open)}</div>
  ),
}));

vi.mock("@/components/notebooks/CreateNotebookDialog", () => ({
  CreateNotebookDialog: ({ open }: { open: boolean }) => (
    <div data-testid="notebook-dialog">{String(open)}</div>
  ),
}));

vi.mock("@/components/podcasts/GeneratePodcastDialog", () => ({
  GeneratePodcastDialog: ({ open }: { open: boolean }) => (
    <div data-testid="podcast-dialog">{String(open)}</div>
  ),
}));

function Consumer() {
  const { openSourceDialog, openNotebookDialog, openPodcastDialog } = useCreateDialogs();
  return (
    <div>
      <button onClick={openSourceDialog} type="button">
        open source
      </button>
      <button onClick={openNotebookDialog} type="button">
        open notebook
      </button>
      <button onClick={openPodcastDialog} type="button">
        open podcast
      </button>
    </div>
  );
}

describe("useCreateDialogs", () => {
  it("throws when hook is used outside provider", () => {
    expect(() => renderHook(() => useCreateDialogs())).toThrow(
      "useCreateDialogs must be used within a CreateDialogsProvider",
    );
  });

  it("opens each managed dialog through the provider actions", () => {
    render(
      <CreateDialogsProvider>
        <Consumer />
      </CreateDialogsProvider>,
    );

    expect(screen.getByTestId("source-dialog")).toHaveTextContent("false");
    expect(screen.getByTestId("notebook-dialog")).toHaveTextContent("false");
    expect(screen.getByTestId("podcast-dialog")).toHaveTextContent("false");

    fireEvent.click(screen.getByRole("button", { name: "open source" }));
    fireEvent.click(screen.getByRole("button", { name: "open notebook" }));
    fireEvent.click(screen.getByRole("button", { name: "open podcast" }));

    expect(screen.getByTestId("source-dialog")).toHaveTextContent("true");
    expect(screen.getByTestId("notebook-dialog")).toHaveTextContent("true");
    expect(screen.getByTestId("podcast-dialog")).toHaveTextContent("true");
  });
});
