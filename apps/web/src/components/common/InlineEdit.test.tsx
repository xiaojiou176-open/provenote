import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { InlineEdit } from "./InlineEdit";

describe("InlineEdit", () => {
  it("enters edit mode and saves a changed value with Enter", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);

    render(<InlineEdit value="Original" onSave={onSave} />);

    fireEvent.click(screen.getByRole("button", { name: "Original" }));
    const input = screen.getByDisplayValue("Original");
    fireEvent.change(input, { target: { value: "Updated" } });
    fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith("Updated");
    });

    expect(screen.getByRole("button", { name: "Original" })).toBeInTheDocument();
  });

  it("cancels edits with Escape without calling onSave", () => {
    const onSave = vi.fn();

    render(<InlineEdit value="Original" onSave={onSave} />);

    fireEvent.click(screen.getByRole("button", { name: "Original" }));
    const input = screen.getByDisplayValue("Original");
    fireEvent.change(input, { target: { value: "Discarded" } });
    fireEvent.keyDown(input, { key: "Escape" });

    expect(onSave).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Original" })).toBeInTheDocument();
  });

  it("resets to the original value when multiline save fails", async () => {
    const onSave = vi.fn().mockRejectedValue(new Error("save failed"));

    render(<InlineEdit value="Original body" onSave={onSave} multiline />);

    fireEvent.click(screen.getByRole("button", { name: "Original body" }));
    const textarea = screen.getByDisplayValue("Original body");
    fireEvent.change(textarea, { target: { value: "Broken body" } });
    fireEvent.blur(textarea);

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith("Broken body");
    });

    expect(screen.getByDisplayValue("Original body")).toHaveAttribute("aria-invalid", "true");
  });

  it("closes edit mode without saving when value is unchanged via Enter or blur", () => {
    const onSave = vi.fn();

    const { rerender } = render(<InlineEdit value="Same value" onSave={onSave} />);

    fireEvent.click(screen.getByRole("button", { name: "Same value" }));
    const input = screen.getByDisplayValue("Same value");
    fireEvent.keyDown(input, { key: "Enter" });

    expect(onSave).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Same value" })).toBeInTheDocument();

    rerender(<InlineEdit value="Body text" onSave={onSave} multiline />);
    fireEvent.click(screen.getByRole("button", { name: "Body text" }));
    const textarea = screen.getByDisplayValue("Body text");
    fireEvent.blur(textarea);

    expect(onSave).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Body text" })).toBeInTheDocument();
  });
});
