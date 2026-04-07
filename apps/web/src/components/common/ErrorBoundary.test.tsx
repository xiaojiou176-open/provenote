import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ErrorBoundary, useErrorBoundary } from "./ErrorBoundary";

function ThrowingChild() {
  throw new Error("boom");
}

describe("ErrorBoundary", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  it("renders the default fallback when a child throws", () => {
    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Error")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try Again" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh" })).toBeInTheDocument();
  });

  it("uses a custom fallback and resetError callback", () => {
    let shouldThrow = true;
    const Fallback = ({ resetError }: { error?: Error; resetError: () => void }) => (
      <button
        onClick={() => {
          shouldThrow = false;
          resetError();
        }}
        type="button"
      >
        recover
      </button>
    );

    function MaybeThrow() {
      if (shouldThrow) {
        throw new Error("boom");
      }
      return <div>recovered</div>;
    }

    render(
      <ErrorBoundary fallback={Fallback}>
        <MaybeThrow />
      </ErrorBoundary>,
    );

    fireEvent.click(screen.getByRole("button", { name: "recover" }));

    expect(screen.getByText("recovered")).toBeInTheDocument();
  });

  it("reloads page from default fallback and exposes throwing helper hook", () => {
    const reloadSpy = vi.fn();
    const originalLocation = window.location;
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...originalLocation, reload: reloadSpy },
    });

    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(reloadSpy).toHaveBeenCalledTimes(1);

    const throwBoundaryError = useErrorBoundary();
    expect(() => throwBoundaryError(new Error("hook-error"))).toThrow("hook-error");
  });

  it("shows debug details in development mode", () => {
    vi.stubEnv("NODE_ENV", "development");

    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Error Details")).toBeInTheDocument();
    expect(screen.getByText("Error: boom")).toBeInTheDocument();

    vi.unstubAllEnvs();
  });
});
