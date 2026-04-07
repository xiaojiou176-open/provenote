import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { SourceContentTab } from "./SourceContentTab";

vi.mock("@/components/ui/tabs", () => ({
  TabsContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/card", () => ({
  Card: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  CardDescription: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      sources: {
        content: "Content",
        noContent: "No content available",
        openOnYoutube: "Open on YouTube",
      },
      common: {
        accessibility: {
          ytVideo: "YouTube Video",
        },
      },
    },
  }),
}));

function buildSource(overrides: Record<string, unknown> = {}) {
  return {
    id: "source:1",
    title: "Test Source",
    full_text: "## Header\n\nBody content",
    asset: {
      url: "https://example.com/article",
    },
    ...overrides,
  };
}

describe("ContentTab (SourceContentTab)", () => {
  it("renders normal link content and markdown", () => {
    render(
      <SourceContentTab
        source={buildSource() as never}
        isYouTubeUrl={false}
        youTubeVideoId={null}
      />,
    );

    expect(screen.getByRole("heading", { name: "Content" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "https://example.com/article" })).toHaveAttribute(
      "href",
      "https://example.com/article",
    );
    expect(screen.getByText("Header")).toBeInTheDocument();
    expect(screen.getByText("Body content")).toBeInTheDocument();
  });

  it("renders YouTube embed and external youtube link", () => {
    render(
      <SourceContentTab
        source={
          buildSource({
            asset: { url: "https://youtu.be/abc123" },
            full_text: "video summary",
          }) as never
        }
        isYouTubeUrl
        youTubeVideoId="abc123"
      />,
    );

    expect(screen.getByTitle("YouTube Video")).toHaveAttribute(
      "src",
      "https://www.youtube.com/embed/abc123",
    );
    expect(screen.getByRole("link", { name: "Open on YouTube" })).toHaveAttribute(
      "href",
      "https://youtu.be/abc123",
    );
  });

  it("falls back to translated empty text when full text is missing", () => {
    render(
      <SourceContentTab
        source={buildSource({ full_text: "" }) as never}
        isYouTubeUrl={false}
        youTubeVideoId={null}
      />,
    );

    expect(screen.getByText("No content available")).toBeInTheDocument();
  });

  it("renders markdown headings, lists, and tables from source content", () => {
    render(
      <SourceContentTab
        source={
          buildSource({
            full_text:
              "# Heading 1\n\n### Heading 3\n\n- first item\n\n1. second item\n\n| Col A | Col B |\n| --- | --- |\n| A1 | B1 |",
          }) as never
        }
        isYouTubeUrl={false}
        youTubeVideoId={null}
      />,
    );

    expect(screen.getByText("Heading 1")).toBeInTheDocument();
    expect(screen.getByText("Heading 3")).toBeInTheDocument();
    expect(screen.getByText("first item")).toBeInTheDocument();
    expect(screen.getByText("second item")).toBeInTheDocument();
    expect(screen.getByText("Col A")).toBeInTheDocument();
    expect(screen.getByText("B1")).toBeInTheDocument();
  });
});
