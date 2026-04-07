import { fireEvent, render, screen } from "@testing-library/react";
import { useForm } from "react-hook-form";
import { describe, expect, it, vi } from "vitest";
import { ProcessingStep } from "./ProcessingStep";

const t = {
  navigation: {
    transformations: "Transformations",
    settings: "Settings",
  },
  common: {
    optional: "optional",
    noMatches: "No matches",
  },
  sources: {
    processDescription: "Choose post-processing options",
    longContextPathTitle: "Long-context to knowledge path",
    longContextPathDescription: "Use the built-in path for long messy context",
    longContextPathHelper: "Turns long context into structured knowledge assets",
    longContextPathSelected: "Recommended path selected",
    longContextPathAdd: "Add recommended transformation",
    longContextPathRemove: "Remove recommended transformation",
    longContextPathExampleChats: "Agent transcripts and exported chat logs",
    longContextPathExampleWeb: "Long webpages and forum discussions",
    longContextPathExampleNotes: "Messy notes, interviews, and meeting dumps",
    longContextBuiltOnTransformation:
      'This path is powered by the built-in "{title}" transformation.',
    enableEmbedding: "Enable embedding",
    embeddingDesc: "Create vector embeddings",
    embeddingAlways: "Embedding always on",
    embeddingAlwaysDesc: "Embedding is always enabled.",
    embeddingNever: "Embedding disabled",
    embeddingNeverDesc: "Embedding is turned off.",
    changeInSettings: "Change this in",
  },
};

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t }),
}));

vi.mock("@/components/ui/checkbox-list", () => ({
  CheckboxList: ({
    items,
    selectedIds,
    onToggle,
    loading,
    emptyMessage,
  }: {
    items: Array<{ id: string; title: string; description: string }>;
    selectedIds: string[];
    onToggle: (id: string) => void;
    loading?: boolean;
    emptyMessage: string;
  }) => (
    <div>
      <div data-testid="checkbox-list-loading">{String(Boolean(loading))}</div>
      <div>{emptyMessage}</div>
      {items.map((item) => (
        <button key={item.id} onClick={() => onToggle(item.id)} type="button">
          {item.title}:{selectedIds.includes(item.id) ? "on" : "off"}
        </button>
      ))}
    </div>
  ),
}));

vi.mock("@/components/ui/checkbox", () => ({
  Checkbox: ({
    id,
    checked,
    onCheckedChange,
  }: {
    id: string;
    checked: boolean;
    onCheckedChange: (checked: boolean) => void;
  }) => (
    <input
      id={id}
      aria-label={id}
      checked={checked}
      onChange={(event) => onCheckedChange(event.target.checked)}
      type="checkbox"
    />
  ),
}));

function renderStep(defaultEmbed = true, embeddingOption: "ask" | "always" | "never" = "ask") {
  function TestHarness() {
    const { control } = useForm({
      defaultValues: {
        type: "link",
        embed: defaultEmbed,
        async_processing: true,
      },
    });

    return (
      <ProcessingStep
        control={control}
        transformations={[
          { id: "tr-1", title: "Summary", description: "Summarize", apply_default: false },
          { id: "tr-2", title: "Keywords", description: "Extract keywords", apply_default: false },
        ]}
        selectedTransformations={["tr-1"]}
        onToggleTransformation={vi.fn()}
        settings={{ default_embedding_option: embeddingOption }}
      />
    );
  }

  return render(<TestHarness />);
}

describe("ProcessingStep", () => {
  it("renders transformation options and toggles embedding when setting is ask", () => {
    renderStep(true, "ask");

    expect(screen.getByText("Transformations (optional)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Summary:on" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Keywords:off" })).toBeInTheDocument();

    const embedCheckbox = screen.getByRole("checkbox", { name: "enable-embedding" });
    expect(embedCheckbox).toBeChecked();

    fireEvent.click(embedCheckbox);
    expect(embedCheckbox).not.toBeChecked();
  });

  it("shows always-on embedding notice", () => {
    renderStep(true, "always");

    expect(screen.getByText("Embedding always on")).toBeInTheDocument();
    expect(screen.getByText(/Embedding is always enabled/)).toBeInTheDocument();
    expect(screen.queryByRole("checkbox", { name: "enable-embedding" })).not.toBeInTheDocument();
  });

  it("shows never embedding notice", () => {
    renderStep(false, "never");

    expect(screen.getByText("Embedding disabled")).toBeInTheDocument();
    expect(screen.getByText(/Embedding is turned off/)).toBeInTheDocument();
    expect(screen.queryByRole("checkbox", { name: "enable-embedding" })).not.toBeInTheDocument();
  });

  it("invokes transformation toggle callback", () => {
    const onToggleTransformation = vi.fn();

    function TestHarness() {
      const { control } = useForm({
        defaultValues: {
          type: "link",
          embed: true,
          async_processing: true,
        },
      });

      return (
        <ProcessingStep
          control={control}
          transformations={[
            { id: "tr-1", title: "Summary", description: "Summarize", apply_default: false },
          ]}
          selectedTransformations={[]}
          onToggleTransformation={onToggleTransformation}
          loading
          settings={{ default_embedding_option: "ask" }}
        />
      );
    }

    render(<TestHarness />);

    expect(screen.getByTestId("checkbox-list-loading")).toHaveTextContent("true");
    fireEvent.click(screen.getByRole("button", { name: "Summary:off" }));
    expect(onToggleTransformation).toHaveBeenCalledWith("tr-1");
  });

  it("surfaces the built-in long-context recommendation when knowledgeization is available", () => {
    const onToggleTransformation = vi.fn();

    function TestHarness() {
      const { control } = useForm({
        defaultValues: {
          type: "text",
          embed: true,
          async_processing: true,
        },
      });

      return (
        <ProcessingStep
          control={control}
          transformations={[
            {
              id: "transformation:chat_knowledgeization",
              title: "Chat Knowledgeization",
              description: "Turn long context into structured knowledge assets",
              apply_default: false,
            },
            { id: "tr-1", title: "Summary", description: "Summarize", apply_default: false },
          ]}
          selectedTransformations={[]}
          onToggleTransformation={onToggleTransformation}
          settings={{ default_embedding_option: "ask" }}
        />
      );
    }

    render(<TestHarness />);

    expect(screen.getByTestId("long-context-recommendation")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Add recommended transformation" }));
    expect(onToggleTransformation).toHaveBeenCalledWith("transformation:chat_knowledgeization");
  });
});
