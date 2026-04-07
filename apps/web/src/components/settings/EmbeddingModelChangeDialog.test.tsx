import { fireEvent, render, screen } from "@testing-library/react";
import { act } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EmbeddingModelChangeDialog } from "./EmbeddingModelChangeDialog";

const hoisted = vi.hoisted(() => ({
  pushMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: hoisted.pushMock,
  }),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      models: {
        embeddingChangeTitle: "Change embedding model",
        embeddingChangeConfirm: "Change from {from} to {to}",
        rebuildRequired: "Rebuild required",
        rebuildReason: "Embeddings must be regenerated",
        whatHappensNext: "What happens next",
        step1: "Step 1",
        step2: "Step 2",
        step3: "Step 3",
        step4: "Step 4",
        proceedToRebuildPrompt: "Proceed?",
        changeModelOnly: "Change only",
        changeAndRebuild: "Change and rebuild",
      },
      common: {
        cancel: "Cancel",
      },
    },
  }),
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, onClick, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

vi.mock("@/components/ui/alert-dialog", () => ({
  AlertDialog: ({ open, children }: { open: boolean; children: React.ReactNode }) =>
    open ? <div>{children}</div> : null,
  AlertDialogContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: { children: React.ReactNode }) => <h2>{children}</h2>,
  AlertDialogDescription: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogFooter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogCancel: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" {...props}>
      {children}
    </button>
  ),
  AlertDialogAction: ({
    children,
    onClick,
    ...props
  }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

describe("EmbeddingModelChangeDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  it("confirms without rebuild and closes immediately", () => {
    const onConfirm = vi.fn();
    const onOpenChange = vi.fn();

    render(
      <EmbeddingModelChangeDialog
        open
        onOpenChange={onOpenChange}
        onConfirm={onConfirm}
        oldModelName="old-model"
        newModelName="new-model"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Change only" }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(hoisted.pushMock).not.toHaveBeenCalled();
  });

  it("redirects to advanced after confirm and rebuild", () => {
    const onConfirm = vi.fn();
    const onOpenChange = vi.fn();

    render(
      <EmbeddingModelChangeDialog
        open
        onOpenChange={onOpenChange}
        onConfirm={onConfirm}
        oldModelName="old-model"
        newModelName="new-model"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Change and rebuild" }));

    expect(onConfirm).toHaveBeenCalledTimes(1);

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(hoisted.pushMock).toHaveBeenCalledWith("/advanced");
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
