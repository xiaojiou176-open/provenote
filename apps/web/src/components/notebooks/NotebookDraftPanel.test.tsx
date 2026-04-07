import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { draftsApi } from "@/lib/api/drafts";
import { useNotebookDrafts } from "@/lib/hooks/use-drafts";
import { useNotebookResearchThreads } from "@/lib/hooks/use-research-threads";
import { enUS } from "@/lib/locales/en-US";
import { NotebookDraftPanel } from "./NotebookDraftPanel";

const hoisted = vi.hoisted(() => ({
  toastMock: vi.fn(),
  getApiErrorMessageMock: vi.fn(() => "resolved-draft-error"),
}));

vi.mock("@/lib/hooks/use-drafts");
vi.mock("@/lib/hooks/use-research-threads");
vi.mock("@/lib/api/drafts", () => ({
  draftsApi: {
    downloadMarkdown: vi.fn(),
    downloadBundle: vi.fn(),
  },
}));
vi.mock("@/lib/hooks/use-toast", () => ({
  useToast: () => ({ toast: hoisted.toastMock }),
}));
vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => {
    const interpolationRe = /\{(\w+)\}/g;
    const translate = (key: string, values?: Record<string, unknown>) => {
      const resolved = key
        .split(".")
        .reduce<unknown>(
          (current, segment) =>
            typeof current === "object" && current !== null
              ? (current as Record<string, unknown>)[segment]
              : undefined,
          enUS,
        );

      if (typeof resolved !== "string") {
        return key;
      }

      if (!values) {
        return resolved;
      }

      return resolved.replace(interpolationRe, (_, name: string) =>
        String(values[name] ?? `{${name}}`),
      );
    };
    const t = Object.assign(translate, enUS);

    return {
      t,
      language: "en-US",
    };
  },
}));
vi.mock("@/lib/utils/error-handler", () => ({
  getApiErrorMessage: hoisted.getApiErrorMessageMock,
}));
vi.mock("@/components/ui/scroll-area", () => ({
  ScrollArea: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));
vi.mock("@/components/ui/button", () => ({
  Button: ({
    children,
    onClick,
    disabled,
    ...props
  }: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
  }) => (
    <button disabled={disabled} onClick={onClick} type="button" {...props}>
      {children}
    </button>
  ),
}));
vi.mock("@/components/ui/card", () => ({
  Card: ({ children, ...props }: { children: ReactNode } & Record<string, unknown>) => (
    <div {...props}>{children}</div>
  ),
  CardHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  CardDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  CardContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));
vi.mock("@/components/ui/input", () => ({
  Input: ({
    value,
    onChange,
    placeholder,
    id,
  }: {
    value: string;
    onChange: (event: { target: { value: string } }) => void;
    placeholder?: string;
    id?: string;
  }) => (
    <input
      id={id}
      onChange={(event) => onChange({ target: { value: event.target.value } })}
      placeholder={placeholder}
      value={value}
    />
  ),
}));
vi.mock("@/components/ui/checkbox", () => ({
  Checkbox: ({
    checked,
    onCheckedChange,
    "aria-label": ariaLabel,
  }: {
    checked: boolean;
    onCheckedChange: () => void;
    "aria-label"?: string;
  }) => (
    <button aria-label={ariaLabel} onClick={onCheckedChange} type="button">
      {checked ? "checked" : "unchecked"}
    </button>
  ),
}));
vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children }: { children: ReactNode }) => <span>{children}</span>,
}));
vi.mock("@/components/ui/alert", () => ({
  Alert: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertTitle: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDescription: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));
vi.mock("@/components/ui/accordion", () => ({
  Accordion: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AccordionItem: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AccordionTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AccordionContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

function createHookMock(overrides: Partial<ReturnType<typeof useNotebookDrafts>> = {}) {
  return {
    drafts: [],
    isLoading: false,
    isFetching: false,
    error: null,
    refetch: vi.fn(),
    createDraft: {
      mutate: vi.fn(),
      isPending: false,
    },
    rerunDraft: {
      mutate: vi.fn(),
      isPending: false,
    },
    verifyDraft: {
      mutate: vi.fn(),
      isPending: false,
    },
    ...overrides,
  } as unknown as ReturnType<typeof useNotebookDrafts>;
}

describe("NotebookDraftPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);
    hoisted.getApiErrorMessageMock.mockImplementation((_error, translate, fallback) =>
      typeof translate === "function" ? translate("resolved-draft-error") : fallback,
    );
    Object.defineProperty(window.URL, "createObjectURL", {
      writable: true,
      value: vi.fn(() => "blob:draft"),
    });
    Object.defineProperty(window.URL, "revokeObjectURL", {
      writable: true,
      value: vi.fn(),
    });
    HTMLAnchorElement.prototype.click = vi.fn();
  });

  it("creates a draft from selected sources", async () => {
    const mutate = vi.fn();
    vi.mocked(useNotebookDrafts).mockReturnValue(
      createHookMock({
        createDraft: {
          mutate,
          isPending: false,
        } as unknown as ReturnType<typeof useNotebookDrafts>["createDraft"],
      }),
    );

    render(
      <NotebookDraftPanel
        notebookId="nb-1"
        notebookName="Notebook A"
        sources={[
          {
            id: "source:1",
            title: "Alpha",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
          {
            id: "source:2",
            title: "Bravo",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
        ]}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("Draft title (optional)"), {
      target: { value: "Research draft" },
    });
    fireEvent.click(screen.getByLabelText("Select Bravo"));
    fireEvent.click(screen.getByTestId("create-notebook-draft"));

    await waitFor(() => {
      expect(mutate).toHaveBeenCalledWith({
        title: "Research draft",
        source_ids: ["source:1"],
        note_ids: [],
        thread_ids: [],
      });
    });
  });

  it("bridges the empty draft lane to the recommended research thread", () => {
    const threadCard = document.createElement("div");
    const scrollIntoView = vi.fn();
    threadCard.dataset.testid = "research-thread-recommendation";
    threadCard.scrollIntoView = scrollIntoView;
    document.body.appendChild(threadCard);

    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [
        {
          id: "research_thread:seed",
          title: "Deep Insight",
          seed_kind: "insight",
          entry_count: 4,
          source_ids: ["source:1", "source:2"],
          note_ids: [],
          entries: [],
          created: "2026-04-03T00:00:00.000Z",
          updated: "2026-04-03T00:00:00.000Z",
        },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);

    render(
      <NotebookDraftPanel
        notebookId="nb-1"
        notebookName="Notebook A"
        sources={[
          {
            id: "source:1",
            title: "Alpha",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
        ]}
      />,
    );

    expect(screen.getByText("Next draft seed is already here")).toBeInTheDocument();
    expect(
      screen.getByText(
        '"Deep Insight" already carries the strongest saved context for the first draft in this notebook (4 entries • 2 sources).',
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Review that insight thread from the thread lane first, then create the draft there so the handoff stays inspectable.",
      ),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Review recommended thread" }));

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });

    threadCard.remove();
  });

  it("prefers the insight-seeded thread when the notebook arrives with a draft seed", () => {
    const threadCard = document.createElement("div");
    const scrollIntoView = vi.fn();
    threadCard.dataset.testid = "research-thread-draft-bridge";
    threadCard.scrollIntoView = scrollIntoView;
    document.body.appendChild(threadCard);

    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [
        {
          id: "research_thread:seed",
          title: "Saved Insight",
          seed_kind: "insight",
          entry_count: 1,
          source_ids: ["source:1"],
          note_ids: [],
          entries: [],
          created: "2026-04-03T00:00:00.000Z",
          updated: "2026-04-03T00:00:00.000Z",
        },
        {
          id: "research_thread:other",
          title: "Deeper Research",
          seed_kind: "insight",
          entry_count: 4,
          source_ids: ["source:1", "source:2"],
          note_ids: ["note:1"],
          entries: [],
          created: "2026-04-03T01:00:00.000Z",
          updated: "2026-04-03T01:00:00.000Z",
        },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);

    render(
      <NotebookDraftPanel
        notebookId="nb-1"
        notebookName="Notebook A"
        draftSeedThreadId="research_thread:seed"
        sources={[
          {
            id: "source:1",
            title: "Alpha",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
        ]}
      />,
    );

    expect(
      screen.getByText("Saved insight is already waiting in the thread lane"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        '"Saved Insight" was just saved into this notebook as a research thread (1 entries • 1 sources).',
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Review that saved thread first, then create the draft there so the source-to-draft handoff stays inspectable.",
      ),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Review saved thread" }));

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });

    threadCard.remove();
  });

  it("renders existing drafts and downloads markdown", async () => {
    const verifyMutate = vi.fn();
    vi.mocked(useNotebookDrafts).mockReturnValue(
      createHookMock({
        drafts: [
          {
            id: "draft-1",
            notebook_id: "nb-1",
            title: "Draft One",
            status: "completed",
            model_id: "model-draft",
            language: "zh-CN",
            near_dedup_threshold: 0.97,
            source_ids: ["source:1"],
            note_ids: [],
            thread_ids: [],
            version: 1,
            metrics: {
              coverage_rate: 0.8,
              missing_count: 1,
              duplicate_count: 0,
              uncited_claims_count: 0,
              dedup_group_count: 0,
              unknown_pid_count: 0,
              unclassified_count: 0,
            },
            coverage_json: {},
            dedup_json: {},
            result_markdown: "# Draft One",
            source_paragraphs: [],
            sections: [{ title: "Summary", source_pids: ["S001-P000001"] }],
            claims: [{ text: "Claim one", source_pids: ["S001-P000001"] }],
            dedup_entries: [],
            created: "2026-01-01T00:00:00.000Z",
            updated: "2026-01-02T00:00:00.000Z",
          },
        ],
        verifyDraft: {
          mutate: verifyMutate,
          isPending: false,
        } as unknown as ReturnType<typeof useNotebookDrafts>["verifyDraft"],
      }),
    );
    vi.mocked(draftsApi.downloadMarkdown).mockResolvedValue({
      data: new Blob(["# Draft One"]),
      headers: {
        "content-disposition": 'attachment; filename="draft-one.md"',
      },
    } as unknown as Awaited<ReturnType<typeof draftsApi.downloadMarkdown>>);
    vi.mocked(draftsApi.downloadBundle).mockResolvedValue({
      data: new Blob(["zip"]),
      headers: {
        "content-disposition": 'attachment; filename="draft-one-bundle.zip"',
      },
    } as unknown as Awaited<ReturnType<typeof draftsApi.downloadBundle>>);

    render(
      <NotebookDraftPanel
        notebookId="nb-1"
        sources={[
          {
            id: "source:1",
            title: "Alpha",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
        ]}
      />,
    );

    expect(screen.getByText("Draft One")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Mark Verified" }));
    fireEvent.click(screen.getByRole("button", { name: "Download Markdown" }));
    fireEvent.click(screen.getByRole("button", { name: "Export Bundle" }));

    await waitFor(() => {
      expect(verifyMutate).toHaveBeenCalledWith("draft-1");
      expect(draftsApi.downloadMarkdown).toHaveBeenCalledWith("draft-1");
      expect(draftsApi.downloadBundle).toHaveBeenCalledWith("draft-1");
    });
  });

  it("summarizes the notebook journey state for sources, draft lane, and verify", () => {
    vi.mocked(useNotebookDrafts).mockReturnValue(
      createHookMock({
        drafts: [
          {
            id: "draft-verified",
            notebook_id: "nb-1",
            title: "Draft One",
            status: "verified",
            model_id: "model-draft",
            language: "zh-CN",
            near_dedup_threshold: 0.97,
            source_ids: ["source:1"],
            note_ids: [],
            thread_ids: ["research_thread:1"],
            version: 2,
            parent_draft_id: "draft-1",
            metrics: {
              coverage_rate: 0.9,
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
            verified_brief_snapshot: { version: 2, metrics: { coverage_rate: 0.9 } },
            created: "2026-01-01T00:00:00.000Z",
            updated: "2026-01-02T00:00:00.000Z",
          },
        ],
      }),
    );

    render(
      <NotebookDraftPanel
        notebookId="nb-1"
        sources={[
          {
            id: "source:1",
            title: "Alpha",
            status: "completed",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
          {
            id: "source:2",
            title: "Bravo",
            status: "running",
            insights_count: 0,
            embedded: false,
            created: "",
            updated: "",
          },
        ]}
      />,
    );

    expect(screen.getByTestId("draft-journey-status")).toHaveTextContent("1/2 ready");
    expect(screen.getByTestId("draft-journey-status")).toHaveTextContent("verified");
    expect(screen.getByTestId("draft-journey-status")).toHaveTextContent("Verified v2");
    expect(screen.getByTestId("draft-source-summary")).toHaveTextContent("2 sources selected");
    expect(screen.getByTestId("draft-source-summary")).toHaveTextContent("1/2 ready");
    expect(screen.getByTestId("draft-source-summary")).toHaveTextContent(
      "1 source(s) are still processing before the draft lane is fully trustworthy.",
    );
  });

  it("renders loading and empty draft states and supports selection helpers", () => {
    vi.mocked(useNotebookDrafts).mockReturnValue(
      createHookMock({
        drafts: [],
        isLoading: true,
      }),
    );

    const { rerender } = render(
      <NotebookDraftPanel notebookId="nb-1" notebookName="Notebook A" sourcesLoading />,
    );

    expect(screen.getByText("Loading notebook sources...")).toBeInTheDocument();
    expect(screen.getByText("Loading drafts...")).toBeInTheDocument();

    vi.mocked(useNotebookDrafts).mockReturnValue(createHookMock({ drafts: [] }));
    rerender(
      <NotebookDraftPanel
        notebookId="nb-1"
        notebookName="Notebook A"
        sources={[
          {
            id: "source:1",
            title: "Alpha",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
          {
            id: "source:2",
            title: "Bravo",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
        ]}
      />,
    );

    expect(screen.getByText("No drafts yet")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Clear selection" }));
    expect(screen.getByTestId("create-notebook-draft")).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Select all" }));
    expect(screen.getByTestId("create-notebook-draft")).not.toBeDisabled();
  });

  it("shows draft errors and handles rerun plus failed download", async () => {
    const rerunMutate = vi.fn();
    vi.mocked(useNotebookDrafts).mockReturnValue(
      createHookMock({
        drafts: [
          {
            id: "draft-2",
            notebook_id: "nb-1",
            title: "Broken Draft",
            status: "failed",
            model_id: "model-draft",
            language: "en-US",
            near_dedup_threshold: 0.9,
            source_ids: [],
            note_ids: [],
            thread_ids: [],
            version: 2,
            metrics: {
              coverage_rate: 0,
              missing_count: 2,
              duplicate_count: 1,
              uncited_claims_count: 1,
              dedup_group_count: 1,
              unknown_pid_count: 1,
              unclassified_count: 1,
            },
            coverage_json: {},
            dedup_json: {},
            result_markdown: "# Broken Draft",
            source_paragraphs: [],
            sections: [{ title: "Summary", source_pids: [] }],
            claims: [{ text: "Claim", source_pids: [] }],
            dedup_entries: [],
            created: "2026-01-01T00:00:00.000Z",
            updated: "2026-01-02T00:00:00.000Z",
          },
        ],
        error: new Error("draft-load-error"),
        rerunDraft: {
          mutate: rerunMutate,
          isPending: false,
        } as unknown as ReturnType<typeof useNotebookDrafts>["rerunDraft"],
      }),
    );
    vi.mocked(draftsApi.downloadMarkdown).mockRejectedValue(new Error("download failed"));

    render(<NotebookDraftPanel notebookId="nb-1" sources={[]} />);

    expect(screen.getByText("Failed to load drafts")).toBeInTheDocument();
    expect(screen.getByText("resolved-draft-error")).toBeInTheDocument();
    expect(
      within(screen.getByTestId("draft-card-draft-2")).getByText("failed"),
    ).toBeInTheDocument();
    expect(screen.getByText("Version 2")).toBeInTheDocument();
    expect(screen.getByText("Coverage")).toBeInTheDocument();
    expect(screen.getByText("0.00")).toBeInTheDocument();
    expect(screen.getByText("Sections")).toBeInTheDocument();
    expect(screen.getByText("Claims")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Rerun" }));
    fireEvent.click(screen.getByRole("button", { name: "Download Markdown" }));

    await waitFor(() => {
      expect(rerunMutate).toHaveBeenCalledWith({ draftId: "draft-2" });
      expect(hoisted.toastMock).toHaveBeenCalledWith({
        title: "Error",
        description: "resolved-draft-error",
        variant: "destructive",
      });
    });
  });

  it("preserves compatible source selections when the linked source list refreshes", async () => {
    const mutate = vi.fn();
    vi.mocked(useNotebookDrafts).mockReturnValue(
      createHookMock({
        createDraft: {
          mutate,
          isPending: false,
        } as unknown as ReturnType<typeof useNotebookDrafts>["createDraft"],
      }),
    );

    const { rerender } = render(
      <NotebookDraftPanel
        notebookId="nb-1"
        sources={[
          {
            id: "source:1",
            title: "Alpha",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
          {
            id: "source:2",
            title: "Bravo",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
        ]}
      />,
    );

    fireEvent.click(screen.getByLabelText("Select Bravo"));

    rerender(
      <NotebookDraftPanel
        notebookId="nb-1"
        sources={[
          {
            id: "source:1",
            title: "Alpha",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
          {
            id: "source:3",
            title: "Charlie",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
        ]}
      />,
    );

    fireEvent.click(screen.getByTestId("create-notebook-draft"));

    await waitFor(() => {
      expect(mutate).toHaveBeenCalledWith({
        title: undefined,
        source_ids: ["source:1"],
        note_ids: [],
        thread_ids: [],
      });
    });
  });

  it("renders pending, verified, and queued draft states with empty section fallbacks", () => {
    vi.mocked(useNotebookDrafts).mockReturnValue(
      createHookMock({
        createDraft: {
          mutate: vi.fn(),
          isPending: true,
        } as unknown as ReturnType<typeof useNotebookDrafts>["createDraft"],
        drafts: [
          {
            id: "draft-verified",
            notebook_id: "nb-1",
            parent_draft_id: "draft-parent",
            title: "Verified Draft",
            status: "verified",
            model_id: "model-draft",
            language: "en-US",
            near_dedup_threshold: 0.9,
            source_ids: ["source:1"],
            note_ids: [],
            thread_ids: [],
            version: 4,
            metrics: {
              coverage_rate: 1,
              missing_count: 0,
              duplicate_count: 0,
              uncited_claims_count: 0,
              dedup_group_count: 0,
              unknown_pid_count: 0,
              unclassified_count: 0,
            },
            coverage_json: {},
            dedup_json: {},
            result_markdown: "# Verified",
            source_paragraphs: [],
            sections: [],
            claims: [],
            dedup_entries: [],
            verified_brief_snapshot: {
              version: 4,
              metrics: {
                coverage_rate: 1,
              },
            },
            created: "2026-01-01T00:00:00.000Z",
            updated: "None",
          },
          {
            id: "draft-running",
            notebook_id: "nb-1",
            title: "Queued Draft",
            status: "queued",
            model_id: "model-draft",
            language: "en-US",
            near_dedup_threshold: 0.9,
            source_ids: ["source:1", "source:2"],
            note_ids: [],
            thread_ids: [],
            version: 5,
            metrics: {
              coverage_rate: 0.5,
              missing_count: 1,
              duplicate_count: 0,
              uncited_claims_count: 0,
              dedup_group_count: 0,
              unknown_pid_count: 0,
              unclassified_count: 0,
            },
            coverage_json: {},
            dedup_json: {},
            result_markdown: "# Queued",
            source_paragraphs: [],
            sections: [{ title: "Summary", source_pids: ["S001-P000001"] }],
            claims: [{ text: "Claim", source_pids: ["S001-P000001"] }],
            dedup_entries: [],
            created: "2026-01-01T00:00:00.000Z",
            updated: "2026-01-02T00:00:00.000Z",
          },
        ],
      }),
    );

    render(
      <NotebookDraftPanel
        notebookId="nb-1"
        sources={[
          {
            id: "source:1",
            title: "Alpha",
            insights_count: 0,
            embedded: true,
            created: "",
            updated: "",
          },
        ]}
      />,
    );

    expect(screen.getByRole("button", { name: "Creating..." })).toBeDisabled();
    expect(screen.getAllByText("verified")).toHaveLength(2);
    expect(
      within(screen.getByTestId("draft-card-draft-running")).getByText("queued"),
    ).toBeInTheDocument();
    expect(screen.getByText(/Parent draft-parent/)).toBeInTheDocument();
    expect(screen.getByText("Verified snapshot frozen")).toBeInTheDocument();
    expect(screen.getByText("Why verify?")).toBeInTheDocument();
    expect(screen.getByText("Updated time unavailable")).toBeInTheDocument();
    expect(screen.getByText("No sections yet.")).toBeInTheDocument();
    expect(screen.getByText("No claims yet.")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Mark Verified" })[0]).toBeDisabled();
  });

  it("downloads markdown with fallback, invalid header, and utf-8 filenames", async () => {
    const originalCreateElement = document.createElement.bind(document);
    const anchor = originalCreateElement("a");
    vi.spyOn(document, "createElement").mockImplementation(((tagName: string) => {
      if (tagName.toLowerCase() === "a") {
        return anchor;
      }
      return originalCreateElement(tagName);
    }) as typeof document.createElement);

    vi.mocked(useNotebookDrafts).mockReturnValue(
      createHookMock({
        drafts: [
          {
            id: "draft-dl-1",
            notebook_id: "nb-1",
            title: "One",
            status: "completed",
            model_id: "model-draft",
            language: "en-US",
            near_dedup_threshold: 0.9,
            source_ids: [],
            note_ids: [],
            thread_ids: [],
            version: 1,
            metrics: {
              coverage_rate: 0.5,
              missing_count: 0,
              duplicate_count: 0,
              uncited_claims_count: 0,
              dedup_group_count: 0,
              unknown_pid_count: 0,
              unclassified_count: 0,
            },
            coverage_json: {},
            dedup_json: {},
            result_markdown: "# One",
            source_paragraphs: [],
            sections: [],
            claims: [],
            dedup_entries: [],
            created: "2026-01-01T00:00:00.000Z",
            updated: "2026-01-02T00:00:00.000Z",
          },
          {
            id: "draft-dl-2",
            notebook_id: "nb-1",
            title: "Two",
            status: "completed",
            model_id: "model-draft",
            language: "en-US",
            near_dedup_threshold: 0.9,
            source_ids: [],
            note_ids: [],
            thread_ids: [],
            version: 2,
            metrics: {
              coverage_rate: 0.5,
              missing_count: 0,
              duplicate_count: 0,
              uncited_claims_count: 0,
              dedup_group_count: 0,
              unknown_pid_count: 0,
              unclassified_count: 0,
            },
            coverage_json: {},
            dedup_json: {},
            result_markdown: "# Two",
            source_paragraphs: [],
            sections: [],
            claims: [],
            dedup_entries: [],
            created: "2026-01-01T00:00:00.000Z",
            updated: "2026-01-02T00:00:00.000Z",
          },
          {
            id: "draft-dl-3",
            notebook_id: "nb-1",
            title: "Three",
            status: "completed",
            model_id: "model-draft",
            language: "en-US",
            near_dedup_threshold: 0.9,
            source_ids: [],
            note_ids: [],
            thread_ids: [],
            version: 3,
            metrics: {
              coverage_rate: 0.5,
              missing_count: 0,
              duplicate_count: 0,
              uncited_claims_count: 0,
              dedup_group_count: 0,
              unknown_pid_count: 0,
              unclassified_count: 0,
            },
            coverage_json: {},
            dedup_json: {},
            result_markdown: "# Three",
            source_paragraphs: [],
            sections: [],
            claims: [],
            dedup_entries: [],
            created: "2026-01-01T00:00:00.000Z",
            updated: "2026-01-02T00:00:00.000Z",
          },
        ],
      }),
    );
    vi.mocked(draftsApi.downloadMarkdown)
      .mockResolvedValueOnce({
        data: new Blob(["# One"]),
        headers: {},
      } as unknown as Awaited<ReturnType<typeof draftsApi.downloadMarkdown>>)
      .mockResolvedValueOnce({
        data: new Blob(["# Two"]),
        headers: {
          "content-disposition": "attachment",
        },
      } as unknown as Awaited<ReturnType<typeof draftsApi.downloadMarkdown>>)
      .mockResolvedValueOnce({
        data: new Blob(["# Three"]),
        headers: {
          "content-disposition": "attachment; filename*=UTF-8''draft%20utf8.md",
        },
      } as unknown as Awaited<ReturnType<typeof draftsApi.downloadMarkdown>>);

    render(<NotebookDraftPanel notebookId="nb-1" sources={[]} />);

    const downloadButtons = screen.getAllByRole("button", { name: "Download Markdown" });
    fireEvent.click(downloadButtons[0]);
    await waitFor(() => {
      expect(anchor.download).toBe("draft-draft-dl-1.md");
    });

    fireEvent.click(downloadButtons[1]);
    await waitFor(() => {
      expect(anchor.download).toBe("draft-draft-dl-2.md");
    });

    fireEvent.click(downloadButtons[2]);
    await waitFor(() => {
      expect(anchor.download).toBe("draft utf8.md");
    });
  });
});
