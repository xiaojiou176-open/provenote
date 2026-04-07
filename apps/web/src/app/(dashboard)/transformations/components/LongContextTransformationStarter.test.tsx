import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useTranslation } from "@/lib/hooks/use-translation";
import { LongContextTransformationStarter } from "./LongContextTransformationStarter";

vi.mock("@/lib/hooks/use-translation");

describe("LongContextTransformationStarter", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    const t = Object.assign(
      (key: string, values?: Record<string, unknown>) => {
        if (key === "transformations.longContextStarterTransformation") {
          return `Current built-in path: ${values?.name}`;
        }
        return key;
      },
      {
        transformations: {
          longContextStarterBuiltIn: "Built-in transformation",
          longContextStarterTitle: "Long-context structuring",
          longContextStarterHeading: "Turn long context into reusable knowledge assets",
          longContextStarterDescription: "Structure the messy material first.",
          longContextStarterInputTitle: "Best-fit inputs",
          longContextStarterInput1: "Long chats",
          longContextStarterInput2: "Forum threads",
          longContextStarterInput3: "Meeting notes",
          longContextStarterOutputTitle: "What you get",
          longContextStarterOutput1: "Process outline",
          longContextStarterOutput2: "Reusable insights",
          longContextStarterOutput3: "Per-turn recaps",
          longContextStarterNextTitle: "Next step",
          longContextStarterNext1: "Inspect the structured insight",
          longContextStarterNext2: "Save as note when you need a durable object",
          longContextStarterNext3: "Open a seeded Ask lane or save to research thread",
          longContextStarterNext4: "Move into auditable or draft-adjacent work",
          longContextStarterAction: "Open long-context starter",
          longContextStarterHint: "Use the playground first.",
        },
      },
    );

    vi.mocked(useTranslation).mockReturnValue({
      t,
    } as unknown as ReturnType<typeof useTranslation>);
  });

  it("shows the long-context continuation ladder and opens the starter", () => {
    const onOpenPlayground = vi.fn();

    render(
      <LongContextTransformationStarter
        transformationName="Chat Knowledgeization"
        onOpenPlayground={onOpenPlayground}
      />,
    );

    expect(screen.getByTestId("long-context-next-ladder")).toBeInTheDocument();
    expect(screen.getAllByText("Open long-context starter")[0]).toBeInTheDocument();
    expect(screen.getByText("Inspect the structured insight")).toBeInTheDocument();
    expect(screen.getByText("Save as note when you need a durable object")).toBeInTheDocument();
    expect(
      screen.getByText("Open a seeded Ask lane or save to research thread"),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open long-context starter" }));
    expect(onOpenPlayground).toHaveBeenCalledTimes(1);
  });
});
