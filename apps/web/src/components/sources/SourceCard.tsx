"use client";

import {
  AlertTriangle,
  CheckCircle,
  Clock,
  ExternalLink,
  FileText,
  Loader2,
  MoreVertical,
  RefreshCw,
  Trash2,
  Unlink,
  Upload,
} from "lucide-react";
import { type ReactNode, useEffect, useState } from "react";
import { ContextToggle } from "@/components/common/ContextToggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useSourceStatus } from "@/lib/hooks/use-sources";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { TranslationKeys } from "@/lib/locales";
import type { SourceListResponse } from "@/lib/types/api";
import type { ContextMode } from "@/lib/types/context";
import { cn } from "@/lib/utils";

interface SourceCardProps {
  source: SourceListResponse;
  onDelete?: (sourceId: string) => void;
  onRetry?: (sourceId: string) => void;
  onRemoveFromNotebook?: (sourceId: string) => void;
  onClick?: (sourceId: string) => void;
  onRefresh?: () => void;
  className?: string;
  showRemoveFromNotebook?: boolean;
  contextMode?: ContextMode;
  onContextModeChange?: (mode: ContextMode) => void;
}

const SOURCE_TYPE_ICONS = {
  link: ExternalLink,
  upload: Upload,
  text: FileText,
} as const;

const getStatusConfig = (t: TranslationKeys) =>
  ({
    new: {
      icon: Clock,
      badgeClassName: "ui-status-badge-processing",
      label: t.sources.statusProcessing,
      description: t.sources.statusPreparingDesc,
    },
    queued: {
      icon: Clock,
      badgeClassName: "ui-status-badge-processing",
      label: t.sources.statusQueued,
      description: t.sources.statusQueuedDesc,
    },
    running: {
      icon: Loader2,
      badgeClassName: "ui-status-badge-processing",
      label: t.sources.statusProcessing,
      description: t.sources.statusProcessingDesc,
    },
    completed: {
      icon: CheckCircle,
      badgeClassName: "ui-status-badge-completed",
      label: t.sources.statusCompleted,
      description: t.sources.statusCompletedDesc,
    },
    failed: {
      icon: AlertTriangle,
      badgeClassName: "ui-status-badge-failed",
      label: t.sources.statusFailed,
      description: t.sources.statusFailedDesc,
    },
  }) as const;

type SourceStatus = "new" | "queued" | "running" | "completed" | "failed";

function isSourceStatus(status: unknown): status is SourceStatus {
  return (
    typeof status === "string" &&
    ["new", "queued", "running", "completed", "failed"].includes(status)
  );
}

function getSourceType(source: SourceListResponse): "link" | "upload" | "text" {
  // Determine type based on asset information
  if (source.asset?.url) {
    return "link";
  }
  if (source.asset?.file_path) {
    return "upload";
  }
  return "text";
}

export function SourceCard({
  source,
  onClick,
  onDelete,
  onRetry,
  onRemoveFromNotebook,
  onRefresh,
  className,
  showRemoveFromNotebook = false,
  contextMode,
  onContextModeChange,
}: SourceCardProps) {
  const { t } = useTranslation();
  const statusConfigMap = getStatusConfig(t);

  // Only fetch status for sources that might have async processing
  const sourceWithStatus = source as SourceListResponse & {
    command_id?: string;
    status?: unknown;
  };

  // Track processing state to continue polling until we detect completion
  const [wasProcessing, setWasProcessing] = useState(false);

  const shouldFetchStatus =
    !!sourceWithStatus.command_id ||
    sourceWithStatus.status === "new" ||
    sourceWithStatus.status === "queued" ||
    sourceWithStatus.status === "running" ||
    wasProcessing; // Keep polling if we were processing to catch the completion

  const { data: statusData, isLoading: statusLoading } = useSourceStatus(
    source.id,
    shouldFetchStatus,
  );

  // Determine current status
  // If source has a command_id but no status, treat as "new" (just created)
  const rawStatus = statusData?.status || sourceWithStatus.status;
  const currentStatus: SourceStatus = isSourceStatus(rawStatus)
    ? rawStatus
    : sourceWithStatus.command_id
      ? "new"
      : "completed";

  // Track processing state and detect completion
  useEffect(() => {
    const currentStatusFromData = statusData?.status || sourceWithStatus.status;

    // If we're currently processing, mark that we were processing
    if (
      currentStatusFromData === "new" ||
      currentStatusFromData === "running" ||
      currentStatusFromData === "queued"
    ) {
      setWasProcessing(true);
    }

    // If we were processing and now completed/failed, trigger refresh and stop polling
    if (
      wasProcessing &&
      (currentStatusFromData === "completed" || currentStatusFromData === "failed")
    ) {
      setWasProcessing(false); // Stop polling

      if (onRefresh) {
        setTimeout(() => onRefresh(), 500); // Small delay to ensure API is updated
      }
    }
  }, [statusData, sourceWithStatus.status, wasProcessing, onRefresh]);

  const statusConfig = statusConfigMap[currentStatus] || statusConfigMap.completed;
  const StatusIcon = statusConfig.icon;
  const sourceType = getSourceType(source);
  const SourceTypeIcon = SOURCE_TYPE_ICONS[sourceType];

  const title = source.title || t.sources.untitledSource;
  const openSourceLabel = `Open source ${title}`;

  const handleRetry = () => {
    if (onRetry) {
      onRetry(source.id);
    }
  };

  const handleDelete = () => {
    if (onDelete) {
      onDelete(source.id);
    }
  };

  const handleRemoveFromNotebook = () => {
    if (onRemoveFromNotebook) {
      onRemoveFromNotebook(source.id);
    }
  };

  const handleCardClick = () => {
    if (onClick) {
      onClick(source.id);
    }
  };

  const isProcessing: boolean =
    currentStatus === "new" || currentStatus === "running" || currentStatus === "queued";
  const isCompleted: boolean = currentStatus === "completed";
  const failedActions: ReactNode =
    currentStatus === "failed" ? (
      <div className="flex gap-2 pt-2 border-t relative z-20">
        <Button
          variant="outline"
          size="sm"
          onClick={handleRetry}
          disabled={!onRetry}
          className="ui-icon-button h-7 text-xs"
        >
          <RefreshCw className="h-3 w-3 mr-1" />
          {String(t.sources.retry)}
        </Button>
      </div>
    ) : null;

  return (
    <Card
      className={cn(
        "ui-card-surface transition-all duration-200 hover:shadow-md group relative border border-border/60 dark:border-border/40",
        onClick && "focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2",
        isProcessing && "ui-loading-pulse",
        className,
      )}
      data-testid={`source-card-${source.id}`}
      aria-busy={isProcessing}
    >
      {onClick ? (
        <button
          type="button"
          onClick={handleCardClick}
          className="absolute inset-0 z-10 rounded-[inherit] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          aria-label={openSourceLabel}
        >
          <span className="sr-only">{openSourceLabel}</span>
        </button>
      ) : null}
      <CardContent className="px-3 py-1">
        {/* Header with status indicator */}
        <div className="flex items-start justify-between gap-3 mb-1">
          <div className="flex-1 min-w-0">
            {/* Status badge - only show if not completed */}
            {!isCompleted && (
              <div className="flex items-center gap-2 mb-2">
                <div
                  className={cn(
                    "ui-status-badge flex items-center gap-1.5 px-2 py-1 rounded-md",
                    statusConfig.badgeClassName,
                  )}
                >
                  <StatusIcon
                    className={cn(
                      "h-3 w-3",
                      isProcessing && "animate-spin motion-reduce:animate-none",
                    )}
                  />
                  {statusLoading && shouldFetchStatus ? t.sources.checking : statusConfig.label}
                </div>

                {/* Source type indicator */}
                <div className="flex items-center gap-1 text-muted-foreground">
                  <SourceTypeIcon className="h-3 w-3" />
                  <span className="text-xs capitalize">{t.common.source}</span>
                </div>
              </div>
            )}

            {/* Title */}
            <div className={cn("mb-1.5", !isCompleted && "mb-1")}>
              <h4
                className="text-sm font-medium leading-tight line-clamp-2 break-all"
                title={title}
              >
                {title}
              </h4>
            </div>

            {/* Processing message for active statuses */}
            {statusData?.message && (isProcessing || currentStatus === "failed") && (
              <p className="text-xs text-muted-foreground mb-2 italic">
                {String(statusData.message)}
              </p>
            )}

            {/* Metadata badges */}
            <div className="flex items-center gap-2 flex-wrap">
              {/* Source type badge */}
              <Badge variant="secondary" className="text-xs flex items-center gap-1">
                <SourceTypeIcon className="h-3 w-3" />
                {sourceType === "link"
                  ? t.sources.addUrl
                  : sourceType === "upload"
                    ? t.sources.uploadFile
                    : t.sources.enterText}
              </Badge>

              {isCompleted && source.insights_count > 0 && (
                <Badge variant="outline" className="text-xs">
                  {t.sources.insightsCount.replace("{count}", source.insights_count.toString())}
                </Badge>
              )}
              {source.topics && source.topics.length > 0 && isCompleted && (
                <>
                  {source.topics.slice(0, 2).map((topic, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {topic}
                    </Badge>
                  ))}
                  {source.topics.length > 2 && (
                    <Badge variant="outline" className="text-xs">
                      +{source.topics.length - 2}
                    </Badge>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Context toggle and actions */}
          <div className="flex items-center gap-1 relative z-20">
            {/* Context toggle - only show if handler provided */}
            {onContextModeChange && contextMode && (
              <ContextToggle
                mode={contextMode}
                hasInsights={source.insights_count > 0}
                onChange={onContextModeChange}
              />
            )}

            {/* Actions dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="ui-actions-reveal ui-icon-button h-8 w-8 p-0 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 focus-visible:opacity-100 transition-opacity relative z-20"
                  onClick={(e) => e.stopPropagation()}
                  aria-label={t.common.actions}
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                {showRemoveFromNotebook && (
                  <>
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveFromNotebook();
                      }}
                      disabled={!onRemoveFromNotebook}
                    >
                      <Unlink className="h-4 w-4 mr-2" />
                      {t.sources.removeFromNotebook}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                  </>
                )}

                {currentStatus === "failed" && (
                  <>
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRetry();
                      }}
                      disabled={!onRetry}
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />
                      {t.sources.retryProcessing}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                  </>
                )}

                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete();
                  }}
                  disabled={!onDelete}
                  variant="destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  {t.sources.deleteSource}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        {failedActions as any}

        {/* Processing progress indicator */}
        {isProcessing && statusData?.processing_info?.progress && (
          <div className="mt-3 pt-2 border-t">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs text-muted-foreground">{t.common.progress}</span>
              <span className="text-xs text-muted-foreground">
                {Math.round(statusData.processing_info.progress as number)}%
              </span>
            </div>
            <div className="w-full bg-muted rounded-full h-1.5">
              <div
                className="bg-primary h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${statusData.processing_info.progress as number}%` }}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
