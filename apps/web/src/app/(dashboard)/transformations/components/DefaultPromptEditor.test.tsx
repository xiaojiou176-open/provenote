import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useDefaultPrompt, useUpdateDefaultPrompt } from "@/lib/hooks/use-transformations";
import { DefaultPromptEditor } from "./DefaultPromptEditor";

const mutate = vi.fn();

vi.mock("@/lib/hooks/use-transformations", () => ({
  useDefaultPrompt: vi.fn(),
  useUpdateDefaultPrompt: vi.fn(),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      transformations: {
        defaultPrompt: "Default Prompt",
        defaultPromptDesc: "Baseline instructions",
        defaultPromptPlaceholder: "Write default instructions",
      },
      common: {
        save: "Save",
      },
    },
  }),
}));

describe("DefaultPromptEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useDefaultPrompt).mockReturnValue({
      data: { transformation_instructions: "Initial instructions" },
      isLoading: false,
    } as unknown as ReturnType<typeof useDefaultPrompt>);

    vi.mocked(useUpdateDefaultPrompt).mockReturnValue({
      mutate,
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateDefaultPrompt>);
  });

  it("loads existing prompt and saves updated content", () => {
    render(<DefaultPromptEditor />);

    fireEvent.click(screen.getByText("Default Prompt"));

    const textarea = screen.getByRole("textbox", { name: "Default Prompt" });
    expect(textarea).toHaveValue("Initial instructions");

    fireEvent.change(textarea, { target: { value: "Refined default instructions" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(mutate).toHaveBeenCalledWith({
      transformation_instructions: "Refined default instructions",
    });
  });

  it("disables input and save when loading/pending", () => {
    vi.mocked(useDefaultPrompt).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as unknown as ReturnType<typeof useDefaultPrompt>);

    vi.mocked(useUpdateDefaultPrompt).mockReturnValue({
      mutate,
      isPending: true,
    } as unknown as ReturnType<typeof useUpdateDefaultPrompt>);

    render(<DefaultPromptEditor />);

    fireEvent.click(screen.getByText("Default Prompt"));

    expect(screen.getByRole("textbox", { name: "Default Prompt" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });
});
