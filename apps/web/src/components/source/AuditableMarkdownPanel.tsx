"use client";

import { isAxiosError } from "axios";
import { AlertTriangle, Download, Loader2, Play } from "lucide-react";
import { useState } from "react";
import { AuditableClaimReviewWorkspace } from "@/components/source/AuditableClaimReviewWorkspace";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { auditableApi } from "@/lib/api/auditable";
import { useAuditableRuns } from "@/lib/hooks/use-auditable-runs";
import { useToast } from "@/lib/hooks/use-toast";
import { useTranslation } from "@/lib/hooks/use-translation";
import { getWorkflowStateLabel } from "@/lib/i18n-state-labels";
import { cn } from "@/lib/utils";
import { getApiErrorMessage } from "@/lib/utils/error-handler";

interface AuditableMarkdownPanelProps {
  sourceId: string;
  linkedNotebookIds?: string[];
  onUseInDraft?: (notebookId: string) => void;
  className?: string;
}

function parseContentDispositionFilename(header?: string | null): string | null {
  if (!header) {
    return null;
  }

  const match = header.match(/filename\*?=([^;]+)/i);
  if (!match?.[1]) {
    return null;
  }

  const value = match[1].trim();
  if (value.toLowerCase().startsWith("utf-8''")) {
    return decodeURIComponent(value.slice(7));
  }

  return value.replace(/^"|"$/g, "");
}

function hasActiveRunStatus(status?: string) {
  return status === "queued" || status === "running";
}

function getStatusBadgeVariant(
  status?: string,
): "default" | "secondary" | "destructive" | "outline" {
  if (status === "failed") {
    return "destructive";
  }
  if (status === "completed") {
    return "default";
  }
  if (status === "queued" || status === "running") {
    return "secondary";
  }
  return "outline";
}

export function AuditableMarkdownPanel({
  sourceId,
  linkedNotebookIds = [],
  onUseInDraft,
  className,
}: AuditableMarkdownPanelProps) {
  const { t } = useTranslation();
  const { toast } = useToast();
  const { latestRun, isLoading, isFetching, error, startRun, repairClaim, repairSection } =
    useAuditableRuns(sourceId);
  const [isDownloading, setIsDownloading] = useState(false);

  const runIsActive = hasActiveRunStatus(latestRun?.status);
  const downloadEnabled = latestRun?.status === "completed" && !isDownloading;

  const metrics = {
    coverageRate: latestRun?.metrics?.coverage_rate ?? 0,
    missing: latestRun?.metrics?.missing_count ?? 0,
    duplicate: latestRun?.metrics?.duplicate_count ?? 0,
    uncitedClaims: latestRun?.metrics?.uncited_claims_count ?? 0,
    unknownPid: latestRun?.metrics?.unknown_pid_count ?? 0,
    unclassified: latestRun?.metrics?.unclassified_count ?? 0,
  };

  const canJumpToDraft = latestRun?.status === "completed" && linkedNotebookIds.length === 1;
  const multipleDraftLanesAvailable =
    latestRun?.status === "completed" && linkedNotebookIds.length > 1;

  const handleStartRun = () => {
    startRun.mutate({});
  };

  const handleDownloadMarkdown = async () => {
    if (!latestRun) {
      return;
    }

    try {
      setIsDownloading(true);
      const response = await auditableApi.downloadMarkdown(latestRun.id);

      const filenameFromHeader = parseContentDispositionFilename(
        response.headers?.["content-disposition"] as string | undefined,
      );
      const filename = filenameFromHeader || `auditable-${latestRun.id}.md`;

      const blobUrl = window.URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);

      toast({
        title: t.common.success,
        description: t.sources.auditableMarkdownDownloaded,
      });
    } catch (downloadError: unknown) {
      let description = getApiErrorMessage(downloadError, (key) => t(key), t.common.error);
      if (isAxiosError(downloadError) && downloadError.response?.status === 404) {
        description = t.sources.auditableMarkdownUnavailable;
      }

      toast({
        title: t.common.error,
        description,
        variant: "destructive",
      });
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <Card className={cn("gap-4", className)}>
      <CardHeader className="pb-0">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle>{t.sources.auditableTitle}</CardTitle>
            <CardDescription>{t.sources.auditableDescription}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {latestRun ? (
              <Badge variant={getStatusBadgeVariant(latestRun.status)}>
                {getWorkflowStateLabel(t, latestRun.status)}
              </Badge>
            ) : null}
            <Button
              size="sm"
              onClick={handleStartRun}
              disabled={startRun.isPending || runIsActive}
              data-testid="start-auditable-run"
            >
              {startRun.isPending || runIsActive ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t.sources.auditableRunning}
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  {t.sources.auditableRunButton}
                </>
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {error ? (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>{t.sources.auditableFailedToLoad}</AlertTitle>
            <AlertDescription>
              {getApiErrorMessage(error, (key) => t(key), t.common.error)}
            </AlertDescription>
          </Alert>
        ) : null}

        {latestRun ? (
          <>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-lg border bg-muted/40 p-3">
                <p className="text-xs text-muted-foreground">
                  {t.sources.auditableMetricCoverageRate}
                </p>
                <p className="text-xl font-semibold">{metrics.coverageRate.toFixed(2)}</p>
              </div>
              <div className="rounded-lg border bg-muted/40 p-3">
                <p className="text-xs text-muted-foreground">{t.sources.auditableMetricMissing}</p>
                <p className="text-xl font-semibold">{metrics.missing}</p>
              </div>
              <div className="rounded-lg border bg-muted/40 p-3">
                <p className="text-xs text-muted-foreground">
                  {t.sources.auditableMetricDuplicate}
                </p>
                <p className="text-xl font-semibold">{metrics.duplicate}</p>
              </div>
              <div className="rounded-lg border bg-muted/40 p-3">
                <p className="text-xs text-muted-foreground">
                  {t.sources.auditableMetricUncitedClaims}
                </p>
                <p className="text-xl font-semibold">{metrics.uncitedClaims}</p>
              </div>
              <div className="rounded-lg border bg-muted/40 p-3">
                <p className="text-xs text-muted-foreground">
                  {t.sources.auditableMetricUnknownPid}
                </p>
                <p className="text-xl font-semibold">{metrics.unknownPid}</p>
              </div>
              <div className="rounded-lg border bg-muted/40 p-3">
                <p className="text-xs text-muted-foreground">
                  {t.sources.auditableMetricUnclassified}
                </p>
                <p className="text-xl font-semibold">{metrics.unclassified}</p>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-muted-foreground">
                {t("sources.auditableLastUpdated", {
                  time: new Date(latestRun.updated).toLocaleString(),
                })}
                {isLoading || isFetching ? ` (${t.sources.auditableRefreshing})` : ""}
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!downloadEnabled}
                  onClick={handleDownloadMarkdown}
                  data-testid="download-auditable-markdown"
                >
                  {isDownloading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      {t.sources.auditablePreparingDownload}
                    </>
                  ) : (
                    <>
                      <Download className="mr-2 h-4 w-4" />
                      {t.sources.auditableDownloadMarkdown}
                    </>
                  )}
                </Button>
                {canJumpToDraft && onUseInDraft ? (
                  <Button
                    size="sm"
                    onClick={() => onUseInDraft(linkedNotebookIds[0])}
                    data-testid="use-source-in-draft"
                  >
                    {t.sources.auditableUseInDraft}
                  </Button>
                ) : null}
              </div>
            </div>

            {canJumpToDraft ? (
              <Alert>
                <AlertTitle>{t.sources.auditableNextStepDraftTitle}</AlertTitle>
                <AlertDescription>{t.sources.auditableNextStepDraftDescription}</AlertDescription>
              </Alert>
            ) : null}

            {multipleDraftLanesAvailable ? (
              <Alert>
                <AlertTitle>{t.sources.auditableNextStepNotebookTitle}</AlertTitle>
                <AlertDescription>
                  {t.sources.auditableNextStepNotebookDescription}
                </AlertDescription>
              </Alert>
            ) : null}

            {latestRun.sections?.length || latestRun.claims?.length ? (
              <AuditableClaimReviewWorkspace
                claims={(latestRun.claims ?? []) as Array<Record<string, unknown>>}
                sections={(latestRun.sections ?? []) as Array<Record<string, unknown>>}
                onRepairClaim={(index) =>
                  repairClaim.mutate({
                    runId: latestRun.id,
                    targetIndex: index,
                  })
                }
                onRepairSection={(index) =>
                  repairSection.mutate({
                    runId: latestRun.id,
                    targetIndex: index,
                  })
                }
                repairClaimPending={repairClaim.isPending}
                repairSectionPending={repairSection.isPending}
              />
            ) : null}

            {latestRun.status === "failed" ? (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>{t.sources.auditableRunFailedTitle}</AlertTitle>
                <AlertDescription>{t.sources.auditableRunFailedDescription}</AlertDescription>
              </Alert>
            ) : null}
          </>
        ) : (
          <p className="text-sm text-muted-foreground">{t.sources.auditableEmptyState}</p>
        )}
      </CardContent>
    </Card>
  );
}
