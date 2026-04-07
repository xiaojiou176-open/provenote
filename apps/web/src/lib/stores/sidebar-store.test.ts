import { act } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.unmock("@/lib/stores/sidebar-store");

import { useSidebarStore } from "@/lib/stores/sidebar-store";

describe("sidebar-store", () => {
  beforeEach(() => {
    localStorage.clear();
    useSidebarStore.setState({ isCollapsed: false });
  });

  it("toggles collapsed state", () => {
    act(() => {
      useSidebarStore.getState().toggleCollapse();
    });

    expect(useSidebarStore.getState().isCollapsed).toBe(true);

    act(() => {
      useSidebarStore.getState().toggleCollapse();
    });

    expect(useSidebarStore.getState().isCollapsed).toBe(false);
  });

  it("sets collapsed state explicitly and persists the latest value", () => {
    act(() => {
      useSidebarStore.getState().setCollapsed(true);
    });

    expect(useSidebarStore.getState().isCollapsed).toBe(true);
    expect(useSidebarStore.persist.getOptions().name).toBe("sidebar-storage");
  });
});
