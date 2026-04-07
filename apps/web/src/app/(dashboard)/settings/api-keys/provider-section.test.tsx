import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Credential } from "@/lib/api/credentials";
import { useCredential, useTestCredential } from "@/lib/hooks/use-credentials";
import { useDeleteModel, useTestModel } from "@/lib/hooks/use-models";
import type { Model, ModelDefaults } from "@/lib/types/models";
import { ProviderSection } from "./provider-section";

vi.mock("@/lib/hooks/use-credentials");
vi.mock("@/lib/hooks/use-models");
vi.mock("./dialogs", () => ({
  CredentialFormDialog: ({
    open,
    provider,
    credential,
  }: {
    open: boolean;
    provider: string;
    credential?: Credential | null;
  }) =>
    open ? (
      <div data-testid="credential-form-dialog">
        {provider}:{credential?.id ?? "new"}
      </div>
    ) : null,
  DeleteCredentialDialog: ({ open }: { open: boolean }) =>
    open ? <div data-testid="delete-credential-dialog">delete-open</div> : null,
  DiscoverModelsDialog: ({ open }: { open: boolean }) =>
    open ? <div data-testid="discover-models-dialog">discover-open</div> : null,
}));
vi.mock("@/components/settings", () => ({
  ModelTestResultDialog: ({
    open,
    onOpenChange,
  }: {
    open: boolean;
    onOpenChange: (open: boolean) => void;
  }) =>
    open ? (
      <button
        data-testid="model-test-result-dialog"
        onClick={() => onOpenChange(false)}
        type="button"
      >
        close-result
      </button>
    ) : null,
}));

const credentialFixture: Credential = {
  id: "cred-1",
  name: "Google Prod",
  provider: "google",
  modalities: ["language", "embedding"],
  has_api_key: true,
  created: "2026-01-01T00:00:00Z",
  updated: "2026-01-01T00:00:00Z",
  model_count: 1,
};

const modelFixture: Model = {
  id: "model-1",
  name: "gemini-3.0-pro",
  provider: "google",
  type: "language",
  credential: "cred-1",
  created: "2026-01-01T00:00:00Z",
  updated: "2026-01-01T00:00:00Z",
};

const defaultsFixture: ModelDefaults = {
  default_chat_model: "model-1",
  default_transformation_model: null,
  default_tools_model: null,
  large_context_model: null,
  default_embedding_model: null,
  default_text_to_speech_model: null,
  default_speech_to_text_model: null,
};

describe("ProviderSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useCredential).mockReturnValue({
      data: credentialFixture,
    } as unknown as ReturnType<typeof useCredential>);
    vi.mocked(useTestCredential).mockReturnValue({
      testCredential: vi.fn(),
      isPending: false,
      testResults: {},
      clearResult: vi.fn(),
    } as unknown as ReturnType<typeof useTestCredential>);
    vi.mocked(useTestModel).mockReturnValue({
      testModel: vi.fn(),
      isPending: false,
      testingModelId: null,
      testResult: null,
      testedModelName: "",
      clearResult: vi.fn(),
    } as unknown as ReturnType<typeof useTestModel>);
    vi.mocked(useDeleteModel).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteModel>);
  });

  it("shows not configured state and disables add button when encryption is unavailable", () => {
    render(
      <ProviderSection
        provider="google"
        credentials={[]}
        models={[]}
        defaults={null}
        allCredentials={[]}
        encryptionReady={false}
      />,
    );

    expect(screen.getByText("Not configured")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add Configuration" })).toBeDisabled();
  });

  it("opens add configuration dialog when provider is ready for a new credential", () => {
    render(
      <ProviderSection
        provider="google"
        credentials={[]}
        models={[]}
        defaults={null}
        allCredentials={[]}
        encryptionReady={true}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Add Configuration" }));
    expect(screen.getByTestId("credential-form-dialog")).toHaveTextContent("google:new");
  });

  it("runs credential/model actions and opens related dialogs", () => {
    const testCredential = vi.fn();
    const testModel = vi.fn();
    const deleteModelMutate = vi.fn();

    vi.mocked(useTestCredential).mockReturnValue({
      testCredential,
      isPending: false,
      testResults: {},
      clearResult: vi.fn(),
    } as unknown as ReturnType<typeof useTestCredential>);
    vi.mocked(useTestModel).mockReturnValue({
      testModel,
      isPending: false,
      testingModelId: null,
      testResult: null,
      testedModelName: "",
      clearResult: vi.fn(),
    } as unknown as ReturnType<typeof useTestModel>);
    vi.mocked(useDeleteModel).mockReturnValue({
      mutate: deleteModelMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteModel>);

    render(
      <ProviderSection
        provider="google"
        credentials={[credentialFixture]}
        models={[modelFixture]}
        defaults={defaultsFixture}
        allCredentials={[credentialFixture]}
        encryptionReady={true}
      />,
    );

    fireEvent.click(screen.getByTitle("Test Connection"));
    expect(testCredential).toHaveBeenCalledWith("cred-1");

    fireEvent.click(screen.getByTitle("Test Model"));
    expect(testModel).toHaveBeenCalledWith("model-1", "gemini-3.0-pro");

    fireEvent.click(screen.getByTitle("Delete Model"));
    expect(deleteModelMutate).toHaveBeenCalledWith("model-1");

    fireEvent.click(screen.getByTestId("credential-sync-models"));
    expect(screen.getByTestId("discover-models-dialog")).toBeInTheDocument();

    fireEvent.click(screen.getByTitle("Edit"));
    expect(screen.getByTestId("credential-form-dialog")).toHaveTextContent("google:cred-1");

    fireEvent.click(screen.getByTestId("credential-delete"));
    expect(screen.getByTestId("delete-credential-dialog")).toBeInTheDocument();
  });

  it("renders linked model groups with default slot labels across modalities", () => {
    render(
      <ProviderSection
        provider="google"
        credentials={[credentialFixture]}
        models={[
          modelFixture,
          {
            ...modelFixture,
            id: "model-embed",
            name: "text-embedding-004",
            type: "embedding",
          },
        ]}
        defaults={{
          ...defaultsFixture,
          default_embedding_model: "model-embed",
        }}
        allCredentials={[credentialFixture]}
        encryptionReady={true}
      />,
    );

    expect(screen.getByText("gemini-3.0-pro")).toBeInTheDocument();
    expect(screen.getByText("(Chat)")).toBeInTheDocument();
    expect(screen.getByText("text-embedding-004")).toBeInTheDocument();
    expect(screen.getByText("(Embedding)")).toBeInTheDocument();
  });

  it("uses fetched credential details in edit dialog when detail query resolves", () => {
    vi.mocked(useCredential).mockReturnValue({
      data: { ...credentialFixture, id: "cred-1", name: "Resolved detail" },
    } as unknown as ReturnType<typeof useCredential>);

    render(
      <ProviderSection
        provider="google"
        credentials={[credentialFixture]}
        models={[modelFixture]}
        defaults={defaultsFixture}
        allCredentials={[credentialFixture]}
        encryptionReady={true}
      />,
    );

    fireEvent.click(screen.getByTitle("Edit"));
    expect(screen.getByTestId("credential-form-dialog")).toHaveTextContent("google:cred-1");
  });

  it("shows pending states for credential and model actions", () => {
    vi.mocked(useTestCredential).mockReturnValue({
      testCredential: vi.fn(),
      isPending: true,
      testResults: { "cred-1": { success: false, message: "fail" } },
      clearResult: vi.fn(),
    } as unknown as ReturnType<typeof useTestCredential>);
    vi.mocked(useTestModel).mockReturnValue({
      testModel: vi.fn(),
      isPending: true,
      testingModelId: "model-1",
      testResult: null,
      testedModelName: "",
      clearResult: vi.fn(),
    } as unknown as ReturnType<typeof useTestModel>);

    render(
      <ProviderSection
        provider="google"
        credentials={[credentialFixture]}
        models={[modelFixture]}
        defaults={defaultsFixture}
        allCredentials={[credentialFixture]}
        encryptionReady={true}
      />,
    );

    const connectionButton = screen.getByTitle("Test Connection");
    const modelButton = screen.getByTitle("Test Model");
    expect(connectionButton).toBeDisabled();
    expect(modelButton).toBeDisabled();
    expect(connectionButton.querySelector(".animate-spin")).not.toBeNull();
    expect(modelButton.querySelector(".animate-spin")).not.toBeNull();
    expect(screen.getByTitle("Delete Model")).toBeInTheDocument();
  });

  it("clears model result dialog state when dialog closes", () => {
    const clearResult = vi.fn();
    vi.mocked(useTestModel).mockReturnValue({
      testModel: vi.fn(),
      isPending: false,
      testingModelId: null,
      testResult: { success: true, message: "ok" },
      testedModelName: "gemini-3.0-pro",
      clearResult,
    } as unknown as ReturnType<typeof useTestModel>);

    render(
      <ProviderSection
        provider="google"
        credentials={[credentialFixture]}
        models={[modelFixture]}
        defaults={defaultsFixture}
        allCredentials={[credentialFixture]}
        encryptionReady={true}
      />,
    );

    fireEvent.click(screen.getByTestId("model-test-result-dialog"));
    expect(clearResult).toHaveBeenCalledTimes(1);
  });
});
