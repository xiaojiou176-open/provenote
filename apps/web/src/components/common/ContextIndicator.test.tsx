import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ContextIndicator } from "./ContextIndicator";

describe("ContextIndicator", () => {
  it("shows the empty-context guidance when nothing is selected", () => {
    render(<ContextIndicator sourcesInsights={0} sourcesFull={0} notesCount={0} />);

    expect(
      screen.getByText(
        "No sources or notes included in context. Toggle icons on cards to include them.",
      ),
    ).toBeInTheDocument();
  });

  it("renders source/note counts and formatted token metadata", () => {
    render(
      <ContextIndicator
        sourcesInsights={2}
        sourcesFull={1}
        notesCount={3}
        tokenCount={1500}
        charCount={2500000}
      />,
    );

    expect(screen.getByText("Context:")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("1.5K tokens")).toBeInTheDocument();
    expect(screen.getByText("2.5M chars")).toBeInTheDocument();
  });
});
