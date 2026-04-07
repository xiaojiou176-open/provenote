import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  convertReferencesToCompactMarkdown,
  convertReferencesToMarkdownLinks,
  convertSourceReferences,
  convertSourceReferencesLegacy,
  createCompactReferenceLinkComponent,
  createReferenceLinkComponent,
  parseSourceReferences,
} from "./source-references";

describe("source-references utils", () => {
  it("parses mixed source/note/insight references", () => {
    const parsed = parseSourceReferences("Use [source:abc] and note:xyz with source_insight:q1");

    expect(parsed).toHaveLength(3);
    expect(parsed.map((item) => `${item.type}:${item.id}`)).toEqual([
      "source:abc",
      "note:xyz",
      "source_insight:q1",
    ]);
  });

  it("returns original text when no references are present", () => {
    const input = "no structured references here";

    expect(parseSourceReferences(input)).toEqual([]);
    expect(convertSourceReferences(input, vi.fn())).toBe(input);
    expect(convertReferencesToMarkdownLinks(input)).toBe(input);
    expect(convertReferencesToCompactMarkdown(input)).toBe(input);
    expect(convertSourceReferencesLegacy(input)).toBe(input);
  });

  it("converts references to markdown links across bracket and bold variants", () => {
    const linked = convertReferencesToMarkdownLinks(
      "[[source:abc]] [source:def] [**note:ghi**] **source_insight:jkl** source:mno",
    );

    expect(linked).toContain("[[[source:abc]]](#ref-source-abc)");
    expect(linked).toContain("[[source:def]](#ref-source-def)");
    expect(linked).toContain("[[**note:ghi**]](#ref-note-ghi)");
    expect(linked).toContain("[**source_insight:jkl**](#ref-source_insight-jkl)");
    expect(linked).toContain("[source:mno](#ref-source-mno)");
  });

  it("skips markdown conversion for malformed or oversized references", () => {
    const oversizedId = `source:${"a".repeat(101)}`;
    const input = `invalid ${oversizedId} should remain`;

    expect(convertReferencesToMarkdownLinks(input)).toBe(input);
  });

  it("converts references to compact markdown with dedup and reference list", () => {
    const compact = convertReferencesToCompactMarkdown(
      "[[source:abc]] and [note:xyz] and source:abc",
      "Refs",
    );

    expect(compact).toContain("[1](#ref-source-abc)");
    expect(compact).toContain("[2](#ref-note-xyz)");
    expect(compact).toContain(
      "[1](#ref-source-abc) and [2](#ref-note-xyz) and [1](#ref-source-abc)",
    );
    expect(compact).toContain("Refs:");
    expect(compact).toContain("[1] - [source:abc](#ref-source-abc)");
    expect(compact).toContain("[2] - [note:xyz](#ref-note-xyz)");
  });

  it("renders clickable reference buttons from plain text conversion", () => {
    const onReferenceClick = vi.fn();

    render(
      <div>
        {convertSourceReferences(
          "Read [[source:abc]] and [note:xyz] plus source_insight:q1 tail",
          onReferenceClick,
        )}
      </div>,
    );

    fireEvent.click(screen.getByRole("button", { name: "[[source:abc]]" }));
    fireEvent.click(screen.getByRole("button", { name: "[note:xyz]" }));
    fireEvent.click(screen.getByRole("button", { name: "source_insight:q1" }));

    expect(onReferenceClick).toHaveBeenNthCalledWith(1, "source", "abc");
    expect(onReferenceClick).toHaveBeenNthCalledWith(2, "note", "xyz");
    expect(onReferenceClick).toHaveBeenNthCalledWith(3, "source_insight", "q1");
    expect(screen.getByText(/tail$/)).toBeInTheDocument();
  });

  it("preserves prefix text with immediate bracketed references", () => {
    const onReferenceClick = vi.fn();

    render(<div>{convertSourceReferences("A[source:abc] [[note:xyz]]", onReferenceClick)}</div>);

    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "[source:abc]" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "[[note:xyz]]" })).toBeInTheDocument();
  });

  it("handles references that start at the very beginning with double brackets", () => {
    const onReferenceClick = vi.fn();

    render(<div>{convertSourceReferences("[[source:abc]] tail", onReferenceClick)}</div>);

    expect(screen.getByRole("button", { name: "[[source:abc]]" })).toBeInTheDocument();
    expect(screen.getByText(/tail$/)).toBeInTheDocument();
  });

  it("creates rich reference link component for refs and regular anchors", () => {
    const onReferenceClick = vi.fn();
    const Link = createReferenceLinkComponent(onReferenceClick);

    render(
      <>
        <Link href="#ref-source_insight-insight-1">insight</Link>
        <Link href="#ref-note-note-2">note</Link>
        <Link href="https://example.com/docs">external</Link>
      </>,
    );

    fireEvent.click(screen.getByRole("button", { name: "insight" }));
    fireEvent.click(screen.getByRole("button", { name: "note" }));

    expect(onReferenceClick).toHaveBeenNthCalledWith(1, "source_insight", "insight-1");
    expect(onReferenceClick).toHaveBeenNthCalledWith(2, "note", "note-2");
    expect(screen.getByRole("link", { name: "external" })).toHaveAttribute(
      "href",
      "https://example.com/docs",
    );
  });

  it("creates compact link component that dispatches reference clicks", () => {
    const onReferenceClick = vi.fn();
    const Link = createCompactReferenceLinkComponent(onReferenceClick);

    render(
      <>
        <Link href="#ref-source-abc">[1]</Link>
        <Link href="https://example.com">external</Link>
      </>,
    );

    fireEvent.click(screen.getByRole("button", { name: "[1]" }));

    expect(onReferenceClick).toHaveBeenCalledWith("source", "abc");
    expect(screen.getByRole("link", { name: "external" })).toHaveAttribute(
      "href",
      "https://example.com",
    );
  });
});
