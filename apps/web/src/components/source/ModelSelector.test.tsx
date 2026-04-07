import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useModelDefaults, useModels } from "@/lib/hooks/use-models";
import { useTranslation } from "@/lib/hooks/use-translation";
import { ModelSelector } from "./ModelSelector";

vi.mock("@/lib/hooks/use-models");
vi.mock("@/lib/hooks/use-translation");

vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  DialogFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/select", () => ({
  Select: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SelectTrigger: ({ children }: { children: ReactNode }) => (
    <button type="button">{children}</button>
  ),
  SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>,
  SelectContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

describe("Source ModelSelector", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useTranslation).mockReturnValue({
      t: {
        common: {
          default: "Default",
          modelConfiguration: "Model configuration",
          model: "Model",
          resetToDefault: "Reset",
          saveChanges: "Save changes",
        },
        transformations: {
          overrideModelDesc: "Override model",
          systemDefault: "System default",
          sessionUseReplacement: "Use {name}",
        },
        models: {
          selectModelPlaceholder: "Select model",
        },
      },
    } as unknown as ReturnType<typeof useTranslation>);

    vi.mocked(useModels).mockReturnValue({
      data: [
        { id: "m-1", name: "Gemini Fast", type: "language", provider: "google" },
        { id: "m-2", name: "Gemini Pro", type: "language", provider: "google" },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof useModels>);

    vi.mocked(useModelDefaults).mockReturnValue({
      data: { default_chat_model: "m-1" },
    } as unknown as ReturnType<typeof useModelDefaults>);
  });

  it("shows default model label when no override is selected", () => {
    render(<ModelSelector currentModel={undefined} onModelChange={vi.fn()} />);

    expect(screen.getByRole("button", { name: /Gemini Fast/i })).toBeInTheDocument();
  });

  it("saves current override and supports reset to default", () => {
    const onModelChange = vi.fn();

    render(<ModelSelector currentModel="m-2" onModelChange={onModelChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));
    expect(onModelChange).toHaveBeenCalledWith("m-2");

    fireEvent.click(screen.getByRole("button", { name: "Reset" }));
    expect(onModelChange).toHaveBeenCalledWith(undefined);
  });
});
