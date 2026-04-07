import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  pushMock: vi.fn(),
  useAuthStoreMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: hoisted.pushMock }),
}));

vi.mock("@/lib/stores/auth-store", () => ({
  useAuthStore: hoisted.useAuthStoreMock,
}));

vi.unmock("@/lib/hooks/use-auth");

let useAuth: typeof import("./use-auth").useAuth;

describe("useAuth", () => {
  beforeAll(async () => {
    ({ useAuth } = await import("./use-auth"));
  });

  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it("treats unhydrated store as loading and skips auth checks", () => {
    const checkAuthRequired = vi.fn();
    const checkAuth = vi.fn();

    hoisted.useAuthStoreMock.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth,
      checkAuthRequired,
      error: null,
      hasHydrated: false,
      authRequired: null,
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.isLoading).toBe(true);
    expect(checkAuthRequired).not.toHaveBeenCalled();
    expect(checkAuth).not.toHaveBeenCalled();
  });

  it("checks auth requirements after hydration and validates credentials when required", async () => {
    const checkAuth = vi.fn();
    const checkAuthRequired = vi.fn().mockResolvedValue(true);

    hoisted.useAuthStoreMock.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth,
      checkAuthRequired,
      error: null,
      hasHydrated: true,
      authRequired: null,
    });

    renderHook(() => useAuth());

    await waitFor(() => {
      expect(checkAuthRequired).toHaveBeenCalledTimes(1);
      expect(checkAuth).toHaveBeenCalledTimes(1);
    });
  });

  it("redirects to stored path after successful login", async () => {
    const login = vi.fn().mockResolvedValue(true);

    hoisted.useAuthStoreMock.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      login,
      logout: vi.fn(),
      checkAuth: vi.fn(),
      checkAuthRequired: vi.fn(),
      error: null,
      hasHydrated: true,
      authRequired: true,
    });

    sessionStorage.setItem("redirectAfterLogin", "/sources?focus=latest");
    const { result } = renderHook(() => useAuth());

    await act(async () => {
      const success = await result.current.login("secret");
      expect(success).toBe(true);
    });

    expect(hoisted.pushMock).toHaveBeenCalledWith("/sources?focus=latest");
    expect(sessionStorage.getItem("redirectAfterLogin")).toBeNull();
  });

  it("falls back to notebooks route after successful login without redirect", async () => {
    const login = vi.fn().mockResolvedValue(true);

    hoisted.useAuthStoreMock.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      login,
      logout: vi.fn(),
      checkAuth: vi.fn(),
      checkAuthRequired: vi.fn(),
      error: null,
      hasHydrated: true,
      authRequired: true,
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      const success = await result.current.login("secret");
      expect(success).toBe(true);
    });

    expect(hoisted.pushMock).toHaveBeenCalledWith("/notebooks");
  });

  it("logs out and routes back to login", () => {
    const logout = vi.fn();

    hoisted.useAuthStoreMock.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout,
      checkAuth: vi.fn(),
      checkAuthRequired: vi.fn(),
      error: null,
      hasHydrated: true,
      authRequired: true,
    });

    const { result } = renderHook(() => useAuth());
    result.current.logout();

    expect(logout).toHaveBeenCalledTimes(1);
    expect(hoisted.pushMock).toHaveBeenCalledWith("/login");
  });
});
