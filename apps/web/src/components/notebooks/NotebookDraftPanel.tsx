"use client";

import { formatDistanceToNow } from "date-fns";
import { Download, FileArchive, FileText, GitBranchPlus, Loader2, RotateCcw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { draftsApi } from "@/lib/api/drafts";
import { useNotebookDrafts } from "@/lib/hooks/use-drafts";
import { useNotebookResearchThreads } from "@/lib/hooks/use-research-threads";
import { useToast } from "@/lib/hooks/use-toast";
import { useTranslation } from "@/lib/hooks/use-translation";
import { getWorkflowStateLabel } from "@/lib/i18n-state-labels";
import type { DraftResponse, SourceListResponse } from "@/lib/types/api";
import { getDateLocale } from "@/lib/utils/date-locale";
import { getApiErrorMessage } from "@/lib/utils/error-handler";
import { getRecommendedResearchThread } from "./research-thread-recommendation";

interface NotebookDraftPanelProps {
  notebookId: string;
  notebookName?: string;
  sources?: SourceListResponse[];
  sourcesLoading?: boolean;
  className?: string;
  draftSeedThreadId?: string;
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

function renderPidList(value: unknown, noneLabel: string) {
  if (!Array.isArray(value) || value.length === 0) {
    return noneLabel;
  }
  return value.join(", ");
}

function getStatusVariant(status: DraftResponse["status"]) {
  if (status === "failed") {
    return "destructive" as const;
  }
  if (status === "verified") {
    return "default" as const;
  }
  if (status === "queued" || status === "running") {
    return "secondary" as const;
  }
  return "outline" as const;
}

function findComparisonBase(draft: DraftResponse, drafts: DraftResponse[]) {
  if (draft.parent_draft_id) {
    return drafts.find((candidate) => candidate.id === draft.parent_draft_id) ?? null;
  }
  return drafts.find((candidate) => candidate.version === draft.version - 1) ?? null;
}

function formatSignedDelta(value: number) {
  if (value === 0) {
    return "0";
  }
  return value > 0 ? `+${value}` : `${value}`;
}

function formatDraftUpdatedLabel(
  value: string,
  locale: ReturnType<typeof getDateLocale>,
  getMessage: (key: string, values?: Record<string, unknown>) => string,
) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return getMessage("notebooks.draftUpdatedUnavailable");
  }
  return getMessage("notebooks.draftUpdatedRelative", {
    time: formatDistanceToNow(parsed, { addSuffix: true, locale }),
  });
}

function getActiveSourceCount(sources: SourceListResponse[]) {
  return sources.filter((source) =>
    source.status ? ["new", "queued", "running", "pending"].includes(source.status) : false,
  ).length;
}

function scrollToTestId(testId: string) {
  const element = document.querySelector(`[data-testid="${testId}"]`);
  if (element instanceof HTMLElement) {
    element.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function getResearchThreadHandoffTarget(isFocusedSeed: boolean) {
  return isFocusedSeed ? "research-thread-draft-bridge" : "research-thread-recommendation";
}

export function NotebookDraftPanel({
  notebookId,
  notebookName,
  sources = [],
  sourcesLoading = false,
  className,
  draftSeedThreadId,
}: NotebookDraftPanelProps) {
  const { t, language } = useTranslation();
  const { toast } = useToast();
  const { drafts, isLoading, error, createDraft, rerunDraft, verifyDraft } =
    useNotebookDrafts(notebookId);
  const { data: researchThreads = [], isLoading: threadsLoading } =
    useNotebookResearchThreads(notebookId);
  const [draftTitle, setDraftTitle] = useState("");
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([]);
  const [downloadingDraftId, setDownloadingDraftId] = useState<string | null>(null);
  const [downloadingBundleId, setDownloadingBundleId] = useState<string | null>(null);

  const dfLocale = getDateLocale(language);

  useEffect(() => {
    if (sources.length === 0) {
      setSelectedSourceIds((current) => (current.length === 0 ? current : []));
      return;
    }

    setSelectedSourceIds((current) => {
      if (current.length === 0) {
        return sources.map((source) => source.id);
      }
      const available = new Set(sources.map((source) => source.id));
      const preserved = current.filter((id) => available.has(id));
      return preserved.length > 0 ? preserved : sources.map((source) => source.id);
    });
  }, [sources]);

  const selectedSourceSet = useMemo(() => new Set(selectedSourceIds), [selectedSourceIds]);
  const latestDraft = drafts[0] ?? null;
  const latestVerifiedDraft = drafts.find((draft) => draft.status === "verified") ?? null;
  const activeSourceCount = useMemo(() => getActiveSourceCount(sources), [sources]);
  const draftSeedThread = useMemo(
    () =>
      draftSeedThreadId
        ? (researchThreads.find((thread) => thread.id === draftSeedThreadId) ?? null)
        : null,
    [draftSeedThreadId, researchThreads],
  );
  const recommendedThread = useMemo(
    () => getRecommendedResearchThread(researchThreads),
    [researchThreads],
  );

  const toggleSource = (sourceId: string) => {
    setSelectedSourceIds((current) =>
      current.includes(sourceId) ? current.filter((id) => id !== sourceId) : [...current, sourceId],
    );
  };

  const handleCreateDraft = () => {
    createDraft.mutate({
      title: draftTitle.trim() || undefined,
      source_ids: selectedSourceIds,
      note_ids: [],
      thread_ids: [],
    });
    setDraftTitle("");
  };

  const handleDownloadDraft = async (draft: DraftResponse) => {
    try {
      setDownloadingDraftId(draft.id);
      const response = await draftsApi.downloadMarkdown(draft.id);
      const filenameFromHeader = parseContentDispositionFilename(
        response.headers?.["content-disposition"] as string | undefined,
      );
      const filename = filenameFromHeader || `draft-${draft.id}.md`;

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
        description: t.notebooks.draftMarkdownDownloaded,
      });
    } catch (downloadError: unknown) {
      toast({
        title: t.common.error,
        description: getApiErrorMessage(downloadError, (key) => t(key), t.common.error),
        variant: "destructive",
      });
    } finally {
      setDownloadingDraftId(null);
    }
  };

  const handleDownloadBundle = async (draft: DraftResponse) => {
    try {
      setDownloadingBundleId(draft.id);
      const response = await draftsApi.downloadBundle(draft.id);
      const filenameFromHeader = parseContentDispositionFilename(
        response.headers?.["content-disposition"] as string | undefined,
      );
      const filename = filenameFromHeader || `draft-${draft.id}-bundle.zip`;

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
        description: t.notebooks.draftBundleDownloaded,
      });
    } catch (downloadError: unknown) {
      toast({
        title: t.common.error,
        description: getApiErrorMessage(downloadError, (key) => t(key), t.common.error),
        variant: "destructive",
      });
    } finally {
      setDownloadingBundleId(null);
    }
  };

  return (
    <Card className={className} data-testid="notebook-drafts-panel">
      <CardHeader>
        <CardTitle>{t.notebooks.draftsTitle}</CardTitle>
        <CardDescription>{t.notebooks.draftsDescription}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-3 md:grid-cols-4" data-testid="draft-journey-status">
          <div className="rounded-lg border bg-muted/30 p-3 text-sm">
            <p className="text-xs text-muted-foreground">{t.notebooks.journeySourceReadiness}</p>
            <p className="font-semibold">
              {t("notebooks.journeyReadyCount", {
                ready: sources.length - activeSourceCount,
                total: sources.length || 0,
              })}
            </p>
          </div>
          <div className="rounded-lg border bg-muted/30 p-3 text-sm">
            <p className="text-xs text-muted-foreground">{t.notebooks.journeyDraftLane}</p>
            <p className="font-semibold">
              {getWorkflowStateLabel(t, latestDraft?.status) || t.notebooks.journeyNoDraftYet}
            </p>
          </div>
          <div className="rounded-lg border bg-muted/30 p-3 text-sm">
            <p className="text-xs text-muted-foreground">{t.notebooks.journeyVerifyState}</p>
            <p className="font-semibold">
              {latestVerifiedDraft
                ? t("notebooks.journeyVerifiedVersion", {
                    version: latestVerifiedDraft.version,
                  })
                : t.notebooks.journeyNotVerified}
            </p>
          </div>
          <div className="rounded-lg border bg-muted/30 p-3 text-sm">
            <p className="text-xs text-muted-foreground">{t.notebooks.journeyNextStep}</p>
            <p className="font-semibold">
              {activeSourceCount > 0
                ? t.notebooks.journeyWaitForSources
                : latestVerifiedDraft
                  ? t.notebooks.journeyUseVerifiedResult
                  : latestDraft
                    ? t.notebooks.journeyCompareAndVerify
                    : t.notebooks.journeyCreateDraft}
            </p>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,320px),minmax(0,1fr)]">
          <div className="space-y-3 rounded-lg border p-4" data-testid="draft-source-selector">
            {!latestDraft && (draftSeedThread || recommendedThread) ? (
              <div className="rounded-md border bg-muted/20 p-4" data-testid="draft-seed-handoff">
                {(() => {
                  const thread = draftSeedThread ?? recommendedThread;
                  if (!thread) {
                    return null;
                  }

                  const isFocusedSeed = Boolean(draftSeedThread);

                  return (
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="secondary">
                            {isFocusedSeed
                              ? t.notebooks.researchThreadBridgeBadge
                              : t.notebooks.researchThreadRecommendedBadge}
                          </Badge>
                          <p className="text-sm font-medium">
                            {isFocusedSeed
                              ? t.notebooks.draftSeedFocusedBridgeTitle
                              : t.notebooks.draftSeedBridgeTitle}
                          </p>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {t(
                            isFocusedSeed
                              ? "notebooks.draftSeedFocusedBridgeDescription"
                              : "notebooks.draftSeedBridgeDescription",
                            {
                              title: thread.title,
                              entryCount: thread.entry_count,
                              sourceCount: thread.source_ids.length,
                            },
                          )}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {threadsLoading
                            ? t.notebooks.outcomeThreadsLoading
                            : t(
                                isFocusedSeed
                                  ? "notebooks.draftSeedFocusedBridgeHelper"
                                  : "notebooks.draftSeedBridgeHelper",
                                {
                                  seedKind: thread.seed_kind.replace(/_/g, " "),
                                },
                              )}
                        </p>
                      </div>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          scrollToTestId(getResearchThreadHandoffTarget(isFocusedSeed))
                        }
                      >
                        <GitBranchPlus className="mr-2 h-4 w-4" />
                        {isFocusedSeed
                          ? t.notebooks.draftSeedFocusedBridgeAction
                          : t.notebooks.draftSeedBridgeAction}
                      </Button>
                    </div>
                  );
                })()}
              </div>
            ) : null}
            <div className="space-y-1">
              <p className="text-sm font-medium">{t.notebooks.draftSourceSelection}</p>
              <p className="text-xs text-muted-foreground">
                {notebookName
                  ? t("notebooks.draftBuildFromNamedNotebook", { name: notebookName })
                  : t.notebooks.draftBuildFromNotebook}
              </p>
            </div>
            <div
              className="flex flex-wrap items-center gap-2 rounded-md border bg-muted/20 px-3 py-2 text-xs text-muted-foreground"
              data-testid="draft-source-summary"
            >
              <Badge variant="outline">
                {t("sources.selectedCount", { count: selectedSourceIds.length })}
              </Badge>
              <Badge variant="outline">
                {t("notebooks.journeyReadyCount", {
                  ready: sources.length - activeSourceCount,
                  total: sources.length || 0,
                })}
              </Badge>
              {activeSourceCount > 0 ? (
                <Badge variant="secondary">
                  {t("notebooks.outcomeSourcesPending", { count: activeSourceCount })}
                </Badge>
              ) : null}
            </div>
            <Input
              id="draft-title-input"
              placeholder={t.notebooks.draftTitlePlaceholder}
              value={draftTitle}
              onChange={(event) => setDraftTitle(event.target.value)}
            />
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setSelectedSourceIds(sources.map((source) => source.id))}
                disabled={sources.length === 0}
              >
                {t.notebooks.draftSelectAll}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setSelectedSourceIds([])}
                disabled={selectedSourceIds.length === 0}
              >
                {t.notebooks.draftClearSelection}
              </Button>
            </div>
            <ScrollArea className="h-44 rounded-md border">
              <div className="space-y-2 p-3">
                {sourcesLoading ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {t.notebooks.loadingNotebookSources}
                  </div>
                ) : sources.length === 0 ? (
                  <p className="text-sm text-muted-foreground">{t.notebooks.draftNoSources}</p>
                ) : (
                  sources.map((source) => (
                    <label
                      key={source.id}
                      className="flex items-start gap-3 rounded-md border p-2 text-sm"
                    >
                      <Checkbox
                        checked={selectedSourceSet.has(source.id)}
                        onCheckedChange={() => toggleSource(source.id)}
                        aria-label={t("notebooks.draftSelectSource", {
                          title: source.title || source.id,
                        })}
                      />
                      <span className="min-w-0">
                        <span className="block font-medium">{source.title || source.id}</span>
                        <span className="block text-xs text-muted-foreground">{source.id}</span>
                      </span>
                    </label>
                  ))
                )}
              </div>
            </ScrollArea>
            <Button
              type="button"
              onClick={handleCreateDraft}
              disabled={createDraft.isPending || selectedSourceIds.length === 0}
              data-testid="create-notebook-draft"
            >
              {createDraft.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t.common.creating}
                </>
              ) : (
                t.notebooks.draftCreate
              )}
            </Button>
          </div>

          <div className="space-y-3">
            {error ? (
              <Alert variant="destructive">
                <AlertTitle>{t.notebooks.failedToLoadDrafts}</AlertTitle>
                <AlertDescription>
                  {getApiErrorMessage(error, (key) => t(key), t.common.error)}
                </AlertDescription>
              </Alert>
            ) : null}

            {isLoading ? (
              <div className="flex items-center gap-2 rounded-lg border p-4 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                {t.notebooks.loadingDrafts}
              </div>
            ) : drafts.length === 0 ? (
              <div className="rounded-lg border border-dashed p-6 text-center">
                <FileText className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
                <p className="font-medium">{t.notebooks.noDraftsYet}</p>
                <p className="mt-2 text-sm text-muted-foreground">{t.notebooks.createFirstDraft}</p>
              </div>
            ) : (
              drafts.map((draft) => (
                <Card key={draft.id} data-testid={`draft-card-${draft.id}`}>
                  <CardHeader className="gap-3 pb-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <CardTitle className="text-base">{draft.title}</CardTitle>
                        <CardDescription>
                          {t("notebooks.draftVersion", { version: draft.version })}
                          {draft.parent_draft_id
                            ? ` • ${t("notebooks.draftParent", { id: draft.parent_draft_id })}`
                            : ""}
                        </CardDescription>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant={getStatusVariant(draft.status)}>
                          {getWorkflowStateLabel(t, draft.status)}
                        </Badge>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => rerunDraft.mutate({ draftId: draft.id })}
                          disabled={rerunDraft.isPending}
                        >
                          <RotateCcw className="mr-2 h-4 w-4" />
                          {t.notebooks.draftRerun}
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => verifyDraft.mutate(draft.id)}
                          disabled={verifyDraft.isPending || draft.status === "verified"}
                        >
                          {t.notebooks.draftMarkVerified}
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownloadDraft(draft)}
                          disabled={downloadingDraftId === draft.id}
                        >
                          {downloadingDraftId === draft.id ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              {t.notebooks.draftPreparingDownload}
                            </>
                          ) : (
                            <>
                              <Download className="mr-2 h-4 w-4" />
                              {t.notebooks.draftDownloadMarkdown}
                            </>
                          )}
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownloadBundle(draft)}
                          disabled={downloadingBundleId === draft.id}
                        >
                          {downloadingBundleId === draft.id ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              {t.notebooks.draftBundling}
                            </>
                          ) : (
                            <>
                              <FileArchive className="mr-2 h-4 w-4" />
                              {t.notebooks.draftExportBundle}
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                    <div className="grid gap-2 sm:grid-cols-3">
                      <div className="rounded-md border bg-muted/40 p-3 text-sm">
                        <p className="text-xs text-muted-foreground">
                          {t.notebooks.draftMetricCoverage}
                        </p>
                        <p className="font-semibold">{draft.metrics.coverage_rate.toFixed(2)}</p>
                      </div>
                      <div className="rounded-md border bg-muted/40 p-3 text-sm">
                        <p className="text-xs text-muted-foreground">
                          {t.notebooks.draftMetricMissingDuplicate}
                        </p>
                        <p className="font-semibold">
                          {draft.metrics.missing_count} / {draft.metrics.duplicate_count}
                        </p>
                      </div>
                      <div className="rounded-md border bg-muted/40 p-3 text-sm">
                        <p className="text-xs text-muted-foreground">
                          {t.notebooks.draftMetricSources}
                        </p>
                        <p className="font-semibold">{draft.source_ids.length}</p>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatDraftUpdatedLabel(draft.updated, dfLocale, (key, values) =>
                        t(key, values),
                      )}
                    </p>
                    {draft.status !== "verified" ? (
                      <Alert data-testid={`draft-verify-callout-${draft.id}`}>
                        <AlertTitle>{t.notebooks.draftWhyVerifyTitle}</AlertTitle>
                        <AlertDescription>{t.notebooks.draftWhyVerifyDescription}</AlertDescription>
                      </Alert>
                    ) : null}
                    {draft.verified_brief_snapshot ? (
                      <div
                        className="rounded-md border bg-muted/30 p-3 text-sm"
                        data-testid={`draft-verified-summary-${draft.id}`}
                      >
                        <p className="font-medium">{t.notebooks.draftVerifiedSnapshotFrozen}</p>
                        <p className="mt-1 text-muted-foreground">
                          {t("notebooks.draftVerifiedSnapshotSummary", {
                            version: String(
                              (draft.verified_brief_snapshot as Record<string, unknown>).version ??
                                draft.version,
                            ),
                            coverage: String(
                              (
                                (draft.verified_brief_snapshot as Record<string, unknown>)
                                  .metrics as Record<string, unknown> | undefined
                              )?.coverage_rate ?? draft.metrics.coverage_rate,
                            ),
                          })}
                        </p>
                      </div>
                    ) : null}
                    {(() => {
                      const comparisonBase = findComparisonBase(draft, drafts);
                      if (!comparisonBase) {
                        return null;
                      }
                      const coverageDelta =
                        draft.metrics.coverage_rate - comparisonBase.metrics.coverage_rate;
                      const sourceDelta =
                        draft.source_ids.length - comparisonBase.source_ids.length;
                      const claimDelta = draft.claims.length - comparisonBase.claims.length;
                      const threadDelta =
                        draft.thread_ids.length - comparisonBase.thread_ids.length;
                      return (
                        <div
                          className="rounded-md border bg-muted/30 p-3 text-sm"
                          data-testid={`draft-compare-summary-${draft.id}`}
                        >
                          <p className="font-medium">
                            {t("notebooks.draftComparedWithVersion", {
                              version: comparisonBase.version,
                            })}
                          </p>
                          <div className="mt-2 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
                            <div>
                              <p className="text-xs text-muted-foreground">
                                {t.notebooks.draftCoverageDelta}
                              </p>
                              <p className="font-semibold">
                                {coverageDelta >= 0 ? "+" : ""}
                                {coverageDelta.toFixed(2)}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">
                                {t.notebooks.draftSourceDelta}
                              </p>
                              <p className="font-semibold">{formatSignedDelta(sourceDelta)}</p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">
                                {t.notebooks.draftClaimDelta}
                              </p>
                              <p className="font-semibold">{formatSignedDelta(claimDelta)}</p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">
                                {t.notebooks.draftThreadDelta}
                              </p>
                              <p className="font-semibold">{formatSignedDelta(threadDelta)}</p>
                            </div>
                          </div>
                          <p className="mt-2 text-xs text-muted-foreground">
                            {t.notebooks.draftCompareHint}
                          </p>
                        </div>
                      );
                    })()}
                  </CardHeader>
                  <CardContent>
                    <Accordion type="single" collapsible className="w-full">
                      <AccordionItem value="claims">
                        <AccordionTrigger>{t.notebooks.draftSectionsAndClaims}</AccordionTrigger>
                        <AccordionContent>
                          <div className="space-y-4">
                            <div>
                              <h4 className="mb-2 font-medium">{t.notebooks.draftSections}</h4>
                              {draft.sections.length === 0 ? (
                                <p className="text-sm text-muted-foreground">
                                  {t.notebooks.draftNoSections}
                                </p>
                              ) : (
                                <ul className="space-y-2 text-sm">
                                  {draft.sections.map((section, index) => (
                                    <li
                                      key={`${draft.id}-section-${index}`}
                                      className="rounded-md border p-3"
                                    >
                                      <p className="font-medium">
                                        {String(
                                          (section as Record<string, unknown>).title ??
                                            t("notebooks.draftSectionFallback", {
                                              index: index + 1,
                                            }),
                                        )}
                                      </p>
                                      <p className="mt-1 text-xs text-muted-foreground">
                                        {t.notebooks.draftPids}:{" "}
                                        {renderPidList(
                                          (section as Record<string, unknown>).source_pids,
                                          t.common.none,
                                        )}
                                      </p>
                                    </li>
                                  ))}
                                </ul>
                              )}
                            </div>
                            <div>
                              <h4 className="mb-2 font-medium">{t.notebooks.draftClaims}</h4>
                              {draft.claims.length === 0 ? (
                                <p className="text-sm text-muted-foreground">
                                  {t.notebooks.draftNoClaims}
                                </p>
                              ) : (
                                <ul className="space-y-2 text-sm">
                                  {draft.claims.map((claim, index) => (
                                    <li
                                      key={`${draft.id}-claim-${index}`}
                                      className="rounded-md border p-3"
                                    >
                                      <p>{String((claim as Record<string, unknown>).text ?? "")}</p>
                                      <p className="mt-1 text-xs text-muted-foreground">
                                        {t.notebooks.draftPids}:{" "}
                                        {renderPidList(
                                          (claim as Record<string, unknown>).source_pids,
                                          t.common.none,
                                        )}
                                      </p>
                                    </li>
                                  ))}
                                </ul>
                              )}
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
