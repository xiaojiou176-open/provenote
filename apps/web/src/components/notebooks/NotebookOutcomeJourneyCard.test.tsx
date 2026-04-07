import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useNotebookDrafts } from "@/lib/hooks/use-drafts";
import { useNotebookResearchThreads } from "@/lib/hooks/use-research-threads";
import { NotebookOutcomeJourneyCard } from "./NotebookOutcomeJourneyCard";

vi.mock("@/lib/hooks/use-drafts");
vi.mock("@/lib/hooks/use-research-threads");

function mockDraftsHook(overrides: Partial<ReturnType<typeof useNotebookDrafts>> = {}) {
  return {
    drafts: [],
    isLoading: false,
    isFetching: false,
    error: null,
    refetch: vi.fn(),
    createDraft: { mutate: vi.fn(), isPending: false },
    rerunDraft: { mutate: vi.fn(), isPending: false },
    verifyDraft: { mutate: vi.fn(), isPending: false },
    ...overrides,
  } as unknown as ReturnType<typeof useNotebookDrafts>;
}

describe("NotebookOutcomeJourneyCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNotebookDrafts).mockReturnValue(mockDraftsHook());
    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);
  });

  it("asks for sources first when the notebook is still empty", () => {
    render(<NotebookOutcomeJourneyCard notebookId="notebook:1" sources={[]} />);

    expect(screen.getByText("Add sources to this notebook")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Drafts stay grounded only when the notebook already has source material. Add or link sources first.",
      ),
    ).toBeInTheDocument();
  });

  it("prompts compare and verify when a completed draft is ready", () => {
    vi.mocked(useNotebookDrafts).mockReturnValue(
      mockDraftsHook({
        drafts: [
          {
            id: "draft-2",
            notebook_id: "notebook:1",
            title: "Notebook Draft",
            status: "completed",
            model_id: "model-1",
            language: "en-US",
            near_dedup_threshold: 0.97,
            source_ids: ["source:1"],
            note_ids: [],
            thread_ids: ["research_thread:1"],
            version: 2,
            metrics: {
              coverage_rate: 0.91,
              missing_count: 0,
              duplicate_count: 0,
              uncited_claims_count: 0,
              dedup_group_count: 0,
              unknown_pid_count: 0,
              unclassified_count: 0,
            },
            coverage_json: {},
            dedup_json: {},
            result_markdown: "# Draft",
            source_paragraphs: [],
            sections: [],
            claims: [],
            dedup_entries: [],
            created: "2026-03-31T00:00:00.000Z",
            updated: "2026-03-31T00:00:00.000Z",
          },
        ],
      }),
    );
    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [
        {
          id: "research_thread:1",
          title: "Saved Insight",
          seed_kind: "insight",
          entry_count: 2,
          source_ids: ["source:1", "source:2"],
          updated: "2026-03-31T00:00:00.000Z",
        },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);

    render(
      <NotebookOutcomeJourneyCard
        notebookId="notebook:1"
        sources={[
          {
            id: "source:1",
            title: "Source One",
            status: "completed",
            insights_count: 0,
            embedded: true,
            created: "2026-03-31T00:00:00.000Z",
            updated: "2026-03-31T00:00:00.000Z",
          },
        ]}
      />,
    );

    expect(screen.getByText("Compare and verify the latest draft")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Review latest draft" })).toBeInTheDocument();
    expect(
      screen.getByText("1 saved thread(s) can feed the next draft revision."),
    ).toBeInTheDocument();
  });

  it("waits for source processing before suggesting the draft lane", () => {
    render(
      <NotebookOutcomeJourneyCard
        notebookId="notebook:1"
        sources={[
          {
            id: "source:1",
            title: "Source One",
            status: "running",
            insights_count: 0,
            embedded: false,
            created: "2026-03-31T00:00:00.000Z",
            updated: "2026-03-31T00:00:00.000Z",
          },
        ]}
      />,
    );

    expect(screen.getByText("Wait for source processing to finish")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Jump to draft lane" })).not.toBeInTheDocument();
  });

  it("scrolls to the draft lane when sources are ready and no draft exists yet", () => {
    const openDraftLane = vi.fn();
    const draftPanel = document.createElement("div");
    const scrollIntoView = vi.fn();
    draftPanel.dataset.testid = "notebook-drafts-panel";
    draftPanel.scrollIntoView = scrollIntoView;
    document.body.appendChild(draftPanel);

    render(
      <NotebookOutcomeJourneyCard
        notebookId="notebook:1"
        onOpenDraftLane={openDraftLane}
        sources={[
          {
            id: "source:1",
            title: "Source One",
            status: "completed",
            insights_count: 0,
            embedded: true,
            created: "2026-03-31T00:00:00.000Z",
            updated: "2026-03-31T00:00:00.000Z",
          },
        ]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Jump to draft lane" }));

    expect(screen.getByText("Create your first draft")).toBeInTheDocument();
    expect(openDraftLane).toHaveBeenCalledTimes(1);
    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });

    draftPanel.remove();
  });

  it("guides notebooks with saved research threads toward the thread lane before the first draft exists", () => {
    const openResearchThreadsLane = vi.fn();
    const researchThreadsPanel = document.createElement("div");
    const scrollIntoView = vi.fn();
    researchThreadsPanel.dataset.testid = "research-threads-panel";
    researchThreadsPanel.scrollIntoView = scrollIntoView;
    document.body.appendChild(researchThreadsPanel);

    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [
        {
          id: "research_thread:1",
          title: "Saved Insight",
          seed_kind: "insight",
          entry_count: 2,
          source_ids: ["source:1", "source:2"],
          updated: "2026-03-31T00:00:00.000Z",
        },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);

    render(
      <NotebookOutcomeJourneyCard
        notebookId="notebook:1"
        onOpenResearchThreadsLane={openResearchThreadsLane}
        sources={[
          {
            id: "source:1",
            title: "Source One",
            status: "completed",
            insights_count: 0,
            embedded: true,
            created: "2026-03-31T00:00:00.000Z",
            updated: "2026-03-31T00:00:00.000Z",
          },
        ]}
      />,
    );

    expect(screen.getByText("Turn saved research into the first draft")).toBeInTheDocument();
    expect(
      screen.getByText(
        "This notebook already has saved research threads. Review the strongest thread and promote it into the first notebook draft from the thread lane.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        'Start with "Saved Insight" first. It currently carries the richest saved thread context in this notebook (2 entries • 2 sources).',
      ),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Review research threads" }));

    expect(openResearchThreadsLane).toHaveBeenCalledTimes(1);
    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });

    researchThreadsPanel.remove();
  });

  it("uses the richest saved thread as the previewed draft seed", () => {
    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [
        {
          id: "research_thread:1",
          title: "Quick Search",
          seed_kind: "search",
          entry_count: 1,
          source_ids: ["source:1"],
          note_ids: [],
          entries: [],
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        },
        {
          id: "research_thread:2",
          title: "Deep Insight",
          seed_kind: "insight",
          entry_count: 4,
          source_ids: ["source:1", "source:2"],
          note_ids: ["note:1"],
          entries: [],
          created: "2026-03-30T00:00:00.000Z",
          updated: "2026-03-30T00:00:00.000Z",
        },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);

    render(
      <NotebookOutcomeJourneyCard
        notebookId="notebook:1"
        sources={[
          {
            id: "source:1",
            title: "Source One",
            status: "completed",
            insights_count: 0,
            embedded: true,
            created: "2026-03-31T00:00:00.000Z",
            updated: "2026-03-31T00:00:00.000Z",
          },
        ]}
      />,
    );

    expect(
      screen.getByText(
        'Start with "Deep Insight" first. It currently carries the richest saved thread context in this notebook (4 entries • 2 sources).',
      ),
    ).toBeInTheDocument();
  });

  it("still prioritizes saved research threads even when notebook sources are not yet ready", () => {
    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [
        {
          id: "research_thread:1",
          title: "Saved Insight",
          seed_kind: "insight",
          entry_count: 2,
          source_ids: ["source:1", "source:2"],
          updated: "2026-03-31T00:00:00.000Z",
        },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);

    render(
      <NotebookOutcomeJourneyCard
        notebookId="notebook:1"
        sources={[
          {
            id: "source:1",
            title: "Source One",
            status: "running",
            insights_count: 0,
            embedded: false,
            created: "2026-03-31T00:00:00.000Z",
            updated: "2026-03-31T00:00:00.000Z",
          },
        ]}
      />,
    );

    expect(screen.getByText("Turn saved research into the first draft")).toBeInTheDocument();
    expect(screen.queryByText("Wait for source processing to finish")).not.toBeInTheDocument();
  });

  it("guides verified notebooks toward research threads", () => {
    const openResearchThreadsLane = vi.fn();
    const researchThreadsPanel = document.createElement("div");
    const scrollIntoView = vi.fn();
    researchThreadsPanel.dataset.testid = "research-threads-panel";
    researchThreadsPanel.scrollIntoView = scrollIntoView;
    document.body.appendChild(researchThreadsPanel);

    vi.mocked(useNotebookDrafts).mockReturnValue(
      mockDraftsHook({
        drafts: [
          {
            id: "draft-3",
            notebook_id: "notebook:1",
            title: "Verified Draft",
            status: "verified",
            model_id: "model-1",
            language: "en-US",
            near_dedup_threshold: 0.97,
            source_ids: ["source:1"],
            note_ids: [],
            thread_ids: ["research_thread:1"],
            version: 3,
            metrics: {
              coverage_rate: 0.95,
              missing_count: 0,
              duplicate_count: 0,
              uncited_claims_count: 0,
              dedup_group_count: 0,
              unknown_pid_count: 0,
              unclassified_count: 0,
            },
            coverage_json: {},
            dedup_json: {},
            result_markdown: "# Draft",
            source_paragraphs: [],
            sections: [],
            claims: [],
            dedup_entries: [],
            created: "2026-03-31T00:00:00.000Z",
            updated: "2026-03-31T00:00:00.000Z",
          },
        ],
      }),
    );

    render(
      <NotebookOutcomeJourneyCard
        notebookId="notebook:1"
        onOpenResearchThreadsLane={openResearchThreadsLane}
        sources={[
          {
            id: "source:1",
            title: "Source One",
            status: "completed",
            insights_count: 0,
            embedded: true,
            created: "2026-03-31T00:00:00.000Z",
            updated: "2026-03-31T00:00:00.000Z",
          },
        ]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Review research threads" }));

    expect(screen.getByText("Verified outcome is ready")).toBeInTheDocument();
    expect(
      screen.getByText(
        "This notebook already has a verified outcome. Research threads can now become input for the next revision instead of living as loose work.",
      ),
    ).toBeInTheDocument();
    expect(openResearchThreadsLane).toHaveBeenCalledTimes(1);

    researchThreadsPanel.remove();
  });

  it("marks draft and verify as attention states when the latest draft failed", () => {
    const failedDraftPanel = document.createElement("div");
    failedDraftPanel.dataset.testid = "draft-card-draft-4";
    failedDraftPanel.scrollIntoView = vi.fn();
    document.body.appendChild(failedDraftPanel);

    vi.mocked(useNotebookDrafts).mockReturnValue(
      mockDraftsHook({
        drafts: [
          {
            id: "draft-4",
            notebook_id: "notebook:1",
            title: "Failed Draft",
            status: "failed",
            model_id: "model-1",
            language: "en-US",
            near_dedup_threshold: 0.97,
            source_ids: ["source:1"],
            note_ids: [],
            thread_ids: [],
            version: 4,
            metrics: {
              coverage_rate: 0.41,
              missing_count: 2,
              duplicate_count: 0,
              uncited_claims_count: 1,
              dedup_group_count: 0,
              unknown_pid_count: 0,
              unclassified_count: 0,
            },
            coverage_json: {},
            dedup_json: {},
            result_markdown: "# Draft",
            source_paragraphs: [],
            sections: [],
            claims: [],
            dedup_entries: [],
            created: "2026-03-31T00:00:00.000Z",
            updated: "2026-03-31T00:00:00.000Z",
          },
        ],
      }),
    );

    render(
      <NotebookOutcomeJourneyCard
        notebookId="notebook:1"
        sources={[
          {
            id: "source:1",
            title: "Source One",
            status: "completed",
            insights_count: 0,
            embedded: true,
            created: "2026-03-31T00:00:00.000Z",
            updated: "2026-03-31T00:00:00.000Z",
          },
        ]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Review latest draft" }));

    expect(screen.getAllByText("attention")).toHaveLength(2);
    expect(screen.getByText("Latest draft is failed (v4).")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Verify freezes markdown + metrics so the outcome becomes the stable reference point.",
      ),
    ).toBeInTheDocument();
    expect(failedDraftPanel.scrollIntoView).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "start",
    });

    failedDraftPanel.remove();
  });

  it("surfaces the just-saved insight thread as the next draft-adjacent seed", () => {
    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [
        {
          id: "research_thread:1",
          title: "Saved Insight",
          seed_kind: "insight",
          entry_count: 2,
          source_ids: ["source:1"],
          note_ids: [],
          entries: [],
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        },
        {
          id: "research_thread:2",
          title: "Deeper Research",
          seed_kind: "insight",
          entry_count: 4,
          source_ids: ["source:1", "source:2"],
          note_ids: ["note:1"],
          entries: [],
          created: "2026-03-31T01:00:00.000Z",
          updated: "2026-03-31T01:00:00.000Z",
        },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);

    render(
      <NotebookOutcomeJourneyCard
        notebookId="notebook:1"
        draftSeedThreadId="research_thread:1"
        sources={[
          {
            id: "source:1",
            title: "Source One",
            status: "completed",
            insights_count: 0,
            embedded: true,
            created: "2026-03-31T00:00:00.000Z",
            updated: "2026-03-31T00:00:00.000Z",
          },
        ]}
      />,
    );

    expect(
      screen.getByText("Your saved insight is now sitting at the draft doorway"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "This insight is already saved as a notebook research thread. Open the thread lane to review that exact seed before promoting it into the first draft.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        '"Saved Insight" is ready as the next draft-adjacent seed (2 entries • 1 sources).',
      ),
    ).toBeInTheDocument();
  });
});
