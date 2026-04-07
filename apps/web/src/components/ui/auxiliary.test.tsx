import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ContextToggle } from "@/components/common/ContextToggle";
import { AddSourceButton } from "@/components/sources/AddSourceButton";
import { themeScript } from "@/lib/theme-script";
import { CheckboxList } from "./checkbox-list";
import { MarkdownEditor } from "./markdown-editor";
import { Toaster } from "./sonner";

vi.mock("@/components/sources/AddSourceDialog", () => ({
  AddSourceDialog: ({ open, defaultNotebookId }: { open: boolean; defaultNotebookId?: string }) => (
    <div data-testid="add-source-dialog">
      {String(open)}:{defaultNotebookId ?? "none"}
    </div>
  ),
}));

vi.mock("next/dynamic", () => ({
  default: () =>
    function MockMarkdownEditor(props: Record<string, unknown>) {
      return <div data-testid="dynamic-markdown-editor">{JSON.stringify(props)}</div>;
    },
}));

vi.mock("sonner", () => ({
  Toaster: (props: Record<string, unknown>) => (
    <div data-testid="sonner-toaster">{JSON.stringify(props)}</div>
  ),
}));

vi.mock("@/lib/stores/theme-store", () => ({
  useThemeStore: (selector: (state: { theme: string; getSystemTheme: () => string }) => unknown) =>
    selector({
      theme: "system",
      getSystemTheme: () => "dark",
    }),
}));

describe("auxiliary ui modules", () => {
  it("cycles context toggle modes based on insight availability", () => {
    const onChange = vi.fn();

    render(<ContextToggle hasInsights mode="off" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: "Not included in chat" }));
    expect(onChange).toHaveBeenCalledWith("insights");

    onChange.mockClear();
    render(<ContextToggle hasInsights={false} mode="off" onChange={onChange} />);
    fireEvent.click(screen.getAllByRole("button", { name: "Not included in chat" })[1]);
    expect(onChange).toHaveBeenCalledWith("full");
  });

  it("opens add-source dialog when button is pressed", () => {
    render(<AddSourceButton defaultNotebookId="nb-1" />);

    fireEvent.click(screen.getByRole("button", { name: "Add Source" }));

    expect(screen.getByTestId("add-source-dialog")).toHaveTextContent("true:nb-1");
  });

  it("renders checkbox list loading, empty, and populated states", () => {
    const onToggle = vi.fn();
    const { rerender } = render(
      <CheckboxList items={[]} loading onToggle={onToggle} selectedIds={[]} />,
    );
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");

    rerender(
      <CheckboxList emptyMessage="Nothing here" items={[]} onToggle={onToggle} selectedIds={[]} />,
    );
    expect(screen.getByText("Nothing here")).toBeInTheDocument();

    rerender(
      <CheckboxList
        items={[{ id: "a", title: "Alpha", description: "First" }]}
        onToggle={onToggle}
        selectedIds={[]}
      />,
    );
    fireEvent.click(screen.getByRole("checkbox"));
    expect(onToggle).toHaveBeenCalledWith("a");
  });

  it("passes effective theme props to toaster", () => {
    render(<Toaster richColors />);

    expect(screen.getByTestId("sonner-toaster")).toHaveTextContent('"theme":"dark"');
    expect(screen.getByTestId("sonner-toaster")).toHaveTextContent('"position":"bottom-right"');
  });

  it("renders markdown editor wrapper with forwarded props", () => {
    render(<MarkdownEditor height={480} name="content" placeholder="Write here" value="hello" />);

    expect(screen.getByTestId("dynamic-markdown-editor")).toHaveTextContent('"height":480');
    expect(screen.getByTestId("dynamic-markdown-editor")).toHaveTextContent(
      '"data-color-mode":"light"',
    );
  });

  it("contains the expected theme hydration fallback logic", () => {
    expect(themeScript).toContain("localStorage.getItem('theme-storage')");
    expect(themeScript).toContain("prefers-color-scheme: dark");
    expect(themeScript).toContain("document.documentElement.setAttribute('data-theme', 'light')");
  });
});
