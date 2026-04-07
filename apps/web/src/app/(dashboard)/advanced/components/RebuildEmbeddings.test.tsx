import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { RebuildEmbeddings } from "./RebuildEmbeddings";

const hoisted = vi.hoisted(() => ({
  useMutationMock: vi.fn(),
  rebuildEmbeddingsMock: vi.fn(),
  getRebuildStatusMock: vi.fn(),
}));

vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useMutation: hoisted.useMutationMock,
  };
});

vi.mock("@/lib/api/embedding", () => ({
  embeddingApi: {
    rebuildEmbeddings: hoisted.rebuildEmbeddingsMock,
    getRebuildStatus: hoisted.getRebuildStatusMock,
  },
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      advanced: {
        rebuildEmbeddings: "Rebuild embeddings",
        rebuildEmbeddingsDesc: "Refresh embeddings for current content",
        rebuild: {
          mode: "Mode",
          existing: "Existing only",
          all: "Everything",
          existingDesc: "Only rebuild existing entries",
          allDesc: "Rebuild all entries",
          include: "Include",
          selectOneError: "Select at least one content type",
          starting: "Starting",
          queued: "Queued",
          running: "Running",
          startBtn: "Start rebuild",
          failed: "Failed",
          completed: "Completed",
          leavePageHint: "You can leave this page",
          startNew: "Start new rebuild",
          itemsProcessed: "{processed}/{total} ({percent}%) processed",
          failedItems: "Failed items: {count}",
          time: "Time",
          whenToRebuild: "When to rebuild",
          whenToRebuildAns: "Rebuild when embeddings drift.",
          howLong: "How long",
          howLongAns: "It depends on dataset size.",
          isSafe: "Is it safe",
          isSafeAns: "Yes, this is safe.",
        },
      },
      navigation: {
        sources: "Sources",
      },
      common: {
        created: "Created: {time}",
        progress: "Progress",
        notes: "Notes",
        insights: "Insights",
        error: "Error",
      },
      notebooks: {
        updated: "Updated",
      },
    },
  }),
}));

vi.mock("@/components/ui/card", () => ({
  Card: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  CardDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  CardContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/select", () => ({
  Select: ({
    value,
    onValueChange,
    children,
  }: {
    value: string;
    onValueChange: (value: string) => void;
    children: ReactNode;
  }) => (
    <select aria-label="Mode" value={value} onChange={(event) => onValueChange(event.target.value)}>
      {children}
    </select>
  ),
  SelectTrigger: ({ children }: { children: ReactNode }) => <>{children}</>,
  SelectValue: () => null,
  SelectContent: ({ children }: { children: ReactNode }) => <>{children}</>,
  SelectItem: ({ value, children }: { value: string; children: ReactNode }) => (
    <option value={value}>{children}</option>
  ),
}));

vi.mock("@/components/ui/checkbox", () => ({
  Checkbox: ({
    id,
    checked,
    onCheckedChange,
  }: {
    id?: string;
    checked?: boolean;
    onCheckedChange?: (checked: boolean) => void;
  }) => (
    <input
      id={id}
      checked={Boolean(checked)}
      onChange={(event) => onCheckedChange?.(event.target.checked)}
      type="checkbox"
    />
  ),
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({
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
}));

vi.mock("@/components/ui/label", () => ({
  Label: ({
    children,
    htmlFor,
    className,
    id,
  }: {
    children: ReactNode;
    htmlFor?: string;
    className?: string;
    id?: string;
  }) => (
    <label className={className} htmlFor={htmlFor} id={id}>
      {children}
    </label>
  ),
}));

vi.mock("@/components/ui/progress", () => ({
  Progress: ({ value }: { value: number }) => <div data-testid="progress">{value}</div>,
}));

vi.mock("@/components/ui/alert", () => ({
  Alert: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDescription: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/accordion", () => ({
  Accordion: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AccordionItem: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AccordionTrigger: ({ children }: { children: ReactNode }) => (
    <button type="button">{children}</button>
  ),
  AccordionContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

describe("RebuildEmbeddings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(globalThis, "setInterval").mockImplementation((callback: TimerHandler) => {
      void (callback as () => Promise<void> | void)();
      return 1 as unknown as ReturnType<typeof setInterval>;
    });
    vi.spyOn(globalThis, "clearInterval").mockImplementation(() => {});
    hoisted.useMutationMock.mockImplementation(
      (options: { onSuccess?: (data: { command_id: string }) => void }) => ({
        mutate: (request: unknown) => {
          hoisted.rebuildEmbeddingsMock(request);
          options.onSuccess?.({ command_id: "cmd-1" });
        },
        reset: vi.fn(),
        isPending: false,
        isError: false,
        error: null,
      }),
    );
    hoisted.getRebuildStatusMock.mockResolvedValue({
      status: "completed",
      progress: {
        total_items: 10,
        processed_items: 10,
        percentage: 100,
      },
      stats: {
        sources_processed: 3,
        notes_processed: 4,
        insights_processed: 3,
        failed_items: 0,
      },
      started_at: "2026-01-01T00:00:00Z",
      completed_at: "2026-01-01T00:00:10Z",
    });
  });

  it("blocks rebuild when no content type is selected", () => {
    render(<RebuildEmbeddings />);

    fireEvent.click(screen.getByLabelText("Sources"));
    fireEvent.click(screen.getByLabelText("Notes"));
    fireEvent.click(screen.getByLabelText("Insights"));

    expect(screen.getByText("Select at least one content type")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start rebuild" })).toBeDisabled();
  });

  it("starts rebuild, polls status, and renders completed progress", async () => {
    render(<RebuildEmbeddings />);

    fireEvent.change(screen.getByLabelText("Mode"), {
      target: { value: "all" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start rebuild" }));

    expect(hoisted.rebuildEmbeddingsMock).toHaveBeenCalledWith({
      mode: "all",
      include_sources: true,
      include_notes: true,
      include_insights: true,
    });

    await waitFor(() => {
      expect(hoisted.getRebuildStatusMock).toHaveBeenCalledWith("cmd-1");
      expect(screen.getByTestId("progress")).toHaveTextContent("100");
    });
  }, 15_000);
});
