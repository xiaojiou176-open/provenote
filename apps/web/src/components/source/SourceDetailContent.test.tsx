import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SourceDetailContent } from "./SourceDetailContent";

const originalCreateElement = document.createElement.bind(document);
let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

const mockState = vi.hoisted(() => ({
  invalidateQueries: vi.fn(),
  openModal: vi.fn(),
  routerPush: vi.fn(),
  contentTabProps: [] as Array<Record<string, unknown>>,
  insightsTabProps: [] as Array<Record<string, unknown>>,
  axiosClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: {},
  },
}));

vi.mock("@tanstack/react-query", async () => {
  const actual =
    await vi.importActual<typeof import("@tanstack/react-query")>("@tanstack/react-query");
  return {
    ...actual,
    useQueryClient: () => ({ invalidateQueries: mockState.invalidateQueries }),
  };
});

vi.mock("@/lib/hooks/use-auditable-runs", () => ({
  useAuditableRuns: () => ({
    latestRun: null,
  }),
}));

vi.mock("@/lib/hooks/use-drafts", () => ({
  useNotebookDrafts: () => ({
    drafts: [],
  }),
}));

const createResearchThreadMutateAsync = vi.fn();

vi.mock("@/lib/hooks/use-research-threads", () => ({
  useCreateResearchThread: () => ({
    mutateAsync: createResearchThreadMutateAsync,
    isPending: false,
  }),
}));

vi.mock("@/lib/hooks/use-sources", () => ({
  useReprocessSource: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
  useSourceProcessingReport: () => ({
    data: null,
    isLoading: false,
  }),
}));

vi.mock("axios", () => {
  const create = vi.fn(() => mockState.axiosClient);
  const isAxiosError = (error: unknown) =>
    Boolean((error as { isAxiosError?: boolean })?.isAxiosError);

  return {
    default: {
      create,
      isAxiosError,
    },
    create,
    isAxiosError,
  };
});

vi.mock("date-fns", () => ({
  formatDistanceToNow: () => "recently",
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockState.routerPush }),
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

vi.mock("@/components/common/InlineEdit", () => ({
  InlineEdit: ({
    value,
    onSave,
  }: {
    value: string;
    onSave: (next: string) => Promise<void> | void;
  }) => (
    <div>
      <span>{value}</span>
      <button onClick={() => void onSave("Renamed Source")} type="button">
        save-title
      </button>
      <button onClick={() => void onSave(value)} type="button">
        save-same-title
      </button>
    </div>
  ),
}));

vi.mock("@/components/source/NotebookAssociations", () => ({
  NotebookAssociations: ({ sourceId }: { sourceId: string }) => (
    <div data-testid="notebook-associations">{sourceId}</div>
  ),
}));

vi.mock("@/components/source/SourceContentTab", () => ({
  SourceContentTab: (props: Record<string, unknown>) => {
    mockState.contentTabProps.push(props);
    return <div data-testid="source-content-tab">content-tab</div>;
  },
}));

vi.mock("@/components/source/SourceInsightsTab", () => ({
  SourceInsightsTab: (props: Record<string, unknown>) => {
    mockState.insightsTabProps.push(props);
    const typedProps = props as {
      insights: Array<{ id: string }>;
      canSaveInsightsAsNotes: boolean;
      onSelectedTransformationChange: (id: string) => void;
      onCreateInsight: () => Promise<void> | void;
      onViewInsight: (insight: { id: string }) => void;
      onDeleteInsight: (insightId: string) => void;
      onSaveInsightAsNote: (insight: { id: string }) => Promise<void> | void;
    };

    return (
      <div data-testid="source-insights-tab">
        <button onClick={() => typedProps.onSelectedTransformationChange("tr-1")} type="button">
          select-transformation
        </button>
        <button onClick={() => void typedProps.onCreateInsight()} type="button">
          create-insight
        </button>
        <button
          onClick={() => typedProps.onViewInsight(typedProps.insights[0] ?? { id: "ins-1" })}
          type="button"
        >
          open-insight-dialog
        </button>
        <button
          onClick={() => typedProps.onDeleteInsight(typedProps.insights[0]?.id ?? "ins-1")}
          type="button"
        >
          request-insight-delete
        </button>
        <button
          disabled={!typedProps.canSaveInsightsAsNotes}
          onClick={() =>
            void typedProps.onSaveInsightAsNote(typedProps.insights[0] ?? { id: "ins-1" })
          }
          type="button"
        >
          save-insight-as-note
        </button>
      </div>
    );
  },
}));

vi.mock("@/components/source/SourceInsightDialog", () => ({
  SourceInsightDialog: ({
    open,
    insight,
    onDelete,
    onOpenChange,
    onSaveAsNote,
    onSaveToResearchThread,
    onResearchThisInsight,
    canSaveAsNote,
    canSaveToResearchThread,
  }: {
    open: boolean;
    insight?: { id: string; insight_type?: string; content?: string; source_id?: string };
    onDelete: (insightId: string) => Promise<void> | void;
    onOpenChange: (open: boolean) => void;
    onSaveAsNote?: (insight: { id: string }) => Promise<void> | void;
    onSaveToResearchThread?: (insight: { id: string }) => Promise<void> | void;
    onResearchThisInsight?: (insight: {
      id: string;
      insight_type?: string;
      content?: string;
      source_id?: string;
    }) => Promise<void> | void;
    canSaveAsNote?: boolean;
    canSaveToResearchThread?: boolean;
  }) =>
    open ? (
      <div data-testid="source-insight-dialog">
        <button onClick={() => onOpenChange(false)} type="button">
          close-insight-dialog
        </button>
        <button onClick={() => void onDelete(insight?.id ?? "ins-1")} type="button">
          delete-from-dialog
        </button>
        <button
          disabled={!canSaveAsNote}
          onClick={() => insight && void onSaveAsNote?.(insight)}
          type="button"
        >
          save-note-from-dialog
        </button>
        <button onClick={() => insight && void onResearchThisInsight?.(insight)} type="button">
          research-from-dialog
        </button>
        <button
          disabled={!canSaveToResearchThread}
          onClick={() => insight && void onSaveToResearchThread?.(insight)}
          type="button"
        >
          save-thread-from-dialog
        </button>
      </div>
    ) : null,
}));

vi.mock("@/components/source/SourceOutcomeJourneyCard", () => ({
  SourceOutcomeJourneyCard: ({
    source,
    onOpenDetails,
  }: {
    source: { id: string };
    onOpenDetails?: () => void;
  }) => (
    <div data-testid="source-outcome-journey-card">
      <span>journey:{source.id}</span>
      <button onClick={() => onOpenDetails?.()} type="button">
        open-journey-details
      </button>
    </div>
  ),
}));

vi.mock("@/components/ui/tabs", () => ({
  Tabs: ({ children, value }: { children: ReactNode; value?: string }) => (
    <div data-testid="tabs-root" data-value={value}>
      {children}
    </div>
  ),
  TabsList: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  TabsTrigger: ({ children }: { children: ReactNode }) => <button type="button">{children}</button>,
  TabsContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/card", () => ({
  Card: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  CardDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  CardContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/alert", () => ({
  Alert: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertTitle: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDescription: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({
    children,
    onClick,
    disabled,
    type,
    ...rest
  }: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    type?: "button" | "submit" | "reset";
  } & Record<string, unknown>) => (
    <button disabled={disabled} onClick={onClick} type={type ?? "button"} {...rest}>
      {children}
    </button>
  ),
}));

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children }: { children: ReactNode }) => <span>{children}</span>,
}));

vi.mock("@/components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuItem: ({
    children,
    onClick,
    disabled,
    className,
  }: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    className?: string;
  }) => (
    <button className={className} disabled={disabled} onClick={onClick} type="button">
      {children}
    </button>
  ),
  DropdownMenuSeparator: () => <hr />,
}));

vi.mock("@/components/ui/alert-dialog", () => ({
  AlertDialog: ({
    open,
    children,
    onOpenChange,
  }: {
    open: boolean;
    children: ReactNode;
    onOpenChange?: (open: boolean) => void;
  }) =>
    open ? (
      <div>
        {children}
        <button onClick={() => onOpenChange?.(false)} type="button">
          alert-close
        </button>
      </div>
    ) : null,
  AlertDialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  AlertDialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  AlertDialogFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogCancel: ({
    children,
    disabled,
    onClick,
  }: {
    children: ReactNode;
    disabled?: boolean;
    onClick?: () => void;
  }) => (
    <button disabled={disabled} onClick={onClick} type="button">
      {children}
    </button>
  ),
  AlertDialogAction: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/lib/utils/date-locale", () => ({
  getDateLocale: () => undefined,
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => {
    const messages = {
      common: {
        error: "Error",
        success: "Success",
        actions: "Actions",
        confirm: "Confirm",
        cancel: "Cancel",
        deleting: "Deleting",
        delete: "Delete",
        download: "Download",
        insights: "Insights",
        url: "URL",
        copyToClipboard: "Copy to clipboard",
        created_label: "Created",
        updated_label: "Updated",
      },
      chat: {
        chatWith: "Chat with {name}",
      },
      navigation: {
        sources: "Sources",
      },
      sources: {
        id: "ID",
        loadFailed: "Load failed",
        selectTransformation: "Select transformation first",
        insightGenerationStarted: "Insight generation started",
        researchThisInsight: "Research this insight",
        saveInsightToResearchThread: "Save to research thread",
        researchInsightSeed: "Continue researching this {type}: {summary}",
        researchInsightSeedFallback: "Continue researching this {type} from the source evidence",
        savedInsightThreadTitle: "{type} research thread",
        saveInsightAsNoteSuccess: "Insight saved as a notebook note",
        saveInsightAsNoteFailed: "Failed to save insight as a note",
        saveInsightNeedsNotebook: "Link this source to a notebook first",
        titlePlaceholder: "Title",
        untitledSource: "Untitled",
        details: "Details",
        content: "Content",
        metadata: "Metadata",
        topics: "Topics",
        uploadedFile: "Uploaded file",
        preparing: "Preparing",
        downloadFile: "Download file",
        fileUnavailable: "File unavailable",
        fileUnavailableDesc: "This file is no longer available",
        notEmbedded: "Not embedded",
        embedded: "Embedded",
        notEmbeddedAlert: "Not embedded alert",
        notEmbeddedDesc: "Embed to use this source in chat.",
        embedContent: "Embed content",
        embedding: "Embedding",
        alreadyEmbedded: "Already embedded",
        deleteSource: "Delete source",
        deleteSourceConfirm: "Delete source?",
        deleteInsight: "Delete insight",
        deleteInsightConfirm: "Delete this insight?",
        urlCopied: "URL copied",
        notFound: "Not found",
      },
    };

    const t = Object.assign((key: string, values?: Record<string, unknown>) => {
      const [scope, field] = key.split(".");
      const template =
        scope && field
          ? ((messages as Record<string, Record<string, string>>)[scope]?.[field] ?? key)
          : key;
      if (!values) {
        return template;
      }
      return template.replace(/\{(\w+)\}/g, (_, name: string) =>
        String(values[name] ?? `{${name}}`),
      );
    }, messages);

    return {
      language: "en",
      t,
    };
  },
}));

vi.mock("@/lib/hooks/use-modal-manager", () => ({
  useModalManager: () => ({
    openModal: mockState.openModal,
  }),
}));

vi.mock("@/lib/hooks/use-sources", () => ({
  useSourceProcessingReport: () => ({
    data: {
      source_id: "source:1",
      source_type: "link",
      title: "Original Source",
      processing_status: "completed",
      processing_message: "Processing history is available for this source.",
      processing_engine: "auto",
      extracted_length: 11,
      paragraph_count: 1,
      embedded: false,
      embedded_chunks: 0,
      insights_count: 1,
      has_file: true,
      file_available: true,
      command_id: "command:1",
      processing_info: { result: { engine: "auto" } },
    },
    refetch: vi.fn(),
  }),
  useReprocessSource: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}));

vi.mock("@/lib/api/sources", () => ({
  sourcesApi: {
    get: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    downloadFile: vi.fn(),
  },
}));

vi.mock("@/lib/api/insights", () => ({
  insightsApi: {
    listForSource: vi.fn(),
    create: vi.fn(),
    saveAsNote: vi.fn(),
    waitForCommand: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("@/lib/api/transformations", () => ({
  transformationsApi: {
    list: vi.fn(),
  },
}));

vi.mock("@/lib/api/embedding", () => ({
  embeddingApi: {
    embedContent: vi.fn(),
  },
}));

function buildSource(overrides: Record<string, unknown> = {}) {
  return {
    id: "source:1",
    title: "Original Source",
    full_text: "hello world",
    embedded: false,
    created: "2026-01-01T00:00:00Z",
    updated: "2026-01-02T00:00:00Z",
    notebooks: [],
    topics: ["topic-a"],
    asset: {
      url: "https://youtu.be/abc123",
      file_path: "/tmp/report.pdf",
    },
    ...overrides,
  };
}

describe("SourceDetailContent", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(async () => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    mockState.routerPush.mockReset();
    createResearchThreadMutateAsync.mockReset();
    mockState.contentTabProps.length = 0;
    mockState.insightsTabProps.length = 0;
    vi.useRealTimers();

    const { sourcesApi } = await import("@/lib/api/sources");
    const { insightsApi } = await import("@/lib/api/insights");
    const { transformationsApi } = await import("@/lib/api/transformations");
    const { embeddingApi } = await import("@/lib/api/embedding");

    vi.mocked(sourcesApi.get).mockResolvedValue(buildSource() as never);
    vi.mocked(sourcesApi.update).mockResolvedValue({} as never);
    vi.mocked(sourcesApi.delete).mockResolvedValue({} as never);
    vi.mocked(sourcesApi.downloadFile).mockResolvedValue({
      data: new Blob(["ok"]),
      headers: {
        "content-disposition": "attachment; filename*=UTF-8''report%20v1.pdf",
      },
    } as never);

    vi.mocked(insightsApi.listForSource).mockResolvedValue([
      {
        id: "ins-1",
        insight_type: "summary",
        content: "insight content",
        created: "2026-01-01T00:00:00Z",
        updated: "2026-01-02T00:00:00Z",
        source_id: "source:1",
      },
    ] as never);
    vi.mocked(insightsApi.create).mockResolvedValue({ command_id: "cmd-1" } as never);
    vi.mocked(insightsApi.saveAsNote).mockResolvedValue({
      id: "note:default",
      title: "Summary from source Original Source",
      content: "Saved note",
      note_type: "ai",
      created: "2026-04-01T00:00:00.000Z",
      updated: "2026-04-01T00:00:00.000Z",
    } as never);
    vi.mocked(insightsApi.waitForCommand).mockResolvedValue(true as never);
    vi.mocked(insightsApi.delete).mockResolvedValue({} as never);
    createResearchThreadMutateAsync.mockResolvedValue({
      id: "research_thread:88",
      notebook_id: "notebook:1",
      title: "summary research thread",
    });

    vi.mocked(transformationsApi.list).mockResolvedValue([
      { id: "tr-1", name: "Summarize", title: "Summarize" },
    ] as never);
    vi.mocked(embeddingApi.embedContent).mockResolvedValue({ message: "Embedded" } as never);

    Object.defineProperty(window, "confirm", {
      configurable: true,
      writable: true,
      value: vi.fn(() => true),
    });

    Object.defineProperty(window.navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn() },
    });

    Object.defineProperty(window, "open", {
      configurable: true,
      writable: true,
      value: vi.fn(),
    });

    Object.defineProperty(window.URL, "createObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(() => "blob:download"),
    });

    Object.defineProperty(window.URL, "revokeObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(),
    });

    vi.spyOn(document, "createElement").mockImplementation((tagName: string) => {
      const el = originalCreateElement(tagName);
      if (tagName.toLowerCase() === "a") {
        Object.defineProperty(el, "click", {
          configurable: true,
          writable: true,
          value: vi.fn(),
        });
      }
      return el;
    });
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("loads source details and wires chat/title/embed/delete actions", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");
    const { embeddingApi } = await import("@/lib/api/embedding");

    const onChatClick = vi.fn();
    const onClose = vi.fn();

    render(
      <SourceDetailContent
        sourceId="source:1"
        showChatButton
        onChatClick={onChatClick}
        onClose={onClose}
      />,
    );

    await waitFor(() => {
      expect(screen.queryByTestId("loading-spinner")).not.toBeInTheDocument();
    });

    expect(screen.getByText("ID: source:1")).toBeInTheDocument();
    expect(mockState.contentTabProps.at(-1)).toEqual(
      expect.objectContaining({
        isYouTubeUrl: true,
        youTubeVideoId: "abc123",
      }),
    );

    fireEvent.click(screen.getByRole("button", { name: "Chat with Sources" }));
    expect(onChatClick).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "save-title" }));
    await waitFor(() => {
      expect(sourcesApi.update).toHaveBeenCalledWith("source:1", { title: "Renamed Source" });
    });

    fireEvent.click((await screen.findAllByRole("button", { name: /Embed content/i }))[0]);
    await waitFor(() => {
      expect(embeddingApi.embedContent).toHaveBeenCalledWith("source:1", "source");
    });

    fireEvent.click(screen.getByRole("button", { name: /Delete source/i }));
    await waitFor(() => {
      expect(sourcesApi.delete).toHaveBeenCalledWith("source:1");
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("handles insight create flow (validation, command polling and fallback timer)", async () => {
    const { insightsApi } = await import("@/lib/api/insights");
    const { toast } = await import("sonner");

    render(<SourceDetailContent sourceId="source:1" />);

    await waitFor(() => {
      expect(screen.getByTestId("source-insights-tab")).toBeInTheDocument();
    });

    fireEvent.click(await screen.findByRole("button", { name: "create-insight" }));
    expect(toast.error).toHaveBeenCalledWith("Select transformation first");

    fireEvent.click(await screen.findByRole("button", { name: "select-transformation" }));
    fireEvent.click(await screen.findByRole("button", { name: "create-insight" }));

    await waitFor(() => {
      expect(insightsApi.create).toHaveBeenCalledWith("source:1", {
        transformation_id: "tr-1",
      });
    });
    await waitFor(() => {
      expect(insightsApi.waitForCommand).toHaveBeenCalledWith("cmd-1", {
        maxAttempts: 120,
        intervalMs: 2000,
      });
    });
    expect(mockState.invalidateQueries).toHaveBeenCalledWith({ queryKey: ["sources"] });
  });

  it("saves an insight into the linked notebook note lane", async () => {
    const { insightsApi } = await import("@/lib/api/insights");
    const { sourcesApi } = await import("@/lib/api/sources");
    const { toast } = await import("sonner");

    vi.mocked(sourcesApi.get).mockResolvedValueOnce(
      buildSource({
        notebooks: ["notebook:1"],
      }) as never,
    );
    vi.mocked(insightsApi.saveAsNote).mockResolvedValueOnce({
      id: "note-1",
      title: "Saved note",
      content: "summary",
      note_type: "ai",
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-01T00:00:00Z",
    } as never);

    render(<SourceDetailContent sourceId="source:1" />);

    await waitFor(() => {
      expect(screen.getByTestId("source-insights-tab")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "save-insight-as-note" }));

    await waitFor(() => {
      expect(insightsApi.saveAsNote).toHaveBeenCalledWith("ins-1", {
        notebook_id: "notebook:1",
      });
    });
    expect(mockState.invalidateQueries).toHaveBeenCalledWith({ queryKey: ["notes"] });
    expect(toast.success).toHaveBeenCalledWith("Insight saved as a notebook note");
    expect(mockState.openModal).toHaveBeenCalledWith("note", "note-1");
  });

  it("opens the details tab from the outcome journey card CTA", async () => {
    render(<SourceDetailContent sourceId="source:1" />);

    await waitFor(() => {
      expect(screen.getByTestId("tabs-root")).toHaveAttribute("data-value", "content");
    });

    fireEvent.click(screen.getByRole("button", { name: "open-journey-details" }));

    expect(screen.getByTestId("tabs-root")).toHaveAttribute("data-value", "details");
  });

  it("blocks saving an insight as note when the source is not linked to a notebook", async () => {
    const { insightsApi } = await import("@/lib/api/insights");

    render(<SourceDetailContent sourceId="source:1" />);

    await waitFor(() => {
      expect(screen.getByTestId("source-insights-tab")).toBeInTheDocument();
    });

    expect(insightsApi.saveAsNote).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "save-insight-as-note" })).toBeDisabled();
    expect(mockState.insightsTabProps.at(-1)).toEqual(
      expect.objectContaining({ canSaveInsightsAsNotes: false }),
    );
  });

  it("supports download/copy/external links and insight delete from dialog + confirmation dialog", async () => {
    const { insightsApi } = await import("@/lib/api/insights");
    const { sourcesApi } = await import("@/lib/api/sources");
    const { toast } = await import("sonner");

    render(<SourceDetailContent sourceId="source:1" />);

    await waitFor(() => {
      expect(screen.getByText("ID: source:1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: /Download file|Download/i })[0]);
    await waitFor(() => {
      expect(sourcesApi.downloadFile).toHaveBeenCalledWith("source:1");
    });
    expect(toast.success).toHaveBeenCalledWith("Success");

    fireEvent.click(await screen.findByRole("button", { name: "Copy to clipboard" }));
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("https://youtu.be/abc123");

    fireEvent.click(await screen.findByRole("button", { name: "URL" }));
    expect(window.open).toHaveBeenCalledWith("https://youtu.be/abc123", "_blank");

    fireEvent.click(await screen.findByRole("button", { name: "open-insight-dialog" }));
    await waitFor(() => {
      expect(screen.getByTestId("source-insight-dialog")).toBeInTheDocument();
    });
    fireEvent.click(await screen.findByRole("button", { name: "delete-from-dialog" }));
    await waitFor(() => {
      expect(insightsApi.delete).toHaveBeenCalledWith("ins-1");
    });

    fireEvent.click(await screen.findByRole("button", { name: "request-insight-delete" }));
    fireEvent.click(await screen.findByRole("button", { name: "Delete" }));
    await waitFor(() => {
      expect(insightsApi.delete).toHaveBeenCalledWith("ins-1");
    });
  });

  it("saves an insight as note from the dialog callback path", async () => {
    const { insightsApi } = await import("@/lib/api/insights");
    const { sourcesApi } = await import("@/lib/api/sources");
    const { toast } = await import("sonner");

    vi.mocked(sourcesApi.get).mockResolvedValueOnce(
      buildSource({ notebooks: ["notebook:dialog"] }) as never,
    );
    vi.mocked(insightsApi.saveAsNote).mockResolvedValueOnce({
      id: "note:dialog",
      title: "Dialog note",
      content: "Saved from dialog",
      note_type: "ai",
      created: "2026-04-01T00:00:00.000Z",
      updated: "2026-04-01T00:00:00.000Z",
    } as never);

    render(<SourceDetailContent sourceId="source:1" />);
    await waitFor(() => {
      expect(screen.getByText("ID: source:1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "open-insight-dialog" }));
    await waitFor(() => {
      expect(screen.getByTestId("source-insight-dialog")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "save-note-from-dialog" }));

    await waitFor(() => {
      expect(insightsApi.saveAsNote).toHaveBeenCalledWith("ins-1", {
        notebook_id: "notebook:dialog",
      });
    });
    expect(toast.success).toHaveBeenCalledWith("Insight saved as a notebook note");
    expect(mockState.openModal).toHaveBeenCalledWith("note", "note:dialog");
  });

  it("opens and dismisses the insight delete confirmation dialog", async () => {
    render(<SourceDetailContent sourceId="source:1" />);
    await waitFor(() => {
      expect(screen.getByText("ID: source:1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "request-insight-delete" }));
    expect(screen.getByText("Delete this insight?")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "alert-close" }));

    await waitFor(() => {
      expect(screen.queryByText("Delete this insight?")).not.toBeInTheDocument();
    });
  });

  it("saves an insight as a notebook note and opens the note modal", async () => {
    const { insightsApi } = await import("@/lib/api/insights");
    const { toast } = await import("sonner");
    const { sourcesApi } = await import("@/lib/api/sources");

    vi.mocked(sourcesApi.get).mockResolvedValueOnce(
      buildSource({ notebooks: ["notebook:1"] }) as never,
    );
    vi.mocked(insightsApi.saveAsNote).mockResolvedValueOnce({
      id: "note:77",
      title: "Summary from source Original Source",
      content: "Saved note",
      note_type: "ai",
      created: "2026-04-01T00:00:00.000Z",
      updated: "2026-04-01T00:00:00.000Z",
    } as never);

    render(<SourceDetailContent sourceId="source:1" />);
    await waitFor(() => {
      expect(screen.getByText("ID: source:1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "save-insight-as-note" }));

    await waitFor(() => {
      expect(insightsApi.saveAsNote).toHaveBeenCalledWith("ins-1", {
        notebook_id: "notebook:1",
      });
    });
    expect(toast.success).toHaveBeenCalledWith("Insight saved as a notebook note");
    expect(mockState.openModal).toHaveBeenCalledWith("note", "note:77");
    expect(mockState.invalidateQueries).toHaveBeenCalledWith({ queryKey: ["notes"] });
  });

  it("routes an inspected insight into the seeded research lane without auto-starting ask", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");

    vi.mocked(sourcesApi.get).mockResolvedValueOnce(
      buildSource({ notebooks: ["notebook:1"] }) as never,
    );

    render(<SourceDetailContent sourceId="source:1" />);

    await waitFor(() => {
      expect(screen.getByText("ID: source:1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "open-insight-dialog" }));
    await waitFor(() => {
      expect(screen.getByTestId("source-insight-dialog")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "research-from-dialog" }));

    await waitFor(() => {
      expect(mockState.routerPush).toHaveBeenCalledTimes(1);
    });

    const pushedUrl = mockState.routerPush.mock.calls[0][0] as string;
    expect(pushedUrl).toContain("/search?mode=ask&autostart=0&q=");
    expect(pushedUrl).toContain("source=source%3A1");
    expect(pushedUrl).toContain("notebook=notebook%3A1");
    const params = new URLSearchParams(pushedUrl.split("?")[1]);
    expect(params.get("q")).toBe("Continue researching this summary: insight content");
  });

  it("saves an inspected insight directly into a notebook research thread", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");

    vi.mocked(sourcesApi.get).mockResolvedValueOnce(
      buildSource({ notebooks: ["notebook:1"] }) as never,
    );

    render(<SourceDetailContent sourceId="source:1" />);

    await waitFor(() => {
      expect(screen.getByText("ID: source:1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "open-insight-dialog" }));
    await waitFor(() => {
      expect(screen.getByTestId("source-insight-dialog")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "save-thread-from-dialog" }));

    await waitFor(() => {
      expect(createResearchThreadMutateAsync).toHaveBeenCalledWith({
        notebookId: "notebook:1",
        payload: {
          title: "summary research thread",
          seed_kind: "insight",
          question: "Continue researching this summary: insight content",
          answer: "insight content",
          insight_id: "ins-1",
          insight_type: "summary",
          source_ids: ["source:1"],
          note_ids: [],
          search_results: [],
        },
      });
    });

    expect(mockState.routerPush).toHaveBeenCalledWith(
      "/notebooks/notebook%3A1?draftSeedThread=research_thread%3A88#research-threads-panel",
    );
  });

  it("marks file as unavailable when download returns 404", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");
    const { toast } = await import("sonner");

    vi.mocked(sourcesApi.downloadFile).mockRejectedValueOnce({
      isAxiosError: true,
      response: { status: 404 },
    } as never);

    render(<SourceDetailContent sourceId="source:1" />);

    await waitFor(() => {
      expect(screen.getByText("ID: source:1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: /Download file|Download/i })[0]);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("File unavailable");
    });
  });

  it("shows generic download error for non-404 failures", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");
    const { toast } = await import("sonner");

    vi.mocked(sourcesApi.downloadFile).mockRejectedValueOnce({
      isAxiosError: true,
      response: { status: 500 },
    } as never);

    render(<SourceDetailContent sourceId="source:1" />);
    await waitFor(() => {
      expect(screen.getByText("ID: source:1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: /Download file|Download/i })[0]);
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Error");
    });
  });

  it("does not delete source when user cancels confirmation", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");
    (window.confirm as unknown as ReturnType<typeof vi.fn>).mockReturnValueOnce(false);

    render(<SourceDetailContent sourceId="source:1" />);
    await waitFor(() => {
      expect(screen.getByText("ID: source:1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /Delete source/i }));
    expect(sourcesApi.delete).not.toHaveBeenCalled();
  });

  it("uses timer fallback when create insight returns no command id", async () => {
    const { insightsApi } = await import("@/lib/api/insights");

    vi.mocked(insightsApi.create).mockResolvedValueOnce({} as never);

    render(<SourceDetailContent sourceId="source:1" />);
    await screen.findByText("ID: source:1");

    fireEvent.click(await screen.findByRole("button", { name: "select-transformation" }));
    fireEvent.click(await screen.findByRole("button", { name: "create-insight" }));

    await waitFor(() => {
      expect(insightsApi.create).toHaveBeenCalledWith("source:1", {
        transformation_id: "tr-1",
      });
    });
    expect(insightsApi.waitForCommand).not.toHaveBeenCalled();
  }, 10000);

  it("handles insight delete failures from dialog", async () => {
    const { insightsApi } = await import("@/lib/api/insights");
    const { toast } = await import("sonner");
    vi.mocked(insightsApi.delete).mockRejectedValueOnce(new Error("delete failed"));

    render(<SourceDetailContent sourceId="source:1" />);
    await waitFor(() => {
      expect(screen.getByText("ID: source:1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "open-insight-dialog" }));
    await waitFor(() => {
      expect(screen.getByTestId("source-insight-dialog")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "delete-from-dialog" }));
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Error");
    });
  }, 10000);

  it("renders text source type when no url or file asset exists", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");
    vi.mocked(sourcesApi.get).mockReset();
    vi.mocked(sourcesApi.get).mockResolvedValue(
      buildSource({
        id: "source:text",
        title: "",
        asset: undefined,
        topics: [],
      }) as never,
    );

    render(<SourceDetailContent sourceId="source:text" />);
    await waitFor(() => {
      expect(screen.getByText("ID: source:text")).toBeInTheDocument();
    });

    expect(screen.getByText("text")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Copy to clipboard" })).not.toBeInTheDocument();
    expect(mockState.contentTabProps.at(-1)).toEqual(
      expect.objectContaining({
        isYouTubeUrl: false,
        youTubeVideoId: null,
      }),
    );
  }, 10000);

  it("shows source load error state when fetch fails", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");
    vi.mocked(sourcesApi.get).mockRejectedValueOnce(new Error("boom"));

    render(<SourceDetailContent sourceId="source:missing" />);

    await waitFor(() => {
      expect(screen.getByText("Load failed")).toBeInTheDocument();
    });
  }, 10000);

  it("returns early for empty source id and keeps loading state", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");
    const { insightsApi } = await import("@/lib/api/insights");
    const { transformationsApi } = await import("@/lib/api/transformations");

    render(<SourceDetailContent sourceId="" />);

    await waitFor(() => {
      expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
    });

    expect(sourcesApi.get).not.toHaveBeenCalled();
    expect(insightsApi.listForSource).not.toHaveBeenCalled();
    expect(transformationsApi.list).not.toHaveBeenCalled();
  });

  it("resets selected insight when insight dialog closes", async () => {
    const { insightsApi } = await import("@/lib/api/insights");
    const { sourcesApi } = await import("@/lib/api/sources");
    vi.mocked(sourcesApi.get).mockResolvedValue(buildSource() as never);

    render(<SourceDetailContent sourceId="source:1" />);
    await screen.findByText("ID: source:1");

    fireEvent.click(screen.getByRole("button", { name: "open-insight-dialog" }));
    await waitFor(() => {
      expect(screen.getByTestId("source-insight-dialog")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "close-insight-dialog" }));
    await waitFor(() => {
      expect(screen.queryByTestId("source-insight-dialog")).not.toBeInTheDocument();
    });
    expect(insightsApi.delete).toHaveBeenCalledTimes(0);
  });

  it("marks file action disabled after 404 and blocks follow-up download attempts", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");
    const { toast } = await import("sonner");

    vi.mocked(sourcesApi.get).mockResolvedValue(
      buildSource({
        id: "source:file-only",
        asset: { file_path: "/tmp/file-only.pdf" },
      }) as never,
    );
    vi.mocked(sourcesApi.downloadFile).mockRejectedValueOnce({
      isAxiosError: true,
      response: { status: 404 },
    } as never);

    render(<SourceDetailContent sourceId="source:file-only" />);
    await screen.findByText("ID: source:file-only");
    vi.mocked(sourcesApi.get).mockResolvedValue(
      buildSource({
        id: "source:file-only",
        asset: { file_path: "/tmp/file-only.pdf" },
        file_available: false,
      }) as never,
    );

    fireEvent.click(screen.getAllByRole("button", { name: /Download file|Download/i })[0]);

    await waitFor(() => {
      expect(sourcesApi.downloadFile).toHaveBeenCalledTimes(1);
      expect(toast.error).toHaveBeenCalledWith("File unavailable");
    });

    fireEvent.click(
      screen.getAllByRole("button", { name: /File unavailable|Download file|Download/i })[0],
    );
    expect(sourcesApi.downloadFile).toHaveBeenCalledTimes(1);
  });

  it("continues create insight flow when command polling rejects", async () => {
    const { insightsApi } = await import("@/lib/api/insights");
    const { sourcesApi } = await import("@/lib/api/sources");
    vi.mocked(sourcesApi.get).mockResolvedValue(buildSource() as never);
    vi.mocked(insightsApi.waitForCommand).mockRejectedValueOnce(new Error("polling failed"));

    render(<SourceDetailContent sourceId="source:1" />);
    await waitFor(() => {
      expect(mockState.insightsTabProps.length).toBeGreaterThan(0);
    });

    fireEvent.click(await screen.findByRole("button", { name: "select-transformation" }));

    await waitFor(() => {
      const props = mockState.insightsTabProps.at(-1) as { selectedTransformation: string };
      expect(props.selectedTransformation).toBe("tr-1");
    });

    fireEvent.click(await screen.findByRole("button", { name: "create-insight" }));

    await waitFor(() => {
      expect(insightsApi.create).toHaveBeenCalledWith("source:1", {
        transformation_id: "tr-1",
      });
      expect(insightsApi.waitForCommand).toHaveBeenCalledWith("cmd-1", {
        maxAttempts: 120,
        intervalMs: 2000,
      });
    });
  }, 10000);

  it("supports no-op title save and recovers from title/embed failures", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");
    const { embeddingApi } = await import("@/lib/api/embedding");
    const { toast } = await import("sonner");

    vi.mocked(sourcesApi.update).mockRejectedValueOnce(new Error("update failed"));
    vi.mocked(embeddingApi.embedContent).mockRejectedValueOnce(new Error("embed failed"));

    render(<SourceDetailContent sourceId="source:1" />);
    await screen.findByText("ID: source:1");

    fireEvent.click(screen.getByRole("button", { name: "save-same-title" }));
    expect(sourcesApi.update).toHaveBeenCalledTimes(0);

    fireEvent.click(screen.getByRole("button", { name: "save-title" }));
    await waitFor(() => {
      expect(sourcesApi.update).toHaveBeenCalledWith("source:1", { title: "Renamed Source" });
      expect(toast.error).toHaveBeenCalledWith("Error");
    });

    fireEvent.click(screen.getAllByRole("button", { name: /Embed content/i })[0]);
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Error");
    });
  });

  it("uses the fallback details CTA when the source is not linked to a notebook", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");

    vi.mocked(sourcesApi.get).mockResolvedValueOnce(
      buildSource({
        notebooks: [],
      }) as never,
    );

    render(<SourceDetailContent sourceId="source:1" />);
    await screen.findByText("ID: source:1");

    expect(screen.getByTestId("tabs-root")).toHaveAttribute("data-value", "content");
    fireEvent.click(screen.getByRole("button", { name: "sources.detailRail.detailsActionFallback" }));

    expect(screen.getByTestId("tabs-root")).toHaveAttribute("data-value", "details");
  });

  it("reports a toast when source deletion fails after confirmation", async () => {
    const { sourcesApi } = await import("@/lib/api/sources");
    const { toast } = await import("sonner");

    (window.confirm as unknown as ReturnType<typeof vi.fn>).mockReturnValueOnce(true);
    vi.mocked(sourcesApi.delete).mockRejectedValueOnce(new Error("delete source failed"));

    render(<SourceDetailContent sourceId="source:1" />);
    await screen.findByText("ID: source:1");

    fireEvent.click(screen.getByRole("button", { name: /Delete source/i }));

    await waitFor(() => {
      expect(sourcesApi.delete).toHaveBeenCalledWith("source:1");
      expect(toast.error).toHaveBeenCalledWith("Error");
    });
  });
});
