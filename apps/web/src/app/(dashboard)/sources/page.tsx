"use client";

import { formatDistanceToNow } from "date-fns";
import {
  AlignLeft,
  ArrowRight,
  ArrowUpDown,
  FileText,
  Link as LinkIcon,
  Trash2,
  Upload,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { type KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { EmptyState } from "@/components/common/EmptyState";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { AppShell } from "@/components/layout/AppShell";
import { useCreateDialogs } from "@/components/providers/CreateDialogsProvider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { sourcesApi } from "@/lib/api/sources";
import { useTranslation } from "@/lib/hooks/use-translation";
import { appLog } from "@/lib/log";
import type { SourceListResponse } from "@/lib/types/api";
import { cn } from "@/lib/utils";
import { getDateLocale } from "@/lib/utils/date-locale";
import { getApiErrorKey } from "@/lib/utils/error-handler";

const SOURCES_PAGE_CONFIG = {
  pageSize: 30,
  loadMoreThresholdPx: 200,
  scrollDebounceMs: 100,
} as const;

export default function SourcesPage() {
  const { t, language } = useTranslation();
  const [sources, setSources] = useState<SourceListResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [sortBy, setSortBy] = useState<"created" | "updated">("updated");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [openingSourceId, setOpeningSourceId] = useState<string | null>(null);
  const [deleteDialog, setDeleteDialog] = useState<{
    open: boolean;
    source: SourceListResponse | null;
  }>({
    open: false,
    source: null,
  });
  const router = useRouter();
  const { openSourceDialog } = useCreateDialogs();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const offsetRef = useRef(0);
  const loadingMoreRef = useRef(false);
  const hasMoreRef = useRef(true);

  const firstSuccessSteps = [
    {
      number: "01",
      title: t.sources.addSource,
      detail: t.sources.processDescription,
    },
    {
      number: "02",
      title: t.sources.insights,
      detail: t.sources.insightsDesc,
    },
    {
      number: "03",
      title: t.sources.outcomeNotebookDraft,
      detail: t.sources.outcomeCreateDraftDescription,
    },
  ];

  const fetchSources = useCallback(
    async (reset = false) => {
      try {
        if (reset) {
          setLoading(true);
          offsetRef.current = 0;
          setSources([]);
          hasMoreRef.current = true;
          setError(null);
        } else {
          loadingMoreRef.current = true;
          setLoadingMore(true);
        }

        const data = await sourcesApi.list({
          limit: SOURCES_PAGE_CONFIG.pageSize,
          offset: offsetRef.current,
          sort_by: sortBy,
          sort_order: sortOrder,
        });

        if (reset) {
          setSources(data);
        } else {
          setSources((prev) => [...prev, ...data]);
        }

        // Check if we have more data
        const hasMoreData = data.length === SOURCES_PAGE_CONFIG.pageSize;
        hasMoreRef.current = hasMoreData;
        offsetRef.current += data.length;
      } catch (err) {
        appLog.error("sources-page", "Failed to fetch sources", {
          offset: offsetRef.current,
          sortBy,
          sortOrder,
          error: err,
        });
        setError(t.sources.failedToLoad);
        toast.error(t.sources.failedToLoad);
      } finally {
        setLoading(false);
        setLoadingMore(false);
        loadingMoreRef.current = false;
      }
    },
    [sortBy, sortOrder, t.sources.failedToLoad],
  );

  // Initial load and when sort changes
  const scrollToSelectedRow = useCallback((index: number) => {
    const scrollContainer = scrollContainerRef.current;
    if (!scrollContainer) {
      return;
    }

    const rows = scrollContainer.querySelectorAll("tbody tr");
    const selectedRow = rows[index] as HTMLElement;
    if (!selectedRow) {
      return;
    }

    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const behavior: ScrollBehavior = prefersReducedMotion ? "auto" : "smooth";
    const containerRect = scrollContainer.getBoundingClientRect();
    const rowRect = selectedRow.getBoundingClientRect();

    if (rowRect.top < containerRect.top) {
      selectedRow.scrollIntoView({ behavior, block: "start" });
    } else if (rowRect.bottom > containerRect.bottom) {
      selectedRow.scrollIntoView({ behavior, block: "end" });
    }
  }, []);

  const selectIndex = useCallback(
    (nextIndex: number) => {
      setSelectedIndex(nextIndex);
      requestAnimationFrame(() => {
        scrollToSelectedRow(nextIndex);
      });
    },
    [scrollToSelectedRow],
  );

  useEffect(() => {
    fetchSources(true);
  }, [fetchSources]);

  const handleContainerKeyDown = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
      const target = e.target as HTMLElement | null;
      if (
        target?.closest(
          "button, a, input, textarea, select, [contenteditable='true'], [role='button'], [role='link'], [role='checkbox'], [role='menuitem']",
        )
      ) {
        return;
      }

      if (sources.length === 0) {
        return;
      }

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          selectIndex(Math.min(selectedIndex + 1, sources.length - 1));
          break;
        case "ArrowUp":
          e.preventDefault();
          selectIndex(Math.max(selectedIndex - 1, 0));
          break;
        case "Enter":
          e.preventDefault();
          if (sources[selectedIndex]) {
            router.push(`/sources/${sources[selectedIndex].id}`);
          }
          break;
        case "Home":
          e.preventDefault();
          selectIndex(0);
          break;
        case "End":
          e.preventDefault();
          selectIndex(sources.length - 1);
          break;
        default:
          break;
      }
    },
    [router, selectedIndex, selectIndex, sources],
  );

  // Set up scroll listener after sources are loaded
  useEffect(() => {
    if (loading || sources.length === 0) {
      return;
    }

    const scrollContainer = scrollContainerRef.current;
    if (!scrollContainer) {
      return;
    }

    let scrollTimeout: NodeJS.Timeout | null = null;

    const handleScroll = () => {
      if (scrollTimeout) {
        clearTimeout(scrollTimeout);
      }

      scrollTimeout = setTimeout(() => {
        if (!scrollContainerRef.current) {
          return;
        }

        const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
        const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

        if (
          distanceFromBottom < SOURCES_PAGE_CONFIG.loadMoreThresholdPx &&
          !loadingMoreRef.current &&
          hasMoreRef.current
        ) {
          fetchSources(false);
        }
      }, SOURCES_PAGE_CONFIG.scrollDebounceMs);
    };

    scrollContainer.addEventListener("scroll", handleScroll);
    handleScroll(); // Check on mount

    return () => {
      scrollContainer.removeEventListener("scroll", handleScroll);
      if (scrollTimeout) {
        clearTimeout(scrollTimeout);
      }
    };
  }, [fetchSources, loading, sources.length]);

  const toggleSort = (field: "created" | "updated") => {
    if (sortBy === field) {
      // Toggle order if clicking the same field
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      // Switch to new field with default desc order
      setSortBy(field);
      setSortOrder("desc");
    }
  };

  const getSourceIcon = (source: SourceListResponse) => {
    if (source.asset?.url) {
      return <LinkIcon className="h-4 w-4" />;
    }
    if (source.asset?.file_path) {
      return <Upload className="h-4 w-4" />;
    }
    return <AlignLeft className="h-4 w-4" />;
  };

  const getSourceType = (source: SourceListResponse) => {
    if (source.asset?.url) {
      return t.sources.type.link;
    }
    if (source.asset?.file_path) {
      return t.sources.type.file;
    }
    return t.sources.type.text;
  };

  const openSource = useCallback(
    (sourceId: string, index?: number) => {
      if (typeof index === "number") {
        setSelectedIndex(index);
      }
      setOpeningSourceId(sourceId);
      router.push(`/sources/${sourceId}`);
    },
    [router],
  );

  const handleRowClick = useCallback(
    (index: number, sourceId: string) => {
      openSource(sourceId, index);
    },
    [openSource],
  );

  const handleDeleteClick = useCallback((e: React.MouseEvent, source: SourceListResponse) => {
    e.stopPropagation(); // Prevent row click
    setDeleteDialog({ open: true, source });
  }, []);

  const latestSourceSummary = useMemo(() => {
    if (sources.length === 0) {
      return null;
    }

    let latestIndex = 0;
    let latestTimestamp = new Date(sources[0].updated || sources[0].created).getTime();

    sources.forEach((source, index) => {
      const candidateTimestamp = new Date(source.updated || source.created).getTime();
      if (candidateTimestamp > latestTimestamp) {
        latestTimestamp = candidateTimestamp;
        latestIndex = index;
      }
    });

    return {
      source: sources[latestIndex],
      index: latestIndex,
      latestActivityAt:
        sources[latestIndex].updated || sources[latestIndex].created || new Date().toISOString(),
      embeddedCount: sources.filter((item) => item.embedded).length,
      insightCount: sources.filter((item) => (item.insights_count || 0) > 0).length,
    };
  }, [sources]);
  const sourceActionRail = useMemo(() => {
    if (sources.length === 0) {
      return [];
    }

    const newestIndex = sources.reduce((latest, source, index, items) => {
      const candidate = new Date(source.updated || source.created).getTime();
      const current = new Date(items[latest].updated || items[latest].created).getTime();
      return candidate > current ? index : latest;
    }, 0);
    const richestInsightIndex = sources.reduce((best, source, index, items) => {
      const candidate = source.insights_count || 0;
      const current = items[best].insights_count || 0;
      return candidate > current ? index : best;
    }, 0);
    const embeddingFocusIndex = sources.findIndex((source) => !source.embedded);

    return [
      {
        id: "newest",
        eyebrow: t("sources.nextRail.newestEyebrow", "Inspect freshest source"),
        title: sources[newestIndex]?.title || t.sources.untitledSource,
        body: t(
          "sources.nextRail.newestBody",
          "Open the source with the newest activity first so you can verify whether the latest import actually produced usable evidence.",
        ),
        actionLabel: t("sources.nextRail.newestAction", "Open freshest source"),
        sourceId: sources[newestIndex]?.id,
        index: newestIndex,
      },
      {
        id: "insights",
        eyebrow: t("sources.nextRail.insightsEyebrow", "Review richest insight lane"),
        title: sources[richestInsightIndex]?.title || t.sources.untitledSource,
        body: t(
          "sources.nextRail.insightsBody",
          "Jump to the source that already has the strongest model output when you want a quick path from evidence to a reusable note or draft.",
        ),
        actionLabel: t("sources.nextRail.insightsAction", "Open insight-rich source"),
        sourceId: sources[richestInsightIndex]?.id,
        index: richestInsightIndex,
      },
      embeddingFocusIndex >= 0
        ? {
            id: "embedding",
            eyebrow: t("sources.nextRail.embeddingEyebrow", "Finish source readiness"),
            title: sources[embeddingFocusIndex]?.title || t.sources.untitledSource,
            body: t(
              "sources.nextRail.embeddingBody",
              "This source still needs embedding. Opening it now keeps the sources-first path honest before you move into notebook or draft lanes.",
            ),
            actionLabel: t("sources.nextRail.embeddingAction", "Open source that needs embedding"),
            sourceId: sources[embeddingFocusIndex]?.id,
            index: embeddingFocusIndex,
          }
        : {
            id: "collect",
            eyebrow: t("sources.nextRail.collectEyebrow", "Add another source"),
            title: t("sources.nextRail.collectTitle", "Bring in the next source"),
            body: t(
              "sources.nextRail.collectBody",
              "Your current sources are already embedded. Add one more source if you want a broader evidence base before drafting.",
            ),
            actionLabel: t.sources.addSource,
            sourceId: null,
            index: null,
          },
    ];
  }, [sources, t, t.sources.addSource, t.sources.untitledSource]);

  const handleDeleteConfirm = async () => {
    if (!deleteDialog.source) {
      return;
    }

    try {
      await sourcesApi.delete(deleteDialog.source.id);
      toast.success(t.sources.deleteSuccess);
      // Remove the deleted source from the list
      setSources((prev) => prev.filter((s) => s.id !== deleteDialog.source?.id));
      setDeleteDialog({ open: false, source: null });
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      appLog.error("sources-page", "Failed to delete source", {
        sourceId: deleteDialog.source?.id,
        error,
      });
      toast.error(t(getApiErrorKey(error.response?.data?.detail || error.message)));
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="flex h-full items-center justify-center">
          <LoadingSpinner />
        </div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <div className="flex h-full items-center justify-center">
          <div className="text-center space-y-3">
            <p className="text-red-500">{error}</p>
            <Button type="button" variant="outline" onClick={() => void fetchSources(true)}>
              {t.common.retry}
            </Button>
          </div>
        </div>
      </AppShell>
    );
  }

  if (sources.length === 0) {
    return (
      <AppShell>
        <div className="ui-page-shell flex h-full w-full max-w-none flex-col gap-6 px-4 py-6 md:px-6">
          <div className="ui-section-enter mb-6">
            <Card className="ui-workbench-hero overflow-hidden border-0 shadow-none">
              <CardContent className="space-y-6 p-6 md:p-8">
                <div className="ui-workbench-grid xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)] xl:items-start">
                  <div className="space-y-4">
                    <Badge variant="secondary" className="ui-workbench-kicker w-fit">
                      {t.sources.outcomePathTitle}
                    </Badge>
                    <div className="space-y-3">
                      <h1 className="ui-page-title">{t.sources.allSources}</h1>
                      <p className="ui-page-lede">{t.sources.outcomePathDescription}</p>
                      <p className="text-sm text-muted-foreground">
                        {`${t.sources.addSource} -> ${t.sources.insights} -> ${t.sources.outcomeNotebookDraft}`}
                      </p>
                    </div>
                    <div className="flex flex-col gap-3 sm:flex-row">
                      <Button
                        type="button"
                        className="ui-primary-cta cursor-pointer"
                        onClick={openSourceDialog}
                      >
                        <Upload className="mr-2 h-4 w-4" />
                        {t.sources.addSource}
                      </Button>
                    </div>
                  </div>

                  <div className="ui-metric-grid">
                    <div className="ui-metric-card">
                      <p className="ui-metric-label">{t.sources.noSourcesYet}</p>
                      <p className="ui-metric-value">0</p>
                      <p className="ui-metric-detail">{t.sources.createFirstSource}</p>
                    </div>

                    {firstSuccessSteps.map((step) => (
                      <div key={step.number} className="ui-metric-card">
                        <p className="ui-metric-label">{step.number}</p>
                        <p className="mt-3 text-base font-semibold">{step.title}</p>
                        <p className="ui-metric-detail">{step.detail}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="ui-section-enter ui-elevated-panel flex-1 border-dashed shadow-none">
            <CardContent className="flex h-full items-center justify-center p-6">
              <EmptyState
                icon={FileText}
                title={t.sources.noSourcesYet}
                description={t.sources.allSourcesDescShort}
              />
            </CardContent>
          </Card>
        </div>
      </AppShell>
    );
  }

  const sourceSummary = latestSourceSummary ?? {
    source: sources[0],
    index: 0,
    latestActivityAt: sources[0].updated || sources[0].created || new Date().toISOString(),
    embeddedCount: sources.filter((item) => item.embedded).length,
    insightCount: sources.filter((item) => (item.insights_count || 0) > 0).length,
  };

  return (
    <AppShell>
      <div className="ui-page-shell flex h-full w-full max-w-none flex-col gap-6 px-4 py-6 md:px-6">
        <div className="ui-section-enter mb-6 flex-shrink-0 space-y-4">
          <Card className="ui-workbench-hero overflow-hidden border-0 shadow-none">
            <CardContent className="space-y-6 p-6 md:p-8">
              <div className="ui-workbench-grid xl:grid-cols-[minmax(0,1.2fr)_minmax(340px,0.8fr)] xl:items-start">
                <div className="space-y-4">
                  <Badge variant="secondary" className="ui-workbench-kicker w-fit">
                    {t.sources.outcomePathTitle}
                  </Badge>
                  <div className="space-y-3">
                    <h1 className="ui-page-title">{t.sources.allSources}</h1>
                    <p className="ui-page-lede">{t.sources.outcomePathDescription}</p>
                    <p className="text-sm text-muted-foreground">
                      {`${t.sources.addSource} -> ${t.sources.insights} -> ${t.sources.outcomeNotebookDraft}`}
                    </p>
                  </div>
                  <div className="flex flex-col gap-3 sm:flex-row">
                    <Button
                      type="button"
                      className="ui-primary-cta cursor-pointer"
                      onClick={openSourceDialog}
                    >
                      <Upload className="mr-2 h-4 w-4" />
                      {t.sources.addSource}
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      className="cursor-pointer"
                      aria-label={`${t.sources.viewSource}: ${sourceSummary.source.title || t.sources.untitledSource}`}
                      onClick={() => openSource(sourceSummary.source.id, sourceSummary.index)}
                    >
                      <ArrowRight className="mr-2 h-4 w-4" />
                      {t.sources.viewSource}
                    </Button>
                  </div>
                </div>

                <div className="ui-metric-grid">
                  <div className="ui-metric-card">
                    <p className="ui-metric-label">{t.common.title}</p>
                    <p className="mt-3 text-base font-semibold">
                      {sourceSummary.source.title || t.sources.untitledSource}
                    </p>
                    <p className="ui-metric-detail">
                      <span suppressHydrationWarning>
                        {formatDistanceToNow(new Date(sourceSummary.latestActivityAt), {
                          addSuffix: true,
                          locale: getDateLocale(language),
                        })}
                      </span>
                    </p>
                  </div>

                  <div className="ui-metric-card">
                    <p className="ui-metric-label">{t.sources.addSource}</p>
                    <p className="ui-metric-value">{sources.length}</p>
                    <p className="ui-metric-detail">{t.sources.allSourcesDescShort}</p>
                  </div>

                  <div className="ui-metric-card">
                    <p className="ui-metric-label">{t.sources.insights}</p>
                    <p className="ui-metric-value">{sourceSummary.insightCount}</p>
                    <p className="ui-metric-detail">{t.sources.insightsDesc}</p>
                  </div>

                  <div className="ui-metric-card">
                    <p className="ui-metric-label">{t.sources.embedded}</p>
                    <p className="ui-metric-value">{sourceSummary.embeddedCount}</p>
                    <div className="mt-3">
                      <Badge
                        variant={sourceSummary.source.embedded ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {sourceSummary.source.embedded ? t.sources.embedded : t.sources.notEmbedded}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-3 xl:grid-cols-3">
            {sourceActionRail.map((action) => (
              <Card
                key={action.id}
                className="ui-elevated-panel shadow-none"
                data-testid={`sources-next-action-${action.id}`}
              >
                <CardContent className="space-y-4 p-5">
                  <p className="ui-metric-label text-primary">{action.eyebrow}</p>
                  <div className="space-y-2">
                    <h2 className="text-lg font-semibold tracking-tight">{action.title}</h2>
                    <p className="text-sm leading-6 text-muted-foreground">{action.body}</p>
                  </div>
                  <Button
                    type="button"
                    variant={action.id === "embedding" ? "outline" : "default"}
                    className={cn("cursor-pointer", action.id !== "embedding" && "ui-primary-cta")}
                    onClick={() => {
                      if (action.sourceId && typeof action.index === "number") {
                        openSource(action.sourceId, action.index);
                        return;
                      }
                      openSourceDialog();
                    }}
                  >
                    <ArrowRight className="mr-2 h-4 w-4" />
                    {action.actionLabel}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="ui-toolbar-surface p-4">
            <h2 className="font-serif text-2xl leading-none tracking-[-0.03em]">
              {t.sources.allSources}
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">{t.sources.allSourcesDesc}</p>
          </div>
        </div>

        <div
          ref={scrollContainerRef}
          role="region"
          aria-label={t.sources.allSources}
          tabIndex={0}
          onKeyDown={handleContainerKeyDown}
          aria-busy={loadingMore}
          className="ui-section-enter ui-table-shell flex-1 overflow-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          <table aria-label={t.sources.allSources} className="w-full min-w-[800px] table-fixed">
            <colgroup>
              <col className="w-[120px]" />
              <col className="w-auto" />
              <col className="w-[140px]" />
              <col className="w-[100px]" />
              <col className="w-[100px]" />
              <col className="w-[100px]" />
            </colgroup>
            <thead className="sticky top-0 bg-background z-10">
              <tr className="border-b bg-muted/50">
                <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                  {t.common.type}
                </th>
                <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
                  {t.common.title}
                </th>
                <th
                  aria-sort={
                    sortBy === "created"
                      ? sortOrder === "asc"
                        ? "ascending"
                        : "descending"
                      : "none"
                  }
                  className="h-12 px-4 text-left align-middle font-medium text-muted-foreground hidden sm:table-cell"
                >
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleSort("created")}
                    className="h-8 px-2 hover:bg-muted ui-icon-button"
                  >
                    {t.common.created_label}
                    <ArrowUpDown
                      className={cn(
                        "ml-2 h-3 w-3",
                        sortBy === "created" ? "opacity-100" : "opacity-30",
                      )}
                    />
                    {sortBy === "created" && (
                      <span className="ml-1 text-xs">{sortOrder === "asc" ? "↑" : "↓"}</span>
                    )}
                  </Button>
                </th>
                <th className="h-12 px-4 text-center align-middle font-medium text-muted-foreground hidden md:table-cell">
                  {t.sources.insights}
                </th>
                <th className="h-12 px-4 text-center align-middle font-medium text-muted-foreground hidden lg:table-cell">
                  {t.sources.embedded}
                </th>
                <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">
                  {t.common.actions}
                </th>
              </tr>
            </thead>
            <tbody>
              {sources.map((source, index) => (
                <tr
                  key={source.id}
                  data-testid={`source-row-${source.id}`}
                  onClick={() => handleRowClick(index, source.id)}
                  onKeyDown={(event) => {
                    const target = event.target as HTMLElement | null;
                    if (
                      target?.closest(
                        "button, a, input, textarea, select, [contenteditable='true'], [role='button'], [role='link'], [role='checkbox'], [role='menuitem']",
                      )
                    ) {
                      return;
                    }

                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      handleRowClick(index, source.id);
                    }
                  }}
                  onMouseEnter={() => setSelectedIndex(index)}
                  tabIndex={0}
                  aria-busy={openingSourceId === source.id}
                  aria-label={(source.title || t.sources.untitledSource).toString()}
                  className={cn(
                    "border-b cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset transition-[background-color,transform,opacity] duration-150 active:scale-[0.998]",
                    selectedIndex === index ? "bg-accent" : "hover:bg-muted/50",
                    openingSourceId === source.id && "opacity-80",
                  )}
                >
                  <td className="h-12 px-4">
                    <div className="flex items-center gap-2">
                      {getSourceIcon(source)}
                      <Badge variant="secondary" className="text-xs">
                        {getSourceType(source)}
                      </Badge>
                    </div>
                  </td>
                  <td className="h-12 px-4">
                    <div className="flex flex-col overflow-hidden">
                      <span className="font-medium truncate">
                        {source.title || t.sources.untitledSource}
                      </span>
                      {source.asset?.url && (
                        <span className="text-xs text-muted-foreground truncate">
                          {source.asset.url}
                        </span>
                      )}
                      {openingSourceId === source.id && (
                        <span className="text-xs text-muted-foreground ui-shimmer">
                          {t.common.processing}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="h-12 px-4 text-muted-foreground text-sm hidden sm:table-cell">
                    <span suppressHydrationWarning>
                      {formatDistanceToNow(new Date(source.created), {
                        addSuffix: true,
                        locale: getDateLocale(language),
                      })}
                    </span>
                  </td>
                  <td className="h-12 px-4 text-center hidden md:table-cell">
                    <span className="text-sm font-medium">{source.insights_count || 0}</span>
                  </td>
                  <td className="h-12 px-4 text-center hidden lg:table-cell">
                    <Badge variant={source.embedded ? "default" : "secondary"} className="text-xs">
                      {source.embedded ? t.sources.yes : t.sources.no}
                    </Badge>
                  </td>
                  <td className="h-12 px-4 text-right">
                    <Button
                      variant="ghost"
                      size="icon"
                      data-testid="source-delete"
                      onClick={(e) => handleDeleteClick(e, source)}
                      className="text-destructive hover:text-destructive"
                      aria-label={`${t.common.delete}: ${source.title || t.sources.untitledSource}`}
                      title={t.common.delete}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
              {loadingMore && (
                <tr>
                  <td colSpan={6} className="h-16 text-center">
                    <div className="flex items-center justify-center">
                      <LoadingSpinner />
                      <span className="ml-2 text-muted-foreground">{t.sources.loadingMore}</span>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <ConfirmDialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog({ open, source: deleteDialog.source })}
        title={t.sources.delete}
        description={t.sources.deleteConfirmWithTitle.replace(
          "{title}",
          deleteDialog.source?.title || t.sources.untitledSource,
        )}
        confirmText={t.common.delete}
        confirmVariant="destructive"
        onConfirm={handleDeleteConfirm}
      />
    </AppShell>
  );
}
