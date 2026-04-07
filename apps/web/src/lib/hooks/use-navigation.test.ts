import { describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  clearReturnToMock: vi.fn(),
  getReturnLabelMock: vi.fn(),
  getReturnPathMock: vi.fn(),
  setReturnToMock: vi.fn(),
  storeState: {
    returnTo: { path: "/sources/1", label: "Back" },
    setReturnTo: vi.fn(),
    clearReturnTo: vi.fn(),
    getReturnPath: vi.fn(),
    getReturnLabel: vi.fn(),
  },
}));

vi.mock("@/lib/stores/navigation-store", () => ({
  useNavigationStore: () => hoisted.storeState,
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      common: {
        backToSources: "Back to sources",
      },
    },
  }),
}));

import { useNavigation } from "./use-navigation";

describe("useNavigation", () => {
  it("forwards navigation store actions and state", () => {
    hoisted.storeState = {
      returnTo: { path: "/sources/1", label: "Back" },
      setReturnTo: hoisted.setReturnToMock,
      clearReturnTo: hoisted.clearReturnToMock,
      getReturnPath: hoisted.getReturnPathMock,
      getReturnLabel: hoisted.getReturnLabelMock,
    };

    const navigation = useNavigation();

    expect(navigation.returnTo).toEqual({ path: "/sources/1", label: "Back" });
    expect(navigation.setReturnTo).toBe(hoisted.setReturnToMock);
    expect(navigation.clearReturnTo).toBe(hoisted.clearReturnToMock);
    expect(navigation.getReturnPath).toBe(hoisted.getReturnPathMock);

    hoisted.getReturnLabelMock.mockReturnValue("Back");
    expect(navigation.getReturnLabel()).toBe("Back");
    expect(hoisted.getReturnLabelMock).toHaveBeenCalledWith("Back to sources");
  });

  it("uses the translated fallback when the store does not provide a label", () => {
    hoisted.storeState = {
      returnTo: null,
      setReturnTo: hoisted.setReturnToMock,
      clearReturnTo: hoisted.clearReturnToMock,
      getReturnPath: hoisted.getReturnPathMock,
      getReturnLabel: hoisted.getReturnLabelMock,
    };

    hoisted.getReturnLabelMock.mockImplementation((fallbackLabel?: string) => fallbackLabel || "");

    const navigation = useNavigation();

    expect(navigation.getReturnLabel()).toBe("Back to sources");
    expect(hoisted.getReturnLabelMock).toHaveBeenCalledWith("Back to sources");
  });
});
