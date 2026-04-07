import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ThemeToggle } from "./ThemeToggle";

const hoisted = vi.hoisted(() => ({
  setThemeMock: vi.fn(),
}));

vi.mock("@/lib/stores/theme-store", () => ({
  useTheme: () => ({
    theme: "dark",
    setTheme: hoisted.setThemeMock,
  }),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      common: {
        theme: "Theme",
        light: "Light",
        dark: "Dark",
        system: "System",
      },
      navigation: {
        theme: "Theme settings",
      },
    },
  }),
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" {...props}>
      {children}
    </button>
  ),
}));

vi.mock("@/components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuItem: ({
    children,
    className,
    onClick,
  }: {
    children: React.ReactNode;
    className?: string;
    onClick?: () => void;
  }) => (
    <button className={className} onClick={onClick} type="button">
      {children}
    </button>
  ),
}));

describe("ThemeToggle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("marks the active theme and switches theme on click", () => {
    render(<ThemeToggle />);

    expect(screen.getByText("Theme")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dark" })).toHaveClass(
      "bg-accent",
      "text-accent-foreground",
    );

    fireEvent.click(screen.getByRole("button", { name: "System" }));
    expect(hoisted.setThemeMock).toHaveBeenCalledWith("system");
  });

  it("supports icon-only mode and allows switching light/dark directly", () => {
    render(<ThemeToggle iconOnly />);

    expect(screen.queryByText("Theme")).not.toBeInTheDocument();
    expect(screen.getByText("Theme settings")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Light" }));
    fireEvent.click(screen.getByRole("button", { name: "Dark" }));

    expect(hoisted.setThemeMock).toHaveBeenNthCalledWith(1, "light");
    expect(hoisted.setThemeMock).toHaveBeenNthCalledWith(2, "dark");
  });
});
