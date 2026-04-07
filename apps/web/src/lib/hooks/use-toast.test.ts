import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  successMock: vi.fn(),
  errorMock: vi.fn(),
  useTranslationMock: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: {
    success: hoisted.successMock,
    error: hoisted.errorMock,
  },
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: hoisted.useTranslationMock,
}));

import { useToast } from "./use-toast";

describe("useToast", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useTranslationMock.mockReturnValue({
      t: {
        common: {
          success: "Success",
          error: "Error",
        },
      },
    });
  });

  it("uses success toast and default title", () => {
    const { result } = renderHook(() => useToast());

    result.current.toast({ description: "Saved item" });

    expect(hoisted.successMock).toHaveBeenCalledWith("Success", {
      description: "Saved item",
    });
  });

  it("uses destructive variant with fallback error title", () => {
    const { result } = renderHook(() => useToast());

    result.current.toast({ variant: "destructive", description: "Request failed" });

    expect(hoisted.errorMock).toHaveBeenCalledWith("Error", {
      description: "Request failed",
    });
  });

  it("prefers explicit title over translation defaults", () => {
    const { result } = renderHook(() => useToast());

    result.current.toast({
      title: "Uploaded",
      description: "Done",
    });
    result.current.toast({
      title: "Cannot upload",
      description: "Bad file",
      variant: "destructive",
    });

    expect(hoisted.successMock).toHaveBeenCalledWith("Uploaded", { description: "Done" });
    expect(hoisted.errorMock).toHaveBeenCalledWith("Cannot upload", {
      description: "Bad file",
    });
  });
});
