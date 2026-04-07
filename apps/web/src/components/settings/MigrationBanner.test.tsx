import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MigrationBanner } from "./MigrationBanner";

describe("MigrationBanner", () => {
  it("renders nothing when no legacy env providers are present", () => {
    const { container } = render(<MigrationBanner providersWithLegacyEnv={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders blocking message when legacy env providers exist", () => {
    render(<MigrationBanner providersWithLegacyEnv={["anthropic", "azure"]} />);
    expect(screen.getByText("Legacy provider ENV detected")).toBeInTheDocument();
    expect(screen.getByText(/anthropic, azure/)).toBeInTheDocument();
  });
});
