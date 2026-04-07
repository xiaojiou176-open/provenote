import { render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ThemeProvider } from "./ThemeProvider";

const hoisted = vi.hoisted(() => ({
  store: {
    theme: "dark",
    getSystemTheme: vi.fn(() => "dark"),
    getEffectiveTheme: vi.fn(() => "dark"),
  },
}));

vi.mock("@/lib/stores/theme-store", () => ({
  useThemeStore: () => hoisted.store,
}));

describe("ThemeProvider", () => {
  beforeEach(() => {
    document.documentElement.className = "";
    document.documentElement.removeAttribute("data-theme");
    vi.clearAllMocks();
  });

  afterEach(() => {
    document.documentElement.className = "";
    document.documentElement.removeAttribute("data-theme");
  });

  it("applies the effective theme class and data attribute on mount", () => {
    hoisted.store.theme = "dark";
    hoisted.store.getEffectiveTheme.mockReturnValue("dark");

    render(
      <ThemeProvider>
        <div>theme child</div>
      </ThemeProvider>,
    );

    expect(document.documentElement).toHaveClass("dark");
    expect(document.documentElement).toHaveAttribute("data-theme", "dark");
  });

  it("listens to system theme changes when theme mode is system and cleans up on unmount", () => {
    const addEventListener = vi.fn();
    const removeEventListener = vi.fn();

    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn().mockReturnValue({
        matches: false,
        media: "(prefers-color-scheme: dark)",
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener,
        removeEventListener,
        dispatchEvent: vi.fn(),
      }),
    });

    hoisted.store.theme = "system";
    hoisted.store.getEffectiveTheme.mockReturnValue("light");
    hoisted.store.getSystemTheme.mockReturnValue("dark");

    const { unmount } = render(
      <ThemeProvider>
        <div>theme child</div>
      </ThemeProvider>,
    );

    expect(addEventListener).toHaveBeenCalledWith("change", expect.any(Function));

    const changeHandler = addEventListener.mock.calls[0]?.[1] as (() => void) | undefined;
    changeHandler?.();

    expect(document.documentElement).toHaveClass("dark");
    expect(document.documentElement).toHaveAttribute("data-theme", "dark");

    unmount();

    expect(removeEventListener).toHaveBeenCalledWith("change", changeHandler);
  });
});
