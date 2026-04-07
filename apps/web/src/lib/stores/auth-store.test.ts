import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  getApiUrlMock: vi.fn(),
  getStoredAuthTokenMock: vi.fn(),
}));

vi.mock("@/lib/config", () => ({
  getApiUrl: hoisted.getApiUrlMock,
}));

vi.mock("@/lib/auth-storage", () => ({
  getStoredAuthToken: hoisted.getStoredAuthTokenMock,
}));

let useAuthStore: typeof import("./auth-store").useAuthStore;

describe("auth-store", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    vi.spyOn(console, "error").mockImplementation(() => {});
    sessionStorage.clear();
    hoisted.getApiUrlMock.mockResolvedValue("http://localhost:5055");
    hoisted.getStoredAuthTokenMock.mockReturnValue(null);
    global.fetch = vi.fn();

    ({ useAuthStore } = await import("./auth-store"));
    useAuthStore.setState({
      isAuthenticated: false,
      token: null,
      isLoading: false,
      error: null,
      lastAuthCheck: null,
      isCheckingAuth: false,
      hasHydrated: false,
      authRequired: null,
    });
  });

  it("marks auth as not required and authenticates immediately", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ auth_enabled: false }),
    } as Response);

    await expect(useAuthStore.getState().checkAuthRequired()).resolves.toBe(false);

    expect(useAuthStore.getState().authRequired).toBe(false);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(useAuthStore.getState().token).toBe("not-required");
  });

  it("keeps auth unauthenticated when auth is required", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ auth_enabled: true }),
    } as Response);

    await expect(useAuthStore.getState().checkAuthRequired()).resolves.toBe(true);

    expect(useAuthStore.getState().authRequired).toBe(true);
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().token).toBeNull();
  });

  it("stores friendly error when auth status check fails to fetch", async () => {
    const networkError = new TypeError("Failed to fetch");
    vi.mocked(fetch).mockRejectedValue(networkError);

    await expect(useAuthStore.getState().checkAuthRequired()).rejects.toThrow("Failed to fetch");

    expect(useAuthStore.getState().authRequired).toBeNull();
    expect(useAuthStore.getState().error).toContain("Unable to connect to server");
  });

  it("defaults to requiring auth when auth status endpoint returns non-ok", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 503,
    } as Response);

    await expect(useAuthStore.getState().checkAuthRequired()).rejects.toThrow(
      "Auth status check failed: 503",
    );

    expect(useAuthStore.getState().authRequired).toBe(true);
  });

  it("authenticates and stores token on successful login", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
    } as Response);

    await expect(useAuthStore.getState().login("good-secret")).resolves.toBe(true);

    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(useAuthStore.getState().token).toBe("good-secret");
    expect(useAuthStore.getState().error).toBeNull();
  });

  it("returns false and maps 401 to invalid password during login", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 401,
    } as Response);

    await expect(useAuthStore.getState().login("bad-secret")).resolves.toBe(false);

    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().error).toBe("Invalid password. Please try again.");
  });

  it("maps 403/500/other login status codes to explicit messages", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({ ok: false, status: 403 } as Response)
      .mockResolvedValueOnce({ ok: false, status: 500 } as Response)
      .mockResolvedValueOnce({ ok: false, status: 418 } as Response);

    await expect(useAuthStore.getState().login("forbidden")).resolves.toBe(false);
    expect(useAuthStore.getState().error).toBe("Access denied. Please check your credentials.");

    await expect(useAuthStore.getState().login("server-error")).resolves.toBe(false);
    expect(useAuthStore.getState().error).toBe("Server error. Please try again later.");

    await expect(useAuthStore.getState().login("teapot")).resolves.toBe(false);
    expect(useAuthStore.getState().error).toBe("Authentication failed (418)");
  });

  it("maps login network and unexpected errors", async () => {
    vi.mocked(fetch)
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockRejectedValueOnce(new Error("socket closed"))
      .mockRejectedValueOnce("unknown");

    await expect(useAuthStore.getState().login("network")).resolves.toBe(false);
    expect(useAuthStore.getState().error).toContain("Unable to connect to server");

    await expect(useAuthStore.getState().login("error-object")).resolves.toBe(false);
    expect(useAuthStore.getState().error).toBe("Network error: socket closed");

    await expect(useAuthStore.getState().login("unknown-error")).resolves.toBe(false);
    expect(useAuthStore.getState().error).toBe(
      "An unexpected error occurred during authentication",
    );
  });

  it("skips network auth validation when cached auth is still fresh", async () => {
    useAuthStore.setState({
      isAuthenticated: true,
      token: "cached-token",
      lastAuthCheck: Date.now(),
    });

    await expect(useAuthStore.getState().checkAuth()).resolves.toBe(true);

    expect(fetch).not.toHaveBeenCalled();
  });

  it("returns current auth state while auth check is already in progress", async () => {
    useAuthStore.setState({
      isAuthenticated: true,
      token: "token",
      isCheckingAuth: true,
      lastAuthCheck: null,
    });

    await expect(useAuthStore.getState().checkAuth()).resolves.toBe(true);

    expect(fetch).not.toHaveBeenCalled();
  });

  it("returns false immediately when no auth token exists", async () => {
    useAuthStore.setState({
      isAuthenticated: true,
      token: null,
      lastAuthCheck: null,
      isCheckingAuth: false,
    });

    await expect(useAuthStore.getState().checkAuth()).resolves.toBe(false);

    expect(fetch).not.toHaveBeenCalled();
  });

  it("stores timestamp and authenticated state when remote check passes", async () => {
    const nowSpy = vi.spyOn(Date, "now").mockReturnValue(1700000000000);
    useAuthStore.setState({
      isAuthenticated: false,
      token: "valid-token",
      lastAuthCheck: null,
      isCheckingAuth: false,
    });
    vi.mocked(fetch).mockResolvedValue({ ok: true, status: 200 } as Response);

    await expect(useAuthStore.getState().checkAuth()).resolves.toBe(true);

    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(useAuthStore.getState().lastAuthCheck).toBe(1700000000000);
    expect(useAuthStore.getState().isCheckingAuth).toBe(false);
    nowSpy.mockRestore();
  });

  it("clears token when remote auth check fails", async () => {
    useAuthStore.setState({
      isAuthenticated: true,
      token: "cached-token",
      lastAuthCheck: null,
    });
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 403,
    } as Response);

    await expect(useAuthStore.getState().checkAuth()).resolves.toBe(false);

    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().isCheckingAuth).toBe(false);
  });

  it("clears token when remote auth check throws", async () => {
    useAuthStore.setState({
      isAuthenticated: true,
      token: "cached-token",
      lastAuthCheck: null,
      isCheckingAuth: false,
    });
    vi.mocked(fetch).mockRejectedValue(new Error("connection reset"));

    await expect(useAuthStore.getState().checkAuth()).resolves.toBe(false);

    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().lastAuthCheck).toBeNull();
  });

  it("rehydrates persisted token from auth storage", () => {
    hoisted.getStoredAuthTokenMock.mockReturnValue("persisted-token");

    const persistOptions = useAuthStore.persist.getOptions();
    const rehydrate = persistOptions.onRehydrateStorage?.();
    const state = {
      token: null,
      isAuthenticated: false,
      setHasHydrated: vi.fn(),
    } as unknown as Parameters<NonNullable<typeof rehydrate>>[0];

    rehydrate?.(state, undefined);

    expect(state.token).toBe("persisted-token");
    expect(state.isAuthenticated).toBe(true);
    expect(state.setHasHydrated).toHaveBeenCalledWith(true);
  });

  it("does not overwrite existing token during rehydrate", () => {
    hoisted.getStoredAuthTokenMock.mockReturnValue("persisted-token");

    const persistOptions = useAuthStore.persist.getOptions();
    const rehydrate = persistOptions.onRehydrateStorage?.();
    const state = {
      token: "existing-token",
      isAuthenticated: true,
      setHasHydrated: vi.fn(),
    } as unknown as Parameters<NonNullable<typeof rehydrate>>[0];

    rehydrate?.(state, undefined);

    expect(state.token).toBe("existing-token");
    expect(state.isAuthenticated).toBe(true);
    expect(state.setHasHydrated).toHaveBeenCalledWith(true);
  });

  it("handles missing state object during rehydrate callback", () => {
    const persistOptions = useAuthStore.persist.getOptions();
    const rehydrate = persistOptions.onRehydrateStorage?.();

    expect(() => rehydrate?.(undefined, undefined)).not.toThrow();
  });

  it("clears auth state on logout", () => {
    useAuthStore.setState({
      isAuthenticated: true,
      token: "to-clear",
      error: "old-error",
    });

    useAuthStore.getState().logout();

    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().error).toBeNull();
  });
});
