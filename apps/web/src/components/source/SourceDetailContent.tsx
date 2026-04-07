"use client";

import { useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { formatDistanceToNow } from "date-fns";
import {
  AlertCircle,
  AlignLeft,
  CheckCircle,
  Copy,
  Database,
  Download,
  ExternalLink,
  Link as LinkIcon,
  MessageSquare,
  MoreVertical,
  Trash2,
  Upload,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { InlineEdit } from "@/components/common/InlineEdit";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { NotebookAssociations } from "@/components/source/NotebookAssociations";
import { SourceContentTab } from "@/components/source/SourceContentTab";
import { SourceInsightDialog } from "@/components/source/SourceInsightDialog";
import { SourceInsightsTab } from "@/components/source/SourceInsightsTab";
import { SourceOutcomeJourneyCard } from "@/components/source/SourceOutcomeJourneyCard";
import { SourceProcessingReportPanel } from "@/components/source/SourceProcessingReportPanel";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { embeddingApi } from "@/lib/api/embedding";
import { insightsApi, type SourceInsightResponse } from "@/lib/api/insights";
import { sourcesApi } from "@/lib/api/sources";
import { transformationsApi } from "@/lib/api/transformations";
import { useAuditableRuns } from "@/lib/hooks/use-auditable-runs";
import { useNotebookDrafts } from "@/lib/hooks/use-drafts";
import { useModalManager } from "@/lib/hooks/use-modal-manager";
import { useCreateResearchThread } from "@/lib/hooks/use-research-threads";
import { useReprocessSource, useSourceProcessingReport } from "@/lib/hooks/use-sources";
import { useTranslation } from "@/lib/hooks/use-translation";
import { appLog } from "@/lib/log";
import type { SourceDetailResponse } from "@/lib/types/api";
import type { Transformation } from "@/lib/types/transformations";
import { getDateLocale } from "@/lib/utils/date-locale";

interface SourceDetailContentProps {
  sourceId: string;
  showChatButton?: boolean;
  onChatClick?: () => void;
  onClose?: () => void;
}

function getYouTubeVideoId(url: string): string | null {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
    /youtube\.com\/watch\?.*v=([^&\n?#]+)/,
  ];

  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) {
      return match[1];
    }
  }
  return null;
}

export function SourceDetailContent({
  sourceId,
  showChatButton = false,
  onChatClick,
  onClose,
}: SourceDetailContentProps) {
  const { t, language } = useTranslation();
  const loadFailedMessage = t.sources.loadFailed;
  const router = useRouter();
  const queryClient = useQueryClient();
  const { openModal } = useModalManager();
  const createResearchThread = useCreateResearchThread();
  const sourceProcessingReportQuery = useSourceProcessingReport(sourceId, Boolean(sourceId));
  const reprocessSource = useReprocessSource();
  const { latestRun } = useAuditableRuns(sourceId);

  const [source, setSource] = useState<SourceDetailResponse | null>(null);
  const [insights, setInsights] = useState<SourceInsightResponse[]>([]);
  const [transformations, setTransformations] = useState<Transformation[]>([]);
  const [selectedTransformation, setSelectedTransformation] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [creatingInsight, setCreatingInsight] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [isEmbedding, setIsEmbedding] = useState(false);
  const [isDownloadingFile, setIsDownloadingFile] = useState(false);
  const [fileAvailable, setFileAvailable] = useState<boolean | null>(null);
  const [selectedInsight, setSelectedInsight] = useState<SourceInsightResponse | null>(null);
  const [savingInsightId, setSavingInsightId] = useState<string | null>(null);
  const [savingInsightThreadId, setSavingInsightThreadId] = useState<string | null>(null);
  const [insightToDelete, setInsightToDelete] = useState<string | null>(null);
  const [deletingInsight, setDeletingInsight] = useState(false);
  const [activeTab, setActiveTab] = useState("content");
  const primaryNotebookId = source?.notebooks?.[0] ?? "";
  const { drafts: notebookDrafts } = useNotebookDrafts(primaryNotebookId);
  const latestNotebookDraft = notebookDrafts[0] ?? null;
  const canSaveInsightsAsNotes = Boolean(primaryNotebookId);

  const fetchSource = useCallback(async () => {
    try {
      setLoading(true);
      const data = await sourcesApi.get(sourceId);
      setSource(data);
      if (typeof data.file_available === "boolean") {
        setFileAvailable(data.file_available);
      } else if (!data.asset?.file_path) {
        setFileAvailable(null);
      } else {
        setFileAvailable(null);
      }
    } catch (err) {
      appLog.error("source-detail", "Failed to fetch source", { sourceId, error: err });
      setError(loadFailedMessage);
    } finally {
      setLoading(false);
    }
  }, [loadFailedMessage, sourceId]);

  const fetchInsights = useCallback(async () => {
    try {
      setLoadingInsights(true);
      const data = await insightsApi.listForSource(sourceId);
      setInsights(data);
    } catch (err) {
      appLog.error("source-detail", "Failed to fetch insights", { sourceId, error: err });
    } finally {
      setLoadingInsights(false);
    }
  }, [sourceId]);

  const fetchTransformations = useCallback(async () => {
    try {
      const data = await transformationsApi.list();
      setTransformations(data);
    } catch (err) {
      appLog.error("source-detail", "Failed to fetch transformations", err);
    }
  }, []);

  useEffect(() => {
    if (!sourceId) {
      return;
    }
    void fetchSource();
    void fetchInsights();
    void fetchTransformations();
  }, [fetchInsights, fetchSource, fetchTransformations, sourceId]);

  const createInsight = async () => {
    if (!selectedTransformation) {
      toast.error(t.sources.selectTransformation);
      return;
    }

    try {
      setCreatingInsight(true);
      const response = await insightsApi.create(sourceId, {
        transformation_id: selectedTransformation,
      });
      toast.success(t.sources.insightGenerationStarted);
      setSelectedTransformation("");

      if (response.command_id) {
        insightsApi
          .waitForCommand(response.command_id, {
            maxAttempts: 120,
            intervalMs: 2000,
          })
          .then((success) => {
            if (success) {
              void fetchInsights();
              queryClient.invalidateQueries({ queryKey: ["sources"] });
            }
          })
          .catch((err) => {
            appLog.error("source-detail", "Failed while waiting for insight command", {
              sourceId,
              error: err,
            });
          });
      } else {
        setTimeout(() => {
          void fetchInsights();
          queryClient.invalidateQueries({ queryKey: ["sources"] });
        }, 5000);
      }
    } catch (err) {
      appLog.error("source-detail", "Failed to create insight", { sourceId, error: err });
      toast.error(t.common.error);
    } finally {
      setCreatingInsight(false);
    }
  };

  const handleDeleteInsight = async (e?: React.MouseEvent) => {
    e?.preventDefault();
    if (!insightToDelete) {
      return;
    }

    try {
      setDeletingInsight(true);
      await insightsApi.delete(insightToDelete);
      toast.success(t.common.success);
      setInsightToDelete(null);
      await fetchInsights();
    } catch (err) {
      appLog.error("source-detail", "Failed to delete insight", {
        sourceId,
        insightId: insightToDelete,
        error: err,
      });
      toast.error(t.common.error);
    } finally {
      setDeletingInsight(false);
    }
  };

  const handleSaveInsightAsNote = async (insight: SourceInsightResponse) => {
    if (!primaryNotebookId) {
      toast.error(t.sources.saveInsightNeedsNotebook);
      return;
    }

    try {
      setSavingInsightId(insight.id);
      const note = await insightsApi.saveAsNote(insight.id, {
        notebook_id: primaryNotebookId,
      });
      toast.success(t.sources.saveInsightAsNoteSuccess);
      setSelectedInsight(null);
      openModal("note", note.id);
      queryClient.invalidateQueries({ queryKey: ["notes"] });
    } catch (err) {
      appLog.error("source-detail", "Failed to save insight as note", {
        sourceId,
        insightId: insight.id,
        notebookId: primaryNotebookId,
        error: err,
      });
      toast.error(t.sources.saveInsightAsNoteFailed);
    } finally {
      setSavingInsightId(null);
    }
  };

  const handleResearchInsight = (insight: SourceInsightResponse) => {
    const normalizedSummary = insight.content.replace(/\s+/g, " ").trim();
    const summary =
      normalizedSummary.length > 180
        ? `${normalizedSummary.slice(0, 177).trimEnd()}...`
        : normalizedSummary;
    const seed = summary
      ? t("sources.researchInsightSeed", {
          type: insight.insight_type || t.sources.sourceInsight,
          summary,
        })
      : t("sources.researchInsightSeedFallback", {
          type: insight.insight_type || t.sources.sourceInsight,
        });
    const params = new URLSearchParams({
      mode: "ask",
      autostart: "0",
      q: seed,
    });

    if (sourceId) {
      params.set("source", sourceId);
    }
    if (primaryNotebookId) {
      params.set("notebook", primaryNotebookId);
    }

    setSelectedInsight(null);
    router.push(`/search?${params.toString()}`);
  };

  const handleSaveInsightToResearchThread = async (insight: SourceInsightResponse) => {
    if (!primaryNotebookId) {
      toast.error(t.sources.saveInsightNeedsNotebook);
      return;
    }

    const normalizedSummary = insight.content.replace(/\s+/g, " ").trim();
    const summary =
      normalizedSummary.length > 180
        ? `${normalizedSummary.slice(0, 177).trimEnd()}...`
        : normalizedSummary;
    const seed = summary
      ? t("sources.researchInsightSeed", {
          type: insight.insight_type || t.sources.sourceInsight,
          summary,
        })
      : t("sources.researchInsightSeedFallback", {
          type: insight.insight_type || t.sources.sourceInsight,
        });

    try {
      setSavingInsightThreadId(insight.id);
      const thread = await createResearchThread.mutateAsync({
        notebookId: primaryNotebookId,
        payload: {
          title: t("sources.savedInsightThreadTitle", {
            type: insight.insight_type || t.sources.sourceInsight,
          }),
          seed_kind: "insight",
          question: seed,
          answer: insight.content,
          insight_id: insight.id,
          insight_type: insight.insight_type,
          source_ids: sourceId ? [sourceId] : [],
          note_ids: [],
          search_results: [],
        },
      });
      setSelectedInsight(null);
      const params = new URLSearchParams({
        draftSeedThread: thread.id,
      });
      router.push(
        `/notebooks/${encodeURIComponent(primaryNotebookId)}?${params.toString()}#research-threads-panel`,
      );
    } catch (err) {
      appLog.error("source-detail", "Failed to save insight to research thread", {
        sourceId,
        insightId: insight.id,
        notebookId: primaryNotebookId,
        error: err,
      });
      toast.error(t.common.error);
    } finally {
      setSavingInsightThreadId(null);
    }
  };

  const handleUpdateTitle = async (title: string) => {
    if (!source || title === source.title) {
      return;
    }

    try {
      await sourcesApi.update(sourceId, { title });
      toast.success(t.common.success);
      setSource({ ...source, title });
    } catch (err) {
      appLog.error("source-detail", "Failed to update source title", {
        sourceId,
        error: err,
      });
      toast.error(t.common.error);
      await fetchSource();
    }
  };

  const handleEmbedContent = async () => {
    if (!source) {
      return;
    }

    try {
      setIsEmbedding(true);
      const response = await embeddingApi.embedContent(sourceId, "source");
      toast.success(response.message || t.common.success);
      await fetchSource();
    } catch (err) {
      appLog.error("source-detail", "Failed to embed source content", {
        sourceId,
        error: err,
      });
      toast.error(t.common.error);
    } finally {
      setIsEmbedding(false);
    }
  };

  const handleReprocessSource = async () => {
    try {
      await reprocessSource.mutateAsync(sourceId);
      await fetchSource();
      await sourceProcessingReportQuery.refetch();
    } catch (reprocessError) {
      appLog.error("source-detail", "Failed to reprocess source", {
        sourceId,
        error: reprocessError,
      });
    }
  };

  const extractFilename = (pathOrUrl: string | undefined, fallback: string) => {
    if (!pathOrUrl) {
      return fallback;
    }
    const segments = pathOrUrl.split(/[/\\]/);
    return segments.pop() || fallback;
  };

  const parseContentDisposition = (header?: string | null) => {
    if (!header) {
      return null;
    }
    const match = header.match(/filename\*?=([^;]+)/i);
    if (!match) {
      return null;
    }
    const value = match[1].trim();
    if (value.toLowerCase().startsWith("utf-8''")) {
      return decodeURIComponent(value.slice(7));
    }
    return value.replace(/^["']|["']$/g, "");
  };

  const handleDownloadFile = async () => {
    if (!source?.asset?.file_path || isDownloadingFile || fileAvailable === false) {
      return;
    }

    try {
      setIsDownloadingFile(true);
      const response = await sourcesApi.downloadFile(source.id);
      const filenameFromHeader = parseContentDisposition(
        response.headers?.["content-disposition"] as string | undefined,
      );
      const fallbackName = extractFilename(source.asset.file_path, `source-${source.id}`);
      const filename = filenameFromHeader || fallbackName;

      const blobUrl = window.URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
      setFileAvailable(true);
      toast.success(t.common.success);
    } catch (err) {
      appLog.error("source-detail", "Failed to download file", {
        sourceId,
        error: err,
      });
      if (isAxiosError(err) && err.response?.status === 404) {
        setFileAvailable(false);
        toast.error(t.sources.fileUnavailable);
      } else {
        toast.error(t.common.error);
      }
    } finally {
      setIsDownloadingFile(false);
    }
  };

  const getSourceIcon = () => {
    if (!source) {
      return null;
    }
    if (source.asset?.url) {
      return <LinkIcon className="h-5 w-5" />;
    }
    if (source.asset?.file_path) {
      return <Upload className="h-5 w-5" />;
    }
    return <AlignLeft className="h-5 w-5" />;
  };

  const getSourceType = () => {
    if (!source) {
      return "unknown";
    }
    if (source.asset?.url) {
      return "link";
    }
    if (source.asset?.file_path) {
      return "file";
    }
    return "text";
  };

  const handleCopyUrl = useCallback(() => {
    if (!source?.asset?.url) {
      return;
    }
    navigator.clipboard.writeText(source.asset.url);
    setCopied(true);
    toast.success(t.sources.urlCopied);
    setTimeout(() => setCopied(false), 2000);
  }, [source, t]);

  const handleOpenExternal = useCallback(() => {
    if (!source?.asset?.url) {
      return;
    }
    window.open(source.asset.url, "_blank");
  }, [source]);

  const isYouTubeUrl = useMemo(() => {
    if (!source?.asset?.url) {
      return false;
    }
    return Boolean(getYouTubeVideoId(source.asset.url));
  }, [source?.asset?.url]);

  const youTubeVideoId = useMemo(() => {
    if (!source?.asset?.url) {
      return null;
    }
    return getYouTubeVideoId(source.asset.url);
  }, [source?.asset?.url]);

  const handleDelete = async () => {
    if (!source) {
      return;
    }

    if (confirm(t.sources.deleteSourceConfirm || t.common.confirm)) {
      try {
        await sourcesApi.delete(source.id);
        toast.success(t.common.success);
        onClose?.();
      } catch (deleteError) {
        appLog.error("source-detail", "Failed to delete source", {
          sourceId: source.id,
          error: deleteError,
        });
        toast.error(t.common.error);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !source) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-8">
        <p className="text-red-500">{error || t.sources.notFound}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="pb-4 px-2">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <InlineEdit
              value={source.title || ""}
              onSave={handleUpdateTitle}
              className="text-2xl font-bold"
              inputClassName="text-2xl font-bold"
              placeholder={t.sources.titlePlaceholder}
              emptyText={t.sources.untitledSource}
            />
            <p className="mt-1 text-sm text-muted-foreground">
              {t.sources.id}: {source.id}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {getSourceIcon()}
            <Badge variant="secondary" className="text-sm">
              {getSourceType()}
            </Badge>

            {showChatButton && onChatClick && (
              <Button variant="outline" size="sm" onClick={onChatClick}>
                <MessageSquare className="h-4 w-4 mr-2" />
                {t.chat.chatWith.replace("{name}", t.navigation.sources)}
              </Button>
            )}

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={t.common.actions}
                  title={t.common.actions}
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {source.asset?.file_path && (
                  <>
                    <DropdownMenuItem
                      onClick={handleDownloadFile}
                      disabled={isDownloadingFile || fileAvailable === false}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      {fileAvailable === false
                        ? t.sources.fileUnavailable
                        : isDownloadingFile
                          ? t.sources.preparing
                          : t.sources.downloadFile}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                  </>
                )}
                <DropdownMenuItem
                  onClick={handleEmbedContent}
                  disabled={isEmbedding || source.embedded}
                >
                  <Database className="mr-2 h-4 w-4" />
                  {isEmbedding
                    ? t.sources.embedding
                    : source.embedded
                      ? t.sources.alreadyEmbedded
                      : t.sources.embedContent}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive" onClick={handleDelete}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  {t.sources.deleteSource}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      <div className="px-2 pb-4">
        <SourceOutcomeJourneyCard
          source={source}
          report={sourceProcessingReportQuery.data}
          latestRun={latestRun}
          latestDraft={latestNotebookDraft}
          onOpenDetails={() => setActiveTab("details")}
        />
      </div>

      <div className="flex-1 overflow-y-auto px-2">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 sticky top-0 z-10">
            <TabsTrigger value="content">{t.sources.content}</TabsTrigger>
            <TabsTrigger value="insights">
              {t.common.insights} {insights.length > 0 && `(${insights.length})`}
            </TabsTrigger>
            <TabsTrigger value="details">{t.sources.details}</TabsTrigger>
          </TabsList>

          <SourceContentTab
            source={source}
            isYouTubeUrl={isYouTubeUrl}
            youTubeVideoId={youTubeVideoId}
          />

          <SourceInsightsTab
            insights={insights}
            transformations={transformations}
            selectedTransformation={selectedTransformation}
            creatingInsight={creatingInsight}
            loadingInsights={loadingInsights}
            canSaveInsightsAsNotes={canSaveInsightsAsNotes}
            canSaveInsightsToResearchThreads={Boolean(primaryNotebookId)}
            savingInsightId={savingInsightId}
            savingInsightThreadId={savingInsightThreadId}
            onSelectedTransformationChange={setSelectedTransformation}
            onCreateInsight={createInsight}
            onViewInsight={setSelectedInsight}
            onDeleteInsight={setInsightToDelete}
            onSaveInsightAsNote={handleSaveInsightAsNote}
            onResearchThisInsight={handleResearchInsight}
            onSaveInsightToResearchThread={handleSaveInsightToResearchThread}
          />

          <TabsContent value="details" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>{t.sources.details}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {!source.embedded && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>{t.sources.notEmbeddedAlert}</AlertTitle>
                    <AlertDescription>
                      {t.sources.notEmbeddedDesc}
                      <div className="mt-3">
                        <Button onClick={handleEmbedContent} disabled={isEmbedding} size="sm">
                          <Database className="mr-2 h-4 w-4" />
                          {isEmbedding ? t.sources.embedding : t.sources.embedContent}
                        </Button>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                <div className="space-y-4">
                  {sourceProcessingReportQuery.data ? (
                    <SourceProcessingReportPanel
                      report={sourceProcessingReportQuery.data}
                      reprocessing={reprocessSource.isPending}
                      onReprocess={handleReprocessSource}
                    />
                  ) : null}

                  {source.asset?.url && (
                    <div>
                      <h3 className="mb-2 text-sm font-semibold">{t.common.url}</h3>
                      <div className="flex items-center gap-2">
                        <code className="flex-1 rounded bg-muted px-2 py-1 text-sm">
                          {source.asset.url}
                        </code>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleCopyUrl}
                          aria-label={t.common.copyToClipboard}
                          title={t.common.copyToClipboard}
                        >
                          {copied ? (
                            <CheckCircle className="h-4 w-4" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleOpenExternal}
                          aria-label={t.common.url}
                          title={t.common.url}
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}

                  {source.asset?.file_path && (
                    <div className="space-y-2">
                      <h3 className="text-sm font-semibold">{t.sources.uploadedFile}</h3>
                      <div className="flex flex-wrap items-center gap-2">
                        <code className="rounded bg-muted px-2 py-1 text-sm">
                          {source.asset.file_path}
                        </code>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleDownloadFile}
                          disabled={isDownloadingFile || fileAvailable === false}
                        >
                          <Download className="mr-2 h-4 w-4" />
                          {fileAvailable === false
                            ? t.sources.fileUnavailable
                            : isDownloadingFile
                              ? t.sources.preparing
                              : t.common.download}
                        </Button>
                      </div>
                      {fileAvailable === false ? (
                        <p className="text-xs text-muted-foreground">
                          {t.sources.fileUnavailableDesc}
                        </p>
                      ) : null}
                    </div>
                  )}

                  {source.topics && source.topics.length > 0 && (
                    <div>
                      <h3 className="mb-2 text-sm font-semibold">{t.sources.topics}</h3>
                      <div className="flex flex-wrap gap-2">
                        {source.topics.map((topic, idx) => (
                          <Badge key={idx} variant="outline">
                            {topic}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold">{t.sources.metadata}</h3>
                    <div className="flex items-center gap-2">
                      <Database className="h-3.5 w-3.5 text-muted-foreground" />
                      <Badge
                        variant={source.embedded ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {source.embedded ? t.sources.embedded : t.sources.notEmbedded}
                      </Badge>
                    </div>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <p className="text-xs font-medium text-muted-foreground">
                        {t.common.created_label}
                      </p>
                      <p className="text-sm">
                        {formatDistanceToNow(new Date(source.created), {
                          addSuffix: true,
                          locale: getDateLocale(language),
                        })}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(source.created).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-muted-foreground">
                        {t.common.updated_label}
                      </p>
                      <p className="text-sm">
                        {formatDistanceToNow(new Date(source.updated), {
                          addSuffix: true,
                          locale: getDateLocale(language),
                        })}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(source.updated).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <NotebookAssociations
              sourceId={sourceId}
              currentNotebookIds={source.notebooks || []}
              onSave={fetchSource}
            />
          </TabsContent>
        </Tabs>
      </div>

      <SourceInsightDialog
        open={Boolean(selectedInsight)}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedInsight(null);
          }
        }}
        insight={selectedInsight ?? undefined}
        canSaveAsNote={canSaveInsightsAsNotes}
        isSavingAsNote={savingInsightId === selectedInsight?.id}
        canSaveToResearchThread={Boolean(primaryNotebookId)}
        isSavingToResearchThread={savingInsightThreadId === selectedInsight?.id}
        onSaveToResearchThread={async (insight) => {
          await handleSaveInsightToResearchThread({
            id: insight.id,
            source_id: insight.source_id ?? sourceId,
            insight_type: insight.insight_type ?? "",
            content: insight.content ?? "",
            created: insight.created ?? "",
            updated: "",
          });
        }}
        onResearchThisInsight={async (insight) => {
          handleResearchInsight({
            id: insight.id,
            source_id: insight.source_id ?? sourceId,
            insight_type: insight.insight_type ?? "",
            content: insight.content ?? "",
            created: insight.created ?? "",
            updated: "",
          });
        }}
        onSaveAsNote={async (insight) => {
          await handleSaveInsightAsNote({
            id: insight.id,
            source_id: insight.source_id ?? sourceId,
            insight_type: insight.insight_type ?? "",
            content: insight.content ?? "",
            created: insight.created ?? "",
            updated: "",
          });
        }}
        onDelete={async (insightId) => {
          try {
            await insightsApi.delete(insightId);
            toast.success(t.common.success);
            setSelectedInsight(null);
            await fetchInsights();
          } catch (err) {
            appLog.error("source-detail", "Failed to delete selected insight", {
              sourceId,
              insightId,
              error: err,
            });
            toast.error(t.common.error);
          }
        }}
      />

      <AlertDialog open={Boolean(insightToDelete)} onOpenChange={() => setInsightToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t.sources.deleteInsight}</AlertDialogTitle>
            <AlertDialogDescription>{t.sources.deleteInsightConfirm}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deletingInsight}>{t.common.cancel}</AlertDialogCancel>
            <AlertDialogAction asChild>
              <Button
                onClick={handleDeleteInsight}
                disabled={deletingInsight}
                variant="destructive"
              >
                {deletingInsight ? t.common.deleting : t.common.delete}
              </Button>
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
