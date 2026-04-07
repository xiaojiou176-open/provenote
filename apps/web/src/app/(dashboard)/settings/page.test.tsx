import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSettings } from "@/lib/hooks/use-settings";
import SettingsPage from "./page";

vi.mock("@/lib/hooks/use-settings");

vi.mock("@/components/layout/AppShell", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-shell">{children}</div>
  ),
}));

vi.mock("./components/SettingsForm", () => ({
  SettingsForm: () => <div data-testid="settings-form">settings form</div>,
}));

describe("SettingsPage", () => {
  const refetch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useSettings).mockReturnValue({
      refetch,
    } as unknown as ReturnType<typeof useSettings>);
  });

  it("renders settings heading and form", () => {
    render(<SettingsPage />);

    expect(screen.getByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByTestId("settings-form")).toBeInTheDocument();
  });

  it("refetches settings when refresh button is clicked", () => {
    render(<SettingsPage />);

    fireEvent.click(screen.getByTestId("settings-refresh"));

    expect(refetch).toHaveBeenCalledTimes(1);
  });
});
