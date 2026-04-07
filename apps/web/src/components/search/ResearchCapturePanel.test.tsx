import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useNotebooks } from "@/lib/hooks/use-notebooks";
import {
  useAppendResearchThreadEntry,
  useCreateResearchThread,
} from "@/lib/hooks/use-research-threads";
import { ResearchCapturePanel } from "./ResearchCapturePanel";

vi.mock("@/lib/hooks/use-notebooks");
vi.mock("@/lib/hooks/use-research-threads");

const hoisted = vi.hoisted(() => ({
  createThreadMutateAsync: vi.fn(),
  appendEntryMutateAsync: vi.fn(),
}));

describe("ResearchCapturePanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    window.sessionStorage.clear();

    vi.mocked(useNotebooks).mockReturnValue({
      data: [{ id: "nb-1", name: "Notebook A", archived: false }],
      isLoading: false,
    } as never);
    vi.mocked(useCreateResearchThread).mockReturnValue({
      mutateAsync: hoisted.createThreadMutateAsync,
      isPending: false,
    } as never);
    vi.mocked(useAppendResearchThreadEntry).mockReturnValue({
      mutateAsync: hoisted.appendEntryMutateAsync,
      isPending: false,
    } as never);
    hoisted.createThreadMutateAsync.mockResolvedValue({
      id: "research_thread:1",
      title: "Ask: Explain this notebook",
    });
    hoisted.appendEntryMutateAsync.mockResolvedValue({
      id: "research_thread:1",
      title: "Ask: Explain this notebook",
    });
  });

  it("creates a research thread after the user selects a notebook and enables auto-save", async () => {
    render(
      <ResearchCapturePanel
        mode="ask"
        query="Explain this notebook"
        answer="Saved final answer"
        sourceIds={["source:1"]}
        noteIds={["note:1"]}
        hasCompletedResult
      />,
    );

    fireEvent.change(screen.getByLabelText("Working notebook"), {
      target: { value: "nb-1" },
    });
    fireEvent.click(screen.getByLabelText("Auto-save completed results"));

    await waitFor(() => {
      expect(hoisted.createThreadMutateAsync).toHaveBeenCalledWith({
        notebookId: "nb-1",
        payload: {
          title: "Ask: Explain this notebook",
          seed_kind: "ask",
          question: "Explain this notebook",
          answer: "Saved final answer",
          source_ids: ["source:1"],
          note_ids: ["note:1"],
          search_results: [],
        },
      });
    });

    expect(screen.getByText("Auto-saved to Ask: Explain this notebook.")).toBeInTheDocument();
  });

  it("prefills the working notebook when a seeded notebook id is provided", async () => {
    render(
      <ResearchCapturePanel
        mode="ask"
        query="Explain this notebook"
        answer="Saved final answer"
        defaultNotebookId="nb-1"
        sourceIds={["source:1"]}
        hasCompletedResult
      />,
    );

    expect(screen.getByLabelText("Working notebook")).toHaveValue("nb-1");

    fireEvent.click(screen.getByLabelText("Auto-save completed results"));

    await waitFor(() => {
      expect(hoisted.createThreadMutateAsync).toHaveBeenCalledWith({
        notebookId: "nb-1",
        payload: expect.objectContaining({
          source_ids: ["source:1"],
        }),
      });
    });
  });

  it("appends to the same session thread when the same notebook/query gets a new completed result", async () => {
    const { unmount } = render(
      <ResearchCapturePanel
        mode="ask"
        query="Explain this notebook"
        answer="First saved answer"
        sourceIds={["source:1"]}
        hasCompletedResult
      />,
    );

    fireEvent.change(screen.getByLabelText("Working notebook"), {
      target: { value: "nb-1" },
    });
    fireEvent.click(screen.getByLabelText("Auto-save completed results"));

    await waitFor(() => {
      expect(hoisted.createThreadMutateAsync).toHaveBeenCalledTimes(1);
    });

    unmount();

    render(
      <ResearchCapturePanel
        mode="ask"
        query="Explain this notebook"
        answer="Updated saved answer"
        sourceIds={["source:1", "source:2"]}
        noteIds={["note:1"]}
        hasCompletedResult
      />,
    );

    await waitFor(() => {
      expect(hoisted.appendEntryMutateAsync).toHaveBeenCalledWith({
        threadId: "research_thread:1",
        payload: {
          entry_type: "answer_snapshot",
          title: "Ask: Explain this notebook",
          content: "Updated saved answer",
          source_ids: ["source:1", "source:2"],
          note_ids: ["note:1"],
          metadata: {
            question: "Explain this notebook",
          },
        },
      });
    });

    expect(screen.getByText("Updated your auto-saved research thread.")).toBeInTheDocument();
  });
});
