import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AddSourceDialog } from "./AddSourceDialog";

const mutateAsyncMock = vi.fn();
let createSourcePending = false;
const toastSuccessMock = vi.fn();
const toastErrorMock = vi.fn();
const toastWarningMock = vi.fn();
const notebooksData = [{ id: "nb-1", name: "Notebook 1" }];
const transformationsData = [
  { id: "tr-default", title: "Default", description: "d", apply_default: true },
  { id: "tr-manual", title: "Manual", description: "m", apply_default: false },
];
const settingsData = { default_embedding_option: "ask" as const };
const notebooksHookMock = vi.fn();
const transformationsHookMock = vi.fn();
const settingsHookMock = vi.fn();
let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

const createFileList = (files: File[]) => {
  const fileList = {
    ...files,
    length: files.length,
    item: (index: number) => files[index] ?? null,
  };
  Object.setPrototypeOf(fileList, FileList.prototype);
  return fileList as unknown as FileList;
};

const parseAndValidateUrlsMock = vi.fn((text: string) => {
  const urls = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const valid: string[] = [];
  const invalid: Array<{ url: string; line: number }> = [];

  urls.forEach((url, index) => {
    if (url.startsWith("https://")) {
      valid.push(url);
    } else {
      invalid.push({ url, line: index + 1 });
    }
  });

  return { valid, invalid };
});

const t = {
  common: {
    cancel: "Cancel",
    back: "Back",
    next: "Next",
    done: "Done",
    adding: "Adding",
    processing: "Processing",
    completed: "Completed",
    failed: "Failed",
    current: "Current",
    error: "Error",
  },
  navigation: {
    notebooks: "Notebooks",
    process: "Process",
  },
  notebooks: {
    searchPlaceholder: "Search notebook",
  },
  sources: {
    addSource: "Add source",
    addNew: "Add new source",
    processDescription: "Source processing",
    processingFiles: "Processing files",
    statusProcessing: "Processing status",
    processingBatchSources: "Processing {count} batch sources",
    processingSource: "Processing source",
    submittingSource: "Submitting source",
    batchSuccess: "Batch success: {count}",
    batchFailed: "Batch failed: {count}",
    batchPartial: "Batch partial success={success} failed={failed}",
  },
};

vi.mock("sonner", () => ({
  toast: {
    success: (...args: unknown[]) => toastSuccessMock(...args),
    error: (...args: unknown[]) => toastErrorMock(...args),
    warning: (...args: unknown[]) => toastWarningMock(...args),
  },
}));

vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({ open, children }: { open: boolean; children: ReactNode }) =>
    open ? <div>{children}</div> : null,
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
}));

vi.mock("@/components/ui/wizard-container", () => ({
  WizardContainer: ({
    children,
    steps,
    onStepClick,
  }: {
    children: ReactNode;
    steps: Array<{ number: number }>;
    onStepClick?: (step: number) => void;
  }) => (
    <div>
      {steps.map((step) => (
        <button key={step.number} onClick={() => onStepClick?.(step.number)} type="button">
          go-step-{step.number}
        </button>
      ))}
      {children}
    </div>
  ),
}));

vi.mock("./steps/NotebooksStep", () => ({
  NotebooksStep: ({ onToggleNotebook }: { onToggleNotebook: (notebookId: string) => void }) => (
    <div data-testid="step-notebooks">
      notebooks-step
      <button onClick={() => onToggleNotebook("nb-1")} type="button">
        toggle-notebook
      </button>
    </div>
  ),
}));

vi.mock("./steps/ProcessingStep", () => ({
  ProcessingStep: ({
    onToggleTransformation,
  }: {
    onToggleTransformation: (transformationId: string) => void;
  }) => (
    <div data-testid="step-processing">
      processing-step
      <button onClick={() => onToggleTransformation("tr-default")} type="button">
        toggle-default-transformation
      </button>
      <button onClick={() => onToggleTransformation("tr-manual")} type="button">
        toggle-manual-transformation
      </button>
    </div>
  ),
}));

vi.mock("./steps/SourceTypeStep", () => ({
  parseAndValidateUrls: (...args: unknown[]) => parseAndValidateUrlsMock(...args),
  SourceTypeStep: ({
    setValue,
    urlValidationErrors,
    onClearUrlErrors,
  }: {
    setValue: (name: string, value: unknown) => void;
    urlValidationErrors?: Array<{ url: string; line: number }>;
    onClearUrlErrors?: () => void;
  }) => (
    <div>
      <button
        type="button"
        onClick={() => {
          setValue("type", "link");
          setValue("url", "https://example.com");
          setValue("title", "");
        }}
      >
        set-link-valid
      </button>
      <button
        type="button"
        onClick={() => {
          setValue("type", "link");
          setValue("url", "not-a-url");
        }}
      >
        set-link-invalid
      </button>
      <button
        type="button"
        onClick={() => {
          setValue("type", "link");
          setValue("url", "https://one.dev\nhttps://two.dev");
        }}
      >
        set-link-batch
      </button>
      <button
        type="button"
        onClick={() => {
          setValue("type", "text");
          setValue("title", "");
          setValue("content", "content");
        }}
      >
        set-text-invalid
      </button>
      <button
        type="button"
        onClick={() => {
          setValue("type", "text");
          setValue("title", "My text source");
          setValue("content", "content");
        }}
      >
        set-text-valid
      </button>
      <button
        type="button"
        onClick={() => {
          setValue("type", "upload");
          setValue(
            "file",
            createFileList([new File(["demo"], "demo.txt", { type: "text/plain" })]),
          );
          setValue("title", "Upload source");
        }}
      >
        set-upload-valid
      </button>
      <button
        type="button"
        onClick={() => {
          setValue("url", "https://still-valid.dev\nhttps://another-valid.dev\nnot-a-url");
        }}
      >
        set-link-mixed
      </button>
      <button
        type="button"
        onClick={() => {
          setValue("type", "upload");
          setValue(
            "file",
            createFileList([
              new File(["a"], "a.txt", { type: "text/plain" }),
              new File(["b"], "b.txt", { type: "text/plain" }),
            ]),
          );
          setValue("title", "Batch upload");
        }}
      >
        set-upload-batch
      </button>
      <button
        type="button"
        onClick={() => {
          setValue("type", "upload");
          setValue("file", createFileList([]));
        }}
      >
        set-upload-empty
      </button>
      <button onClick={onClearUrlErrors} type="button">
        clear-url-errors
      </button>
      <div data-testid="url-errors-count">{urlValidationErrors?.length ?? 0}</div>
    </div>
  ),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t }),
}));

vi.mock("@/lib/hooks/use-notebooks", () => ({
  useNotebooks: () => notebooksHookMock(),
}));

vi.mock("@/lib/hooks/use-transformations", () => ({
  useTransformations: () => transformationsHookMock(),
}));

vi.mock("@/lib/hooks/use-settings", () => ({
  useSettings: () => settingsHookMock(),
}));

vi.mock("@/lib/hooks/use-sources", () => ({
  useCreateSource: () => ({
    mutateAsync: (...args: unknown[]) => mutateAsyncMock(...args),
    isPending: createSourcePending,
  }),
}));

describe("AddSourceDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    notebooksHookMock.mockReturnValue({ data: notebooksData, isLoading: false });
    transformationsHookMock.mockReturnValue({
      data: transformationsData,
      isLoading: false,
    });
    settingsHookMock.mockReturnValue({
      data: settingsData,
    });
    createSourcePending = false;
    vi.useRealTimers();
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("walks through steps and submits single source", async () => {
    mutateAsyncMock.mockResolvedValue({ id: "source-1" });
    const onOpenChange = vi.fn();

    render(<AddSourceDialog open onOpenChange={onOpenChange} defaultNotebookId="nb-default" />);

    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "set-link-valid" }));
    expect(screen.getByRole("button", { name: "Next" })).not.toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByTestId("step-notebooks")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByTestId("step-processing")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Done" }));

    await waitFor(() => {
      expect(mutateAsyncMock).toHaveBeenCalledWith({
        type: "link",
        notebooks: ["nb-default"],
        url: "https://example.com",
        content: undefined,
        title: "",
        transformations: ["tr-default"],
        embed: true,
        delete_source: false,
        async_processing: true,
      });
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it("blocks step transition when url validation fails", async () => {
    render(<AddSourceDialog open onOpenChange={vi.fn()} defaultNotebookId="nb-default" />);

    fireEvent.click(screen.getByRole("button", { name: "set-link-invalid" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(screen.queryByTestId("step-notebooks")).not.toBeInTheDocument();
    expect(screen.getByTestId("url-errors-count")).toHaveTextContent("1");
  });

  it("handles batch submit with partial failures and warns user", async () => {
    mutateAsyncMock
      .mockResolvedValueOnce({ id: "source-1" })
      .mockRejectedValueOnce(new Error("second failed"));

    const onOpenChange = vi.fn();
    render(<AddSourceDialog open onOpenChange={onOpenChange} defaultNotebookId="nb-default" />);

    fireEvent.click(screen.getByRole("button", { name: "set-link-batch" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Done" }));

    await waitFor(() => {
      expect(mutateAsyncMock).toHaveBeenCalledTimes(2);
      expect(mutateAsyncMock).toHaveBeenNthCalledWith(
        1,
        expect.objectContaining({ type: "link", url: "https://one.dev" }),
      );
      expect(mutateAsyncMock).toHaveBeenNthCalledWith(
        2,
        expect.objectContaining({ type: "link", url: "https://two.dev" }),
      );
      expect(toastWarningMock).toHaveBeenCalledWith("Batch partial success=1 failed=1");
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it("validates text mode title and allows submit after title is set", async () => {
    mutateAsyncMock.mockResolvedValue({ id: "source-text-1" });

    render(<AddSourceDialog open onOpenChange={vi.fn()} defaultNotebookId="nb-default" />);

    fireEvent.click(screen.getByRole("button", { name: "set-text-invalid" }));
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "set-text-valid" }));
    expect(screen.getByRole("button", { name: "Next" })).not.toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Done" }));

    await waitFor(() => {
      expect(mutateAsyncMock).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "text",
          title: "My text source",
          content: "content",
        }),
      );
    });
  });

  it("submits upload source and includes uploaded file", async () => {
    mutateAsyncMock.mockResolvedValue({ id: "source-upload-1" });

    render(<AddSourceDialog open onOpenChange={vi.fn()} defaultNotebookId="nb-default" />);

    fireEvent.click(screen.getByRole("button", { name: "set-upload-valid" }));
    expect(screen.getByRole("button", { name: "Next" })).not.toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Done" }));

    await waitFor(() => {
      expect(mutateAsyncMock).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "upload",
          file: expect.any(File),
        }),
      );
    });
  });

  it("shows processing view while batch submission is in progress", async () => {
    let resolveFirst: (() => void) | null = null;
    const firstPending = new Promise<void>((resolve) => {
      resolveFirst = resolve;
    });

    mutateAsyncMock.mockImplementationOnce(() => firstPending).mockResolvedValueOnce({});

    render(<AddSourceDialog open onOpenChange={vi.fn()} defaultNotebookId="nb-default" />);

    fireEvent.click(screen.getByRole("button", { name: "set-link-batch" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Done" }));

    expect(await screen.findAllByText("Processing files")).toHaveLength(2);
    expect(screen.getByText("0 / 2")).toBeInTheDocument();

    resolveFirst?.();
    await waitFor(() => {
      expect(mutateAsyncMock).toHaveBeenCalledTimes(2);
    });
  });

  it("handles upload batch full failures and shows batch failed summary", async () => {
    mutateAsyncMock.mockRejectedValue(new Error("upload failed"));
    const onOpenChange = vi.fn();

    render(<AddSourceDialog open onOpenChange={onOpenChange} defaultNotebookId="nb-default" />);

    fireEvent.click(screen.getByRole("button", { name: "set-upload-batch" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "toggle-notebook" }));
    fireEvent.click(screen.getByRole("button", { name: "go-step-3" }));
    fireEvent.click(screen.getByRole("button", { name: "Done" }));

    await waitFor(() => {
      expect(mutateAsyncMock).toHaveBeenCalledTimes(2);
      expect(mutateAsyncMock).toHaveBeenNthCalledWith(
        1,
        expect.objectContaining({
          type: "upload",
          file: expect.any(File),
          notebooks: ["nb-default", "nb-1"],
        }),
      );
      expect(mutateAsyncMock).toHaveBeenNthCalledWith(
        2,
        expect.objectContaining({
          type: "upload",
          file: expect.any(File),
          notebooks: ["nb-default", "nb-1"],
        }),
      );
      expect(toastErrorMock).toHaveBeenCalledWith("Batch failed: 2");
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it("clears URL validation errors and keeps upload next disabled for empty file list", () => {
    render(<AddSourceDialog open onOpenChange={vi.fn()} defaultNotebookId="nb-default" />);

    fireEvent.click(screen.getByRole("button", { name: "set-link-invalid" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByTestId("url-errors-count")).toHaveTextContent("1");

    fireEvent.click(screen.getByRole("button", { name: "clear-url-errors" }));
    expect(screen.getByTestId("url-errors-count")).toHaveTextContent("0");

    fireEvent.click(screen.getByRole("button", { name: "set-upload-empty" }));
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  it("returns from processing view after submit error timeout", async () => {
    mutateAsyncMock.mockRejectedValue(new Error("submit failed"));

    render(<AddSourceDialog open onOpenChange={vi.fn()} defaultNotebookId="nb-default" />);

    fireEvent.click(screen.getByRole("button", { name: "set-link-valid" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Done" }));

    await waitFor(() => {
      expect(screen.getByText("Error")).toBeInTheDocument();
    });

    await waitFor(
      () => {
        expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
      },
      { timeout: 4000 },
    );
  });

  it("shows busy done CTA when mutation is pending", () => {
    createSourcePending = true;
    render(<AddSourceDialog open onOpenChange={vi.fn()} defaultNotebookId="nb-default" />);

    fireEvent.click(screen.getByRole("button", { name: "set-link-valid" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    const doneButton = screen.getByRole("button", { name: "Adding" });
    expect(doneButton).toBeDisabled();
    expect(doneButton).toHaveAttribute("aria-busy", "true");
  });

  it("resets wizard step after timeout error and close", async () => {
    mutateAsyncMock.mockRejectedValue(new Error("submit failed"));
    const onOpenChange = vi.fn();

    render(<AddSourceDialog open onOpenChange={onOpenChange} defaultNotebookId="nb-default" />);

    fireEvent.click(screen.getByRole("button", { name: "set-link-valid" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "go-step-3" }));
    fireEvent.click(screen.getByRole("button", { name: "Done" }));

    await waitFor(() => {
      expect(screen.getByText("Error")).toBeInTheDocument();
    });
    await waitFor(
      () => {
        expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
      },
      { timeout: 4000 },
    );
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  it("closes dialog correctly when no default transformations are available", () => {
    transformationsHookMock.mockReturnValue({
      data: [],
      isLoading: false,
    });

    const onOpenChange = vi.fn();
    render(<AddSourceDialog open onOpenChange={onOpenChange} defaultNotebookId="nb-default" />);

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
