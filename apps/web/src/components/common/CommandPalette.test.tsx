import { act, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CommandPalette } from "./CommandPalette";

const hoisted = vi.hoisted(() => ({
  pushMock: vi.fn(),
  openSourceDialog: vi.fn(),
  openNotebookDialog: vi.fn(),
  openPodcastDialog: vi.fn(),
  setTheme: vi.fn(),
  notebooksData: [
    { id: "nb-1", name: "Alpha Notebook", description: "first notebook" },
    { id: "nb-2", name: "Research", description: "long term" },
  ],
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: hoisted.pushMock }),
}));

vi.mock("@/components/ui/command", () => ({
  CommandDialog: ({ open, children }: { open: boolean; children: ReactNode }) =>
    open ? <div data-testid="command-dialog">{children}</div> : null,
  CommandInput: ({
    value,
    onValueChange,
    placeholder,
    "aria-label": ariaLabel,
  }: {
    value?: string;
    onValueChange?: (value: string) => void;
    placeholder?: string;
    "aria-label"?: string;
  }) => (
    <input
      aria-label={ariaLabel}
      placeholder={placeholder}
      value={value ?? ""}
      onChange={(event) => onValueChange?.(event.target.value)}
    />
  ),
  CommandList: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CommandEmpty: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CommandGroup: ({ heading, children }: { heading?: string; children: ReactNode }) => (
    <section aria-label={heading}>{children}</section>
  ),
  CommandItem: ({
    children,
    onSelect,
    disabled,
  }: {
    children: ReactNode;
    onSelect?: () => void;
    disabled?: boolean;
  }) => (
    <button disabled={disabled} onClick={() => onSelect?.()} type="button">
      {children}
    </button>
  ),
  CommandSeparator: () => <hr />,
}));

vi.mock("@/components/providers/CreateDialogsProvider", () => ({
  useCreateDialogs: () => ({
    openSourceDialog: hoisted.openSourceDialog,
    openNotebookDialog: hoisted.openNotebookDialog,
    openPodcastDialog: hoisted.openPodcastDialog,
  }),
}));

vi.mock("@/lib/hooks/use-notebooks", () => ({
  useNotebooks: () => ({
    data: hoisted.notebooksData,
    isLoading: false,
  }),
}));

vi.mock("@/lib/stores/theme-store", () => ({
  useTheme: () => ({
    setTheme: hoisted.setTheme,
  }),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      common: {
        newSource: "New source",
        newNotebook: "New notebook",
        newPodcast: "New podcast",
        light: "Light",
        dark: "Dark",
        system: "System",
        quickActions: "Quick actions",
        quickActionsDesc: "Quick actions description",
        search: "Search",
        loading: "Loading",
      },
      navigation: {
        sources: "Sources",
        notebooks: "Notebooks",
        askAndSearch: "Ask and Search",
        podcasts: "Podcasts",
        models: "Models",
        transformations: "Transformations",
        settings: "Settings",
        advanced: "Advanced",
        nav: "Navigation",
        create: "Create",
        theme: "Theme",
      },
      notebooks: {
        title: "Notebook results",
      },
      searchPage: {
        enterSearchPlaceholder: "Search commands",
        matches: "{count} matches",
        noResultsFor: "No results for {query}",
        searchAndAsk: "Search and ask",
        searchResultsFor: "Search for {query}",
        askAbout: "Ask about {query}",
        orSearchKb: "Or search KB",
      },
    },
  }),
}));

describe("CommandPalette", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("opens with ctrl+k and routes search queries when there is no command match", async () => {
    render(<CommandPalette />);

    fireEvent.keyDown(document, { key: "k", ctrlKey: true });

    expect(screen.getByTestId("command-dialog")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search"), {
      target: { value: "deep topic" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Search for deep topic/ }));
    act(() => {
      vi.runAllTimers();
    });

    expect(hoisted.pushMock).toHaveBeenCalledWith("/search?q=deep%20topic&mode=search");
  });

  it("opens notebook create action and theme switch when command matches exist", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(document, { key: "k", metaKey: true });
    fireEvent.change(screen.getByLabelText("Search"), {
      target: { value: "notebook" },
    });

    fireEvent.click(screen.getByRole("button", { name: /New notebook/ }));
    act(() => {
      vi.runAllTimers();
    });
    expect(hoisted.openNotebookDialog).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(document, { key: "k", metaKey: true });
    fireEvent.change(screen.getByLabelText("Search"), {
      target: { value: "dark" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Dark" }));
    act(() => {
      vi.runAllTimers();
    });
    expect(hoisted.setTheme).toHaveBeenCalledWith("dark");
  });

  it("ignores shortcut toggles while focus is inside editable controls", () => {
    render(
      <div>
        <input aria-label="outside-input" />
        <CommandPalette />
      </div>,
    );

    const input = screen.getByLabelText("outside-input");
    input.focus();
    fireEvent.keyDown(input, { key: "k", ctrlKey: true });

    expect(screen.queryByTestId("command-dialog")).not.toBeInTheDocument();
  });
});
