import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  useCreateCredential,
  useDeleteCredential,
  useDiscoverModels,
  useRegisterModels,
  useUpdateCredential,
} from "@/lib/hooks/use-credentials";
import { CredentialFormDialog, DeleteCredentialDialog, DiscoverModelsDialog } from "./dialogs";

vi.mock("@/lib/hooks/use-credentials");

const credentialFixture = {
  id: "cred-1",
  name: "Prod key",
  provider: "google",
  modalities: ["language"],
  has_api_key: true,
  created: "2026-01-01T00:00:00Z",
  updated: "2026-01-01T00:00:00Z",
  model_count: 0,
};

describe("CredentialFormDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useDiscoverModels).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useDiscoverModels>);
    vi.mocked(useRegisterModels).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useRegisterModels>);
    vi.mocked(useDeleteCredential).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteCredential>);
  });

  it("enforces required fields and submits create payload", () => {
    const onOpenChange = vi.fn();
    const createMutate = vi.fn((_data, options) => options?.onSuccess?.());

    vi.mocked(useCreateCredential).mockReturnValue({
      mutate: createMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateCredential>);

    vi.mocked(useUpdateCredential).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateCredential>);

    render(<CredentialFormDialog open onOpenChange={onOpenChange} provider="google" />);

    const submitButton = screen.getByRole("button", { name: "Add Configuration" });
    expect(submitButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Configuration Name"), {
      target: { value: "Prod key" },
    });
    fireEvent.change(screen.getByLabelText("API Key"), {
      target: { value: "sk-secret" },
    });

    expect(submitButton).toBeEnabled();
    fireEvent.click(submitButton);

    expect(createMutate).toHaveBeenCalledTimes(1);
    expect(createMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Prod key",
        provider: "google",
        api_key: "sk-secret",
      }),
      expect.any(Object),
    );
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("toggles API key visibility", () => {
    vi.mocked(useCreateCredential).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateCredential>);

    vi.mocked(useUpdateCredential).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateCredential>);

    render(<CredentialFormDialog open onOpenChange={vi.fn()} provider="google" />);

    const apiKeyInput = screen.getByLabelText("API Key");
    expect(apiKeyInput).toHaveAttribute("type", "password");

    fireEvent.click(screen.getByRole("button", { name: "Show API key" }));
    expect(apiKeyInput).toHaveAttribute("type", "text");

    fireEvent.click(screen.getByRole("button", { name: "Hide API key" }));
    expect(apiKeyInput).toHaveAttribute("type", "password");
  });

  it("renders provider docs link for api-key based providers", () => {
    vi.mocked(useCreateCredential).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateCredential>);

    vi.mocked(useUpdateCredential).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateCredential>);

    render(<CredentialFormDialog open onOpenChange={vi.fn()} provider="google" />);

    expect(screen.getByRole("link", { name: "Get API Key →" })).toHaveAttribute(
      "href",
      "https://aistudio.google.com/app/apikey",
    );
  });

  it("submits only changed fields in edit mode", () => {
    const onOpenChange = vi.fn();
    const updateMutate = vi.fn((_data, options) => options?.onSuccess?.());

    vi.mocked(useCreateCredential).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateCredential>);

    vi.mocked(useUpdateCredential).mockReturnValue({
      mutate: updateMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateCredential>);

    render(
      <CredentialFormDialog
        open
        onOpenChange={onOpenChange}
        provider="google"
        credential={{
          id: "cred-1",
          name: "Old name",
          provider: "google",
          modalities: ["language"],
          has_api_key: true,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-01T00:00:00Z",
          model_count: 0,
        }}
      />,
    );

    fireEvent.change(screen.getByLabelText("Configuration Name"), {
      target: { value: "New name" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(updateMutate).toHaveBeenCalledWith(
      {
        credentialId: "cred-1",
        data: { name: "New name" },
      },
      expect.any(Object),
    );
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("keeps actions disabled while submit is pending", () => {
    vi.mocked(useCreateCredential).mockReturnValue({
      mutate: vi.fn(),
      isPending: true,
    } as unknown as ReturnType<typeof useCreateCredential>);

    vi.mocked(useUpdateCredential).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateCredential>);

    render(<CredentialFormDialog open onOpenChange={vi.fn()} provider="google" />);

    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Add Configuration" })).toBeDisabled();
  });

  it("supports vertex provider fields without requiring an api key", () => {
    const createMutate = vi.fn((_data, options) => options?.onSuccess?.());

    vi.mocked(useCreateCredential).mockReturnValue({
      mutate: createMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateCredential>);

    vi.mocked(useUpdateCredential).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateCredential>);

    render(<CredentialFormDialog open onOpenChange={vi.fn()} provider="vertex" />);

    expect(screen.queryByLabelText("API Key")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Base URL")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Configuration Name"), {
      target: { value: "Vertex prod" },
    });
    fireEvent.change(screen.getByLabelText("GCP Project ID"), {
      target: { value: "gcp-project" },
    });
    fireEvent.change(screen.getByLabelText("Region"), {
      target: { value: "us-central1" },
    });
    fireEvent.change(screen.getByPlaceholderText("/path/to/service-account.json"), {
      target: { value: "/tmp/sa.json" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Add Configuration" }));

    expect(createMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Vertex prod",
        provider: "vertex",
        project: "gcp-project",
        location: "us-central1",
        credentials_path: "/tmp/sa.json",
      }),
      expect.any(Object),
    );
  });

  it("submits updated base url in edit mode", () => {
    const updateMutate = vi.fn((_data, options) => options?.onSuccess?.());

    vi.mocked(useCreateCredential).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateCredential>);

    vi.mocked(useUpdateCredential).mockReturnValue({
      mutate: updateMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateCredential>);

    render(
      <CredentialFormDialog
        open
        onOpenChange={vi.fn()}
        provider="google"
        credential={{
          ...credentialFixture,
          name: "Prod key",
          base_url: "https://old.example.com",
          modalities: ["language"],
        }}
      />,
    );

    fireEvent.change(screen.getByLabelText("Base URL"), {
      target: { value: "https://new.example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(updateMutate).toHaveBeenCalledWith(
      {
        credentialId: "cred-1",
        data: {
          base_url: "https://new.example.com",
        },
      },
      expect.any(Object),
    );
  });
});

describe("DiscoverModelsDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state while model discovery is pending", () => {
    vi.mocked(useDiscoverModels).mockReturnValue({
      mutate: vi.fn(),
      isPending: true,
    } as unknown as ReturnType<typeof useDiscoverModels>);

    vi.mocked(useRegisterModels).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useRegisterModels>);

    render(
      <DiscoverModelsDialog open onOpenChange={vi.fn()} credential={{ ...credentialFixture }} />,
    );

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("renders discovery error returned from hook callback", async () => {
    vi.mocked(useDiscoverModels).mockReturnValue({
      mutate: (_credentialId, options) => options?.onError?.(new Error("discover failed")),
      isPending: false,
    } as unknown as ReturnType<typeof useDiscoverModels>);

    vi.mocked(useRegisterModels).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useRegisterModels>);

    render(
      <DiscoverModelsDialog open onOpenChange={vi.fn()} credential={{ ...credentialFixture }} />,
    );

    expect(await screen.findByText("discover failed")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add (0)" })).toBeDisabled();
  });

  it("registers selected discovered models and closes dialog", async () => {
    const onOpenChange = vi.fn();
    const registerMutate = vi.fn((_payload, options) => options?.onSuccess?.());

    vi.mocked(useDiscoverModels).mockReturnValue({
      mutate: (_credentialId, options) =>
        options?.onSuccess?.({
          credential_id: "cred-1",
          provider: "google",
          discovered: [{ name: "gemini-3.0-pro", provider: "google", description: "Pro" }],
        }),
      isPending: false,
    } as unknown as ReturnType<typeof useDiscoverModels>);

    vi.mocked(useRegisterModels).mockReturnValue({
      mutate: registerMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useRegisterModels>);

    render(
      <DiscoverModelsDialog
        open
        onOpenChange={onOpenChange}
        credential={{ ...credentialFixture }}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("gemini-3.0-pro")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("checkbox")[0]);
    fireEvent.click(screen.getByRole("button", { name: "Add (1)" }));

    expect(registerMutate).toHaveBeenCalledWith(
      {
        credentialId: "cred-1",
        models: [
          {
            name: "gemini-3.0-pro",
            provider: "google",
            model_type: "language",
          },
        ],
      },
      expect.any(Object),
    );
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("adds a custom model when search query does not match discovered models", async () => {
    const registerMutate = vi.fn();

    vi.mocked(useDiscoverModels).mockReturnValue({
      mutate: (_credentialId, options) =>
        options?.onSuccess?.({
          credential_id: "cred-1",
          provider: "google",
          discovered: [{ name: "gemini-3.0-pro", provider: "google", description: "Pro" }],
        }),
      isPending: false,
    } as unknown as ReturnType<typeof useDiscoverModels>);

    vi.mocked(useRegisterModels).mockReturnValue({
      mutate: registerMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useRegisterModels>);

    render(
      <DiscoverModelsDialog open onOpenChange={vi.fn()} credential={{ ...credentialFixture }} />,
    );

    await screen.findByText("gemini-3.0-pro");

    fireEvent.change(screen.getByPlaceholderText("Search or type a model name..."), {
      target: { value: "custom-model-v1" },
    });
    fireEvent.click(screen.getByText('Add "custom-model-v1"'));
    fireEvent.click(screen.getByRole("button", { name: "Add (1)" }));

    expect(registerMutate).toHaveBeenCalledWith(
      {
        credentialId: "cred-1",
        models: [
          {
            name: "custom-model-v1",
            provider: "google",
            model_type: "language",
          },
        ],
      },
      expect.any(Object),
    );
  });

  it("toggles all discovered models on and off before registering", async () => {
    vi.mocked(useDiscoverModels).mockReturnValue({
      mutate: (_credentialId, options) =>
        options?.onSuccess?.({
          credential_id: "cred-1",
          provider: "google",
          discovered: [
            { name: "gemini-3.0-pro", provider: "google", description: "Pro" },
            { name: "gemini-3.0-flash", provider: "google", description: "Flash" },
          ],
        }),
      isPending: false,
    } as unknown as ReturnType<typeof useDiscoverModels>);

    vi.mocked(useRegisterModels).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useRegisterModels>);

    render(
      <DiscoverModelsDialog open onOpenChange={vi.fn()} credential={{ ...credentialFixture }} />,
    );

    await screen.findByText("gemini-3.0-pro");

    fireEvent.click(screen.getByRole("button", { name: "Add Selected (0/2)" }));
    expect(screen.getByRole("button", { name: "Add (2)" })).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: "Remove (2/2)" }));
    expect(screen.getByRole("button", { name: "Add (0)" })).toBeDisabled();
  });

  it("shows no results state when search is empty after discovery and keeps add disabled", async () => {
    vi.mocked(useDiscoverModels).mockReturnValue({
      mutate: (_credentialId, options) =>
        options?.onSuccess?.({
          credential_id: "cred-1",
          provider: "google",
          discovered: [],
        }),
      isPending: false,
    } as unknown as ReturnType<typeof useDiscoverModels>);

    vi.mocked(useRegisterModels).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useRegisterModels>);

    render(
      <DiscoverModelsDialog open onOpenChange={vi.fn()} credential={{ ...credentialFixture }} />,
    );

    expect(await screen.findByText("No models found from this provider")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add (0)" })).toBeDisabled();
  });

  it("disables register button and shows spinner while register is pending", async () => {
    vi.mocked(useDiscoverModels).mockReturnValue({
      mutate: (_credentialId, options) =>
        options?.onSuccess?.({
          credential_id: "cred-1",
          provider: "google",
          discovered: [{ name: "gemini-3.0-pro", provider: "google", description: "Pro" }],
        }),
      isPending: false,
    } as unknown as ReturnType<typeof useDiscoverModels>);

    vi.mocked(useRegisterModels).mockReturnValue({
      mutate: vi.fn(),
      isPending: true,
    } as unknown as ReturnType<typeof useRegisterModels>);

    render(
      <DiscoverModelsDialog open onOpenChange={vi.fn()} credential={{ ...credentialFixture }} />,
    );

    await screen.findByText("gemini-3.0-pro");
    fireEvent.click(screen.getAllByRole("checkbox")[0]);

    const addButton = screen.getByRole("button", { name: "Add (1)" });
    expect(addButton).toBeDisabled();
    expect(addButton.querySelector(".animate-spin")).not.toBeNull();
  });
});

describe("DeleteCredentialDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("deletes linked models when user confirms destructive action", () => {
    const onOpenChange = vi.fn();
    const deleteMutate = vi.fn((_data, options) => options?.onSuccess?.());

    vi.mocked(useDeleteCredential).mockReturnValue({
      mutate: deleteMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteCredential>);

    render(
      <DeleteCredentialDialog
        open
        onOpenChange={onOpenChange}
        credential={{
          id: "cred-1",
          name: "Prod key",
          provider: "google",
          modalities: ["language"],
          has_api_key: true,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-01T00:00:00Z",
          model_count: 2,
        }}
        allCredentials={[]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Delete with Models" }));

    expect(deleteMutate).toHaveBeenCalledWith(
      { credentialId: "cred-1", options: { delete_models: true } },
      expect.any(Object),
    );
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("deletes credential only when no linked models exist", () => {
    const onOpenChange = vi.fn();
    const deleteMutate = vi.fn((_data, options) => options?.onSuccess?.());

    vi.mocked(useDeleteCredential).mockReturnValue({
      mutate: deleteMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteCredential>);

    render(
      <DeleteCredentialDialog
        open
        onOpenChange={onOpenChange}
        credential={{ ...credentialFixture, model_count: 0 }}
        allCredentials={[]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    expect(deleteMutate).toHaveBeenCalledWith({ credentialId: "cred-1" }, expect.any(Object));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("migrates linked models to another credential before delete", () => {
    const deleteMutate = vi.fn((_data, options) => options?.onSuccess?.());
    const onOpenChange = vi.fn();

    vi.mocked(useDeleteCredential).mockReturnValue({
      mutate: deleteMutate,
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteCredential>);

    render(
      <DeleteCredentialDialog
        open
        onOpenChange={onOpenChange}
        credential={{ ...credentialFixture, model_count: 2 }}
        allCredentials={[
          credentialFixture,
          {
            ...credentialFixture,
            id: "cred-2",
            name: "Backup key",
          },
        ]}
      />,
    );

    fireEvent.click(screen.getByRole("combobox"));
    fireEvent.click(screen.getByRole("option", { name: "Backup key" }));
    fireEvent.click(screen.getByRole("button", { name: "Migrate & Delete" }));

    expect(deleteMutate).toHaveBeenCalledWith(
      {
        credentialId: "cred-1",
        options: { migrate_to: "cred-2" },
      },
      expect.any(Object),
    );
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("closes delete dialog when user cancels", () => {
    const onOpenChange = vi.fn();

    vi.mocked(useDeleteCredential).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteCredential>);

    render(
      <DeleteCredentialDialog
        open
        onOpenChange={onOpenChange}
        credential={{ ...credentialFixture, model_count: 1 }}
        allCredentials={[]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
