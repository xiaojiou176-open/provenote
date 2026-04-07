import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useNotebooks } from "@/lib/hooks/use-notebooks";
import { useCreateResearchThread } from "@/lib/hooks/use-research-threads";
import { SaveToResearchThreadDialog } from "./SaveToResearchThreadDialog";

const mutateAsyncMock = vi.fn();

vi.mock("@/lib/hooks/use-notebooks");
vi.mock("@/lib/hooks/use-research-threads");
vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => {
    const messages = {
      common: {
        cancel: "Cancel",
      },
      searchPage: {
        researchCaptureAnswerLabel: "answer",
        researchCaptureSearchResultLabel: "search result",
        saveToResearchThreadTitle: "Save to research thread",
        saveToResearchThreadDescription:
          "Persist this {resultType} as a notebook research artifact instead of a loose note.",
        researchCaptureLoadingNotebooks: "Loading notebooks...",
        saveResearchThread: "Save thread",
      },
      sources: {
        noNotebooksFound: "No notebooks found.",
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
    return { t };
  },
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

vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({ open, children }: { open: boolean; children: ReactNode }) =>
    open ? <div>{children}</div> : null,
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  DialogFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
}));

vi.mock("@/components/ui/input", () => ({
  Input: ({
    value,
    onChange,
  }: {
    value: string;
    onChange: (event: { target: { value: string } }) => void;
  }) => (
    <input
      aria-label="thread-title"
      onChange={(event) => onChange({ target: { value: event.target.value } })}
      value={value}
    />
  ),
}));

vi.mock("@/components/ui/checkbox-list", () => ({
  CheckboxList: ({
    items,
    selectedIds,
    onToggle,
    emptyMessage,
  }: {
    items: Array<{ id: string; title: string }>;
    selectedIds: string[];
    onToggle: (id: string) => void;
    emptyMessage?: string;
  }) => (
    <div>
      {items.length === 0 ? (
        <span>{emptyMessage}</span>
      ) : (
        items.map((item) => (
          <button key={item.id} onClick={() => onToggle(item.id)} type="button">
            {item.title}:{selectedIds.includes(item.id) ? "on" : "off"}
          </button>
        ))
      )}
    </div>
  ),
}));

describe("SaveToResearchThreadDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNotebooks).mockReturnValue({
      data: [
        { id: "nb-1", name: "Notebook A", description: "First" },
        { id: "nb-2", name: "Notebook B", description: "Second" },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebooks>);
    vi.mocked(useCreateResearchThread).mockReturnValue({
      mutateAsync: mutateAsyncMock,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateResearchThread>);
  });

  it("saves the selected ask result into each selected notebook", async () => {
    const onOpenChange = vi.fn();
    mutateAsyncMock.mockResolvedValue(undefined);

    render(
      <SaveToResearchThreadDialog
        open
        onOpenChange={onOpenChange}
        mode="ask"
        defaultTitle="Ask Result"
        question="What changed?"
        answer="A lot changed."
        sourceIds={["source:1"]}
        noteIds={["note:1"]}
      />,
    );

    fireEvent.change(screen.getByLabelText("thread-title"), { target: { value: "Fresh Thread" } });
    fireEvent.click(screen.getByRole("button", { name: "Notebook A:off" }));
    fireEvent.click(screen.getByRole("button", { name: "Notebook B:off" }));
    fireEvent.click(screen.getByRole("button", { name: "Save thread" }));

    await waitFor(() => {
      expect(mutateAsyncMock).toHaveBeenCalledTimes(2);
    });

    expect(mutateAsyncMock).toHaveBeenNthCalledWith(1, {
      notebookId: "nb-1",
      payload: {
        title: "Fresh Thread",
        seed_kind: "ask",
        question: "What changed?",
        answer: "A lot changed.",
        source_ids: ["source:1"],
        note_ids: ["note:1"],
        search_results: [],
      },
    });
    expect(mutateAsyncMock).toHaveBeenNthCalledWith(2, {
      notebookId: "nb-2",
      payload: {
        title: "Fresh Thread",
        seed_kind: "ask",
        question: "What changed?",
        answer: "A lot changed.",
        source_ids: ["source:1"],
        note_ids: ["note:1"],
        search_results: [],
      },
    });
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("shows loading and empty notebook messages", () => {
    vi.mocked(useNotebooks).mockReturnValue({
      data: [],
      isLoading: true,
    } as unknown as ReturnType<typeof useNotebooks>);

    const { rerender } = render(
      <SaveToResearchThreadDialog
        open
        onOpenChange={vi.fn()}
        mode="search"
        defaultTitle="Search"
      />,
    );

    expect(screen.getByText("Loading notebooks...")).toBeInTheDocument();

    vi.mocked(useNotebooks).mockReturnValue({
      data: [],
      isLoading: false,
    } as unknown as ReturnType<typeof useNotebooks>);

    rerender(
      <SaveToResearchThreadDialog
        open
        onOpenChange={vi.fn()}
        mode="search"
        defaultTitle="Search"
      />,
    );

    expect(screen.getByText("No notebooks found.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save thread" })).toBeDisabled();
  });

  it("preselects seeded notebook ids when provided", async () => {
    mutateAsyncMock.mockResolvedValue(undefined);

    render(
      <SaveToResearchThreadDialog
        open
        onOpenChange={vi.fn()}
        mode="ask"
        defaultTitle="Ask Result"
        defaultNotebookIds={["nb-2"]}
        question="What changed?"
        answer="A lot changed."
        sourceIds={["source:1"]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Save thread" }));

    await waitFor(() => {
      expect(mutateAsyncMock).toHaveBeenCalledWith({
        notebookId: "nb-2",
        payload: {
          title: "Ask Result",
          seed_kind: "ask",
          question: "What changed?",
          answer: "A lot changed.",
          source_ids: ["source:1"],
          note_ids: [],
          search_results: [],
        },
      });
    });
  });

  it("falls back to the default title for search mode, clones results, supports deselect, and cancels", async () => {
    const onOpenChange = vi.fn();
    mutateAsyncMock.mockResolvedValue(undefined);

    render(
      <SaveToResearchThreadDialog
        open
        onOpenChange={onOpenChange}
        mode="search"
        defaultTitle="Saved Search"
        searchResults={[
          {
            title: "Result A",
            url: "https://example.com/a",
            snippet: "Snippet A",
          } as never,
        ]}
      />,
    );

    fireEvent.change(screen.getByLabelText("thread-title"), { target: { value: "   " } });
    fireEvent.click(screen.getByRole("button", { name: "Notebook A:off" }));
    fireEvent.click(screen.getByRole("button", { name: "Notebook A:on" }));
    fireEvent.click(screen.getByRole("button", { name: "Notebook B:off" }));
    fireEvent.click(screen.getByRole("button", { name: "Save thread" }));

    await waitFor(() => {
      expect(mutateAsyncMock).toHaveBeenCalledWith({
        notebookId: "nb-2",
        payload: {
          title: "Saved Search",
          seed_kind: "search",
          question: undefined,
          answer: undefined,
          source_ids: [],
          note_ids: [],
          search_results: [
            {
              title: "Result A",
              url: "https://example.com/a",
              snippet: "Snippet A",
            },
          ],
        },
      });
    });

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
