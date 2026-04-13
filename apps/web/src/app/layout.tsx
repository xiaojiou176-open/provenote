import type { Metadata } from "next";
import { Atkinson_Hyperlegible, Crimson_Pro, Geist_Mono } from "next/font/google";
import { headers } from "next/headers";
import "./globals.css";
import { ConnectionGuard } from "@/components/common/ConnectionGuard";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { I18nProvider } from "@/components/providers/I18nProvider";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { Toaster } from "@/components/ui/sonner";
import { resources } from "@/lib/locales";
import { themeScript } from "@/lib/theme-script";

const atkinsonSans = Atkinson_Hyperlegible({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-atkinson-sans",
  display: "swap",
});

const crimsonDisplay = Crimson_Pro({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-crimson-display",
  display: "swap",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
});

const SUPPORTED_HTML_LANGS = [
  "zh-CN",
  "en-US",
  "zh-TW",
  "pt-BR",
  "ja-JP",
  "it-IT",
  "fr-FR",
  "ru-RU",
] as const;

type SupportedHtmlLang = (typeof SUPPORTED_HTML_LANGS)[number];

const LANGUAGE_FALLBACKS: Record<string, SupportedHtmlLang> = {
  zh: "zh-CN",
  en: "en-US",
  pt: "pt-BR",
  ja: "ja-JP",
  it: "it-IT",
  fr: "fr-FR",
  ru: "ru-RU",
};

const REPO_SOCIAL_PREVIEW_IMAGE =
  "https://raw.githubusercontent.com/xiaojiou176-open/provenote/main/docs/assets/social/provenote-social-preview.png";

function resolveHtmlLang(acceptLanguageHeader: string | null): SupportedHtmlLang {
  if (!acceptLanguageHeader) {
    return "en-US";
  }

  const supported = new Set<string>(SUPPORTED_HTML_LANGS);
  const candidates = acceptLanguageHeader
    .split(",")
    .map((entry) => entry.split(";")[0]?.trim())
    .filter((entry): entry is string => Boolean(entry));

  for (const candidate of candidates) {
    if (supported.has(candidate)) {
      return candidate as SupportedHtmlLang;
    }

    const base = candidate.split("-")[0]?.toLowerCase();
    if (base && LANGUAGE_FALLBACKS[base]) {
      return LANGUAGE_FALLBACKS[base];
    }
  }

  return "en-US";
}

export const metadata: Metadata = {
  title: "Provenote | Long Context To Structured Insight",
  description:
    "Turn messy long context into structured insight, auditable markdown, notebook drafts, and outcome-first research workflows in one source-grounded workbench.",
  applicationName: "Provenote",
  metadataBase: new URL("https://github.com/xiaojiou176-open/provenote"),
  keywords: [
    "long context",
    "structured insight",
    "auditable markdown",
    "notebook drafts",
    "research threads",
    "source-grounded AI",
    "MCP",
  ],
  openGraph: {
    title: "Provenote | Long Context To Structured Insight",
    description:
      "Turn messy long context into structured insight, auditable markdown, notebook drafts, and outcome-first research workflows in one source-grounded workbench.",
    siteName: "Provenote",
    type: "website",
    images: [
      {
        url: REPO_SOCIAL_PREVIEW_IMAGE,
        width: 1280,
        height: 640,
        alt: "Provenote social preview showing the long-context-to-structured-insight workbench story.",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Provenote | Long Context To Structured Insight",
    description:
      "Turn messy long context into structured insight, auditable markdown, notebook drafts, and outcome-first research workflows in one source-grounded workbench.",
    images: [REPO_SOCIAL_PREVIEW_IMAGE],
  },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const requestHeaders = await headers();
  const htmlLang = resolveHtmlLang(requestHeaders.get("accept-language"));
  const skipToMainContentLabel =
    resources[htmlLang].translation.common.accessibility.skipToMainContent ??
    resources["en-US"].translation.common.accessibility.skipToMainContent;

  return (
    <html lang={htmlLang} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body
        className={`${atkinsonSans.variable} ${crimsonDisplay.variable} ${geistMono.variable} font-sans`}
      >
        <a
          href="#main-content"
          aria-label={skipToMainContentLabel}
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[200] focus:rounded-md focus:bg-background focus:px-3 focus:py-2 focus:text-foreground focus:shadow-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          {skipToMainContentLabel}
        </a>
        <ErrorBoundary>
          <ThemeProvider>
            <QueryProvider>
              <I18nProvider>
                <ConnectionGuard>
                  {children}
                  <Toaster />
                </ConnectionGuard>
              </I18nProvider>
            </QueryProvider>
          </ThemeProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
