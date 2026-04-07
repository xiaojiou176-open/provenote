import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LoginPage from "./page";

vi.mock("@/components/common/ErrorBoundary", () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="error-boundary">{children}</div>
  ),
}));

vi.mock("@/components/auth/LoginForm", () => ({
  LoginForm: () => <div data-testid="login-form">login form</div>,
}));

describe("LoginPage", () => {
  it("wraps login form with the shared error boundary", () => {
    render(<LoginPage />);

    expect(screen.getByTestId("error-boundary")).toBeInTheDocument();
    expect(screen.getByTestId("login-form")).toBeInTheDocument();
  });
});
