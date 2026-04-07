import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuth } from "@/lib/hooks/use-auth";
import DashboardLayout from "./layout";

const hoisted = vi.hoisted(() => ({
  pushMock: vi.fn(),
  pathname: "/notebooks",
  useVersionCheckMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: hoisted.pushMock }),
  usePathname: () => hoisted.pathname,
}));

vi.mock("@/lib/hooks/use-auth");

vi.mock("@/lib/hooks/use-version-check", () => ({
  useVersionCheck: hoisted.useVersionCheckMock,
}));

vi.mock("@/components/common/ErrorBoundary", () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/components/providers/CreateDialogsProvider", () => ({
  CreateDialogsProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/components/providers/ModalProvider", () => ({
  ModalProvider: () => <div data-testid="modal-provider" />,
}));

vi.mock("@/components/common/CommandPalette", () => ({
  CommandPalette: () => <div data-testid="command-palette" />,
}));

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

function mockAuthState(overrides: Partial<ReturnType<typeof useAuth>>) {
  vi.mocked(useAuth).mockReturnValue({
    isAuthenticated: true,
    isLoading: false,
    authRequired: true,
    login: vi.fn(),
    logout: vi.fn(),
    error: null,
    ...overrides,
  } as ReturnType<typeof useAuth>);
}

describe("DashboardLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    hoisted.pathname = "/notebooks";
    window.history.replaceState({}, "", "/notebooks");
  });

  it("shows loading spinner while auth state is loading", () => {
    mockAuthState({ isLoading: true, isAuthenticated: false, authRequired: null });

    render(
      <DashboardLayout>
        <div>dashboard</div>
      </DashboardLayout>,
    );

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
    expect(screen.queryByText("dashboard")).not.toBeInTheDocument();
  });

  it("redirects to login and stores return path when auth is required", async () => {
    mockAuthState({ isLoading: false, isAuthenticated: false, authRequired: true });
    window.history.replaceState({}, "", "/advanced?tab=2");

    const { container } = render(
      <DashboardLayout>
        <div>private-content</div>
      </DashboardLayout>,
    );

    await waitFor(() => {
      expect(hoisted.pushMock).toHaveBeenCalledWith("/login");
    });

    expect(sessionStorage.getItem("redirectAfterLogin")).toBe("/advanced?tab=2");
    expect(container).toBeEmptyDOMElement();
  });

  it("renders shell content and route progress transition for authenticated users", async () => {
    mockAuthState({ isLoading: false, isAuthenticated: true, authRequired: true });

    const { container } = render(
      <DashboardLayout>
        <div>dashboard-content</div>
      </DashboardLayout>,
    );

    await waitFor(() => {
      expect(screen.getByText("dashboard-content")).toBeInTheDocument();
    });

    const progress = container.querySelector(".ui-route-progress");
    expect(progress).toHaveClass("ui-route-progress-active");

    expect(progress).not.toBeNull();
    fireEvent.animationEnd(progress as Element);
    await waitFor(() => {
      expect(container.querySelector(".ui-route-progress")).not.toHaveClass(
        "ui-route-progress-active",
      );
    });
    expect(screen.getByTestId("modal-provider")).toBeInTheDocument();
    expect(screen.getByTestId("command-palette")).toBeInTheDocument();
    // Layout has internal state updates, so this hook can run multiple times via re-renders.
    expect(hoisted.useVersionCheckMock.mock.calls.length).toBeGreaterThanOrEqual(1);
  });

  it("renders dashboard content when auth is not required", async () => {
    mockAuthState({ isLoading: false, isAuthenticated: false, authRequired: false });

    render(
      <DashboardLayout>
        <div>public-dashboard-content</div>
      </DashboardLayout>,
    );

    await waitFor(() => {
      expect(screen.getByText("public-dashboard-content")).toBeInTheDocument();
    });
    expect(hoisted.pushMock).not.toHaveBeenCalled();
  });
});
