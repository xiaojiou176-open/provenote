import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LanguageToggle } from "./LanguageToggle";

const hoisted = vi.hoisted(() => ({
  language: "zh-Hans",
  setLanguageMock: vi.fn(),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    language: hoisted.language,
    setLanguage: hoisted.setLanguageMock,
    t: {
      common: {
        language: "Language",
        english: "English",
        chinese: "Chinese",
        traditionalChinese: "Traditional Chinese",
        portuguese: "Portuguese",
        japanese: "Japanese",
        french: "French",
        russian: "Russian",
        bengali: "Bengali",
      },
      navigation: {
        language: "Language settings",
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

describe("LanguageToggle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.language = "zh-Hans";
  });

  it("highlights simplified Chinese and switches to another locale", () => {
    render(<LanguageToggle />);

    expect(screen.getByText("Language")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Chinese" })).toHaveClass("bg-accent");

    fireEvent.click(screen.getByRole("button", { name: "French" }));
    expect(hoisted.setLanguageMock).toHaveBeenCalledWith("fr-FR");
  });

  it("covers iconOnly mode and the remaining locale highlighting branches", () => {
    const { rerender } = render(<LanguageToggle iconOnly />);

    expect(screen.queryByText("Language")).not.toBeInTheDocument();
    expect(screen.getByText("Language settings")).toBeInTheDocument();

    hoisted.language = "en-US";
    rerender(<LanguageToggle iconOnly />);
    expect(screen.getByRole("button", { name: "English" })).toHaveClass("bg-accent");

    hoisted.language = "zh-TW";
    rerender(<LanguageToggle iconOnly />);
    expect(screen.getByRole("button", { name: "Traditional Chinese" })).toHaveClass("bg-accent");

    hoisted.language = "pt-BR";
    rerender(<LanguageToggle iconOnly />);
    expect(screen.getByRole("button", { name: "Portuguese" })).toHaveClass("bg-accent");

    hoisted.language = "ja-JP";
    rerender(<LanguageToggle iconOnly />);
    expect(screen.getByRole("button", { name: "Japanese" })).toHaveClass("bg-accent");

    hoisted.language = "ru-RU";
    rerender(<LanguageToggle iconOnly />);
    expect(screen.getByRole("button", { name: "Russian" })).toHaveClass("bg-accent");

    hoisted.language = "bn-IN";
    rerender(<LanguageToggle iconOnly />);
    expect(screen.getByRole("button", { name: "Bengali" })).toHaveClass("bg-accent");
  });

  it("dispatches every locale action and falls back to English when language is empty", () => {
    hoisted.language = "";
    render(<LanguageToggle />);

    expect(screen.getByRole("button", { name: "English" })).toHaveClass("bg-accent");

    fireEvent.click(screen.getByRole("button", { name: "English" }));
    fireEvent.click(screen.getByRole("button", { name: "Chinese" }));
    fireEvent.click(screen.getByRole("button", { name: "Traditional Chinese" }));
    fireEvent.click(screen.getByRole("button", { name: "Portuguese" }));
    fireEvent.click(screen.getByRole("button", { name: "Japanese" }));
    fireEvent.click(screen.getByRole("button", { name: "Russian" }));
    fireEvent.click(screen.getByRole("button", { name: "Bengali" }));

    expect(hoisted.setLanguageMock).toHaveBeenNthCalledWith(1, "en-US");
    expect(hoisted.setLanguageMock).toHaveBeenNthCalledWith(2, "zh-CN");
    expect(hoisted.setLanguageMock).toHaveBeenNthCalledWith(3, "zh-TW");
    expect(hoisted.setLanguageMock).toHaveBeenNthCalledWith(4, "pt-BR");
    expect(hoisted.setLanguageMock).toHaveBeenNthCalledWith(5, "ja-JP");
    expect(hoisted.setLanguageMock).toHaveBeenNthCalledWith(6, "ru-RU");
    expect(hoisted.setLanguageMock).toHaveBeenNthCalledWith(7, "bn-IN");
  });

  it("matches locale prefixes for highlighting", () => {
    const { rerender } = render(<LanguageToggle />);

    hoisted.language = "en-GB";
    rerender(<LanguageToggle />);
    expect(screen.getByRole("button", { name: "English" })).toHaveClass("bg-accent");

    hoisted.language = "fr-CA";
    rerender(<LanguageToggle />);
    expect(screen.getByRole("button", { name: "French" })).toHaveClass("bg-accent");

    hoisted.language = "zh";
    rerender(<LanguageToggle />);
    expect(screen.getByRole("button", { name: "Chinese" })).toHaveClass("bg-accent");
  });
});
