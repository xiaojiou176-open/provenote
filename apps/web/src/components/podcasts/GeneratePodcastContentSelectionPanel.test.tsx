import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { GeneratePodcastContentSelectionPanel } from "./GeneratePodcastContentSelectionPanel";

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    language: "en-US",
    t: {
      podcasts: {
        content: "Content",
        contentDesc: "Choose notebook content",
        itemsSelected: "{count} items",
        tokens: "{count} tokens",
        chars: "{count} chars",
        loadingNotebooks: "Loading notebooks",
        noNotebooksFoundInPodcasts: "No notebooks found",
        sources: "Sources",
        notes: "Notes",
        noContentSelected: "No content selected",
        noSources: "No sources",
        untitledSource: "Untitled source",
        link: "Link",
        file: "File",
        embedded: "Embedded",
        notEmbedded: "Not embedded",
        selectMode: "Select mode",
        noNotes: "No notes",
        untitledNote: "Untitled note",
        summary: "Summary",
        fullContent: "Full content",
      },
      common: {
        updated: "Updated",
      },
    },
  }),
}));

vi.mock("@/components/ui/accordion", () => ({
  Accordion: ({
    children,
    onValueChange,
  }: {
    children: ReactNode;
    onValueChange?: (value: string[]) => void;
  }) => (
    <div>
      <button onClick={() => onValueChange?.(["nb-1"])} type="button">
        expand-notebook
      </button>
      {children}
    </div>
  ),
  AccordionItem: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AccordionTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AccordionContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children }: { children: ReactNode }) => <span>{children}</span>,
}));

vi.mock("@/components/ui/checkbox", () => ({
  Checkbox: ({
    id,
    checked,
    onCheckedChange,
  }: {
    id?: string;
    checked?: boolean | "indeterminate";
    onCheckedChange?: (checked: boolean) => void;
  }) => (
    <input
      aria-label={id}
      checked={checked === true}
      data-indeterminate={String(checked === "indeterminate")}
      onChange={(event) => onCheckedChange?.(event.target.checked)}
      type="checkbox"
    />
  ),
}));

vi.mock("@/components/ui/label", () => ({
  Label: ({ children, htmlFor }: { children: ReactNode; htmlFor?: string }) => (
    <label htmlFor={htmlFor}>{children}</label>
  ),
}));

vi.mock("@/components/ui/scroll-area", () => ({
  ScrollArea: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/select", () => ({
  Select: ({
    children,
    value,
    onValueChange,
    disabled,
  }: {
    children: ReactNode;
    value: string;
    onValueChange: (value: string) => void;
    disabled?: boolean;
  }) => (
    <div data-disabled={String(Boolean(disabled))}>
      <button onClick={() => onValueChange("full")} type="button">
        mode:{value}
      </button>
      {children}
    </div>
  ),
  SelectTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>,
  SelectContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SelectItem: ({
    children,
    disabled,
    value,
  }: {
    children: ReactNode;
    disabled?: boolean;
    value: string;
  }) => (
    <div data-disabled={String(Boolean(disabled))} data-testid={`select-item-${value}`}>
      {children}
    </div>
  ),
}));

vi.mock("@/components/ui/separator", () => ({
  Separator: () => <hr />,
}));

describe("GeneratePodcastContentSelectionPanel", () => {
  const queryClient = {
    prefetchQuery: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading and empty states", () => {
    const { rerender } = render(
      <GeneratePodcastContentSelectionPanel
        charCount={0}
        expandedNotebooks={[]}
        fetchingNotebookIds={new Set()}
        handleNoteToggle={() => undefined}
        handleNotebookToggle={() => undefined}
        handleSourceModeChange={() => undefined}
        isLoading
        notebooks={[]}
        notesByNotebook={{}}
        queryClient={queryClient as never}
        selections={{}}
        selectedNotebookSummaries={[]}
        setExpandedNotebooks={() => undefined}
        sourcesByNotebook={{}}
        tokenCount={0}
      />,
    );

    expect(screen.getByText("Loading notebooks")).toBeInTheDocument();

    rerender(
      <GeneratePodcastContentSelectionPanel
        charCount={0}
        expandedNotebooks={[]}
        fetchingNotebookIds={new Set()}
        handleNoteToggle={() => undefined}
        handleNotebookToggle={() => undefined}
        handleSourceModeChange={() => undefined}
        isLoading={false}
        notebooks={[]}
        notesByNotebook={{}}
        queryClient={queryClient as never}
        selections={{}}
        selectedNotebookSummaries={[]}
        setExpandedNotebooks={() => undefined}
        sourcesByNotebook={{}}
        tokenCount={0}
      />,
    );

    expect(screen.getByText("No notebooks found")).toBeInTheDocument();
  });

  it("renders notebook/source/note selections and triggers callbacks with prefetch", () => {
    const handleNotebookToggle = vi.fn();
    const handleSourceModeChange = vi.fn();
    const handleNoteToggle = vi.fn();

    render(
      <GeneratePodcastContentSelectionPanel
        charCount={2400}
        expandedNotebooks={["nb-1"]}
        fetchingNotebookIds={new Set(["nb-1"])}
        handleNoteToggle={handleNoteToggle}
        handleNotebookToggle={handleNotebookToggle}
        handleSourceModeChange={handleSourceModeChange}
        isLoading={false}
        notebooks={[{ id: "nb-1", name: "Research" } as never]}
        notesByNotebook={{
          "nb-1": [{ id: "note-1", title: "Note 1", updated: "2026-01-01T00:00:00Z" } as never],
        }}
        queryClient={queryClient as never}
        selections={{
          "nb-1": {
            sources: { "source-1": "insights", "source-2": "off" },
            notes: { "note-1": "full" },
          },
        }}
        selectedNotebookSummaries={[{ notebookId: "nb-1", notes: 1, sources: 1 }]}
        setExpandedNotebooks={() => undefined}
        sourcesByNotebook={{
          "nb-1": [
            {
              id: "source-1",
              title: "Source A",
              embedded: true,
              insights_count: 2,
              asset: { url: "https://example.com" },
            } as never,
            {
              id: "source-2",
              title: "Source B",
              embedded: false,
              insights_count: 0,
              asset: null,
            } as never,
          ],
        }}
        tokenCount={1200}
      />,
    );

    expect(screen.getByText("2 items")).toBeInTheDocument();
    expect(screen.getByText(/1\.2K tokens \/ 2\.4K chars/)).toBeInTheDocument();
    expect(screen.getByText("Source A")).toBeInTheDocument();
    expect(screen.getByText("Note 1")).toBeInTheDocument();
    const insightOptions = screen.getAllByTestId("select-item-insights");
    expect(insightOptions[0]).toHaveAttribute("data-disabled", "false");
    expect(insightOptions[1]).toHaveAttribute("data-disabled", "true");

    fireEvent.click(screen.getByLabelText("notebook-toggle-nb-1"));
    expect(handleNotebookToggle).toHaveBeenCalledWith("nb-1", true);
    expect(queryClient.prefetchQuery).toHaveBeenCalledTimes(2);

    fireEvent.click(screen.getByRole("button", { name: "expand-notebook" }));

    fireEvent.click(screen.getByLabelText("source-selection-source-1"));
    expect(handleSourceModeChange).toHaveBeenCalledWith("nb-1", "source-1", "off");

    fireEvent.click(screen.getByRole("button", { name: "mode:off" }));
    expect(handleSourceModeChange).toHaveBeenCalledWith("nb-1", "source-2", "full");

    fireEvent.click(screen.getByLabelText("note-selection-note-1"));
    expect(handleNoteToggle).toHaveBeenCalledWith("nb-1", "note-1", false);

    const fullOptions = screen.getAllByTestId("select-item-full");
    expect(insightOptions[0]).toHaveAttribute("data-disabled", "false");
    expect(insightOptions[1]).toHaveAttribute("data-disabled", "true");
    expect(fullOptions[0]).toHaveAttribute("data-disabled", "false");
    expect(fullOptions[1]).toHaveAttribute("data-disabled", "false");
  });
});
