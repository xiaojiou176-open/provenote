import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  getConfigMock: vi.fn(),
  infoMock: vi.fn(),
  t: {
    advanced: {
      updateAvailable: "Update {version}",
      updateAvailableDesc: "A new release is available",
      viewOnGithub: "View on GitHub",
    },
  },
}));

vi.mock("sonner", () => ({
  toast: {
    info: hoisted.infoMock,
  },
}));

vi.mock("@/lib/config", () => ({
  getConfig: hoisted.getConfigMock,
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t: hoisted.t }),
}));

import { useVersionCheck } from "./use-version-check";

describe("useVersionCheck", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    process.env.NEXT_PUBLIC_REPOSITORY_URL = "https://github.com/example/provenote";
    hoisted.getConfigMock.mockResolvedValue({
      hasUpdate: true,
      latestVersion: "9.9.9",
    });
    window.open = vi.fn();
  });

  it("shows version toast once and persists dismissal", async () => {
    renderHook(() => useVersionCheck());

    await waitFor(() => {
      expect(hoisted.infoMock).toHaveBeenCalledTimes(1);
    });

    const [, options] = hoisted.infoMock.mock.calls[0];
    expect(options.description).toBe("A new release is available");

    options.action.onClick();
    expect(window.open).toHaveBeenCalledWith("https://github.com/example/provenote", "_blank");

    options.onDismiss();
    expect(sessionStorage.getItem("version_notification_dismissed_9.9.9")).toBe("true");
  });

  it("skips toast when update has already been dismissed or config has no update", async () => {
    sessionStorage.setItem("version_notification_dismissed_9.9.9", "true");
    renderHook(() => useVersionCheck());

    await waitFor(() => {
      expect(hoisted.getConfigMock).toHaveBeenCalledTimes(1);
    });
    expect(hoisted.infoMock).not.toHaveBeenCalled();

    hoisted.getConfigMock.mockResolvedValueOnce({
      hasUpdate: false,
      latestVersion: null,
    });
    renderHook(() => useVersionCheck());

    await waitFor(() => {
      expect(hoisted.getConfigMock).toHaveBeenCalledTimes(2);
    });
    expect(hoisted.infoMock).not.toHaveBeenCalled();
  });

  it("skips update toast when no repo-local repository URL is configured", async () => {
    delete process.env.NEXT_PUBLIC_REPOSITORY_URL;

    renderHook(() => useVersionCheck());

    await waitFor(() => {
      expect(hoisted.getConfigMock).toHaveBeenCalledTimes(1);
    });
    expect(hoisted.infoMock).not.toHaveBeenCalled();
  });

  it("does not re-run the version check on rerender after the first pass", async () => {
    const { rerender } = renderHook(() => useVersionCheck());

    await waitFor(() => {
      expect(hoisted.getConfigMock).toHaveBeenCalledTimes(1);
    });

    hoisted.t = {
      advanced: {
        ...hoisted.t.advanced,
      },
    };
    rerender();
    expect(hoisted.getConfigMock).toHaveBeenCalledTimes(1);
  });
});
