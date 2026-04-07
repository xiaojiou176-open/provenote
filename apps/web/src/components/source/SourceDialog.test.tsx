import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SourceDialog } from "./SourceDialog";

vi.mock("./SourceDetailContent", () => ({
  SourceDetailContent: ({
    sourceId,
    onChatClick,
    onClose,
  }: {
    sourceId: string;
    onChatClick?: () => void;
    onClose?: () => void;
  }) => (
    <div data-testid="source-detail-content" data-source-id={sourceId}>
      <button onClick={onChatClick} type="button">
        trigger-chat
      </button>
      <button onClick={onClose} type="button">
        trigger-close
      </button>
    </div>
  ),
}));

describe("SourceDialog", () => {
  const originalWindowOpen = window.open;
  const windowOpenSpy = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    window.open = windowOpenSpy as unknown as typeof window.open;
  });

  afterEach(() => {
    window.open = originalWindowOpen;
  });

  it("returns null when source id is missing", () => {
    const { container } = render(<SourceDialog open onOpenChange={vi.fn()} sourceId={null} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("normalizes source id and opens source chat route in new tab", () => {
    render(<SourceDialog open onOpenChange={vi.fn()} sourceId="abc-123" />);

    expect(screen.getByTestId("source-detail-content")).toHaveAttribute(
      "data-source-id",
      "source:abc-123",
    );

    fireEvent.click(screen.getByRole("button", { name: "trigger-chat" }));

    expect(windowOpenSpy).toHaveBeenCalledWith("/sources/source:abc-123", "_blank");
  });

  it("keeps prefixed source id and closes via child callback", () => {
    const onOpenChange = vi.fn();
    render(<SourceDialog open onOpenChange={onOpenChange} sourceId="source:xyz" />);

    expect(screen.getByTestId("source-detail-content")).toHaveAttribute(
      "data-source-id",
      "source:xyz",
    );

    fireEvent.click(screen.getByRole("button", { name: "trigger-close" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("supports keyboard close through Escape", async () => {
    const onOpenChange = vi.fn();
    render(<SourceDialog open onOpenChange={onOpenChange} sourceId="source:key-1" />);

    fireEvent.keyDown(document, { key: "Escape" });

    await waitFor(() => {
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });
});
