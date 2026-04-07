import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  acceptLanguage: "en-US" as string | null,
}));

vi.mock("next/font/google", () => ({
  Geist: () => ({ variable: "--font-geist-sans" }),
  Geist_Mono: () => ({ variable: "--font-geist-mono" }),
}));

vi.mock("@tailwindcss/postcss", () => ({
  default: () => ({
    postcssPlugin: "tailwindcss-test-noop",
    Once() {},
  }),
}));

vi.mock("./globals.css", () => ({}));
vi.mock("next/headers", () => ({
  headers: vi.fn(async () => ({
    get: (name: string) => (name === "accept-language" ? hoisted.acceptLanguage : null),
  })),
}));

vi.mock("@/components/common/ConnectionGuard", () => ({
  ConnectionGuard: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="connection-guard">{children}</div>
  ),
}));

vi.mock("@/components/common/ErrorBoundary", () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="error-boundary">{children}</div>
  ),
}));

vi.mock("@/components/providers/I18nProvider", () => ({
  I18nProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="i18n-provider">{children}</div>
  ),
}));

vi.mock("@/components/providers/QueryProvider", () => ({
  QueryProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="query-provider">{children}</div>
  ),
}));

vi.mock("@/components/providers/ThemeProvider", () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="theme-provider">{children}</div>
  ),
}));

vi.mock("@/components/ui/sonner", () => ({
  Toaster: () => <div data-testid="toaster" />,
}));

vi.mock("@/lib/theme-script", () => ({
  themeScript: "window.__theme='test'",
}));

async function getRootLayout() {
  const mod = await import("./layout");
  return mod.default;
}

async function getMetadata() {
  const mod = await import("./layout");
  return mod.metadata;
}

async function renderLayoutMarkup(acceptLanguage: string | null) {
  hoisted.acceptLanguage = acceptLanguage;
  const RootLayout = await getRootLayout();
  const tree = await RootLayout({
    children: <main id="main-content">main</main>,
  });
  return renderToStaticMarkup(tree);
}

describe("RootLayout", () => {
  it("exports long-context-first metadata with share surfaces", async () => {
    const metadata = await getMetadata();

    expect(metadata.title).toBe("Provenote | Long Context To Structured Insight");
    expect(metadata.description).toContain("messy long context");
    expect(metadata.metadataBase?.toString()).toBe("https://github.com/xiaojiou176/provenote");
    expect(metadata.openGraph?.title).toBe("Provenote | Long Context To Structured Insight");
    expect(metadata.openGraph?.images).toEqual([
      {
        url: "https://raw.githubusercontent.com/xiaojiou176/provenote/main/docs/assets/social/provenote-social-preview.png",
        width: 1280,
        height: 640,
        alt: "Provenote social preview showing the long-context-to-structured-insight workbench story.",
      },
    ]);
    expect(metadata.twitter?.card).toBe("summary_large_image");
    expect(metadata.twitter?.images).toEqual([
      "https://raw.githubusercontent.com/xiaojiou176/provenote/main/docs/assets/social/provenote-social-preview.png",
    ]);
  });

  it("uses explicitly supported locale from accept-language header", async () => {
    const markup = await renderLayoutMarkup("ja-JP,zh-CN;q=0.8");

    expect(markup).toContain('<html lang="ja-JP"');
    expect(markup).toContain('href="#main-content"');
    expect(markup).toContain('data-testid="toaster"');
  });

  it("falls back from base language to supported region locale", async () => {
    const markup = await renderLayoutMarkup("pt;q=0.9,en;q=0.7");

    expect(markup).toContain('<html lang="pt-BR"');
  });

  it("defaults to en-US when accept-language header is absent", async () => {
    const markup = await renderLayoutMarkup(null);

    expect(markup).toContain('<html lang="en-US"');
  });

  it("defaults to en-US when accept-language has no supported locale", async () => {
    const markup = await renderLayoutMarkup("de-DE,es-ES;q=0.8");

    expect(markup).toContain('<html lang="en-US"');
  });
});
