import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { toast } from "sonner";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useCreateNote } from "@/lib/hooks/use-notes";
import { useTranslation } from "@/lib/hooks/use-translation";
import { MessageActions } from "./MessageActions";

const mutate = vi.fn();
const writeText = vi.fn();
let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/lib/hooks/use-notes");
vi.mock("@/lib/hooks/use-translation");

vi.mock("@/components/ui/tooltip", () => ({
  TooltipProvider: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  Tooltip: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  TooltipTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  TooltipContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

describe("MessageActions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);

    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        common: {
          saveToNote: "Save to note",
          copyToClipboard: "Copy",
          error: "Error",
        },
        sources: {
          cannotSaveNoteNoNotebook: "Notebook missing",
        },
      },
    } as unknown as ReturnType<typeof useTranslation>);

    vi.mocked(useCreateNote).mockReturnValue({
      mutate,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateNote>);
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("saves ai message to notebook", () => {
    render(<MessageActions content="hello" notebookId="nb-1" />);

    fireEvent.click(screen.getByRole("button", { name: "Save to note" }));

    expect(mutate).toHaveBeenCalledWith({
      content: "hello",
      note_type: "ai",
      notebook_id: "nb-1",
    });
  });

  it("copies content to clipboard and shows success toast", async () => {
    writeText.mockResolvedValue(undefined);

    render(<MessageActions content="copy me" notebookId="nb-1" />);

    fireEvent.click(screen.getByRole("button", { name: "Copy" }));

    await waitFor(() => {
      expect(writeText).toHaveBeenCalledWith("copy me");
      expect(toast.success).toHaveBeenCalledWith("Copy");
    });
  });

  it("shows an error toast when saving without a notebook id", () => {
    render(<MessageActions content="orphan answer" />);

    fireEvent.click(screen.getByRole("button", { name: "Save to note" }));

    expect(toast.error).toHaveBeenCalledWith("Notebook missing");
  });

  it("falls back to execCommand copy when clipboard api is unavailable", async () => {
    const execCommandMock = vi.fn(() => true);
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommandMock,
    });
    Object.defineProperty(globalThis.navigator, "clipboard", {
      value: undefined,
      configurable: true,
    });

    render(<MessageActions content="legacy copy" notebookId="nb-1" />);
    fireEvent.click(screen.getByRole("button", { name: "Copy" }));

    await waitFor(() => {
      expect(execCommandMock).toHaveBeenCalledWith("copy");
      expect(toast.success).toHaveBeenCalledWith("Copy");
    });
  });

  it("shows error toast when clipboard copy fails", async () => {
    writeText.mockRejectedValue(new Error("denied"));

    render(<MessageActions content="copy failure" notebookId="nb-1" />);
    fireEvent.click(screen.getByRole("button", { name: "Copy" }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Error");
    });
  });
});
