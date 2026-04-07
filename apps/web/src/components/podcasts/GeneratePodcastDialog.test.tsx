import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GeneratePodcastDialog } from "./GeneratePodcastDialog";

const hoisted = vi.hoisted(() => ({
  useQueriesMock: vi.fn(),
  useQueryClientMock: vi.fn(),
  queryClient: {
    prefetchQuery: vi.fn(),
  },
  useNotebooksMock: vi.fn(),
  useEpisodeProfilesMock: vi.fn(),
  useGeneratePodcastMock: vi.fn(),
  mutateAsyncMock: vi.fn(),
  toastMock: vi.fn(),
  buildContextMock: vi.fn(),
}));

let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQueries: hoisted.useQueriesMock,
    useQueryClient: hoisted.useQueryClientMock,
  };
});

vi.mock("@/lib/hooks/use-notebooks", () => ({
  useNotebooks: hoisted.useNotebooksMock,
}));

vi.mock("@/lib/hooks/use-podcasts", () => ({
  useEpisodeProfiles: hoisted.useEpisodeProfilesMock,
  useGeneratePodcast: hoisted.useGeneratePodcastMock,
}));

vi.mock("@/lib/hooks/use-toast", () => ({
  useToast: () => ({ toast: hoisted.toastMock }),
}));

vi.mock("@/lib/api/chat", () => ({
  chatApi: {
    buildContext: hoisted.buildContextMock,
  },
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    language: "en-US",
    t: {
      common: {
        success: "Success",
        cancel: "Cancel",
        refreshPage: "Refresh page",
        notebookLabel: "Notebook: {name}",
      },
      podcasts: {
        generateEpisode: "Generate Episode",
        generateEpisodeDesc: "Generate description",
        episodeSettings: "Episode Settings",
        loadingProfiles: "Loading profiles",
        noProfilesFound: "No profiles",
        episodeProfile: "Episode Profile",
        episodeProfilePlaceholder: "Select profile",
        usesSpeakerProfile: "Uses speaker profile",
        episodeName: "Episode Name",
        episodeNamePlaceholder: "Type episode name",
        additionalInstructions: "Additional Instructions",
        instructionsPlaceholder: "Type instructions",
        generating: "Generating",
        generate: "Generate",
        profileRequired: "Profile required",
        profileRequiredDesc: "Choose profile first",
        nameRequired: "Name required",
        nameRequiredDesc: "Type a name",
        addContext: "Add context",
        addContextDesc: "Select at least one item",
        podcastTaskStarted: "Podcast task started",
        generationFailed: "Generation failed",
        buildContextFailed: "Build context failed",
      },
    },
  }),
}));

vi.mock("@/components/podcasts/GeneratePodcastContentSelectionPanel", () => ({
  GeneratePodcastContentSelectionPanel: ({
    fetchingNotebookIds,
    handleNotebookToggle,
    tokenCount,
    charCount,
  }: {
    fetchingNotebookIds: Set<string>;
    handleNotebookToggle: (notebookId: string, checked: boolean | "indeterminate") => void;
    tokenCount: number;
    charCount: number;
  }) => (
    <div>
      <div data-testid="fetching-count">{fetchingNotebookIds.size}</div>
      <div data-testid="context-counts">
        {tokenCount}:{charCount}
      </div>
      <button type="button" onClick={() => handleNotebookToggle("nb-1", true)}>
        Select Context
      </button>
    </div>
  ),
}));

vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({
    open,
    onOpenChange,
    children,
  }: {
    open: boolean;
    onOpenChange?: (open: boolean) => void;
    children: ReactNode;
  }) =>
    open ? (
      <div>
        <button onClick={() => onOpenChange?.(false)} type="button">
          dialog-close
        </button>
        {children}
      </div>
    ) : null,
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
}));

vi.mock("@/components/ui/select", () => ({
  Select: ({
    onValueChange,
    disabled,
    children,
  }: {
    onValueChange?: (value: string) => void;
    disabled?: boolean;
    children: ReactNode;
  }) => (
    <div>
      <button disabled={disabled} onClick={() => onValueChange?.("epf-1")} type="button">
        select-profile
      </button>
      {children}
    </div>
  ),
  SelectTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>,
  SelectContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

describe("GeneratePodcastDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);

    hoisted.useQueryClientMock.mockReturnValue(hoisted.queryClient);
    hoisted.useNotebooksMock.mockReturnValue({
      data: [{ id: "nb-1", name: "Notebook One" }],
      isLoading: false,
    });
    hoisted.useEpisodeProfilesMock.mockReturnValue({
      isLoading: false,
      episodeProfiles: [
        {
          id: "epf-1",
          name: "Interview Format",
          speaker_config: "Host Pack",
        },
      ],
    });
    hoisted.useGeneratePodcastMock.mockReturnValue({
      mutateAsync: hoisted.mutateAsyncMock,
      isPending: false,
    });

    hoisted.useQueriesMock.mockImplementation(
      (input: { queries: Array<{ queryKey: readonly unknown[] }> }) =>
        input.queries.map(() => ({
          data: undefined,
          isFetching: false,
        })),
    );

    hoisted.buildContextMock.mockResolvedValue({
      token_count: 12,
      char_count: 1200,
      context: { summary: "hello" },
    });
    hoisted.mutateAsyncMock.mockResolvedValue({ job_id: "job-1" });
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("builds context and submits podcast generation payload", async () => {
    const onOpenChange = vi.fn();
    const sourcesResult = {
      data: [{ id: "source-1", title: "Source A", insights_count: 1 }],
      isFetching: false,
    };
    const notesResult = {
      data: [{ id: "note-1", title: "Note A", updated: "2026-01-01T00:00:00Z" }],
      isFetching: false,
    };
    hoisted.useQueriesMock.mockImplementation(
      (input: { queries: Array<{ queryKey: readonly unknown[] }> }) => {
        const firstKey = String(input.queries[0]?.queryKey?.[0] ?? "");
        if (firstKey === "sources") {
          return input.queries.map(() => sourcesResult);
        }
        if (firstKey === "notes") {
          return input.queries.map(() => notesResult);
        }
        return [];
      },
    );

    render(<GeneratePodcastDialog open onOpenChange={onOpenChange} />);

    fireEvent.click(screen.getAllByRole("button", { name: "select-profile" })[1]);
    fireEvent.click(screen.getByRole("button", { name: "Select Context" }));
    fireEvent.change(document.getElementById("episode_name") as HTMLInputElement, {
      target: { value: " Daily Brief " },
    });
    fireEvent.change(document.getElementById("instructions") as HTMLTextAreaElement, {
      target: { value: " keep it concise " },
    });

    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    await waitFor(() => {
      expect(hoisted.mutateAsyncMock).toHaveBeenCalledTimes(1);
    });

    expect(hoisted.mutateAsyncMock).toHaveBeenCalledWith(
      expect.objectContaining({
        episode_profile: "Interview Format",
        speaker_profile: "Host Pack",
        episode_name: "Daily Brief",
        briefing_suffix: "keep it concise",
      }),
    );

    const payload = hoisted.mutateAsyncMock.mock.calls[0][0] as { content: string };
    expect(payload.content).toContain("Notebook: Notebook One");
    expect(payload.content).toContain('"summary": "hello"');

    expect(hoisted.toastMock).toHaveBeenCalledWith({
      title: "Success",
      description: "Podcast task started",
    });

    await waitFor(
      () => {
        expect(onOpenChange).toHaveBeenCalledWith(false);
      },
      { timeout: 1500 },
    );
  });

  it("shows destructive toast when generation fails", async () => {
    hoisted.mutateAsyncMock.mockRejectedValueOnce(new Error("backend down"));
    const sourcesResult = {
      data: [{ id: "source-1", title: "Source A", insights_count: 1 }],
      isFetching: false,
    };
    const notesResult = {
      data: [{ id: "note-1", title: "Note A", updated: "2026-01-01T00:00:00Z" }],
      isFetching: false,
    };
    hoisted.useQueriesMock.mockImplementation(
      (input: { queries: Array<{ queryKey: readonly unknown[] }> }) => {
        const firstKey = String(input.queries[0]?.queryKey?.[0] ?? "");
        if (firstKey === "sources") {
          return input.queries.map(() => sourcesResult);
        }
        if (firstKey === "notes") {
          return input.queries.map(() => notesResult);
        }
        return [];
      },
    );

    render(<GeneratePodcastDialog open onOpenChange={vi.fn()} />);

    fireEvent.click(screen.getAllByRole("button", { name: "select-profile" })[1]);
    fireEvent.click(screen.getByRole("button", { name: "Select Context" }));
    fireEvent.change(document.getElementById("episode_name") as HTMLInputElement, {
      target: { value: "Daily Brief" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    await waitFor(() => {
      expect(hoisted.toastMock).toHaveBeenCalledWith({
        title: "Generation failed",
        description: "backend down",
        variant: "destructive",
      });
    });
  });

  it("blocks submission when no episode profile is available", async () => {
    hoisted.useEpisodeProfilesMock.mockReturnValue({
      isLoading: false,
      episodeProfiles: [],
    });

    render(<GeneratePodcastDialog open onOpenChange={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    await waitFor(() => {
      expect(hoisted.toastMock).toHaveBeenCalledWith({
        title: "Profile required",
        description: "Choose profile first",
        variant: "destructive",
      });
    });
    expect(hoisted.mutateAsyncMock).not.toHaveBeenCalled();
  });

  it("requires a non-empty episode name and selected context before submitting", async () => {
    hoisted.useQueriesMock.mockImplementation(
      (input: { queries: Array<{ queryKey: readonly unknown[] }> }) =>
        input.queries.map(() => ({
          data: [],
          isFetching: false,
        })),
    );

    render(<GeneratePodcastDialog open onOpenChange={vi.fn()} />);

    fireEvent.click(screen.getAllByRole("button", { name: "select-profile" })[1]);
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    await waitFor(() => {
      expect(hoisted.toastMock).toHaveBeenCalledWith({
        title: "Name required",
        description: "Type a name",
        variant: "destructive",
      });
    });

    hoisted.toastMock.mockClear();
    fireEvent.change(document.getElementById("episode_name") as HTMLInputElement, {
      target: { value: "Named episode" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    await waitFor(() => {
      expect(hoisted.toastMock).toHaveBeenCalledWith({
        title: "Add context",
        description: "Select at least one item",
        variant: "destructive",
      });
    });
    expect(hoisted.buildContextMock).not.toHaveBeenCalled();
  });

  it("surfaces build-context failures as destructive toast copy", async () => {
    hoisted.buildContextMock.mockRejectedValue(new Error("bad context"));
    const sourcesResult = {
      data: [{ id: "source-1", title: "Source A", insights_count: 1 }],
      isFetching: false,
    };
    const notesResult = {
      data: [{ id: "note-1", title: "Note A", updated: "2026-01-01T00:00:00Z" }],
      isFetching: false,
    };
    hoisted.useQueriesMock.mockImplementation(
      (input: { queries: Array<{ queryKey: readonly unknown[] }> }) => {
        const firstKey = String(input.queries[0]?.queryKey?.[0] ?? "");
        if (firstKey === "sources") {
          return input.queries.map(() => sourcesResult);
        }
        if (firstKey === "notes") {
          return input.queries.map(() => notesResult);
        }
        return [];
      },
    );

    render(<GeneratePodcastDialog open onOpenChange={vi.fn()} />);

    fireEvent.click(screen.getAllByRole("button", { name: "select-profile" })[1]);
    fireEvent.click(screen.getByRole("button", { name: "Select Context" }));
    fireEvent.change(document.getElementById("episode_name") as HTMLInputElement, {
      target: { value: "Named episode" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    await waitFor(() => {
      expect(hoisted.toastMock).toHaveBeenCalledWith({
        title: "Generation failed",
        description: "Build context failed",
        variant: "destructive",
      });
    });
    expect(hoisted.mutateAsyncMock).not.toHaveBeenCalled();
  });

  it("resets local form state when dialog closes and reopens", async () => {
    const onOpenChange = vi.fn();
    const { rerender } = render(<GeneratePodcastDialog open onOpenChange={onOpenChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Select Context" }));
    fireEvent.change(document.getElementById("episode_name") as HTMLInputElement, {
      target: { value: "Episode before close" },
    });
    fireEvent.change(document.getElementById("instructions") as HTMLTextAreaElement, {
      target: { value: "retain me" },
    });

    fireEvent.click(screen.getByRole("button", { name: "dialog-close" }));
    rerender(<GeneratePodcastDialog open={false} onOpenChange={onOpenChange} />);
    rerender(<GeneratePodcastDialog open onOpenChange={onOpenChange} />);

    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(document.getElementById("episode_name")).toHaveValue("");
    expect(document.getElementById("instructions")).toHaveValue("");
    expect(screen.getByTestId("context-counts")).toHaveTextContent("0:0");
  });

  it("passes fetching notebook ids into content panel diagnostics", () => {
    hoisted.useQueriesMock.mockImplementation(
      (input: { queries: Array<{ queryKey: readonly unknown[] }> }) => {
        const firstKey = String(input.queries[0]?.queryKey?.[0] ?? "");
        if (firstKey === "sources") {
          return input.queries.map(() => ({
            data: undefined,
            isFetching: true,
          }));
        }
        if (firstKey === "notes") {
          return input.queries.map(() => ({
            data: undefined,
            isFetching: false,
          }));
        }
        return [];
      },
    );

    render(<GeneratePodcastDialog open onOpenChange={vi.fn()} />);

    expect(screen.getByTestId("fetching-count")).toHaveTextContent("1");
  });

  it("forwards cancel action to parent close handler", () => {
    const onOpenChange = vi.fn();

    render(<GeneratePodcastDialog open onOpenChange={onOpenChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
