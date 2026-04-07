import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useInsight, useSaveInsightAsNote } from "@/lib/hooks/use-insights";
import { useModalManager } from "@/lib/hooks/use-modal-manager";
import { useSource } from "@/lib/hooks/use-sources";
import { useTranslation } from "@/lib/hooks/use-translation";
import { SourceInsightDialog } from "./SourceInsightDialog";

const openModal = vi.fn();
const saveInsightMutateAsync = vi.fn();

vi.mock("@/lib/hooks/use-insights");
vi.mock("@/lib/hooks/use-modal-manager");
vi.mock("@/lib/hooks/use-sources");
vi.mock("@/lib/hooks/use-translation");

vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({ open, children }: { open: boolean; children: ReactNode }) =>
    open ? <div>{children}</div> : null,
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
}));

describe("SourceInsightDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useModalManager).mockReturnValue({
      openModal,
    } as unknown as ReturnType<typeof useModalManager>);

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        sources: {
          sourceInsight: "Source insight",
          viewSource: "View source",
          researchThisInsight: "Research this insight",
          saveInsightToResearchThread: "Save to research thread",
          saveInsightAsNote: "Save as note",
          insightsNextLaneTitle: "Choose the next lane for this structured result",
          insightsNextLaneDescription:
            "Move it into a note, a research thread, or a seeded research lane.",
          saveInsightNeedsNotebook: "Link source to notebook first",
          saveInsightAsNoteSuccess: "Insight saved as note",
          saveInsightAsNoteFailed: "Failed to save insight as a note",
          savedInsightThreadTitle: "{type} research thread",
          noInsightSelected: "No insight selected",
          deleteInsightConfirm: "Delete this insight? This action is permanent",
        },
        common: {
          loading: "Loading",
          cancel: "Cancel",
          deleting: "Deleting",
          delete: "Delete",
          deleteForever: "Delete forever",
          saving: "Saving",
        },
      },
    } as unknown as ReturnType<typeof useTranslation>);

    vi.mocked(useInsight).mockReturnValue({
      data: undefined,
      isLoading: false,
    } as unknown as ReturnType<typeof useInsight>);

    vi.mocked(useSource).mockReturnValue({
      data: undefined,
    } as unknown as ReturnType<typeof useSource>);

    saveInsightMutateAsync.mockResolvedValue({
      id: "note:1",
      title: "Saved note",
      content: "fetched content",
    });
    vi.mocked(useSaveInsightAsNote).mockReturnValue({
      mutateAsync: saveInsightMutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useSaveInsightAsNote>);
  });

  it("requests prefixed insight id when opening dialog", () => {
    render(
      <SourceInsightDialog
        open
        onOpenChange={vi.fn()}
        insight={{ id: "abc", insight_type: "summary", content: "hello", source_id: "source:1" }}
      />,
    );

    expect(useInsight).toHaveBeenCalledWith("source_insight:abc", {
      enabled: true,
    });
  });

  it("keeps prefixed insight id and avoids delete when id is missing", async () => {
    const onDelete = vi.fn();
    render(
      <SourceInsightDialog
        open
        onOpenChange={vi.fn()}
        onDelete={onDelete}
        insight={{ id: "source_insight:ready", insight_type: "summary", content: "hello" }}
      />,
    );

    expect(useInsight).toHaveBeenCalledWith("source_insight:ready", {
      enabled: true,
    });

    fireEvent.click(screen.getByRole("button", { name: "Delete insight" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    await waitFor(() => {
      expect(onDelete).toHaveBeenCalledWith("source_insight:ready");
    });
  });

  it("prefers fetched source id when opening source modal", async () => {
    vi.mocked(useInsight).mockReturnValue({
      data: {
        id: "source_insight:abc",
        insight_type: "summary",
        content: "fetched content",
        source_id: "source:fetched",
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useInsight>);

    render(
      <SourceInsightDialog
        open
        onOpenChange={vi.fn()}
        insight={{
          id: "abc",
          insight_type: "summary",
          content: "inline",
          source_id: "source:inline",
        }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "View source" }));

    await waitFor(() => {
      expect(openModal).toHaveBeenCalledWith("source", "source:fetched");
    });
  });

  it("passes the fetched insight payload to save-as-note handlers", async () => {
    const onSaveAsNote = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useInsight).mockReturnValue({
      data: {
        id: "source_insight:abc",
        insight_type: "summary",
        content: "fetched content",
        source_id: "source:fetched",
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useInsight>);

    render(
      <SourceInsightDialog
        open
        onOpenChange={vi.fn()}
        canSaveAsNote
        onSaveAsNote={onSaveAsNote}
        insight={{ id: "abc", insight_type: "summary", content: "inline", source_id: "source:1" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Save as note" }));

    await waitFor(() => {
      expect(onSaveAsNote).toHaveBeenCalledWith({
        id: "source_insight:abc",
        insight_type: "summary",
        content: "fetched content",
        created: undefined,
        source_id: "source:fetched",
      });
    });
  });

  it("passes the fetched insight payload to research handlers", async () => {
    const onResearchThisInsight = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useInsight).mockReturnValue({
      data: {
        id: "source_insight:abc",
        insight_type: "summary",
        content: "fetched content",
        source_id: "source:fetched",
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useInsight>);

    render(
      <SourceInsightDialog
        open
        onOpenChange={vi.fn()}
        onResearchThisInsight={onResearchThisInsight}
        insight={{ id: "abc", insight_type: "summary", content: "inline", source_id: "source:1" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Research this insight" }));

    await waitFor(() => {
      expect(onResearchThisInsight).toHaveBeenCalledWith({
        id: "source_insight:abc",
        insight_type: "summary",
        content: "fetched content",
        created: undefined,
        source_id: "source:fetched",
      });
    });
  });

  it("passes the fetched insight payload to direct thread-save handlers", async () => {
    const onSaveToResearchThread = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useInsight).mockReturnValue({
      data: {
        id: "source_insight:abc",
        insight_type: "summary",
        content: "fetched content",
        source_id: "source:fetched",
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useInsight>);

    render(
      <SourceInsightDialog
        open
        onOpenChange={vi.fn()}
        canSaveToResearchThread
        onSaveToResearchThread={onSaveToResearchThread}
        insight={{ id: "abc", insight_type: "summary", content: "inline", source_id: "source:1" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Save to research thread" }));

    await waitFor(() => {
      expect(onSaveToResearchThread).toHaveBeenCalledWith({
        id: "source_insight:abc",
        insight_type: "summary",
        content: "fetched content",
        created: undefined,
        source_id: "source:fetched",
      });
    });
  });

  it("renders the structured-result next-lane guidance", () => {
    render(
      <SourceInsightDialog
        open
        onOpenChange={vi.fn()}
        canSaveAsNote
        canSaveToResearchThread
        onSaveAsNote={vi.fn()}
        onSaveToResearchThread={vi.fn()}
        onResearchThisInsight={vi.fn()}
        insight={{ id: "abc", insight_type: "summary", content: "inline", source_id: "source:1" }}
      />,
    );

    expect(screen.getByTestId("structured-insight-next-steps")).toHaveTextContent(
      "Choose the next lane for this structured result",
    );
    expect(
      screen.getByText("Move it into a note, a research thread, or a seeded research lane."),
    ).toBeInTheDocument();
    expect(screen.getByTestId("structured-insight-actions")).toBeInTheDocument();
  });

  it("shows the notebook-link hint and hides note/thread save actions when notebook context is unavailable", () => {
    render(
      <SourceInsightDialog
        open
        onOpenChange={vi.fn()}
        canSaveAsNote={false}
        canSaveToResearchThread={false}
        onSaveAsNote={vi.fn()}
        onSaveToResearchThread={vi.fn()}
        onResearchThisInsight={vi.fn()}
        insight={{ id: "abc", insight_type: "summary", content: "inline" }}
      />,
    );

    expect(screen.getByText("Link source to notebook first")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save as note" })).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Save to research thread" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Research this insight" })).toBeInTheDocument();
  });

  it("uses source notebook context for direct save fallback when available", async () => {
    const onOpenChange = vi.fn();

    vi.mocked(useSource).mockReturnValue({
      data: {
        id: "source:1",
        notebooks: ["notebook:1"],
      },
    } as unknown as ReturnType<typeof useSource>);

    render(
      <SourceInsightDialog
        open
        onOpenChange={onOpenChange}
        insight={{ id: "abc", insight_type: "summary", content: "inline", source_id: "source:1" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Save as note" }));

    await waitFor(() => {
      expect(saveInsightMutateAsync).toHaveBeenCalledWith({
        insightId: "source_insight:abc",
        notebookId: "notebook:1",
      });
      expect(onOpenChange).toHaveBeenCalledWith(false);
      expect(openModal).toHaveBeenCalledWith("note", "note:1");
    });
  });

  it("renders loading state and then empty fallback when no insight is available", () => {
    vi.mocked(useInsight).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as unknown as ReturnType<typeof useInsight>);

    const { rerender } = render(<SourceInsightDialog open onOpenChange={vi.fn()} />);

    expect(screen.getByText("Loading")).toBeInTheDocument();

    vi.mocked(useInsight).mockReturnValue({
      data: undefined,
      isLoading: false,
    } as unknown as ReturnType<typeof useInsight>);

    rerender(<SourceInsightDialog open onOpenChange={vi.fn()} />);
    expect(screen.getByText("No insight selected")).toBeInTheDocument();
  });

  it("confirms delete and closes dialog after delete succeeds", async () => {
    const onDelete = vi.fn().mockResolvedValue(undefined);
    const onOpenChange = vi.fn();

    render(
      <SourceInsightDialog
        open
        onDelete={onDelete}
        onOpenChange={onOpenChange}
        insight={{ id: "abc", insight_type: "summary", content: "inline" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Delete insight" }));
    expect(screen.getByText(/Delete this insight/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => {
      expect(onDelete).toHaveBeenCalledWith("abc");
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it("can cancel delete confirmation and keeps dialog open", () => {
    render(
      <SourceInsightDialog
        open
        onDelete={vi.fn().mockResolvedValue(undefined)}
        onOpenChange={vi.fn()}
        insight={{ id: "abc", insight_type: "summary", content: "inline" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Delete insight" }));
    expect(screen.getByText(/Delete this insight/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByText(/Delete this insight/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete insight" })).toBeInTheDocument();
  });

  it("resets pending delete confirmation when dialog closes", () => {
    const { rerender } = render(
      <SourceInsightDialog
        open
        onDelete={vi.fn().mockResolvedValue(undefined)}
        onOpenChange={vi.fn()}
        insight={{ id: "abc", insight_type: "summary", content: "inline" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Delete insight" }));
    expect(screen.getByText(/Delete this insight/)).toBeInTheDocument();

    rerender(
      <SourceInsightDialog
        open={false}
        onDelete={vi.fn().mockResolvedValue(undefined)}
        onOpenChange={vi.fn()}
        insight={{ id: "abc", insight_type: "summary", content: "inline" }}
      />,
    );
    rerender(
      <SourceInsightDialog
        open
        onDelete={vi.fn().mockResolvedValue(undefined)}
        onOpenChange={vi.fn()}
        insight={{ id: "abc", insight_type: "summary", content: "inline" }}
      />,
    );

    expect(screen.queryByText(/Delete this insight/)).not.toBeInTheDocument();
  });

  it("renders markdown tables from insight content", () => {
    vi.mocked(useInsight).mockReturnValue({
      data: {
        id: "source_insight:tbl",
        insight_type: "table",
        content: "| Col | Val |\n| --- | --- |\n| A | 1 |",
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useInsight>);

    render(
      <SourceInsightDialog
        open
        onOpenChange={vi.fn()}
        insight={{ id: "tbl", insight_type: "table", content: "" }}
      />,
    );

    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByText("Col")).toBeInTheDocument();
    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("uses deleteForever fallback copy when confirm text has no second sentence", () => {
    vi.mocked(useTranslation).mockReturnValue({
      t: {
        sources: {
          sourceInsight: "Source insight",
          viewSource: "View source",
          noInsightSelected: "No insight selected",
          deleteInsightConfirm: "Delete immediately",
        },
        common: {
          loading: "Loading",
          cancel: "Cancel",
          deleting: "Deleting",
          delete: "Delete",
          deleteForever: "Delete forever",
        },
      },
    } as unknown as ReturnType<typeof useTranslation>);

    render(
      <SourceInsightDialog
        open
        onDelete={vi.fn().mockResolvedValue(undefined)}
        onOpenChange={vi.fn()}
        insight={{ id: "abc", insight_type: "summary", content: "inline" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Delete insight" }));
    expect(screen.getByText("Delete forever")).toBeInTheDocument();
  });
});
