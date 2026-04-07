import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AdvancedModelsDialog } from "./AdvancedModelsDialog";

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      searchPage: {
        advancedModelTitle: "Advanced models",
        advancedModelDesc: "Tune the model stack",
        strategyModel: "Strategy",
        answerModel: "Answer",
        finalAnswerModel: "Final answer",
        selectStrategyPlaceholder: "Pick strategy",
        selectAnswerPlaceholder: "Pick answer",
        selectFinalPlaceholder: "Pick final answer",
        saveChanges: "Save changes",
      },
      common: {
        cancel: "Cancel",
      },
    },
  }),
}));

vi.mock("@/components/common/ModelSelector", () => ({
  ModelSelector: ({
    label,
    value,
    onChange,
  }: {
    label: string;
    value: string;
    onChange: (value: string) => void;
  }) => (
    <button onClick={() => onChange(`${value}-updated`)} type="button">
      {label}:{value}
    </button>
  ),
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, onClick, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({ open, children }: { open: boolean; children: React.ReactNode }) =>
    open ? <div>{children}</div> : null,
  DialogContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: React.ReactNode }) => <p>{children}</p>,
  DialogFooter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe("AdvancedModelsDialog", () => {
  it("updates model selections and saves the merged payload", () => {
    const onOpenChange = vi.fn();
    const onSave = vi.fn();

    render(
      <AdvancedModelsDialog
        open
        onOpenChange={onOpenChange}
        onSave={onSave}
        defaultModels={{
          strategy: "strategy-a",
          answer: "answer-a",
          finalAnswer: "final-a",
        }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Strategy:strategy-a" }));
    fireEvent.click(screen.getByRole("button", { name: "Answer:answer-a" }));
    fireEvent.click(screen.getByRole("button", { name: "Final answer:final-a" }));
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    expect(onSave).toHaveBeenCalledWith({
      strategy: "strategy-a-updated",
      answer: "answer-a-updated",
      finalAnswer: "final-a-updated",
    });
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
