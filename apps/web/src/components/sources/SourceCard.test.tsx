import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SourceCard } from "./SourceCard";

const useSourceStatusMock = vi.fn();

const t = {
  common: {
    source: "source",
    actions: "Actions",
    progress: "Progress",
  },
  sources: {
    statusProcessing: "Processing",
    statusPreparingDesc: "Preparing",
    statusQueued: "Queued",
    statusQueuedDesc: "Queued desc",
    statusProcessingDesc: "Processing desc",
    statusCompleted: "Completed",
    statusCompletedDesc: "Completed desc",
    statusFailed: "Failed",
    statusFailedDesc: "Failed desc",
    untitledSource: "Untitled source",
    checking: "Checking",
    addUrl: "Add URL",
    uploadFile: "Upload file",
    enterText: "Enter text",
    insightsCount: "Insights {count}",
    retry: "Retry",
    removeFromNotebook: "Remove from notebook",
    retryProcessing: "Retry processing",
    deleteSource: "Delete source",
  },
};

vi.mock("@/lib/hooks/use-sources", () => ({
  useSourceStatus: (...args: unknown[]) => useSourceStatusMock(...args),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t }),
}));

vi.mock("@/components/common/ContextToggle", () => ({
  ContextToggle: ({ onChange }: { onChange: (mode: "off" | "insights" | "full") => void }) => (
    <button onClick={() => onChange("insights")} type="button">
      context-toggle
    </button>
  ),
}));

vi.mock("@/components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DropdownMenuItem: ({
    children,
    onClick,
    disabled,
  }: {
    children: ReactNode;
    onClick?: (event: { stopPropagation: () => void }) => void;
    disabled?: boolean;
  }) => (
    <button
      onClick={() => onClick?.({ stopPropagation: () => undefined })}
      disabled={disabled}
      type="button"
    >
      {children}
    </button>
  ),
  DropdownMenuSeparator: () => <hr />,
}));

describe("SourceCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSourceStatusMock.mockReturnValue({
      data: { status: "completed" },
      isLoading: false,
    });
  });

  it("handles failed state actions and context toggle", async () => {
    const onDelete = vi.fn();
    const onRetry = vi.fn();
    const onRemoveFromNotebook = vi.fn();
    const onContextModeChange = vi.fn();

    useSourceStatusMock.mockReturnValue({
      data: { status: "failed", message: "failed because parser error" },
      isLoading: false,
    });

    render(
      <SourceCard
        source={{
          id: "source-1",
          title: "Broken source",
          asset: null,
          embedded: false,
          embedded_chunks: 0,
          insights_count: 0,
          topics: ["topic-a", "topic-b", "topic-c"],
          created: "2026-01-01T00:00:00.000Z",
          updated: "2026-01-01T00:00:00.000Z",
        }}
        onDelete={onDelete}
        onRetry={onRetry}
        onRemoveFromNotebook={onRemoveFromNotebook}
        showRemoveFromNotebook
        contextMode="full"
        onContextModeChange={onContextModeChange}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledWith("source-1");

    fireEvent.click(screen.getByRole("button", { name: "Remove from notebook" }));
    fireEvent.click(screen.getByRole("button", { name: "Retry processing" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete source" }));
    fireEvent.click(screen.getByRole("button", { name: "context-toggle" }));

    expect(onRemoveFromNotebook).toHaveBeenCalledWith("source-1");
    expect(onRetry).toHaveBeenCalledWith("source-1");
    expect(onDelete).toHaveBeenCalledWith("source-1");
    expect(onContextModeChange).toHaveBeenCalledWith("insights");
    expect(screen.getByText("failed because parser error")).toBeInTheDocument();
  });

  it("shows processing progress and keeps card busy", () => {
    useSourceStatusMock.mockReturnValue({
      data: {
        status: "running",
        processing_info: { progress: 42.2 },
      },
      isLoading: false,
    });

    render(
      <SourceCard
        source={{
          id: "source-2",
          title: "Processing source",
          asset: { file_path: "/tmp/file.pdf" },
          embedded: false,
          embedded_chunks: 0,
          insights_count: 0,
          created: "2026-01-01T00:00:00.000Z",
          updated: "2026-01-01T00:00:00.000Z",
        }}
      />,
    );

    const card = screen.getByTestId("source-card-source-2");
    expect(card).toHaveAttribute("aria-busy", "true");
    expect(screen.getByText("42%")).toBeInTheDocument();
    expect(screen.getByText("Progress")).toBeInTheDocument();
  });

  it("triggers refresh after processing transitions to completed", async () => {
    const onRefresh = vi.fn();
    const statusState: { status: "running" | "completed" } = { status: "running" };
    useSourceStatusMock.mockImplementation(() => ({
      data: { status: statusState.status },
      isLoading: false,
    }));

    const { rerender } = render(
      <SourceCard
        source={{
          id: "source-3",
          title: "Refreshing source",
          asset: null,
          embedded: false,
          embedded_chunks: 0,
          insights_count: 0,
          created: "2026-01-01T00:00:00.000Z",
          updated: "2026-01-01T00:00:00.000Z",
          status: "running",
        }}
        onRefresh={onRefresh}
      />,
    );

    await waitFor(() => {
      expect(screen.getByTestId("source-card-source-3")).toHaveAttribute("aria-busy", "true");
    });

    statusState.status = "completed";
    rerender(
      <SourceCard
        source={{
          id: "source-3",
          title: "Refreshing source",
          asset: null,
          embedded: false,
          embedded_chunks: 0,
          insights_count: 0,
          created: "2026-01-01T00:00:00.000Z",
          updated: "2026-01-01T00:00:00.000Z",
          status: "completed",
        }}
        onRefresh={onRefresh}
      />,
    );

    await waitFor(
      () => {
        expect(onRefresh).toHaveBeenCalledTimes(1);
      },
      { timeout: 2000 },
    );
  });

  it("opens source when card action button is clicked", () => {
    const onClick = vi.fn();

    render(
      <SourceCard
        source={{
          id: "source-4",
          title: "Clickable source",
          asset: { url: "https://example.com" },
          embedded: true,
          embedded_chunks: 3,
          insights_count: 2,
          topics: ["alpha", "beta", "gamma"],
          created: "2026-01-01T00:00:00.000Z",
          updated: "2026-01-01T00:00:00.000Z",
        }}
        onClick={onClick}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open source Clickable source" }));
    expect(onClick).toHaveBeenCalledWith("source-4");
    expect(screen.getByText("Insights 2")).toBeInTheDocument();
    expect(screen.getByText("+1")).toBeInTheDocument();
  });

  it("does not bubble card click when actions trigger is clicked", () => {
    const onClick = vi.fn();

    render(
      <SourceCard
        source={{
          id: "source-5",
          title: "No bubble",
          asset: null,
          embedded: true,
          embedded_chunks: 1,
          insights_count: 0,
          created: "2026-01-01T00:00:00.000Z",
          updated: "2026-01-01T00:00:00.000Z",
        }}
        onClick={onClick}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Actions" }));
    expect(onClick).not.toHaveBeenCalled();
  });

  it("shows checking status while loading status for async source", () => {
    useSourceStatusMock.mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    render(
      <SourceCard
        source={{
          id: "source-6",
          title: "Queued source",
          command_id: "cmd-1",
          asset: null,
          embedded: false,
          embedded_chunks: 0,
          insights_count: 0,
          created: "2026-01-01T00:00:00.000Z",
          updated: "2026-01-01T00:00:00.000Z",
        }}
      />,
    );

    expect(screen.getByText("Checking")).toBeInTheDocument();
    expect(screen.getByTestId("source-card-source-6")).toHaveAttribute("aria-busy", "true");
  });

  it("falls back to completed status and keeps destructive actions disabled without handlers", () => {
    useSourceStatusMock.mockReturnValue({
      data: { status: "mystery-status" },
      isLoading: false,
    });

    render(
      <SourceCard
        source={{
          id: "source-7",
          title: "No handlers",
          asset: null,
          embedded: true,
          embedded_chunks: 0,
          insights_count: 0,
          created: "2026-01-01T00:00:00.000Z",
          updated: "2026-01-01T00:00:00.000Z",
        }}
        showRemoveFromNotebook
      />,
    );

    const card = screen.getByTestId("source-card-source-7");
    fireEvent.click(card);
    expect(card).toHaveAttribute("aria-busy", "false");

    expect(screen.getByRole("button", { name: "Remove from notebook" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Delete source" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Retry processing" })).not.toBeInTheDocument();
  });
});
