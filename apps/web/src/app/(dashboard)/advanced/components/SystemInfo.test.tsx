import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SystemInfo } from "./SystemInfo";

const hoisted = vi.hoisted(() => ({
  getConfigMock: vi.fn(),
}));

vi.mock("@/lib/config", () => ({
  getConfig: hoisted.getConfigMock,
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      advanced: {
        systemInfo: "System info",
        currentVersion: "Current version",
        latestVersion: "Latest version",
        status: "Status",
        updateAvailable: "Update {version}",
        upToDate: "Up to date",
        unknown: "Unknown",
        viewOnGithub: "View on GitHub",
        updateCheckFailed: "Update check failed",
      },
      common: {
        loading: "Loading",
      },
    },
  }),
}));

describe("SystemInfo", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_REPOSITORY_URL = "https://github.com/example/notebooklab";
  });

  it("shows update metadata and github link when an update is available", async () => {
    hoisted.getConfigMock.mockResolvedValue({
      version: "1.0.0",
      latestVersion: "1.1.0",
      hasUpdate: true,
    });

    render(<SystemInfo />);

    expect(screen.getByText("Loading")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Current version")).toBeInTheDocument();
    });

    expect(screen.getByText("1.0.0")).toBeInTheDocument();
    expect(screen.getByText("1.1.0")).toBeInTheDocument();
    expect(screen.getByText("Update 1.1.0")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View on GitHub" })).toHaveAttribute(
      "href",
      "https://github.com/example/notebooklab",
    );
  });

  it("shows fallback status when version check cannot resolve latest release", async () => {
    hoisted.getConfigMock.mockResolvedValue({
      version: "1.0.0",
      latestVersion: null,
      hasUpdate: false,
    });

    render(<SystemInfo />);

    await waitFor(() => {
      expect(screen.getByText("Update check failed")).toBeInTheDocument();
    });

    expect(screen.getByText("Unknown")).toBeInTheDocument();
  });

  it("hides update link and latest-version metadata when no repo-local repository URL is configured", async () => {
    delete process.env.NEXT_PUBLIC_REPOSITORY_URL;
    hoisted.getConfigMock.mockResolvedValue({
      version: "1.0.0",
      latestVersion: "1.1.0",
      hasUpdate: true,
    });

    render(<SystemInfo />);

    await waitFor(() => {
      expect(screen.getByText("Current version")).toBeInTheDocument();
    });

    expect(screen.queryByText("1.1.0")).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "View on GitHub" })).not.toBeInTheDocument();
    expect(screen.getByText("Unknown")).toBeInTheDocument();
  });
});
