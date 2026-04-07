import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAutoAssignDefaults, useUpdateModelDefaults } from "@/lib/hooks/use-models";
import type { Model, ModelDefaults } from "@/lib/types/models";
import { DefaultModelSelectors } from "./default-model-selectors";

vi.mock("@/lib/hooks/use-models");

vi.mock("@/components/ui/select", async () => {
  const React = await import("react");

  const textFromNode = (node: ReactNode): string => {
    if (typeof node === "string" || typeof node === "number") {
      return String(node);
    }
    if (Array.isArray(node)) {
      return node
        .map((item) => textFromNode(item))
        .join(" ")
        .replace(/\s+/g, " ")
        .trim();
    }
    if (React.isValidElement(node)) {
      return textFromNode(node.props?.children);
    }
    return "";
  };

  const SelectItem = ({ value, children }: { value: string; children: ReactNode }) => (
    <option value={value}>{textFromNode(children)}</option>
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
      children,
    }: {
      value?: string;
      onValueChange?: (value: string) => void;
      children: ReactNode;
    }) => {
      const items: React.ReactElement[] = [];
      collectItems(children, items);
      return (
        <select value={value ?? ""} onChange={(event) => onValueChange?.(event.target.value)}>
          <option value="" />
          {items}
        </select>
      );
    },
    SelectTrigger: ({ id, children }: { id?: string; children: ReactNode }) => (
      <span id={id}>{children}</span>
    ),
    SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>,
    SelectContent: ({ children }: { children: ReactNode }) => <>{children}</>,
    SelectItem,
  };
});

vi.mock("@/components/settings/EmbeddingModelChangeDialog", () => ({
  EmbeddingModelChangeDialog: ({
    open,
    onOpenChange,
    onConfirm,
    oldModelName,
    newModelName,
  }: {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onConfirm: () => void;
    oldModelName?: string;
    newModelName?: string;
  }) =>
    open ? (
      <div data-testid="embedding-change-dialog">
        <span>{oldModelName}</span>
        <span>{newModelName}</span>
        <button type="button" onClick={onConfirm}>
          Confirm embedding change
        </button>
        <button type="button" onClick={() => onOpenChange(false)}>
          Cancel embedding change
        </button>
      </div>
    ) : null,
}));

const translation = {
  common: {
    remove: "Remove",
  },
  navigation: {
    advanced: "Advanced",
  },
  models: {
    defaultAssignments: "Default assignments",
    defaultAssignmentsDesc: "Default assignments description",
    missingRequiredModels: "Missing: {models}",
    autoAssigning: "Auto assigning",
    autoAssign: "Auto assign",
    chatModelLabel: "Chat model",
    chatModelDesc: "Chat description",
    embeddingModelLabel: "Embedding model",
    embeddingModelDesc: "Embedding description",
    ttsModelLabel: "TTS model",
    ttsModelDesc: "TTS description",
    sttModelLabel: "STT model",
    sttModelDesc: "STT description",
    transformationModelLabel: "Transformation model",
    transformationModelDesc: "Transformation description",
    toolsModelLabel: "Tools model",
    toolsModelDesc: "Tools description",
    largeContextModelLabel: "Large context model",
    largeContextModelDesc: "Large context description",
    requiredModelPlaceholder: "Required",
    selectModelPlaceholder: "Select model",
  },
};

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t: translation }),
}));

const modelsFixture: Model[] = [
  {
    id: "lang-zeta",
    name: "Zeta",
    provider: "google",
    type: "language",
    created: "2026-01-01",
    updated: "2026-01-01",
  },
  {
    id: "lang-alpha",
    name: "Alpha",
    provider: "google",
    type: "language",
    created: "2026-01-01",
    updated: "2026-01-01",
  },
  {
    id: "embed-1",
    name: "Embed One",
    provider: "google",
    type: "embedding",
    created: "2026-01-01",
    updated: "2026-01-01",
  },
  {
    id: "embed-2",
    name: "Embed Two",
    provider: "google",
    type: "embedding",
    created: "2026-01-01",
    updated: "2026-01-01",
  },
  {
    id: "tts-1",
    name: "TTS",
    provider: "google",
    type: "text_to_speech",
    created: "2026-01-01",
    updated: "2026-01-01",
  },
  {
    id: "stt-1",
    name: "STT",
    provider: "google",
    type: "speech_to_text",
    created: "2026-01-01",
    updated: "2026-01-01",
  },
];

const defaultsFixture: ModelDefaults = {
  default_chat_model: "lang-zeta",
  default_embedding_model: "embed-1",
  default_text_to_speech_model: "tts-1",
  default_speech_to_text_model: "stt-1",
  default_transformation_model: "lang-alpha",
  default_tools_model: "lang-zeta",
  large_context_model: null,
};

describe("DefaultModelSelectors", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useUpdateModelDefaults).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateModelDefaults>);
    vi.mocked(useAutoAssignDefaults).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useAutoAssignDefaults>);
  });

  it("shows missing-required alert and triggers auto-assign", () => {
    const autoAssignMutate = vi.fn();
    vi.mocked(useAutoAssignDefaults).mockReturnValue({
      mutate: autoAssignMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useAutoAssignDefaults>);

    render(
      <DefaultModelSelectors
        models={modelsFixture}
        defaults={{
          ...defaultsFixture,
          default_chat_model: null,
          default_transformation_model: null,
          default_embedding_model: null,
        }}
      />,
    );

    expect(screen.getByText(/Missing:/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Auto assign" }));
    expect(autoAssignMutate).toHaveBeenCalledTimes(1);
  });

  it("renders sorted model options and clears optional defaults", () => {
    const updateMutate = vi.fn();
    vi.mocked(useUpdateModelDefaults).mockReturnValue({
      mutate: updateMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateModelDefaults>);

    render(<DefaultModelSelectors models={modelsFixture} defaults={defaultsFixture} />);

    const selects = screen.getAllByRole("combobox");
    const chatOptions = Array.from(selects[0].querySelectorAll("option")).map(
      (option) => option.textContent,
    );
    const alphaIndex = chatOptions.findIndex((text) => text?.includes("Alpha"));
    const zetaIndex = chatOptions.findIndex((text) => text?.includes("Zeta"));

    expect(alphaIndex).toBeGreaterThan(-1);
    expect(zetaIndex).toBeGreaterThan(-1);
    expect(alphaIndex).toBeLessThan(zetaIndex);

    fireEvent.click(screen.getByRole("button", { name: "Remove Tools model" }));

    expect(updateMutate).toHaveBeenCalledWith({ default_tools_model: null });
  });

  it("asks for confirmation before changing embedding default", () => {
    const updateMutate = vi.fn();
    vi.mocked(useUpdateModelDefaults).mockReturnValue({
      mutate: updateMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateModelDefaults>);

    render(<DefaultModelSelectors models={modelsFixture} defaults={defaultsFixture} />);

    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[1], { target: { value: "embed-2" } });

    expect(updateMutate).not.toHaveBeenCalled();
    expect(screen.getByTestId("embedding-change-dialog")).toHaveTextContent("Embed One");
    expect(screen.getByTestId("embedding-change-dialog")).toHaveTextContent("Embed Two");

    fireEvent.click(screen.getByRole("button", { name: "Confirm embedding change" }));
    expect(updateMutate).toHaveBeenCalledWith({ default_embedding_model: "embed-2" });
  });

  it("updates non-embedding defaults immediately", () => {
    const updateMutate = vi.fn();
    vi.mocked(useUpdateModelDefaults).mockReturnValue({
      mutate: updateMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateModelDefaults>);

    render(<DefaultModelSelectors models={modelsFixture} defaults={defaultsFixture} />);

    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[0], { target: { value: "lang-alpha" } });

    expect(updateMutate).toHaveBeenCalledWith({ default_chat_model: "lang-alpha" });
  });

  it("cancels embedding change confirmation without mutating defaults", () => {
    const updateMutate = vi.fn();
    vi.mocked(useUpdateModelDefaults).mockReturnValue({
      mutate: updateMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateModelDefaults>);

    render(<DefaultModelSelectors models={modelsFixture} defaults={defaultsFixture} />);

    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[1], { target: { value: "embed-2" } });

    expect(screen.getByTestId("embedding-change-dialog")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Cancel embedding change" }));

    expect(screen.queryByTestId("embedding-change-dialog")).not.toBeInTheDocument();
    expect(updateMutate).not.toHaveBeenCalled();
  });

  it("shows pending auto-assign state", () => {
    vi.mocked(useAutoAssignDefaults).mockReturnValue({
      mutate: vi.fn(),
      isPending: true,
    } as unknown as ReturnType<typeof useAutoAssignDefaults>);

    render(
      <DefaultModelSelectors
        models={modelsFixture}
        defaults={{ ...defaultsFixture, default_embedding_model: null }}
      />,
    );

    const pendingButton = screen.getByRole("button", { name: "Auto assigning" });
    expect(pendingButton).toBeDisabled();
  });
});
