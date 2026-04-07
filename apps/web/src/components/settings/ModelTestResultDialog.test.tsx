import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ModelTestResultDialog } from "./ModelTestResultDialog";

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      models: {
        testModelSuccess: "Model test passed",
        testModelFailed: "Model test failed",
      },
      common: {
        done: "Done",
      },
    },
  }),
}));

describe("ModelTestResultDialog", () => {
  it("renders nothing when no result is provided", () => {
    const { container } = render(
      <ModelTestResultDialog
        open
        modelName="Gemini Pro"
        onOpenChange={() => undefined}
        result={null}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("renders success payload and closes on done", () => {
    const onOpenChange = vi.fn();

    render(
      <ModelTestResultDialog
        open
        modelName="Gemini Pro"
        onOpenChange={onOpenChange}
        result={{ success: true, message: "Connected", details: "Latency: 42ms" }}
      />,
    );

    expect(screen.getByText("Model test passed")).toBeInTheDocument();
    expect(screen.getByText("Gemini Pro")).toBeInTheDocument();
    expect(screen.getByText("Connected")).toBeInTheDocument();
    expect(screen.getByText("Latency: 42ms")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Done" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
