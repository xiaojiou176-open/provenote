import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { act } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ConnectionGuard } from "./ConnectionGuard";

const hoisted = vi.hoisted(() => ({
  getConfigMock: vi.fn(),
  resetConfigMock: vi.fn(),
}));

vi.mock("@/lib/config", () => ({
  getConfig: hoisted.getConfigMock,
  resetConfig: hoisted.resetConfigMock,
}));

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: ({ label }: { label?: string }) => (
    <div data-testid="loading-spinner">{label}</div>
  ),
}));

vi.mock("@/components/errors/ConnectionErrorOverlay", () => ({
  ConnectionErrorOverlay: ({
    error,
    onRetry,
  }: {
    error: { type: string };
    onRetry: () => void;
  }) => (
    <div data-testid="connection-error">
      <span>{error.type}</span>
      <button onClick={onRetry} type="button">
        retry
      </button>
    </div>
  ),
}));

describe("ConnectionGuard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a loading state and then renders children when config is online", async () => {
    hoisted.getConfigMock.mockResolvedValue({
      apiUrl: "http://localhost:5055",
      dbStatus: "online",
    });

    render(
      <ConnectionGuard>
        <div data-testid="guard-child">ready</div>
      </ConnectionGuard>,
    );

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("guard-child")).toBeInTheDocument();
    });

    expect(hoisted.resetConfigMock).toHaveBeenCalledTimes(1);
  });

  it("renders the offline overlay and retries when user presses R", async () => {
    hoisted.getConfigMock
      .mockResolvedValueOnce({
        apiUrl: "http://localhost:5055",
        dbStatus: "offline",
      })
      .mockResolvedValueOnce({
        apiUrl: "http://localhost:5055",
        dbStatus: "online",
      });

    render(
      <ConnectionGuard>
        <div data-testid="guard-child">ready</div>
      </ConnectionGuard>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("connection-error")).toHaveTextContent("database-offline");
    });

    await waitFor(() => {
      expect(hoisted.getConfigMock).toHaveBeenCalledTimes(1);
    });

    act(() => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "r", bubbles: true }));
    });

    await waitFor(() => {
      expect(hoisted.getConfigMock).toHaveBeenCalledTimes(2);
    });

    await waitFor(() => {
      expect(screen.getByTestId("guard-child")).toBeInTheDocument();
    });

    expect(hoisted.getConfigMock).toHaveBeenCalledTimes(2);
  });

  it("surfaces API errors and retries when the overlay button is clicked", async () => {
    hoisted.getConfigMock.mockRejectedValueOnce(new Error("socket refused")).mockResolvedValueOnce({
      apiUrl: "http://localhost:5055",
      dbStatus: "online",
    });

    render(
      <ConnectionGuard>
        <div data-testid="guard-child">ready</div>
      </ConnectionGuard>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("connection-error")).toHaveTextContent("api-unreachable");
    });

    fireEvent.click(screen.getByRole("button", { name: "retry" }));

    await waitFor(() => {
      expect(hoisted.getConfigMock).toHaveBeenCalledTimes(2);
    });
    await waitFor(() => {
      expect(screen.getByTestId("guard-child")).toBeInTheDocument();
    });

    expect(hoisted.resetConfigMock).toHaveBeenCalledTimes(2);
  });
});
