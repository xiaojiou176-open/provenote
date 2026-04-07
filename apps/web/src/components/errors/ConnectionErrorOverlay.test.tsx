import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConnectionErrorOverlay } from "./ConnectionErrorOverlay";

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      connectionErrors: {
        apiTitle: "API unavailable",
        apiDesc: "The API cannot be reached",
        dbTitle: "Database unavailable",
        dbDesc: "The database cannot be reached",
        troubleshooting: "Troubleshooting",
        apiUnreachable1: "Check API URL",
        apiUnreachable2: "Check API process",
        apiUnreachable3: "Check container port",
        dbFailed1: "Check database process",
        dbFailed2: "Check credentials",
        dbFailed3: "Check namespace",
        quickFixes: "Quick fixes",
        setApiUrl: "Set API URL",
        dockerLabel: "Docker",
        localDevLabel: "Local",
        checkSurreal: "Check SurrealDB",
        seeDocumentation: "See docs",
        docLink: "Project docs",
        showTechnical: "Show technical details",
        attemptedUrl: "Attempted URL",
        message: "Message",
        technicalDetails: "Technical details",
        stackTrace: "Stack trace",
        retryLabel: "Retry now",
        retryHint: "Retry after fixing configuration",
      },
    },
  }),
}));

describe("ConnectionErrorOverlay", () => {
  it("renders API troubleshooting, toggles technical details, and retries", () => {
    const onRetry = vi.fn();

    render(
      <ConnectionErrorOverlay
        error={{
          type: "api-unreachable",
          details: {
            attemptedUrl: "http://localhost:5055",
            message: "fetch failed",
            technicalMessage: "ECONNREFUSED",
            stack: "stack-trace",
          },
        }}
        onRetry={onRetry}
      />,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("API unavailable")).toBeInTheDocument();
    expect(screen.getByText("Set API URL")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Show technical details" }));
    expect(screen.getByText(/Attempted URL:/)).toBeInTheDocument();
    expect(screen.getByText(/ECONNREFUSED/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry now" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("renders database troubleshooting branch without technical section", () => {
    render(
      <ConnectionErrorOverlay
        error={{
          type: "database-offline",
        }}
        onRetry={() => undefined}
      />,
    );

    expect(screen.getByText("Database unavailable")).toBeInTheDocument();
    expect(screen.getByText("Check SurrealDB")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Show technical details" }),
    ).not.toBeInTheDocument();
  });
});
