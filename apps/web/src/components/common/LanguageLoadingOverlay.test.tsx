import { render, screen } from "@testing-library/react";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { emitLanguageChangeEnd, emitLanguageChangeStart } from "@/lib/i18n-events";
import { LanguageLoadingOverlay } from "./LanguageLoadingOverlay";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (_key: string, options?: { defaultValue?: string }) => options?.defaultValue ?? "Loading...",
  }),
}));

describe("LanguageLoadingOverlay", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("appears on language change start and disappears on language change end", () => {
    render(<LanguageLoadingOverlay />);

    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();

    act(() => {
      emitLanguageChangeStart("fr-FR");
    });

    expect(screen.getByText("Loading...")).toBeInTheDocument();

    act(() => {
      emitLanguageChangeEnd("fr-FR");
    });

    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
  });

  it("falls back to the safety timeout when no completion event arrives", () => {
    render(<LanguageLoadingOverlay />);

    act(() => {
      emitLanguageChangeStart("ja-JP");
    });

    expect(screen.getByText("Loading...")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1500);
    });

    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
  });
});
