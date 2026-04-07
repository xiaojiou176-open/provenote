import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { I18nProvider } from "./I18nProvider";

vi.mock("@/components/common/LanguageLoadingOverlay", () => ({
  LanguageLoadingOverlay: () => <div data-testid="language-loading-overlay">overlay</div>,
}));

describe("I18nProvider", () => {
  it("renders the loading overlay and children after mount", async () => {
    render(
      <I18nProvider>
        <div data-testid="i18n-child">child</div>
      </I18nProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("language-loading-overlay")).toBeInTheDocument();
      expect(screen.getByTestId("i18n-child")).toBeInTheDocument();
    });
  });
});
