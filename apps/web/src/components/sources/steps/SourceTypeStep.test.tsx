import { fireEvent, render, screen } from "@testing-library/react";
import { useForm } from "react-hook-form";
import { describe, expect, it, vi } from "vitest";
import { parseAndValidateUrls, SourceTypeStep } from "./SourceTypeStep";

interface FormData {
  type: "link" | "upload" | "text";
  title?: string;
  url?: string;
  content?: string;
  file?: unknown;
  notebooks?: string[];
  transformations?: string[];
  embed: boolean;
  async_processing: boolean;
}

const t = {
  common: {
    optional: "optional",
    title: "Title",
    batchMode: "Batch mode",
  },
  sources: {
    title: "Source type",
    processDescription: "Configure source",
    addUrl: "Add URL",
    uploadFile: "Upload file",
    enterText: "Enter text",
    urlLabel: "URLs",
    urlsCount: "URLs {count}",
    maxItems: "max {count}",
    enterUrlsPlaceholder: "Paste URLs",
    batchUrlHint: "One URL per line",
    invalidUrlsDetected: "Invalid URLs",
    lineLabel: "Line {line}",
    fixInvalidUrls: "Fix invalid URLs",
    fileLabel: "Files",
    filesCount: "Files {count}",
    selectMultipleFilesHint: "Select multiple files",
    selectedFiles: "Selected files",
    maxFilesAllowed: "Maximum files: {count}",
    textContentLabel: "Text content",
    htmlDetected: "HTML content detected",
    textPlaceholder: "Write text",
    titleRequired: "Title is required",
    titleGenerated: "Title generated automatically",
    titlePlaceholder: "Source title",
    batchCount: "Batch {count} {type}",
    batchTitlesAuto: "Titles are auto generated. ",
    batchCommonSettings: "Shared settings apply.",
  },
};

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t }),
}));

function renderStep({
  defaultValues,
  urlValidationErrors,
}: {
  defaultValues: FormData;
  urlValidationErrors?: Array<{ url: string; line: number }>;
}) {
  function TestHarness() {
    const { control, register, setValue } = useForm<FormData>({ defaultValues });

    return (
      <SourceTypeStep
        control={control}
        register={register}
        setValue={setValue}
        errors={{}}
        urlValidationErrors={urlValidationErrors}
      />
    );
  }

  return render(<TestHarness />);
}

describe("SourceTypeStep", () => {
  it("parses urls and reports invalid rows", () => {
    expect(parseAndValidateUrls("https://ok.dev\nnot-url\n\nhttps://two.dev")).toEqual({
      valid: ["https://ok.dev", "https://two.dev"],
      invalid: [{ url: "not-url", line: 2 }],
    });
  });

  it("enters batch mode for multi-url input and hides title field", () => {
    const { container } = renderStep({
      defaultValues: { type: "link", embed: false, async_processing: true, url: "" },
    });

    const urlTextarea = container.querySelector("#url") as HTMLTextAreaElement;
    fireEvent.change(urlTextarea, {
      target: { value: "https://one.dev\nhttps://two.dev" },
    });

    expect(screen.getByText("URLs 2")).toBeInTheDocument();
    expect(screen.getByText("Batch mode")).toBeInTheDocument();
    expect(screen.getByText("Batch 2 Add URL")).toBeInTheDocument();
    expect(container.querySelector("#source-title")).not.toBeInTheDocument();
  });

  it("renders url validation errors", () => {
    renderStep({
      defaultValues: { type: "link", embed: false, async_processing: true, url: "bad-url" },
      urlValidationErrors: [{ url: "bad-url", line: 4 }],
    });

    expect(screen.getByText("Invalid URLs")).toBeInTheDocument();
    expect(screen.getByText("Line 4")).toBeInTheDocument();
    expect(screen.getByText("bad-url")).toBeInTheDocument();
  });

  it("shows upload max-limit error when selecting more than 50 files", () => {
    const { container } = renderStep({
      defaultValues: { type: "upload", embed: false, async_processing: true },
    });

    const fileInput = container.querySelector("#file") as HTMLInputElement;
    const files = Array.from(
      { length: 51 },
      (_, index) => new File(["x"], `f-${index}.txt`, { type: "text/plain" }),
    );

    fireEvent.change(fileInput, {
      target: { files },
    });

    expect(screen.getByText("Maximum files: 50")).toBeInTheDocument();
  });

  it("detects html paste in text mode", () => {
    const { container } = renderStep({
      defaultValues: {
        type: "text",
        title: "A",
        content: "",
        embed: false,
        async_processing: true,
      },
    });

    const textArea = container.querySelector("#content") as HTMLTextAreaElement;

    fireEvent.paste(textArea, {
      clipboardData: {
        getData: (type: string) => (type === "text/html" ? "<b>hello</b>" : "hello"),
      },
    });

    expect(screen.getByText("HTML content detected")).toBeInTheDocument();
    expect(textArea.value).toContain("<b>hello</b>");
  });
});
