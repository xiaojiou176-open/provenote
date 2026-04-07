import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { SourceProcessingReportPanel } from "./SourceProcessingReportPanel";

vi.mock("@/components/ui/button", () => ({
  Button: ({
    children,
    onClick,
    disabled,
    ...props
  }: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
  }) => (
    <button disabled={disabled} onClick={onClick} type="button" {...props}>
      {children}
    </button>
  ),
}));

vi.mock("@/components/ui/card", () => ({
  Card: ({ children, ...props }: { children: ReactNode } & Record<string, unknown>) => (
    <div {...props}>{children}</div>
  ),
  CardContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
}));

describe("SourceProcessingReportPanel", () => {
  it("renders detailed processing info and reprocess action", () => {
    const onReprocess = vi.fn();

    render(
      <SourceProcessingReportPanel
        report={{
          source_id: "source:1",
          source_type: "upload",
          title: "Quarterly Report",
          processing_status: "failed",
          processing_message: "OCR failed on page 4",
          processing_engine: "tika",
          extracted_length: 2500,
          paragraph_count: 18,
          embedded: true,
          embedded_chunks: 12,
          insights_count: 3,
          has_file: true,
          file_available: false,
          command_id: "command:1",
          processing_info: {
            page_errors: ["page-4"],
          },
        }}
        reprocessing={false}
        onReprocess={onReprocess}
      />,
    );

    expect(screen.getByText("OCR failed on page 4")).toBeInTheDocument();
    expect(screen.getByText("Status: failed • Engine: tika")).toBeInTheDocument();
    expect(screen.getByText("upload")).toBeInTheDocument();
    expect(screen.getByText("2500")).toBeInTheDocument();
    expect(screen.getByText("18")).toBeInTheDocument();
    expect(screen.getByText("yes / 12")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("no")).toBeInTheDocument();
    expect(screen.getByText(/Failure detected/)).toBeInTheDocument();
    expect(screen.getByText(/page-4/)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("source-reprocess"));

    expect(onReprocess).toHaveBeenCalledTimes(1);
  });

  it("renders fallback metadata state and disabled reprocessing state", () => {
    render(
      <SourceProcessingReportPanel
        report={{
          source_id: "source:2",
          source_type: "link",
          title: null,
          processing_status: "",
          processing_message: "No metadata yet",
          processing_engine: undefined,
          extracted_length: 0,
          paragraph_count: 0,
          embedded: false,
          embedded_chunks: 0,
          insights_count: 0,
          has_file: false,
          file_available: undefined,
          command_id: null,
          processing_info: null,
        }}
        reprocessing
        onReprocess={vi.fn()}
      />,
    );

    expect(screen.getByText("Status: n/a • Engine: n/a")).toBeInTheDocument();
    expect(screen.getByText(/No detailed processing metadata recorded yet/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reprocessing..." })).toBeDisabled();
  });
});
