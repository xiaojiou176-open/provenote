import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LoginForm } from "./LoginForm";

const hoisted = vi.hoisted(() => ({
  pushMock: vi.fn(),
  reloadMock: vi.fn(),
  loginMock: vi.fn(),
  checkAuthRequiredMock: vi.fn(),
  getConfigMock: vi.fn(),
  authStoreState: {
    authRequired: true as boolean | null,
    checkAuthRequired: vi.fn(),
    hasHydrated: true,
    isAuthenticated: false,
  },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: hoisted.pushMock }),
}));

vi.mock("@/lib/hooks/use-auth", () => ({
  useAuth: () => ({
    login: hoisted.loginMock,
    isLoading: false,
    error: null as string | null,
  }),
}));

vi.mock("@/lib/stores/auth-store", () => ({
  useAuthStore: () => hoisted.authStoreState,
}));

vi.mock("@/lib/config", () => ({
  getConfig: hoisted.getConfigMock,
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    language: "en-US",
    t: {
      common: {
        connectionError: "Connection error",
        unableToConnect: "Unable to connect",
        diagnosticInfo: "Diagnostic info",
        version: "Version",
        built: "Built",
        apiUrl: "API URL",
        frontendUrl: "Frontend URL",
        checkConsoleLogs: "Check console logs",
        retryConnection: "Retry connection",
      },
      auth: {
        loginTitle: "Sign in",
        loginDesc: "Use your password to continue",
        passwordPlaceholder: "Password",
        signingIn: "Signing in",
        signIn: "Sign in",
        connectErrorHint: "Connect error hint",
      },
    },
  }),
}));

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">loading</div>,
}));

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.authStoreState = {
      authRequired: true,
      checkAuthRequired: hoisted.checkAuthRequiredMock,
      hasHydrated: true,
      isAuthenticated: false,
    };
    hoisted.getConfigMock.mockResolvedValue({
      apiUrl: "http://localhost:5055",
      version: "1.0.0",
      buildTime: "2026-01-01T00:00:00.000Z",
    });
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...window.location,
        href: "http://localhost:3100/login",
        reload: hoisted.reloadMock,
      },
    });
  });

  it("shows loading spinner while hydration or auth check is pending", async () => {
    hoisted.authStoreState = {
      authRequired: null,
      checkAuthRequired: hoisted.checkAuthRequiredMock,
      hasHydrated: false,
      isAuthenticated: false,
    };

    render(<LoginForm />);

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Sign in" })).not.toBeInTheDocument();
    await act(async () => {
      await Promise.resolve();
    });
  });

  it("redirects to notebooks when auth is not required", async () => {
    hoisted.authStoreState = {
      authRequired: null,
      checkAuthRequired: hoisted.checkAuthRequiredMock.mockResolvedValue(false),
      hasHydrated: true,
      isAuthenticated: false,
    };

    render(<LoginForm />);

    await waitFor(() => {
      expect(hoisted.checkAuthRequiredMock).toHaveBeenCalledTimes(1);
      expect(hoisted.pushMock).toHaveBeenCalledWith("/notebooks");
    });
  });

  it("renders connection diagnostics and retries reload when auth state is unknown", async () => {
    hoisted.authStoreState = {
      authRequired: null,
      checkAuthRequired: hoisted.checkAuthRequiredMock,
      hasHydrated: true,
      isAuthenticated: false,
    };

    render(<LoginForm />);

    expect(await screen.findByText("Connection error")).toBeInTheDocument();
    expect(screen.getByText("Diagnostic info:")).toBeInTheDocument();
    expect(screen.getByText(/Version:/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry connection" }));
    expect(hoisted.reloadMock).toHaveBeenCalledTimes(1);
  });

  it("submits password to login and disables submit when password is blank", async () => {
    hoisted.loginMock.mockResolvedValue(true);

    render(<LoginForm />);

    const submit = screen.getByRole("button", { name: "Sign in" });
    expect(submit).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "secret-pass" },
    });

    expect(submit).not.toBeDisabled();
    fireEvent.click(submit);

    await waitFor(() => {
      expect(hoisted.loginMock).toHaveBeenCalledWith("secret-pass");
    });
  });
});
