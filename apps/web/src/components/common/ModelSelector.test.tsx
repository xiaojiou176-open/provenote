import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ModelSelector } from "./ModelSelector";

const hoisted = vi.hoisted(() => ({
  useModelsMock: vi.fn(),
}));

vi.mock("@/lib/hooks/use-models", () => ({
  useModels: () => hoisted.useModelsMock(),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      settings: {
        embeddingOptionPlaceholder: "Choose a model",
      },
      common: {
        noResults: "No results",
      },
    },
  }),
}));

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">loading</div>,
}));

vi.mock("@/components/ui/label", () => ({
  Label: ({ children, htmlFor }: { children: React.ReactNode; htmlFor?: string }) => (
    <label htmlFor={htmlFor}>{children}</label>
  ),
}));

vi.mock("@/components/ui/select", () => ({
  Select: ({
    children,
    value,
    onValueChange,
    disabled,
  }: {
    children: React.ReactNode;
    value: string;
    onValueChange: (value: string) => void;
    disabled?: boolean;
  }) => (
    <div data-disabled={String(Boolean(disabled))}>
      <button onClick={() => onValueChange("model-2")} type="button">
        trigger:{value}
      </button>
      {children}
    </div>
  ),
  SelectTrigger: ({ id, children }: { id?: string; children: React.ReactNode }) => (
    <div data-testid={id}>{children}</div>
  ),
  SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>,
  SelectContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <div data-testid={`option-${value}`}>{children}</div>
  ),
}));

describe("ModelSelector", () => {
  it("shows loading state while models are being fetched", () => {
    hoisted.useModelsMock.mockReturnValue({
      data: [],
      isLoading: true,
    });

    render(
      <ModelSelector label="Model" modelType="language" onChange={() => undefined} value="" />,
    );

    expect(screen.getByText("Model")).toBeInTheDocument();
    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("filters models by type and forwards selection changes", () => {
    const onChange = vi.fn();
    hoisted.useModelsMock.mockReturnValue({
      data: [
        { id: "model-1", name: "Gemini Flash", type: "language", provider: "google" },
        { id: "model-2", name: "Embed 004", type: "embedding", provider: "google" },
      ],
      isLoading: false,
    });

    render(
      <ModelSelector
        id="model-selector"
        label="Model"
        modelType="embedding"
        onChange={onChange}
        value=""
      />,
    );

    expect(screen.getByText("Choose a model")).toBeInTheDocument();
    expect(screen.getByTestId("option-model-2")).toHaveTextContent("Embed 004");
    expect(screen.queryByTestId("option-model-1")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "trigger:" }));
    expect(onChange).toHaveBeenCalledWith("model-2");
  });
});
