import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AppShell } from "./AppShell";

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      common: {
        accessibility: {
          openSidebarNavigation: "Open sidebar navigation",
        },
      },
    },
  }),
}));

vi.mock("./AppSidebar", () => ({
  AppSidebar: ({
    mobileOpen,
    onMobileOpenChange,
  }: {
    mobileOpen: boolean;
    onMobileOpenChange: (open: boolean) => void;
  }) => (
    <div data-open={String(mobileOpen)} data-testid="app-sidebar">
      <button onClick={() => onMobileOpenChange(false)} type="button">
        Close sidebar
      </button>
    </div>
  ),
}));

vi.mock("./SetupBanner", () => ({
  SetupBanner: () => <div data-testid="setup-banner">setup banner</div>,
}));

describe("AppShell", () => {
  it("renders children, banner, and opens the mobile sidebar", () => {
    render(
      <AppShell>
        <div data-testid="shell-child">child content</div>
      </AppShell>,
    );

    expect(screen.getByTestId("setup-banner")).toBeInTheDocument();
    expect(screen.getByTestId("shell-child")).toBeInTheDocument();
    expect(screen.getByTestId("app-sidebar")).toHaveAttribute("data-open", "false");

    const openButton = screen.getByRole("button", {
      name: "Open sidebar navigation",
    });
    fireEvent.click(openButton);

    expect(screen.getByTestId("app-sidebar")).toHaveAttribute("data-open", "true");
    expect(openButton).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
  });
});
