import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SearchPage from "./page";

const hoisted = vi.hoisted(() => ({
  searchParamsGet: vi.fn(),
  searchMutate: vi.fn(),
  openModal: vi.fn(),
  askSendAsk: vi.fn(),
  askCancel: vi.fn(),
  researchCaptureSpy: vi.fn(),
  searchPending: false,
  modelsLoading: false,
  modelDefaults: {
    default_chat_model: "chat-1",
    default_embedding_model: "embed-1",
  },
  availableModels: [
    { id: "chat-1", name: "Gemini Pro" },
    { id: "embed-1", name: "Embedding 001" },
  ],
  searchMutationData: undefined as
    | {
        total_count: number;
        search_type: string;
        results: Array<{
          id: string;
          title: string;
          parent_id: string | null;
          final_score: number;
          matches?: string[];
        }>;
      }
    | undefined,
  askState: {
    isStreaming: false,
    strategy: null as unknown,
    answers: [] as unknown[],
    finalAnswer: null as string | null,
  },
}));

vi.mock("next/navigation", () => ({
  useSearchParams: () => ({
    get: hoisted.searchParamsGet,
  }),
}));

vi.mock("@/components/layout/AppShell", () => ({
  AppShell: ({ children }: { children: ReactNode }) => (
    <div data-testid="app-shell">{children}</div>
  ),
}));

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: ({ className }: { className?: string }) => (
    <span data-testid="loading-spinner" className={className}>
      loading
    </span>
  ),
}));

vi.mock("@/components/search/AdvancedModelsDialog", () => ({
  AdvancedModelsDialog: ({
    open,
    defaultModels,
    onSave,
  }: {
    open: boolean;
    defaultModels: { strategy: string; answer: string; finalAnswer: string };
    onSave: (models: { strategy: string; answer: string; finalAnswer: string }) => void;
  }) =>
    open ? (
      <div>
        <div data-testid="advanced-default-models">{JSON.stringify(defaultModels)}</div>
        <button
          onClick={() =>
            onSave({
              strategy: "chat-strategy-custom",
              answer: "chat-answer-custom",
              finalAnswer: "chat-final-custom",
            })
          }
          type="button"
        >
          apply-custom-models
        </button>
      </div>
    ) : null,
}));

vi.mock("@/components/search/ResearchCapturePanel", () => ({
  ResearchCapturePanel: (props: Record<string, unknown>) => {
    hoisted.researchCaptureSpy(props);
    return (
      <div data-testid={`research-capture-${String(props.mode)}`}>
        {props.hasCompletedResult ? "completed" : "pending"}
      </div>
    );
  },
}));

vi.mock("@/components/search/SaveToResearchThreadDialog", () => ({
  SaveToResearchThreadDialog: ({ open, answer }: { open: boolean; answer?: string }) =>
    open ? <div data-testid="save-dialog">{answer}</div> : null,
}));

vi.mock("@/components/search/StreamingResponse", () => ({
  StreamingResponse: () => <div data-testid="streaming-response">streaming</div>,
}));

vi.mock("@/components/ui/select", () => ({
  Select: ({
    value,
    onValueChange,
    children,
  }: {
    value?: string;
    onValueChange?: (value: string) => void;
    children: ReactNode;
  }) => (
    <div data-select-value={value}>
      <button onClick={() => onValueChange?.("nb-1")} type="button">
        select-notebook
      </button>
      {children}
    </div>
  ),
  SelectTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>,
  SelectContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/tabs", async () => {
  const React = await import("react");
  const TabsContext = React.createContext<{
    value: string;
    onValueChange?: (value: string) => void;
  }>({
    value: "ask",
  });

  return {
    Tabs: ({
      children,
      value,
      onValueChange,
    }: {
      children: ReactNode;
      value: string;
      onValueChange?: (value: string) => void;
    }) => (
      <TabsContext.Provider value={{ value, onValueChange }}>
        <div>{children}</div>
      </TabsContext.Provider>
    ),
    TabsList: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    TabsTrigger: ({ value, children }: { value: "ask" | "search"; children: ReactNode }) => {
      const ctx = React.useContext(TabsContext);
      return (
        <button
          data-testid={`tab-trigger-${value}`}
          data-state={ctx.value === value ? "active" : "inactive"}
          onClick={() => ctx.onValueChange?.(value)}
          type="button"
        >
          {children}
        </button>
      );
    },
    TabsContent: ({ value, children }: { value: "ask" | "search"; children: ReactNode }) => {
      const ctx = React.useContext(TabsContext);
      return ctx.value === value ? <div>{children}</div> : null;
    },
  };
});

vi.mock("@/components/ui/radio-group", async () => {
  const React = await import("react");
  const Context = React.createContext<{
    value?: string;
    disabled?: boolean;
    onValueChange?: (value: string) => void;
  }>({});

  return {
    RadioGroup: ({
      value,
      disabled,
      onValueChange,
      children,
    }: {
      value?: string;
      disabled?: boolean;
      onValueChange?: (value: string) => void;
      children: ReactNode;
    }) => (
      <Context.Provider value={{ value, disabled, onValueChange }}>
        <div>{children}</div>
      </Context.Provider>
    ),
    RadioGroupItem: ({
      value,
      id,
      disabled,
    }: {
      value: string;
      id?: string;
      disabled?: boolean;
    }) => {
      const ctx = React.useContext(Context);
      const checked = ctx.value === value;
      return (
        <input
          type="radio"
          id={id}
          value={value}
          checked={checked}
          disabled={Boolean(disabled || ctx.disabled)}
          onChange={() => ctx.onValueChange?.(value)}
        />
      );
    },
  };
});

vi.mock("@/components/ui/checkbox", () => ({
  Checkbox: ({
    id,
    checked,
    onCheckedChange,
    disabled,
  }: {
    id?: string;
    checked?: boolean;
    disabled?: boolean;
    onCheckedChange?: (checked: boolean) => void;
  }) => (
    <input
      type="checkbox"
      id={id}
      checked={Boolean(checked)}
      disabled={disabled}
      onChange={(event) => onCheckedChange?.(event.target.checked)}
    />
  ),
}));

vi.mock("@/components/ui/collapsible", () => ({
  Collapsible: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CollapsibleTrigger: ({ children }: { children: ReactNode }) => (
    <button type="button">{children}</button>
  ),
  CollapsibleContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/lib/hooks/use-search", () => ({
  useSearch: () => ({
    mutate: hoisted.searchMutate,
    isPending: hoisted.searchPending,
    data: hoisted.searchMutationData,
  }),
}));

vi.mock("@/lib/hooks/use-ask", () => ({
  useAsk: () => ({
    sendAsk: hoisted.askSendAsk,
    cancel: hoisted.askCancel,
    isStreaming: hoisted.askState.isStreaming,
    strategy: hoisted.askState.strategy,
    answers: hoisted.askState.answers,
    finalAnswer: hoisted.askState.finalAnswer,
  }),
}));

vi.mock("@/lib/hooks/use-models", () => ({
  useModelDefaults: () => ({ data: hoisted.modelDefaults, isLoading: hoisted.modelsLoading }),
  useModels: () => ({ data: hoisted.availableModels }),
}));

vi.mock("@/lib/hooks/use-modal-manager", () => ({
  useModalManager: () => ({ openModal: hoisted.openModal }),
}));

const translation = {
  common: {
    cancel: "Cancel",
    remove: "Remove",
    accessibility: {
      searchKB: "Search knowledge base",
      enterQuestion: "Enter question",
      enterSearch: "Search input",
      searchKBBtn: "Search button",
    },
  },
  searchPage: {
    notSet: "Not set",
    resultsFound: "{count} results",
    askAndSearch: "Ask and Search",
    chooseAMode: "Choose mode",
    askBeta: "Ask",
    search: "Search",
    askYourKb: "Ask your KB",
    askYourKbDesc: "Ask description",
    question: "Question",
    enterQuestionPlaceholder: "Enter question",
    pressToSubmit: "Press cmd+enter",
    noEmbeddingModel: "No embedding model configured",
    usingCustomModels: "Using custom models",
    usingDefaultModels: "Using default models",
    advanced: "Advanced",
    strategy: "Strategy",
    answer: "Answer",
    final: "Final",
    processing: "Processing",
    ask: "Ask",
    saveToNotebooks: "Save to notebooks",
    searchDesc: "Search description",
    enterSearchPlaceholder: "Type search",
    pressToSearch: "Press Enter to search",
    searchType: "Search type",
    vectorSearchWarning: "Vector search unavailable",
    textSearch: "Text",
    vectorSearch: "Vector",
    searchIn: "Search in",
    searchSources: "Sources",
    searchNotes: "Notes",
    noResultsFor: "No results for {query}",
    matches: "Matches {count}",
    capturedAskThreadFallback: "Captured ask thread",
    capturedSearchThreadFallback: "Captured search thread",
    saveToResearchThreadTitle: "Save to research thread",
  },
};

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t: translation }),
}));

function setUrlParams(params: Record<string, string | null>) {
  hoisted.searchParamsGet.mockImplementation((key: string) => params[key] ?? null);
}

describe("SearchPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    hoisted.researchCaptureSpy.mockClear();
    hoisted.searchPending = false;
    hoisted.modelsLoading = false;
    hoisted.searchMutationData = undefined;
    hoisted.askState = {
      isStreaming: false,
      strategy: null,
      answers: [],
      finalAnswer: null,
    };
    hoisted.modelDefaults = {
      default_chat_model: "chat-1",
      default_embedding_model: "embed-1",
    };
    hoisted.availableModels = [
      { id: "chat-1", name: "Gemini Pro" },
      { id: "embed-1", name: "Embedding 001" },
    ];
    setUrlParams({ q: "", mode: "search" });
  });

  it("auto-triggers search from URL params in search mode", () => {
    setUrlParams({ q: "hello world", mode: "search" });

    render(<SearchPage />);

    expect(hoisted.searchMutate).toHaveBeenCalledWith({
      query: "hello world",
      type: "text",
      limit: 100,
      search_sources: true,
      search_notes: true,
      minimum_score: 0.2,
    });
  });

  it("submits manual search from button", () => {
    render(<SearchPage />);

    const input = screen.getByRole("textbox", { name: "Search input" });
    fireEvent.change(input, { target: { value: "  fetch docs  " } });
    fireEvent.click(screen.getByLabelText("Search button"));

    expect(hoisted.searchMutate).toHaveBeenCalledWith({
      query: "  fetch docs  ",
      type: "text",
      limit: 100,
      search_sources: true,
      search_notes: true,
      minimum_score: 0.2,
    });
  });

  it("does not submit on enter while composing", () => {
    render(<SearchPage />);

    const input = screen.getByRole("textbox", { name: "Search input" });
    fireEvent.change(input, { target: { value: "composing query" } });

    fireEvent.compositionStart(input);
    fireEvent.keyDown(input, { key: "Enter" });
    expect(hoisted.searchMutate).not.toHaveBeenCalled();

    fireEvent.compositionEnd(input);
    fireEvent.keyDown(input, { key: "Enter" });
    expect(hoisted.searchMutate).toHaveBeenCalledTimes(1);
  });

  it("shows vector warning and disables vector option without embedding model", () => {
    hoisted.modelDefaults = {
      default_chat_model: "chat-1",
      default_embedding_model: null,
    };

    render(<SearchPage />);

    expect(screen.getByText("Vector search unavailable")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Vector" })).toBeDisabled();
  });

  it("maps source_insight to insight modal and ignores null parent results", () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);

    hoisted.searchMutationData = {
      total_count: 2,
      search_type: "text",
      results: [
        {
          id: "r-1",
          title: "Insight result",
          parent_id: "source_insight:ins-1",
          final_score: 0.88,
          matches: ["matched snippet"],
        },
        {
          id: "r-2",
          title: "Broken result",
          parent_id: null,
          final_score: 0.55,
          matches: ["should be skipped"],
        },
      ],
    };

    render(<SearchPage />);

    fireEvent.click(screen.getByRole("button", { name: "Insight result" }));

    expect(hoisted.openModal).toHaveBeenCalledWith("insight", "ins-1");
    expect(screen.queryByRole("button", { name: "Broken result" })).not.toBeInTheDocument();
    expect(warnSpy).toHaveBeenCalled();

    warnSpy.mockRestore();
  });

  it("submits ask mode with custom models and opens save dialog for final answer", () => {
    setUrlParams({ q: "Explain this notebook", mode: "ask" });
    hoisted.askState.finalAnswer = "Saved final answer";

    render(<SearchPage />);

    fireEvent.click(screen.getByRole("button", { name: "Advanced" }));
    fireEvent.click(screen.getByRole("button", { name: "apply-custom-models" }));
    fireEvent.click(screen.getAllByRole("button", { name: "Ask" }).at(-1)!);

    expect(hoisted.askSendAsk).toHaveBeenCalledWith("Explain this notebook", {
      strategy: "chat-strategy-custom",
      answer: "chat-answer-custom",
      finalAnswer: "chat-final-custom",
    });

    fireEvent.click(screen.getByRole("button", { name: "Save to research thread" }));
    expect(screen.getByTestId("save-dialog")).toHaveTextContent("Saved final answer");
  });

  it("passes completed ask context into the research capture panel", async () => {
    setUrlParams({ q: "Explain this notebook", mode: "ask" });
    hoisted.askState.finalAnswer = "Saved final answer";

    render(<SearchPage />);

    await waitFor(() => {
      expect(screen.getByTestId("research-capture-ask")).toHaveTextContent("completed");
    });

    expect(hoisted.researchCaptureSpy).toHaveBeenCalled();
  });

  it("keeps research capture out of the first screen until ask has a completed result", () => {
    setUrlParams({ q: "Explain this notebook", mode: "ask" });

    render(<SearchPage />);

    expect(screen.queryByTestId("research-capture-ask")).not.toBeInTheDocument();
    expect(hoisted.researchCaptureSpy).not.toHaveBeenCalled();
  });

  it("shows cancel button during streaming and forwards cancel action", () => {
    setUrlParams({ q: "Streaming prompt", mode: "ask" });
    hoisted.askState.isStreaming = true;

    render(<SearchPage />);

    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Processing/ })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(hoisted.askCancel).toHaveBeenCalledTimes(1);
  });

  it("submits ask when ctrl+enter is pressed in ask textarea", () => {
    setUrlParams({ q: "", mode: "ask" });

    render(<SearchPage />);

    const textarea = screen.getByRole("textbox", { name: "Enter question" });
    fireEvent.change(textarea, { target: { value: "Question from shortcut" } });
    fireEvent.keyDown(textarea, { key: "Enter", ctrlKey: true });

    expect(hoisted.askSendAsk).toHaveBeenCalledWith("Question from shortcut", {
      strategy: "chat-1",
      answer: "chat-1",
      finalAnswer: "chat-1",
    });
  });

  it("switches to vector search and respects source/note scope toggles", () => {
    render(<SearchPage />);

    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    const input = screen.getByRole("textbox", { name: "Search input" });
    fireEvent.change(input, { target: { value: "vector search" } });
    fireEvent.click(screen.getByRole("radio", { name: "Vector" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Notes" }));
    fireEvent.click(screen.getByLabelText("Search button"));

    expect(hoisted.searchMutate).toHaveBeenLastCalledWith({
      query: "vector search",
      type: "vector",
      limit: 100,
      search_sources: true,
      search_notes: false,
      minimum_score: 0.2,
    });
  });

  it("submits search with sources disabled", () => {
    render(<SearchPage />);

    const input = screen.getByRole("textbox", { name: "Search input" });
    fireEvent.change(input, { target: { value: "notes only" } });
    fireEvent.click(screen.getByRole("checkbox", { name: "Sources" }));
    fireEvent.click(screen.getByLabelText("Search button"));

    expect(hoisted.searchMutate).toHaveBeenLastCalledWith({
      query: "notes only",
      type: "text",
      limit: 100,
      search_sources: false,
      search_notes: true,
      minimum_score: 0.2,
    });
  });

  it("renders empty search results state with result count badge", () => {
    setUrlParams({ q: "nothing", mode: "search" });
    hoisted.searchMutationData = {
      total_count: 0,
      search_type: "vector",
      results: [],
    };

    render(<SearchPage />);

    expect(screen.getByText("0 results")).toBeInTheDocument();
    expect(screen.getAllByText("Vector")).toHaveLength(2);
    expect(screen.getByText("No results for nothing")).toBeInTheDocument();
  });

  it("syncs updated URL params into search state after initial render", async () => {
    const { rerender } = render(<SearchPage />);

    setUrlParams({ q: "rerendered query", mode: "search" });
    rerender(<SearchPage />);

    await waitFor(() => {
      expect(screen.getByRole("textbox", { name: "Search input" })).toHaveValue("rerendered query");
    });
  });

  it("ignores URL mode changes with an empty query and keeps current input state", async () => {
    const { rerender } = render(<SearchPage />);

    fireEvent.change(screen.getByRole("textbox", { name: "Search input" }), {
      target: { value: "keep this query" },
    });

    setUrlParams({ q: "", mode: "ask" });
    rerender(<SearchPage />);

    await waitFor(() => {
      expect(screen.getByRole("textbox", { name: "Search input" })).toHaveValue("keep this query");
      expect(screen.getByTestId("tab-trigger-search")).toHaveAttribute("data-state", "active");
    });
    expect(hoisted.askSendAsk).not.toHaveBeenCalled();
  });

  it("auto-triggers ask from URL params when ask mode and default model exist", () => {
    setUrlParams({ q: "Need answer", mode: "ask" });

    render(<SearchPage />);

    expect(hoisted.askSendAsk).toHaveBeenCalledWith("Need answer", {
      strategy: "chat-1",
      answer: "chat-1",
      finalAnswer: "chat-1",
    });
  });

  it("prefills ask mode without auto-triggering when autostart is disabled", () => {
    setUrlParams({
      q: "Investigate this insight",
      mode: "ask",
      autostart: "0",
      source: "source:1",
      notebook: "notebook:9",
    });

    render(<SearchPage />);

    expect(hoisted.askSendAsk).not.toHaveBeenCalled();
    expect(screen.getByRole("textbox", { name: "Enter question" })).toHaveValue(
      "Investigate this insight",
    );
    expect(screen.getByTestId("tab-trigger-ask")).toHaveAttribute("data-state", "active");
    expect(hoisted.researchCaptureSpy).toHaveBeenLastCalledWith(
      expect.objectContaining({
        defaultNotebookId: "notebook:9",
        sourceIds: ["source:1"],
      }),
    );
  });

  it("does not auto-trigger ask while defaults are still loading", () => {
    setUrlParams({ q: "Wait for models", mode: "ask" });
    hoisted.modelsLoading = true;

    render(<SearchPage />);

    expect(hoisted.askSendAsk).not.toHaveBeenCalled();
  });

  it("does not submit ask when default chat model is unavailable and shows fallback model labels", () => {
    setUrlParams({ q: "Missing model", mode: "ask" });
    hoisted.modelDefaults = {
      default_chat_model: null,
      default_embedding_model: "embed-1",
    };
    hoisted.availableModels = undefined;

    render(<SearchPage />);

    fireEvent.click(screen.getByRole("button", { name: "Advanced" }));
    expect(screen.getByTestId("advanced-default-models")).toHaveTextContent(
      JSON.stringify({ strategy: "", answer: "", finalAnswer: "" }),
    );

    fireEvent.click(screen.getAllByRole("button", { name: "Ask" }).at(-1)!);
    expect(hoisted.askSendAsk).not.toHaveBeenCalled();
  });

  it("ignores non-enter key presses on the search input", () => {
    render(<SearchPage />);

    const input = screen.getByRole("textbox", { name: "Search input" });
    fireEvent.change(input, { target: { value: "typed value" } });
    fireEvent.keyDown(input, { key: "Escape" });

    expect(hoisted.searchMutate).not.toHaveBeenCalled();
  });

  it("keeps ask shortcut inactive when Enter is pressed without Ctrl/Cmd modifier", () => {
    setUrlParams({ q: "", mode: "ask" });
    render(<SearchPage />);

    const textarea = screen.getByRole("textbox", { name: "Enter question" });
    fireEvent.change(textarea, { target: { value: "No shortcut submit" } });
    fireEvent.keyDown(textarea, { key: "Enter" });

    expect(hoisted.askSendAsk).not.toHaveBeenCalled();
  });

  it("updates active tab and ask question when URL params switch to ask mode", async () => {
    const { rerender } = render(<SearchPage />);

    setUrlParams({ q: "ask from url", mode: "ask" });
    rerender(<SearchPage />);

    await waitFor(() => {
      expect(screen.getByRole("textbox", { name: "Enter question" })).toHaveValue("ask from url");
      expect(screen.getByTestId("tab-trigger-ask")).toHaveAttribute("data-state", "active");
    });
  });

  it("renders pending state for search submit button", () => {
    hoisted.searchPending = true;
    render(<SearchPage />);

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
    expect(screen.getByLabelText("Search button")).toHaveAttribute("aria-busy", "true");
  });

  it("opens source modal for non-insight search result and skips score badge for zero score", () => {
    hoisted.searchMutationData = {
      total_count: 1,
      search_type: "text",
      results: [
        {
          id: "source-result",
          title: "Source result",
          parent_id: "source:source-99",
          final_score: 0,
          matches: [],
        },
      ],
    };

    render(<SearchPage />);
    fireEvent.click(screen.getByRole("button", { name: "Source result" }));

    expect(hoisted.openModal).toHaveBeenCalledWith("source", "source-99");
    expect(screen.queryByText("0.00")).not.toBeInTheDocument();
  });

  it("switches tabs through trigger clicks", () => {
    render(<SearchPage />);

    expect(screen.getByTestId("tab-trigger-search")).toHaveAttribute("data-state", "active");
    fireEvent.click(screen.getByTestId("tab-trigger-ask"));
    expect(screen.getByTestId("tab-trigger-ask")).toHaveAttribute("data-state", "active");
  });
});
