import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useTransformations } from "@/lib/hooks/use-transformations";
import type { Transformation } from "@/lib/types/transformations";
import TransformationsPage from "./page";

vi.mock("@/lib/hooks/use-transformations");
vi.mock("@/components/layout/AppShell", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-shell">{children}</div>
  ),
}));
vi.mock("./components/DefaultPromptEditor", () => ({
  DefaultPromptEditor: () => <div data-testid="default-prompt-editor">default prompt</div>,
}));
vi.mock("./components/TransformationsList", () => ({
  TransformationsList: ({
    transformations,
    onPlayground,
    isLoading,
  }: {
    transformations?: Transformation[];
    isLoading: boolean;
    onPlayground?: (transformation: Transformation) => void;
  }) => (
    <div data-testid="transformations-list">
      <span>loading:{String(isLoading)}</span>
      <span>count:{transformations?.length ?? 0}</span>
      <button
        onClick={() => transformations?.[0] && onPlayground?.(transformations[0])}
        type="button"
      >
        open-playground
      </button>
    </div>
  ),
}));
vi.mock("./components/TransformationPlayground", () => ({
  TransformationPlayground: ({
    transformations,
    selectedTransformation,
  }: {
    transformations?: Transformation[];
    selectedTransformation?: Transformation;
  }) => (
    <div data-testid="transformation-playground">
      selected:{selectedTransformation?.name ?? "none"} total:{transformations?.length ?? 0}
    </div>
  ),
}));

const sampleTransformations: Transformation[] = [
  {
    id: "tr-1",
    name: "summary",
    title: "Summary",
    description: "Summarize source",
    prompt: "Summarize",
    apply_default: false,
    created: "2026-01-01T00:00:00Z",
    updated: "2026-01-01T00:00:00Z",
  },
  {
    id: "transformation:chat_knowledgeization",
    name: "Chat Knowledgeization",
    title: "Chat Knowledgeization",
    description: "Turn long context into structured knowledge assets.",
    prompt: "@prompt-pack:chat_knowledgeization",
    apply_default: false,
    created: "2026-01-01T00:00:00Z",
    updated: "2026-01-01T00:00:00Z",
  },
];

describe("TransformationsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("refreshes transformations when refresh action is clicked", () => {
    const refetch = vi.fn();
    vi.mocked(useTransformations).mockReturnValue({
      data: sampleTransformations,
      isLoading: false,
      refetch,
    } as unknown as ReturnType<typeof useTransformations>);

    render(<TransformationsPage />);

    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("switches to playground tab when list requests playground run", () => {
    vi.mocked(useTransformations).mockReturnValue({
      data: sampleTransformations,
      isLoading: false,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useTransformations>);

    render(<TransformationsPage />);

    expect(screen.queryByTestId("transformation-playground")).not.toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Playground" })).toHaveAttribute(
      "data-state",
      "inactive",
    );

    fireEvent.click(screen.getByRole("button", { name: "open-playground" }));

    expect(screen.getByRole("tab", { name: "Playground" })).toHaveAttribute("data-state", "active");
    expect(screen.getByTestId("transformation-playground")).toHaveTextContent("selected:summary");
  });

  it("surfaces the long-context starter for the built-in knowledgeization path", () => {
    vi.mocked(useTransformations).mockReturnValue({
      data: sampleTransformations,
      isLoading: false,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useTransformations>);

    render(<TransformationsPage />);

    expect(screen.getByTestId("long-context-starter")).toBeInTheDocument();
    expect(screen.getAllByTestId("long-context-next-ladder").at(-1)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("open-long-context-starter"));

    expect(screen.getByRole("tab", { name: "Playground" })).toHaveAttribute("data-state", "active");
    expect(screen.getByTestId("transformation-playground")).toHaveTextContent(
      "selected:Chat Knowledgeization",
    );
  });
});
