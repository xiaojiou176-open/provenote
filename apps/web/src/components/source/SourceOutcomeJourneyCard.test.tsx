import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SourceOutcomeJourneyCard } from "./SourceOutcomeJourneyCard";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("SourceOutcomeJourneyCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.scrollTo = vi.fn();
  });

  it("guides users to link a notebook before draft creation", () => {
    render(
      <SourceOutcomeJourneyCard
        source={{
          id: "source:1",
          title: "Source One",
          full_text: "Body",
          notebooks: [],
          asset: null,
          embedded: true,
          embedded_chunks: 1,
          insights_count: 0,
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        report={{
          source_id: "source:1",
          processing_status: "completed",
          processing_message: "Ready",
          paragraph_count: 3,
          insights_count: 0,
          embedded: true,
          embedded_chunks: 3,
          last_embedded_at: "2026-03-31T00:00:00.000Z",
          can_reprocess: true,
        }}
        latestRun={null}
        latestDraft={null}
        onOpenDetails={vi.fn()}
      />,
    );

    expect(screen.getByText("Add this source to a notebook")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Open details and link notebook" }),
    ).toBeInTheDocument();
  });

  it("routes users to the notebook draft lane once auditable work is complete", () => {
    render(
      <SourceOutcomeJourneyCard
        source={{
          id: "source:1",
          title: "Source One",
          full_text: "Body",
          notebooks: ["notebook:1"],
          asset: null,
          embedded: true,
          embedded_chunks: 1,
          insights_count: 0,
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        report={{
          source_id: "source:1",
          processing_status: "completed",
          processing_message: "Ready",
          paragraph_count: 3,
          insights_count: 0,
          embedded: true,
          embedded_chunks: 3,
          last_embedded_at: "2026-03-31T00:00:00.000Z",
          can_reprocess: true,
        }}
        latestRun={{
          id: "run-1",
          source_id: "source:1",
          status: "completed",
          coverage_rate: 1,
          missing_count: 0,
          duplicate_count: 0,
          uncited_claims_count: 0,
          unknown_pid_count: 0,
          unclassified_count: 0,
          metrics: {
            coverage_rate: 1,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          markdown: "# Audit",
          result_markdown: "# Audit",
          claims: [],
          sections: [],
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        latestDraft={null}
        onOpenDetails={vi.fn()}
      />,
    );

    expect(screen.getByText("Create a notebook draft")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open notebook draft lane" })).toHaveAttribute(
      "href",
      "/notebooks/notebook%3A1",
    );
  });

  it("keeps the multi-notebook handoff focused on choosing the draft notebook", () => {
    const onOpenDetails = vi.fn();

    render(
      <SourceOutcomeJourneyCard
        source={{
          id: "source:1",
          title: "Source One",
          full_text: "Body",
          notebooks: ["notebook:1", "notebook:2"],
          asset: null,
          embedded: true,
          embedded_chunks: 1,
          insights_count: 0,
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        report={{
          source_id: "source:1",
          processing_status: "completed",
          processing_message: "Ready",
          paragraph_count: 3,
          insights_count: 0,
          embedded: true,
          embedded_chunks: 3,
          last_embedded_at: "2026-03-31T00:00:00.000Z",
          can_reprocess: true,
        }}
        latestRun={{
          id: "run-1",
          source_id: "source:1",
          status: "completed",
          coverage_rate: 1,
          missing_count: 0,
          duplicate_count: 0,
          uncited_claims_count: 0,
          unknown_pid_count: 0,
          unclassified_count: 0,
          metrics: {
            coverage_rate: 1,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          markdown: "# Audit",
          result_markdown: "# Audit",
          claims: [],
          sections: [],
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        latestDraft={null}
        onOpenDetails={onOpenDetails}
      />,
    );

    expect(screen.getByText("Choose a notebook for the draft")).toBeInTheDocument();
    expect(
      screen.getByText(
        "This source already has an auditable result and is linked to 2 notebooks. Open details to choose which notebook should carry the first draft.",
      ),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Choose draft notebook" }));
    expect(onOpenDetails).toHaveBeenCalledTimes(1);
    expect(
      screen.queryByRole("link", { name: "Open notebook draft lane" }),
    ).not.toBeInTheDocument();
  });

  it("keeps focus on the auditable lane while a run is still in progress", () => {
    render(
      <SourceOutcomeJourneyCard
        source={{
          id: "source:1",
          title: "Source One",
          full_text: "Body",
          notebooks: ["notebook:1"],
          asset: null,
          embedded: true,
          embedded_chunks: 1,
          insights_count: 0,
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        report={{
          source_id: "source:1",
          processing_status: "running",
          processing_message: "Working",
          paragraph_count: 3,
          insights_count: 0,
          embedded: true,
          embedded_chunks: 2,
          last_embedded_at: "2026-03-31T00:00:00.000Z",
          can_reprocess: true,
        }}
        latestRun={{
          id: "run-1",
          source_id: "source:1",
          status: "running",
          coverage_rate: 0.82,
          missing_count: 1,
          duplicate_count: 0,
          uncited_claims_count: 0,
          unknown_pid_count: 0,
          unclassified_count: 0,
          metrics: {
            coverage_rate: 0.82,
            missing_count: 1,
            duplicate_count: 0,
            uncited_claims_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          markdown: "# Audit",
          result_markdown: "# Audit",
          claims: [],
          sections: [],
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        latestDraft={null}
        onOpenDetails={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Review auditable status above" }));

    expect(screen.getByText("Run Auditable Markdown")).toBeInTheDocument();
    expect(window.scrollTo).toHaveBeenCalledWith({ top: 0, behavior: "smooth" });
  });

  it("promotes verified notebook outcomes once a draft has been verified", () => {
    render(
      <SourceOutcomeJourneyCard
        source={{
          id: "source:1",
          title: "Source One",
          full_text: "Body",
          notebooks: ["notebook:1"],
          asset: null,
          embedded: true,
          embedded_chunks: 1,
          insights_count: 0,
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        report={{
          source_id: "source:1",
          processing_status: "completed",
          processing_message: "Ready",
          paragraph_count: 3,
          insights_count: 0,
          embedded: true,
          embedded_chunks: 3,
          last_embedded_at: "2026-03-31T00:00:00.000Z",
          can_reprocess: true,
        }}
        latestRun={{
          id: "run-1",
          source_id: "source:1",
          status: "completed",
          coverage_rate: 1,
          missing_count: 0,
          duplicate_count: 0,
          uncited_claims_count: 0,
          unknown_pid_count: 0,
          unclassified_count: 0,
          metrics: {
            coverage_rate: 1,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          markdown: "# Audit",
          result_markdown: "# Audit",
          claims: [],
          sections: [],
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        latestDraft={{
          id: "draft-1",
          notebook_id: "notebook:1",
          title: "Notebook Draft",
          status: "verified",
          model_id: "model-1",
          language: "en-US",
          near_dedup_threshold: 0.97,
          source_ids: ["source:1"],
          note_ids: [],
          thread_ids: [],
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
        }}
        onOpenDetails={vi.fn()}
      />,
    );

    expect(screen.getByText("Verified outcome is ready")).toBeInTheDocument();
    expect(
      screen.getByText(
        "This source has already been carried into a verified notebook draft. You can continue from the notebook when you want a higher-level result.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open verified notebook" })).toHaveAttribute(
      "href",
      "/notebooks/notebook%3A1",
    );
  });

  it("routes users back to the notebook when a draft already exists but still needs review", () => {
    render(
      <SourceOutcomeJourneyCard
        source={{
          id: "source:1",
          title: "Source One",
          full_text: "Body",
          notebooks: ["notebook:1"],
          asset: null,
          embedded: true,
          embedded_chunks: 1,
          insights_count: 0,
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        report={{
          source_id: "source:1",
          processing_status: "completed",
          processing_message: "Ready",
          paragraph_count: 3,
          insights_count: 0,
          embedded: true,
          embedded_chunks: 3,
          last_embedded_at: "2026-03-31T00:00:00.000Z",
          can_reprocess: true,
        }}
        latestRun={{
          id: "run-1",
          source_id: "source:1",
          status: "completed",
          coverage_rate: 1,
          missing_count: 0,
          duplicate_count: 0,
          uncited_claims_count: 0,
          unknown_pid_count: 0,
          unclassified_count: 0,
          metrics: {
            coverage_rate: 1,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          markdown: "# Audit",
          result_markdown: "# Audit",
          claims: [],
          sections: [],
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        latestDraft={{
          id: "draft-2",
          notebook_id: "notebook:1",
          title: "Notebook Draft",
          status: "completed",
          model_id: "model-1",
          language: "en-US",
          near_dedup_threshold: 0.97,
          source_ids: ["source:1"],
          note_ids: [],
          thread_ids: [],
          version: 2,
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
        }}
        onOpenDetails={vi.fn()}
      />,
    );

    expect(screen.getByText("Review and verify the latest draft")).toBeInTheDocument();
    expect(
      screen.getByText(
        "The draft already exists. The shortest outcome path now is to compare it, then freeze the verified snapshot.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open draft review" })).toHaveAttribute(
      "href",
      "/notebooks/notebook%3A1",
    );
  });

  it("surfaces attention states when processing, auditable work, and draft verification fail", () => {
    render(
      <SourceOutcomeJourneyCard
        source={{
          id: "source:1",
          title: "Source One",
          full_text: "Body",
          notebooks: ["notebook:1"],
          asset: null,
          embedded: true,
          embedded_chunks: 1,
          insights_count: 0,
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        report={{
          source_id: "source:1",
          processing_status: "failed",
          processing_message: "Needs attention",
          paragraph_count: 0,
          insights_count: 0,
          embedded: false,
          embedded_chunks: 0,
          last_embedded_at: null,
          can_reprocess: true,
        }}
        latestRun={{
          id: "run-1",
          source_id: "source:1",
          status: "failed",
          coverage_rate: 0.42,
          missing_count: 3,
          duplicate_count: 0,
          uncited_claims_count: 1,
          unknown_pid_count: 0,
          unclassified_count: 0,
          metrics: {
            coverage_rate: 0.42,
            missing_count: 3,
            duplicate_count: 0,
            uncited_claims_count: 1,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          markdown: "# Audit",
          result_markdown: "# Audit",
          claims: [],
          sections: [],
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        latestDraft={{
          id: "draft-3",
          notebook_id: "notebook:1",
          title: "Notebook Draft",
          status: "failed",
          model_id: "model-1",
          language: "en-US",
          near_dedup_threshold: 0.97,
          source_ids: ["source:1"],
          note_ids: [],
          thread_ids: [],
          version: 4,
          metrics: {
            coverage_rate: 0.42,
            missing_count: 3,
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
        }}
        onOpenDetails={vi.fn()}
      />,
    );

    expect(screen.getAllByText("attention")).toHaveLength(4);
    expect(screen.getByText("Latest run is failed with coverage 0.42.")).toBeInTheDocument();
    expect(screen.getByText("Latest draft is failed in notebook notebook:1.")).toBeInTheDocument();
    expect(
      screen.getByText("Verify freezes the draft markdown and metrics into the outcome snapshot."),
    ).toBeInTheDocument();
  });

  it("keeps notebook drafts active while processing details are still loading", () => {
    render(
      <SourceOutcomeJourneyCard
        source={{
          id: "source:1",
          title: "Source One",
          full_text: "Body",
          notebooks: ["notebook:1"],
          asset: null,
          embedded: true,
          embedded_chunks: 1,
          insights_count: 0,
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        latestRun={{
          id: "run-1",
          source_id: "source:1",
          status: "completed",
          coverage_rate: 1,
          missing_count: 0,
          duplicate_count: 0,
          uncited_claims_count: 0,
          unknown_pid_count: 0,
          unclassified_count: 0,
          metrics: {
            coverage_rate: 1,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          markdown: "# Audit",
          result_markdown: "# Audit",
          claims: [],
          sections: [],
          created: "2026-03-31T00:00:00.000Z",
          updated: "2026-03-31T00:00:00.000Z",
        }}
        latestDraft={{
          id: "draft-queued",
          notebook_id: "notebook:1",
          title: "Queued Draft",
          status: "queued",
          model_id: "model-1",
          language: "en-US",
          near_dedup_threshold: 0.97,
          source_ids: ["source:1"],
          note_ids: [],
          thread_ids: [],
          version: 1,
          metrics: {
            coverage_rate: 0,
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
        }}
        onOpenDetails={vi.fn()}
      />,
    );

    expect(screen.getByText("Processing QA is still loading.")).toBeInTheDocument();
    expect(screen.getByText("Latest draft is queued in notebook notebook:1.")).toBeInTheDocument();
    expect(
      screen.getByText("Verify freezes the draft markdown and metrics into the outcome snapshot."),
    ).toBeInTheDocument();
  });
});
