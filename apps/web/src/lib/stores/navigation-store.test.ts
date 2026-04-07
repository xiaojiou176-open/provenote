import { act } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

async function loadNavigationStore() {
  const module = await import("./navigation-store");
  return module.useNavigationStore;
}

describe("navigation-store", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-03-08T12:00:00Z"));
  });

  it("stores return target with timestamp and exposes current path/label", async () => {
    vi.resetModules();
    const useNavigationStore = await loadNavigationStore();
    useNavigationStore.setState({ returnTo: undefined });

    act(() => {
      useNavigationStore.getState().setReturnTo("/sources/source-1", "Back to source", {
        scrollPosition: 120,
      });
    });

    const state = useNavigationStore.getState();
    expect(state.returnTo?.path).toBe("/sources/source-1");
    expect(state.returnTo?.label).toBe("Back to source");
    expect(state.returnTo?.preserveState?.scrollPosition).toBe(120);
    expect(state.returnTo?.preserveState?.timestamp).toBe(Date.now());
    expect(state.getReturnPath()).toBe("/sources/source-1");
    expect(state.getReturnLabel()).toBe("Back to source");
  });

  it("falls back to sources when preserved context is stale", async () => {
    vi.resetModules();
    const useNavigationStore = await loadNavigationStore();
    useNavigationStore.setState({ returnTo: undefined });

    act(() => {
      useNavigationStore.setState({
        returnTo: {
          path: "/sources/source-9",
          label: "Stale label",
          preserveState: {
            timestamp: Date.now() - 3_700_000,
          },
        },
      });
    });

    expect(useNavigationStore.getState().getReturnPath()).toBe("/sources");
    expect(useNavigationStore.getState().getReturnLabel("Back to Sources")).toBe("Back to Sources");
    expect(useNavigationStore.getState().returnTo).toBeUndefined();
  });

  it("falls back to default label when context is stale for label lookup", async () => {
    vi.resetModules();
    const useNavigationStore = await loadNavigationStore();
    useNavigationStore.setState({
      returnTo: {
        path: "/sources/source-2",
        label: "Old label",
        preserveState: { timestamp: Date.now() - 3_700_000 },
      },
    });

    expect(useNavigationStore.getState().getReturnLabel("Back to Sources")).toBe("Back to Sources");
    expect(useNavigationStore.getState().returnTo).toBeUndefined();
  });

  it("clears stored navigation context explicitly", async () => {
    vi.resetModules();
    const useNavigationStore = await loadNavigationStore();
    useNavigationStore.setState({ returnTo: undefined });

    act(() => {
      useNavigationStore.getState().setReturnTo("/notebooks/1", "Back to notebook");
      useNavigationStore.getState().clearReturnTo();
    });

    expect(useNavigationStore.getState().returnTo).toBeUndefined();
    expect(useNavigationStore.getState().getReturnPath()).toBe("/sources");
  });

  it("safely handles storage errors for getItem/setItem/removeItem", async () => {
    vi.resetModules();
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("read unavailable");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("write unavailable");
    });
    vi.spyOn(Storage.prototype, "removeItem").mockImplementation(() => {
      throw new Error("remove unavailable");
    });

    const useNavigationStore = await loadNavigationStore();

    expect(() => {
      act(() => {
        useNavigationStore.getState().setReturnTo("/sources/source-3", "Back to source");
      });
    }).not.toThrow();

    expect(() => useNavigationStore.persist.clearStorage()).not.toThrow();
  });
});
