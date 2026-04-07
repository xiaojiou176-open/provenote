import { renderHook } from "@testing-library/react";
import { act } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useIsDesktop, useMediaQuery } from "./use-media-query";

describe("useMediaQuery", () => {
  beforeEach(() => {
    let matches = false;
    const listeners = new Set<(event: MediaQueryListEvent) => void>();

    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn((query: string) => ({
        matches,
        media: query,
        addEventListener: (_: string, listener: (event: MediaQueryListEvent) => void) => {
          listeners.add(listener);
        },
        removeEventListener: (_: string, listener: (event: MediaQueryListEvent) => void) => {
          listeners.delete(listener);
        },
        dispatch(nextMatches: boolean) {
          matches = nextMatches;
          for (const listener of listeners) {
            listener({ matches: nextMatches } as MediaQueryListEvent);
          }
        },
      })),
    });
  });

  it("tracks media query changes", () => {
    const { result } = renderHook(() => useMediaQuery("(min-width: 1024px)"));
    const mediaQuery = window.matchMedia("(min-width: 1024px)") as MediaQueryList & {
      dispatch: (value: boolean) => void;
    };

    expect(result.current).toBe(false);

    act(() => {
      mediaQuery.dispatch(true);
    });

    expect(result.current).toBe(true);
  });

  it("useIsDesktop delegates to the desktop breakpoint", () => {
    const { result } = renderHook(() => useIsDesktop());

    expect(window.matchMedia).toHaveBeenCalledWith("(min-width: 1024px)");
    expect(result.current).toBe(false);
  });
});
