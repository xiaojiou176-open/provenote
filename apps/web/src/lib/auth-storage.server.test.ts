import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe("auth storage server-side guards", () => {
  it("returns null without a browser window", async () => {
    vi.stubGlobal("window", undefined);
    const { getStoredAuthToken } = await import("./auth-storage");

    expect(getStoredAuthToken()).toBeNull();
  });

  it("does nothing when clearing tokens without a browser window", async () => {
    vi.stubGlobal("window", undefined);
    const { clearStoredAuthToken } = await import("./auth-storage");

    expect(() => clearStoredAuthToken()).not.toThrow();
  });
});
