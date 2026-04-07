import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useExecuteTransformation } from "@/lib/hooks/use-transformations";
import { appLog } from "@/lib/log";
import type { Transformation } from "@/lib/types/transformations";
import { TransformationPlayground } from "./TransformationPlayground";

const mutateAsync = vi.fn();

vi.mock("@/lib/hooks/use-transformations", () => ({
  useExecuteTransformation: vi.fn(),
}));

vi.mock("@/lib/log", () => ({
  appLog: {
    error: vi.fn(),
  },
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      transformations: {
        playground: "Playground",
        desc: "Run transformation tests",
        selectToStart: "Select transformation",
        model: "Model",
        selectModel: "Select model",
        inputLabel: "Input text",
        inputPlaceholder: "Paste source text",
        running: "Running",
        runTest: "Run test",
        outputLabel: "Output",
      },
      navigation: {
        transformation: "Transformation",
      },
    },
  }),
}));

vi.mock("@/components/common/ModelSelector", () => ({
  ModelSelector: ({
    label,
    value,
    onChange,
    placeholder,
  }: {
    label: string;
    value: string;
    onChange: (value: string) => void;
    placeholder: string;
  }) => (
    <label>
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{placeholder}</option>
        <option value="model-1">model-1</option>
      </select>
    </label>
  ),
}));

vi.mock("@/components/ui/select", () => ({
  Select: ({
    value,
    onValueChange,
    name,
    children,
  }: {
    value: string;
    onValueChange: (value: string) => void;
    name?: string;
    children: ReactNode;
  }) => (
    <label>
      {name ?? "select"}
      <select value={value} onChange={(event) => onValueChange(event.target.value)}>
        {children}
      </select>
    </label>
  ),
  SelectTrigger: ({ children }: { children: ReactNode }) => <>{children}</>,
  SelectValue: ({ placeholder }: { placeholder: string }) => (
    <option value="">{placeholder}</option>
  ),
  SelectContent: ({ children }: { children: ReactNode }) => <>{children}</>,
  SelectItem: ({ value, children }: { value: string; children: ReactNode }) => (
    <option value={value}>{children}</option>
  ),
}));

describe("TransformationPlayground", () => {
  const transformations: Transformation[] = [
    {
      id: "tr-1",
      name: "summary",
      title: "Summary",
      description: "Summarize",
      prompt: "Prompt",
      apply_default: false,
      created: "2026-01-01T00:00:00Z",
      updated: "2026-01-01T00:00:00Z",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useExecuteTransformation).mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useExecuteTransformation>);
  });

  it("keeps run button disabled when required fields are missing", () => {
    render(<TransformationPlayground transformations={transformations} />);

    const runButton = screen.getByRole("button", { name: "Run test" });
    expect(runButton).toBeDisabled();

    fireEvent.click(runButton);
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it("executes selected transformation and renders output", async () => {
    mutateAsync.mockResolvedValue({
      output: "## Generated output\n\n| Col A | Col B |\n| --- | --- |\n| one | two |",
    });

    render(
      <TransformationPlayground
        transformations={transformations}
        selectedTransformation={transformations[0]}
      />,
    );

    fireEvent.change(screen.getByRole("combobox", { name: "Model" }), {
      target: { value: "model-1" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Input text" }), {
      target: { value: "Input body" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Run test" }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        transformation_id: "tr-1",
        model_id: "model-1",
        input_text: "Input body",
      });
      expect(screen.getByText("Generated output")).toBeInTheDocument();
      expect(screen.getByText("Output")).toBeInTheDocument();
      expect(screen.getByRole("table")).toBeInTheDocument();
      expect(screen.getByText("one")).toBeInTheDocument();
    });
  });

  it("shows pending state while execution is in progress", () => {
    vi.mocked(useExecuteTransformation).mockReturnValue({
      mutateAsync,
      isPending: true,
    } as unknown as ReturnType<typeof useExecuteTransformation>);

    render(
      <TransformationPlayground
        transformations={transformations}
        selectedTransformation={transformations[0]}
      />,
    );

    expect(screen.getByRole("button", { name: "Running" })).toBeDisabled();
  });

  it("supports keyboard submit shortcut and blocks incomplete keyboard submits", async () => {
    mutateAsync.mockResolvedValue({ output: "Keyboard output" });

    render(
      <TransformationPlayground
        transformations={transformations}
        selectedTransformation={transformations[0]}
      />,
    );

    const input = screen.getByRole("textbox", { name: "Input text" });

    fireEvent.keyDown(input, { key: "Enter", ctrlKey: true });
    expect(mutateAsync).not.toHaveBeenCalled();

    fireEvent.change(screen.getByRole("combobox", { name: "Model" }), {
      target: { value: "model-1" },
    });
    fireEvent.change(input, { target: { value: "Keyboard body" } });
    fireEvent.keyDown(input, { key: "Enter", ctrlKey: true });

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        transformation_id: "tr-1",
        model_id: "model-1",
        input_text: "Keyboard body",
      });
      expect(screen.getByText("Keyboard output")).toBeInTheDocument();
    });
  });

  it("recovers after a failed submit by allowing retry", async () => {
    const error = new Error("network failure");

    mutateAsync.mockRejectedValueOnce(error).mockResolvedValueOnce({ output: "Recovered output" });

    render(
      <TransformationPlayground
        transformations={transformations}
        selectedTransformation={transformations[0]}
      />,
    );

    fireEvent.change(screen.getByRole("combobox", { name: "Model" }), {
      target: { value: "model-1" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Input text" }), {
      target: { value: "Recover body" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Run test" }));
    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(1);
      expect(appLog.error).toHaveBeenCalledWith(
        "transformation-playground",
        "Failed to execute transformation",
        {
          transformationId: "tr-1",
          modelId: "model-1",
          error,
        },
      );
    });

    fireEvent.click(screen.getByRole("button", { name: "Run test" }));
    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(2);
      expect(screen.getByText("Recovered output")).toBeInTheDocument();
    });
  });
});
