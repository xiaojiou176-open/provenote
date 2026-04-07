"use client";

import { AlertTriangle, Database, FileText, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { SourceProcessingReportResponse } from "@/lib/types/api";

interface SourceProcessingReportPanelProps {
  report: SourceProcessingReportResponse;
  reprocessing: boolean;
  onReprocess: () => void;
}

function renderValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  if (typeof value === "boolean") {
    return value ? "yes" : "no";
  }
  return String(value);
}

export function SourceProcessingReportPanel({
  report,
  reprocessing,
  onReprocess,
}: SourceProcessingReportPanelProps) {
  return (
    <Card data-testid="source-processing-report">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Processing QA</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md border bg-muted/40 p-3 text-sm">
          <p className="font-medium">{report.processing_message}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Status: {renderValue(report.processing_status)} • Engine:{" "}
            {renderValue(report.processing_engine)}
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <div className="rounded-md border p-3 text-sm">
            <p className="text-xs text-muted-foreground">Source type</p>
            <p className="font-medium">{report.source_type}</p>
          </div>
          <div className="rounded-md border p-3 text-sm">
            <p className="text-xs text-muted-foreground">Extracted length</p>
            <p className="font-medium">{report.extracted_length}</p>
          </div>
          <div className="rounded-md border p-3 text-sm">
            <p className="text-xs text-muted-foreground">Paragraph count</p>
            <p className="font-medium">{report.paragraph_count}</p>
          </div>
          <div className="rounded-md border p-3 text-sm">
            <p className="text-xs text-muted-foreground">Embedded / chunks</p>
            <p className="font-medium">
              {renderValue(report.embedded)} / {report.embedded_chunks}
            </p>
          </div>
          <div className="rounded-md border p-3 text-sm">
            <p className="text-xs text-muted-foreground">Insights</p>
            <p className="font-medium">{report.insights_count}</p>
          </div>
          <div className="rounded-md border p-3 text-sm">
            <p className="text-xs text-muted-foreground">File available</p>
            <p className="font-medium">{renderValue(report.file_available)}</p>
          </div>
        </div>

        {report.processing_info ? (
          <div className="rounded-md border p-3 text-sm">
            <div className="mb-2 flex items-center gap-2 font-medium">
              <Database className="h-4 w-4" />
              Raw processing info
            </div>
            <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-muted-foreground">
              {JSON.stringify(report.processing_info, null, 2)}
            </pre>
          </div>
        ) : (
          <div className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
            <div className="mb-2 flex items-center gap-2 font-medium text-foreground">
              <FileText className="h-4 w-4" />
              No detailed processing metadata recorded yet
            </div>
            This source can still be reprocessed if you want a fresh command-backed run.
          </div>
        )}

        {report.processing_status === "failed" ? (
          <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
            <div className="mb-1 flex items-center gap-2 font-medium">
              <AlertTriangle className="h-4 w-4" />
              Failure detected
            </div>
            Reprocess will queue a fresh source processing command using the current source payload.
          </div>
        ) : null}

        <Button
          type="button"
          variant="outline"
          onClick={onReprocess}
          disabled={reprocessing}
          data-testid="source-reprocess"
        >
          <RotateCcw className="mr-2 h-4 w-4" />
          {reprocessing ? "Reprocessing..." : "Reprocess source"}
        </Button>
      </CardContent>
    </Card>
  );
}
