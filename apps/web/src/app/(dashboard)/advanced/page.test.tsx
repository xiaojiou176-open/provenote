import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AdvancedPage from "./page";

vi.mock("@/components/layout/AppShell", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-shell">{children}</div>
  ),
}));

vi.mock("./components/SystemInfo", () => ({
  SystemInfo: () => <section data-testid="system-info">system info</section>,
}));

vi.mock("./components/RebuildEmbeddings", () => ({
  RebuildEmbeddings: () => <section data-testid="rebuild-embeddings">rebuild embeddings</section>,
}));

describe("AdvancedPage", () => {
  it("renders route readiness marker and advanced sections", () => {
    render(<AdvancedPage />);

    expect(screen.getByTestId("a11y-route-advanced-ready")).toBeInTheDocument();
    expect(screen.getByTestId("system-info")).toBeInTheDocument();
    expect(screen.getByTestId("rebuild-embeddings")).toBeInTheDocument();
  });
});
