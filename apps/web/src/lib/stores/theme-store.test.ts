import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useTheme, useThemeStore } from "./theme-store";

function createMatchMedia(matches: boolean): (query: string) => MediaQueryList {
  return (query: string) =>
    ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }) as MediaQueryList;
}

describe("theme store", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    document.documentElement.className = "";
    document.documentElement.removeAttribute("data-theme");
    useThemeStore.setState({ theme: "system" });
  });

  it("sets explicit theme and updates document attributes", () => {
    act(() => {
      useThemeStore.getState().setTheme("dark");
    });

    expect(useThemeStore.getState().theme).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(document.documentElement.classList.contains("light")).toBe(false);
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("resolves system theme from matchMedia and effective theme helper", () => {
    vi.spyOn(window, "matchMedia").mockImplementation(createMatchMedia(true));

    act(() => {
      useThemeStore.getState().setTheme("system");
    });

    expect(useThemeStore.getState().getSystemTheme()).toBe("dark");
    expect(useThemeStore.getState().getEffectiveTheme()).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("returns light system theme when media query does not match", () => {
    vi.spyOn(window, "matchMedia").mockImplementation(createMatchMedia(false));

    expect(useThemeStore.getState().getSystemTheme()).toBe("light");
  });

  it("falls back to light when window is unavailable", () => {
    const windowDescriptor = Object.getOwnPropertyDescriptor(globalThis, "window");
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      writable: true,
      value: undefined,
    });

    try {
      expect(useThemeStore.getState().getSystemTheme()).toBe("light");
    } finally {
      if (windowDescriptor) {
        Object.defineProperty(globalThis, "window", windowDescriptor);
      }
    }
  });

  it("updates state without touching document when setTheme runs without window", () => {
    const windowDescriptor = Object.getOwnPropertyDescriptor(globalThis, "window");
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      writable: true,
      value: undefined,
    });

    try {
      expect(() => useThemeStore.getState().setTheme("dark")).not.toThrow();
      expect(useThemeStore.getState().theme).toBe("dark");
    } finally {
      if (windowDescriptor) {
        Object.defineProperty(globalThis, "window", windowDescriptor);
      }
    }
  });

  it("useTheme exposes effectiveTheme and isDark flags", () => {
    vi.spyOn(window, "matchMedia").mockImplementation(createMatchMedia(false));
    const { result } = renderHook(() => useTheme());

    expect(result.current.theme).toBe("system");
    expect(result.current.effectiveTheme).toBe("light");
    expect(result.current.isDark).toBe(false);

    act(() => {
      result.current.setTheme("dark");
    });

    expect(result.current.theme).toBe("dark");
    expect(result.current.effectiveTheme).toBe("dark");
    expect(result.current.isDark).toBe(true);
  });
});
