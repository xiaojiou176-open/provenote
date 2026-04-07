import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { useCredentialStatus } from "@/lib/hooks/use-credentials";
import { SetupBanner } from "./SetupBanner";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@/lib/hooks/use-credentials", () => ({
  useCredentialStatus: vi.fn(),
}));
vi.mock("@/lib/repo-links", () => ({
  getRepositoryBlobUrl: () => "https://example.com/docs/configuration.md",
}));

describe("SetupBanner", () => {
  it("renders nothing when credential status has not loaded yet", () => {
    vi.mocked(useCredentialStatus).mockReturnValue({
      data: undefined,
    } as ReturnType<typeof useCredentialStatus>);

    const { container } = render(<SetupBanner />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when encryption is ready and no legacy env is detected", () => {
    vi.mocked(useCredentialStatus).mockReturnValue({
      data: {
        configured: { google: true },
        source: { google: "database" },
        legacy_env_detected: { google: false },
        encryption_configured: true,
      },
    } as ReturnType<typeof useCredentialStatus>);

    const { container } = render(<SetupBanner />);
    expect(container.firstChild).toBeNull();
  });

  it("shows blocking banner when legacy env variables are detected", () => {
    vi.mocked(useCredentialStatus).mockReturnValue({
      data: {
        configured: { google: false },
        source: { google: "none" },
        legacy_env_detected: { google: true },
        encryption_configured: true,
      },
    } as ReturnType<typeof useCredentialStatus>);

    render(<SetupBanner />);
    expect(screen.getByText("Legacy provider ENV is blocked")).toBeInTheDocument();
    expect(screen.getByText(/Remove provider ENV values for 1 provider/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open API Keys/i })).toBeInTheDocument();
  });

  it("shows encryption setup guidance when encryption is not configured", () => {
    vi.mocked(useCredentialStatus).mockReturnValue({
      data: {
        configured: { google: false },
        source: { google: "none" },
        legacy_env_detected: { google: false },
        encryption_configured: false,
      },
    } as ReturnType<typeof useCredentialStatus>);

    render(<SetupBanner />);

    expect(screen.getByText("Encryption key not configured")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /View docs/i })).toBeInTheDocument();
  });
});
