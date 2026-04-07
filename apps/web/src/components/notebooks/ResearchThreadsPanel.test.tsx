import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  useCreateDraftFromResearchThread,
  useNotebookResearchThreads,
} from "@/lib/hooks/use-research-threads";
import { enUS } from "@/lib/locales/en-US";
import { ResearchThreadsPanel } from "./ResearchThreadsPanel";

const mutateMock = vi.fn();

vi.mock("date-fns", () => ({
  formatDistanceToNow: () => "2 minutes ago",
}));

vi.mock("@/lib/hooks/use-research-threads");
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

    return { t, language: "en-US" };
  },
}));
vi.mock("@/lib/utils/date-locale", () => ({
  getDateLocale: () => undefined,
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({
    children,
    onClick,
    disabled,
  }: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
  }) => (
    <button disabled={disabled} onClick={onClick} type="button">
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

describe("ResearchThreadsPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useCreateDraftFromResearchThread).mockReturnValue({
      mutate: mutateMock,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateDraftFromResearchThread>);
  });

  it("renders loading state", () => {
    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);

    render(<ResearchThreadsPanel notebookId="nb-1" />);

    expect(screen.getByText("Loading research threads...")).toBeInTheDocument();
  });

  it("renders empty state when no threads exist", () => {
    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);

    render(<ResearchThreadsPanel notebookId="nb-1" />);

    expect(
      screen.getByText(
        "No research threads yet. Save ask/search work into a notebook thread first.",
      ),
    ).toBeInTheDocument();
  });

  it("renders threads and creates a draft from the selected thread", () => {
    const draftPanel = document.createElement("div");
    const scrollIntoView = vi.fn();
    draftPanel.dataset.testid = "notebook-drafts-panel";
    draftPanel.scrollIntoView = scrollIntoView;
    document.body.appendChild(draftPanel);

    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [
        {
          id: "thread-1",
          title: "Saved Insight",
          seed_kind: "insight",
          entry_count: 2,
          source_ids: ["source:1", "source:2"],
          updated: "2026-03-30T06:00:00Z",
        },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);

    render(<ResearchThreadsPanel notebookId="nb-1" />);

    expect(
      screen.getByText(
        "Use saved research threads as the clean handoff point into the next notebook draft revision.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Recommended first")).toBeInTheDocument();
    expect(screen.getByText("Best next draft seed")).toBeInTheDocument();
    expect(
      screen.getByText(
        '"Saved Insight" currently carries the richest saved thread context in this notebook (2 entries • 2 sources).',
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Treat this as a transparent recommendation, not an automatic decision. It is simply the strongest insight thread to review first.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("research-thread-card-thread-1")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Start from recommended thread" }));

    expect(mutateMock).toHaveBeenCalledWith(
      "thread-1",
      expect.objectContaining({
        onSuccess: expect.any(Function),
      }),
    );

    const mutateOptions = mutateMock.mock.calls[0][1] as { onSuccess?: () => void };
    mutateOptions.onSuccess?.();

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });

    draftPanel.remove();
  });

  it("reorders threads so the richest saved context is recommended first", () => {
    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [
        {
          id: "thread-1",
          title: "Quick Search",
          seed_kind: "search",
          entry_count: 1,
          source_ids: ["source:1"],
          updated: "2026-03-31T06:00:00Z",
        },
        {
          id: "thread-2",
          title: "Deep Insight",
          seed_kind: "insight",
          entry_count: 4,
          source_ids: ["source:1", "source:2"],
          updated: "2026-03-30T06:00:00Z",
        },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);

    render(<ResearchThreadsPanel notebookId="nb-1" />);

    expect(screen.getByTestId("research-thread-recommendation")).toHaveTextContent("Deep Insight");
    expect(screen.getByTestId("research-thread-recommendation")).toHaveTextContent(
      "4 entries • 2 sources",
    );
    expect(screen.queryByTestId("research-thread-card-thread-2")).not.toBeInTheDocument();
  });

  it("highlights the just-saved insight thread as a draft-adjacent bridge", () => {
    vi.mocked(useNotebookResearchThreads).mockReturnValue({
      data: [
        {
          id: "thread-1",
          title: "Saved Insight",
          seed_kind: "insight",
          entry_count: 1,
          source_ids: ["source:1"],
          note_ids: [],
          updated: "2026-03-31T06:00:00Z",
        },
        {
          id: "thread-2",
          title: "Deep Insight",
          seed_kind: "insight",
          entry_count: 4,
          source_ids: ["source:1", "source:2"],
          note_ids: ["note:1"],
          updated: "2026-03-30T06:00:00Z",
        },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebookResearchThreads>);

    render(<ResearchThreadsPanel notebookId="nb-1" draftSeedThreadId="thread-1" />);

    expect(screen.getByTestId("research-thread-draft-bridge")).toHaveTextContent(
      "Saved from insight",
    );
    expect(screen.getByTestId("research-thread-draft-bridge")).toHaveTextContent(
      "This thread is ready to become a draft seed",
    );
    expect(screen.getByTestId("research-thread-draft-bridge")).toHaveTextContent(
      '"Saved Insight" just captured this insight into the notebook lane (1 entries • 1 sources). Review it here when you want to turn this specific insight into a draft.',
    );
    expect(screen.queryByTestId("research-thread-card-thread-1")).not.toBeInTheDocument();
  });
});
