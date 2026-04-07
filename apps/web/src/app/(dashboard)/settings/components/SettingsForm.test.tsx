import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSettings, useUpdateSettings } from "@/lib/hooks/use-settings";
import { SettingsForm } from "./SettingsForm";

vi.mock("@/lib/hooks/use-settings");

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">loading</div>,
}));

vi.mock("@/components/ui/select", async () => {
  const React = await import("react");

  const SelectItem = ({ value, children }: { value: string; children: ReactNode }) => (
    <option value={value}>{children}</option>
  );

  const collectItems = (nodes: ReactNode, items: React.ReactElement[]) => {
    React.Children.forEach(nodes, (child) => {
      if (!React.isValidElement(child)) {
        return;
      }
      if (child.type === SelectItem) {
        items.push(child);
        return;
      }
      if (child.props?.children) {
        collectItems(child.props.children, items);
      }
    });
  };

  return {
    Select: ({
      value,
      onValueChange,
      disabled,
      name,
      children,
    }: {
      value?: string;
      onValueChange?: (value: string) => void;
      disabled?: boolean;
      name?: string;
      children: ReactNode;
    }) => {
      const items: React.ReactElement[] = [];
      collectItems(children, items);
      return (
        <select
          data-testid={`select-${name ?? "field"}`}
          value={value ?? ""}
          disabled={disabled}
          onChange={(event) => onValueChange?.(event.target.value)}
        >
          <option value="" />
          {items}
        </select>
      );
    },
    SelectTrigger: ({ children }: { children: ReactNode }) => <>{children}</>,
    SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>,
    SelectContent: ({ children }: { children: ReactNode }) => <>{children}</>,
    SelectItem,
  };
});

const translation = {
  common: {
    save: "Save",
    saving: "Saving",
    saveSuccess: "Saved successfully",
    error: "Error",
    yes: "Yes",
    no: "No",
  },
  settings: {
    loadFailed: "Failed to load settings",
    contentProcessing: "Content processing",
    contentProcessingDesc: "Content processing description",
    docEngine: "Document Engine",
    docEnginePlaceholder: "Select doc engine",
    autoRecommended: "Auto",
    docling: "Docling",
    simple: "Simple",
    helpMeChoose: "Help me choose",
    docHelp: "Doc help",
    urlEngine: "URL Engine",
    urlEnginePlaceholder: "Select url engine",
    firecrawl: "Firecrawl",
    jina: "Jina",
    urlHelp: "URL help",
    embeddingAndSearch: "Embedding and search",
    embeddingAndSearchDesc: "Embedding and search description",
    defaultEmbeddingOption: "Embedding option",
    embeddingOptionPlaceholder: "Select embedding option",
    ask: "Ask",
    always: "Always",
    never: "Never",
    embeddingHelp: "Embedding help",
    fileManagement: "File management",
    fileManagementDesc: "File management description",
    autoDeleteFiles: "Auto delete files",
    autoDeletePlaceholder: "Select auto delete option",
    filesHelp: "Files help",
  },
};

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t: translation }),
}));

const settingsFixture = {
  default_content_processing_engine_doc: "auto",
  default_content_processing_engine_url: "firecrawl",
  default_embedding_option: "ask",
  auto_delete_files: "no",
};

describe("SettingsForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state", () => {
    vi.mocked(useSettings).mockReturnValue({
      isLoading: true,
      data: undefined,
      error: null,
    } as unknown as ReturnType<typeof useSettings>);

    vi.mocked(useUpdateSettings).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateSettings>);

    render(<SettingsForm />);

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("renders error state with error message", () => {
    vi.mocked(useSettings).mockReturnValue({
      isLoading: false,
      data: undefined,
      error: new Error("network down"),
    } as unknown as ReturnType<typeof useSettings>);

    vi.mocked(useUpdateSettings).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateSettings>);

    render(<SettingsForm />);

    expect(screen.getByText("Failed to load settings")).toBeInTheDocument();
    expect(screen.getByText("network down")).toBeInTheDocument();
  });

  it("updates values and saves settings", async () => {
    const mutateAsync = vi.fn().mockResolvedValue({});

    vi.mocked(useSettings).mockReturnValue({
      isLoading: false,
      data: settingsFixture,
      error: null,
    } as unknown as ReturnType<typeof useSettings>);

    vi.mocked(useUpdateSettings).mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateSettings>);

    render(<SettingsForm />);

    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[0], { target: { value: "docling" } });
    fireEvent.change(selects[2], { target: { value: "always" } });

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          default_content_processing_engine_doc: "docling",
          default_embedding_option: "always",
        }),
      );
    });

    expect(await screen.findByText("Saved successfully")).toBeInTheDocument();
  });

  it("disables save button while update is pending", () => {
    vi.mocked(useSettings).mockReturnValue({
      isLoading: false,
      data: settingsFixture,
      error: null,
    } as unknown as ReturnType<typeof useSettings>);

    vi.mocked(useUpdateSettings).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: true,
    } as unknown as ReturnType<typeof useUpdateSettings>);

    render(<SettingsForm />);

    const saveButton = screen.getByRole("button", { name: /Saving/ });
    expect(saveButton).toBeDisabled();
  });

  it("shows error message when save fails", async () => {
    const mutateAsync = vi.fn().mockRejectedValue(new Error("save failed"));

    vi.mocked(useSettings).mockReturnValue({
      isLoading: false,
      data: settingsFixture,
      error: null,
    } as unknown as ReturnType<typeof useSettings>);

    vi.mocked(useUpdateSettings).mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateSettings>);

    render(<SettingsForm />);

    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[1], { target: { value: "jina" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Error")).toBeInTheDocument();
  });

  it("expands help accordions and updates file management values", () => {
    vi.mocked(useSettings).mockReturnValue({
      isLoading: false,
      data: settingsFixture,
      error: null,
    } as unknown as ReturnType<typeof useSettings>);

    vi.mocked(useUpdateSettings).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateSettings>);

    render(<SettingsForm />);

    fireEvent.click(screen.getAllByText("Help me choose")[0]);
    fireEvent.click(screen.getAllByText("Help me choose")[3]);

    expect(screen.getByText("Doc help")).toBeInTheDocument();
    expect(screen.getByText("Files help")).toBeInTheDocument();

    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[3], { target: { value: "yes" } });
    expect(selects[3]).toHaveValue("yes");
  });
});
