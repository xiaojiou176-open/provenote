import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useCredentialStatus, useCredentials } from "@/lib/hooks/use-credentials";
import { useModelDefaults, useModels } from "@/lib/hooks/use-models";
import ApiKeysPage from "./page";

vi.mock("@/components/layout/AppShell", () => ({
  AppShell: ({ children }: { children: ReactNode }) => (
    <div data-testid="app-shell">{children}</div>
  ),
}));

vi.mock("@/components/settings", () => ({
  MigrationBanner: ({ providersWithLegacyEnv }: { providersWithLegacyEnv: string[] }) => (
    <div data-testid="migration-banner">{providersWithLegacyEnv.join(",") || "none"}</div>
  ),
}));

vi.mock("./default-model-selectors", () => ({
  DefaultModelSelectors: () => <div data-testid="default-model-selectors">default selectors</div>,
}));

vi.mock("./provider-section", () => ({
  ProviderSection: ({ provider }: { provider: string }) => (
    <div data-testid={`provider-section-${provider}`}>{provider}</div>
  ),
}));

vi.mock("@/lib/hooks/use-credentials");
vi.mock("@/lib/hooks/use-models");

function mockData({
  credentialsLoading = false,
  modelsLoading = false,
  defaultsLoading = false,
  encryptionConfigured = true,
  legacyGoogle = false,
  includeModels = true,
  includeDefaults = true,
  withStatus = true,
}: {
  credentialsLoading?: boolean;
  modelsLoading?: boolean;
  defaultsLoading?: boolean;
  encryptionConfigured?: boolean;
  legacyGoogle?: boolean;
  includeModels?: boolean;
  includeDefaults?: boolean;
  withStatus?: boolean;
} = {}) {
  vi.mocked(useCredentials).mockReturnValue({
    data: [
      {
        id: "cred-google",
        name: "Google prod",
        provider: "google",
        modalities: ["language"],
        has_api_key: true,
        created: "2026-01-01T00:00:00Z",
        updated: "2026-01-01T00:00:00Z",
        model_count: 1,
      },
    ],
    isLoading: credentialsLoading,
  } as unknown as ReturnType<typeof useCredentials>);

  vi.mocked(useModels).mockReturnValue({
    data: includeModels
      ? [
          {
            id: "model-chat",
            name: "gemini-3.0-pro",
            provider: "google",
            type: "language",
            credential: "cred-google",
          },
        ]
      : undefined,
    isLoading: modelsLoading,
  } as unknown as ReturnType<typeof useModels>);

  vi.mocked(useModelDefaults).mockReturnValue({
    data: includeDefaults
      ? {
          default_chat_model: "model-chat",
          default_transformation_model: "model-chat",
          default_tools_model: null,
          large_context_model: null,
          default_embedding_model: null,
          default_text_to_speech_model: null,
          default_speech_to_text_model: null,
        }
      : undefined,
    isLoading: defaultsLoading,
  } as unknown as ReturnType<typeof useModelDefaults>);

  vi.mocked(useCredentialStatus).mockReturnValue({
    data: withStatus
      ? {
          encryption_configured: encryptionConfigured,
          configured: { google: true },
          source: { google: "database" },
          legacy_env_detected: { google: legacyGoogle },
        }
      : undefined,
  } as unknown as ReturnType<typeof useCredentialStatus>);
}

describe("ApiKeysPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_REPOSITORY_URL = "https://github.com/example/provenote";
  });

  it("renders loading state while data is fetching", () => {
    mockData({ credentialsLoading: true });

    render(<ApiKeysPage />);

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("shows encryption warning when encryption is not configured", () => {
    mockData({ encryptionConfigured: false });

    render(<ApiKeysPage />);

    expect(screen.getByText("Encryption key not configured")).toBeInTheDocument();
    expect(screen.queryByTestId("migration-banner")).not.toBeInTheDocument();
  });

  it("shows legacy env alert and hides default selectors when legacy env exists", () => {
    mockData({ legacyGoogle: true });

    render(<ApiKeysPage />);

    expect(screen.getByText("Legacy provider ENV detected")).toBeInTheDocument();
    expect(screen.queryByTestId("default-model-selectors")).not.toBeInTheDocument();
    expect(screen.queryByTestId("provider-section-google")).not.toBeInTheDocument();
  });

  it("renders provider sections and defaults when ready", () => {
    mockData();

    render(<ApiKeysPage />);

    expect(screen.getByTestId("a11y-route-settings-api-keys-ready")).toBeInTheDocument();
    expect(screen.getByTestId("default-model-selectors")).toBeInTheDocument();
    expect(screen.getByTestId("provider-section-google")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Learn how to configure API keys →" })).toHaveAttribute(
      "href",
      "https://github.com/example/provenote/blob/main/docs/configuration.md",
    );
  });

  it("treats missing credential status as encryption ready and still renders providers", () => {
    mockData({ withStatus: false });

    render(<ApiKeysPage />);

    expect(screen.queryByText("Encryption key not configured")).not.toBeInTheDocument();
    expect(screen.getByTestId("migration-banner")).toHaveTextContent("none");
    expect(screen.getByTestId("provider-section-google")).toBeInTheDocument();
  });

  it("hides default selectors when models/defaults are unavailable but still shows provider cards", () => {
    mockData({ includeModels: false, includeDefaults: false });

    render(<ApiKeysPage />);

    expect(screen.queryByTestId("default-model-selectors")).not.toBeInTheDocument();
    expect(screen.getByTestId("provider-section-google")).toBeInTheDocument();
  });

  it("hides the learn-more link when no repo-local repository URL is configured", () => {
    delete process.env.NEXT_PUBLIC_REPOSITORY_URL;
    mockData();

    render(<ApiKeysPage />);

    expect(
      screen.queryByRole("link", { name: "Learn how to configure API keys →" }),
    ).not.toBeInTheDocument();
  });
});
