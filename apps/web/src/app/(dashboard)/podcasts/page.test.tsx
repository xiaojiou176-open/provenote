import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import PodcastsPage from "./page";

const tabsState = vi.hoisted(() => ({
  value: "episodes",
  onValueChange: (_value: string) => {},
}));

vi.mock("@/components/layout/AppShell", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-shell">{children}</div>
  ),
}));

vi.mock("@/components/podcasts/EpisodesTab", () => ({
  EpisodesTab: () => <div data-testid="episodes-tab">episodes</div>,
}));

vi.mock("@/components/podcasts/TemplatesTab", () => ({
  TemplatesTab: () => <div data-testid="templates-tab">templates</div>,
}));

vi.mock("@/components/ui/tabs", () => ({
  Tabs: ({
    value,
    onValueChange,
    children,
  }: {
    value: string;
    onValueChange: (value: string) => void;
    children: React.ReactNode;
  }) => {
    tabsState.value = value;
    tabsState.onValueChange = onValueChange;
    return <div data-testid="tabs-root">{children}</div>;
  },
  TabsList: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TabsTrigger: ({ value, children }: { value: string; children: React.ReactNode }) => (
    <button onClick={() => tabsState.onValueChange(value)} type="button">
      {children}
    </button>
  ),
  TabsContent: ({ value, children }: { value: string; children: React.ReactNode }) =>
    tabsState.value === value ? <div data-testid={`content-${value}`}>{children}</div> : null,
}));

describe("PodcastsPage", () => {
  it("renders readiness marker and shows episodes tab by default", () => {
    render(<PodcastsPage />);

    expect(screen.getByTestId("a11y-route-podcasts-ready")).toBeInTheDocument();
    expect(screen.getByTestId("episodes-tab")).toBeInTheDocument();
    expect(screen.queryByTestId("templates-tab")).not.toBeInTheDocument();
  });

  it("switches to templates tab when templates trigger is clicked", () => {
    render(<PodcastsPage />);

    fireEvent.click(screen.getByRole("button", { name: "Templates" }));

    expect(screen.getByTestId("templates-tab")).toBeInTheDocument();
    expect(screen.queryByTestId("episodes-tab")).not.toBeInTheDocument();
  });
});
