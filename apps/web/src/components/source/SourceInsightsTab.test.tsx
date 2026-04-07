import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useTranslation } from "@/lib/hooks/use-translation";
import { SourceInsightsTab } from "./SourceInsightsTab";

vi.mock("@/lib/hooks/use-translation");

vi.mock("@/components/ui/tabs", () => ({
  TabsContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/select", () => ({
  Select: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SelectTrigger: ({ children }: { children: ReactNode }) => (
    <button type="button">{children}</button>
  ),
  SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>,
  SelectContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

describe("SourceInsightsTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        common: {
          insights: "Insights",
          creating: "Creating",
          create: "Create",
          saving: "Saving",
        },
        sources: {
          insightsDesc: "Insight description",
          generateNewInsight: "Generate insight",
          selectTransformation: "Select transformation",
          noInsightsYet: "No insights yet",
          createFirstInsight: "Create the first insight",
          researchThisInsight: "Research this insight",
          saveInsightToResearchThread: "Save to research thread",
          saveInsightAsNote: "Save as note",
          insightsNextLaneTitle: "Choose the next lane for this structured result",
          insightsNextLaneDescription:
            "Move it into a note, a research thread, or a seeded research lane.",
          saveInsightNeedsNotebook: "Link the source to a notebook first.",
          viewInsight: "View insight",
        },
      },
    } as unknown as ReturnType<typeof useTranslation>);
  });

  it("creates insight and triggers item actions", () => {
    const onCreateInsight = vi.fn();
    const onSaveInsightAsNote = vi.fn();
    const onViewInsight = vi.fn();
    const onDeleteInsight = vi.fn();

    render(
      <SourceInsightsTab
        insights={[
          {
            id: "ins-1",
            insight_type: "summary",
            content: "This is a generated insight",
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
            source_id: "source:1",
          },
        ]}
        transformations={[{ id: "tr-1", name: "Summarize", title: "Summarize" }]}
        selectedTransformation="tr-1"
        creatingInsight={false}
        loadingInsights={false}
        canSaveInsightsAsNotes={true}
        canSaveInsightsToResearchThreads={true}
        savingInsightId={null}
        savingInsightThreadId={null}
        onSelectedTransformationChange={vi.fn()}
        onCreateInsight={onCreateInsight}
        onSaveInsightAsNote={onSaveInsightAsNote}
        onResearchThisInsight={vi.fn()}
        onSaveInsightToResearchThread={vi.fn()}
        onViewInsight={onViewInsight}
        onDeleteInsight={onDeleteInsight}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Create" }));
    expect(onCreateInsight).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Save as note" }));
    expect(onSaveInsightAsNote).toHaveBeenCalledWith(
      expect.objectContaining({ id: "ins-1", insight_type: "summary" }),
    );

    fireEvent.click(screen.getAllByRole("button", { name: "View insight" })[0]);
    expect(onViewInsight).toHaveBeenCalledWith(
      expect.objectContaining({ id: "ins-1", insight_type: "summary" }),
    );

    fireEvent.click(screen.getByRole("button", { name: "Delete insight" }));
    expect(onDeleteInsight).toHaveBeenCalledWith("ins-1");
  });

  it("renders loading and empty states", () => {
    const { rerender } = render(
      <SourceInsightsTab
        insights={[]}
        transformations={[]}
        selectedTransformation=""
        creatingInsight={false}
        loadingInsights={true}
        canSaveInsightsAsNotes={false}
        canSaveInsightsToResearchThreads={false}
        savingInsightId={null}
        savingInsightThreadId={null}
        onSelectedTransformationChange={vi.fn()}
        onCreateInsight={vi.fn()}
        onSaveInsightAsNote={vi.fn()}
        onResearchThisInsight={vi.fn()}
        onSaveInsightToResearchThread={vi.fn()}
        onViewInsight={vi.fn()}
        onDeleteInsight={vi.fn()}
      />,
    );

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();

    rerender(
      <SourceInsightsTab
        insights={[]}
        transformations={[]}
        selectedTransformation=""
        creatingInsight={false}
        loadingInsights={false}
        canSaveInsightsAsNotes={false}
        canSaveInsightsToResearchThreads={false}
        savingInsightId={null}
        savingInsightThreadId={null}
        onSelectedTransformationChange={vi.fn()}
        onCreateInsight={vi.fn()}
        onSaveInsightAsNote={vi.fn()}
        onResearchThisInsight={vi.fn()}
        onSaveInsightToResearchThread={vi.fn()}
        onViewInsight={vi.fn()}
        onDeleteInsight={vi.fn()}
      />,
    );

    expect(screen.getByText("No insights yet")).toBeInTheDocument();
  });

  it("renders creating state and falls back to transformation name", () => {
    render(
      <SourceInsightsTab
        insights={[]}
        transformations={[{ id: "tr-1", name: "Name fallback", title: "" }]}
        selectedTransformation="tr-1"
        creatingInsight={true}
        loadingInsights={false}
        canSaveInsightsAsNotes={true}
        canSaveInsightsToResearchThreads={true}
        savingInsightId={null}
        savingInsightThreadId={null}
        onSelectedTransformationChange={vi.fn()}
        onCreateInsight={vi.fn()}
        onSaveInsightAsNote={vi.fn()}
        onResearchThisInsight={vi.fn()}
        onSaveInsightToResearchThread={vi.fn()}
        onViewInsight={vi.fn()}
        onDeleteInsight={vi.fn()}
      />,
    );

    expect(screen.getByText("Name fallback")).toBeInTheDocument();
    expect(screen.getByText("Creating")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Creating" })).toBeDisabled();
  });

  it("truncates long insight content with ellipsis", () => {
    render(
      <SourceInsightsTab
        insights={[
          {
            id: "ins-long",
            insight_type: "summary",
            content: "x".repeat(181),
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
            source_id: "source:long",
          },
        ]}
        transformations={[]}
        selectedTransformation="tr-1"
        creatingInsight={false}
        loadingInsights={false}
        canSaveInsightsAsNotes={true}
        canSaveInsightsToResearchThreads={true}
        savingInsightId={null}
        savingInsightThreadId={null}
        onSelectedTransformationChange={vi.fn()}
        onCreateInsight={vi.fn()}
        onSaveInsightAsNote={vi.fn()}
        onResearchThisInsight={vi.fn()}
        onSaveInsightToResearchThread={vi.fn()}
        onViewInsight={vi.fn()}
        onDeleteInsight={vi.fn()}
      />,
    );

    expect(screen.getByText(/…$/)).toBeInTheDocument();
  });

  it("disables note saving until the source is linked to a notebook", () => {
    render(
      <SourceInsightsTab
        insights={[
          {
            id: "ins-locked",
            insight_type: "summary",
            content: "Notebook link required",
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
            source_id: "source:1",
          },
        ]}
        transformations={[]}
        selectedTransformation=""
        creatingInsight={false}
        loadingInsights={false}
        canSaveInsightsAsNotes={false}
        canSaveInsightsToResearchThreads={false}
        savingInsightId={null}
        savingInsightThreadId={null}
        onSelectedTransformationChange={vi.fn()}
        onCreateInsight={vi.fn()}
        onSaveInsightAsNote={vi.fn()}
        onResearchThisInsight={vi.fn()}
        onSaveInsightToResearchThread={vi.fn()}
        onViewInsight={vi.fn()}
        onDeleteInsight={vi.fn()}
      />,
    );

    expect(screen.getByText("Link the source to a notebook first.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save as note" })).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Save to research thread" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Research this insight" })).toBeInTheDocument();
  });

  it("surfaces direct research and thread-save actions from the insight list", () => {
    const onResearchThisInsight = vi.fn();
    const onSaveInsightToResearchThread = vi.fn();

    render(
      <SourceInsightsTab
        insights={[
          {
            id: "ins-path",
            insight_type: "summary",
            content: "Move this insight forward",
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
            source_id: "source:path",
          },
        ]}
        transformations={[]}
        selectedTransformation=""
        creatingInsight={false}
        loadingInsights={false}
        canSaveInsightsAsNotes={true}
        canSaveInsightsToResearchThreads={true}
        savingInsightId={null}
        savingInsightThreadId={null}
        onSelectedTransformationChange={vi.fn()}
        onCreateInsight={vi.fn()}
        onSaveInsightAsNote={vi.fn()}
        onResearchThisInsight={onResearchThisInsight}
        onSaveInsightToResearchThread={onSaveInsightToResearchThread}
        onViewInsight={vi.fn()}
        onDeleteInsight={vi.fn()}
      />,
    );

    expect(screen.getByText("Choose the next lane for this structured result")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Research this insight" }));
    expect(onResearchThisInsight).toHaveBeenCalledWith(expect.objectContaining({ id: "ins-path" }));

    fireEvent.click(screen.getByRole("button", { name: "Save to research thread" }));
    expect(onSaveInsightToResearchThread).toHaveBeenCalledWith(
      expect.objectContaining({ id: "ins-path" }),
    );
  });

  it("keeps one view action while surfacing the note-first lane", () => {
    render(
      <SourceInsightsTab
        insights={[
          {
            id: "ins-focus",
            insight_type: "summary",
            content: "One strong next step",
            created: "2026-01-01T00:00:00Z",
            updated: "2026-01-02T00:00:00Z",
            source_id: "source:focus",
          },
        ]}
        transformations={[]}
        selectedTransformation=""
        creatingInsight={false}
        loadingInsights={false}
        canSaveInsightsAsNotes={true}
        canSaveInsightsToResearchThreads={true}
        savingInsightId={null}
        savingInsightThreadId={null}
        onSelectedTransformationChange={vi.fn()}
        onCreateInsight={vi.fn()}
        onSaveInsightAsNote={vi.fn()}
        onResearchThisInsight={vi.fn()}
        onSaveInsightToResearchThread={vi.fn()}
        onViewInsight={vi.fn()}
        onDeleteInsight={vi.fn()}
      />,
    );

    expect(screen.getAllByRole("button", { name: "View insight" })).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Save as note" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save to research thread" })).toBeInTheDocument();
  });
});
