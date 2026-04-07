import { fireEvent, render, screen } from "@testing-library/react";
import { PanelLeft } from "lucide-react";
import { describe, expect, it, vi } from "vitest";
import { CollapsibleColumn, createCollapseButton } from "./CollapsibleColumn";

describe("CollapsibleColumn", () => {
  it("renders collapsed vertical trigger and toggles via click", () => {
    const onToggle = vi.fn();

    render(
      <CollapsibleColumn
        isCollapsed
        onToggle={onToggle}
        collapsedIcon={PanelLeft}
        collapsedLabel="Notes"
      >
        <div>children</div>
      </CollapsibleColumn>,
    );

    const trigger = screen.getByRole("button", { name: "Expand Notes" });
    fireEvent.click(trigger);
    expect(onToggle).toHaveBeenCalledTimes(1);
    expect(trigger).toHaveAttribute("aria-label", "Expand Notes");
  });

  it("renders children when expanded", () => {
    render(
      <CollapsibleColumn
        isCollapsed={false}
        onToggle={() => undefined}
        collapsedIcon={PanelLeft}
        collapsedLabel="Notes"
      >
        <div data-testid="expanded-content">expanded</div>
      </CollapsibleColumn>,
    );

    expect(screen.getByTestId("expanded-content")).toHaveTextContent("expanded");
  });

  it("factory collapse button stops propagation and toggles", () => {
    const onToggle = vi.fn();
    const parentClick = vi.fn();

    render(<div onClick={parentClick}>{createCollapseButton(onToggle, "Sources")}</div>);

    fireEvent.click(screen.getByRole("button", { name: "Collapse Sources" }));
    expect(onToggle).toHaveBeenCalledTimes(1);
    expect(parentClick).not.toHaveBeenCalled();
  });
});
