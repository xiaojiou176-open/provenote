import { beforeEach, describe, expect, it, vi } from "vitest";
import { clearStoredAuthToken, getStoredAuthToken } from "./auth-storage";

describe("auth storage", () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("returns null when no browser token exists", () => {
    expect(getStoredAuthToken()).toBeNull();
  });

  it("prefers a session token when present", () => {
    sessionStorage.setItem("auth-storage", JSON.stringify({ state: { token: "session-token" } }));
    localStorage.setItem("auth-storage", JSON.stringify({ state: { token: "legacy-token" } }));

    expect(getStoredAuthToken()).toBe("session-token");
    expect(localStorage.getItem("auth-storage")).not.toBeNull();
  });

  it("migrates legacy local storage tokens into session storage", () => {
    localStorage.setItem("auth-storage", JSON.stringify({ state: { token: "legacy-token" } }));

    expect(getStoredAuthToken()).toBe("legacy-token");
    expect(sessionStorage.getItem("auth-storage")).toContain("legacy-token");
    expect(localStorage.getItem("auth-storage")).toBeNull();
  });

  it("returns null and logs when stored payload is invalid", () => {
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    localStorage.setItem("auth-storage", "{not-json");

    expect(getStoredAuthToken()).toBeNull();
    expect(consoleErrorSpy).toHaveBeenCalled();
  });

  it("clears session and local storage tokens", () => {
    sessionStorage.setItem("auth-storage", JSON.stringify({ state: { token: "session-token" } }));
    localStorage.setItem("auth-storage", JSON.stringify({ state: { token: "legacy-token" } }));

    clearStoredAuthToken();

    expect(sessionStorage.getItem("auth-storage")).toBeNull();
    expect(localStorage.getItem("auth-storage")).toBeNull();
  });
});
