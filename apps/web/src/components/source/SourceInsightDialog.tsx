"use client";

import { FileText, GitBranchPlus, MessageCircleQuestion, StickyNote } from "lucide-react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useInsight, useSaveInsightAsNote } from "@/lib/hooks/use-insights";
import { useModalManager } from "@/lib/hooks/use-modal-manager";
import { useSource } from "@/lib/hooks/use-sources";
import { useTranslation } from "@/lib/hooks/use-translation";

interface SourceInsightDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  insight?: {
    id: string;
    insight_type?: string;
    content?: string;
    created?: string;
    source_id?: string;
  };
  onDelete?: (insightId: string) => Promise<void>;
  canSaveAsNote?: boolean;
  isSavingAsNote?: boolean;
  onSaveAsNote?: (insight: {
    id: string;
    insight_type?: string;
    content?: string;
    created?: string;
    source_id?: string;
  }) => Promise<void> | void;
  canSaveToResearchThread?: boolean;
  isSavingToResearchThread?: boolean;
  onSaveToResearchThread?: (insight: {
    id: string;
    insight_type?: string;
    content?: string;
    created?: string;
    source_id?: string;
  }) => Promise<void> | void;
  onResearchThisInsight?: (insight: {
    id: string;
    insight_type?: string;
    content?: string;
    created?: string;
    source_id?: string;
  }) => Promise<void> | void;
}

export function SourceInsightDialog({
  open,
  onOpenChange,
  insight,
  onDelete,
  canSaveAsNote = false,
  isSavingAsNote = false,
  onSaveAsNote,
  canSaveToResearchThread = false,
  isSavingToResearchThread = false,
  onSaveToResearchThread,
  onResearchThisInsight,
}: SourceInsightDialogProps) {
  const { t } = useTranslation();
  const { openModal } = useModalManager();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Ensure insight ID has 'source_insight:' prefix for API calls
  const insightIdWithPrefix = insight?.id
    ? insight.id.includes(":")
      ? insight.id
      : `source_insight:${insight.id}`
    : "";

  const { data: fetchedInsight, isLoading } = useInsight(insightIdWithPrefix, {
    enabled: open && !!insight?.id,
  });

  // Use fetched data if available, otherwise fall back to passed-in insight
  const displayInsight = fetchedInsight ?? insight;

  // Get source_id from fetched data (preferred) or passed-in insight
  const sourceId = fetchedInsight?.source_id ?? insight?.source_id;
  const { data: source } = useSource(open ? (sourceId ?? "") : "");
  const saveInsightAsNote = useSaveInsightAsNote();
  const primaryNotebookId = source?.notebooks?.[0];
  const isSaving = isSavingAsNote || isSavingToResearchThread || saveInsightAsNote.isPending;
  const hasParentSaveHandler = Boolean(onSaveAsNote);
  const canUseNotebookSave = Boolean(onSaveAsNote && canSaveAsNote);
  const canUseResearchThreadSave = Boolean(onSaveToResearchThread && canSaveToResearchThread);
  const canSaveDirectly = Boolean(displayInsight?.id);
  const canShowSaveAsNote = canSaveDirectly && (!hasParentSaveHandler || canUseNotebookSave);
  const canShowSaveToResearchThread = canSaveDirectly && canUseResearchThreadSave;

  const handleViewSource = () => {
    if (sourceId) {
      openModal("source", sourceId);
    }
  };

  const handleSaveAsNote = async () => {
    if (!displayInsight) {
      return;
    }

    if (hasParentSaveHandler) {
      if (!canUseNotebookSave || !onSaveAsNote) {
        return;
      }
      await onSaveAsNote({
        id: displayInsight.id,
        insight_type: displayInsight.insight_type,
        content: displayInsight.content,
        created: displayInsight.created,
        source_id: sourceId,
      });
      return;
    }

    const note = await saveInsightAsNote.mutateAsync({
      insightId: displayInsight.id.includes(":")
        ? displayInsight.id
        : `source_insight:${displayInsight.id}`,
      notebookId: primaryNotebookId,
    });
    onOpenChange(false);
    openModal("note", note.id);
  };

  const handleResearchThisInsight = async () => {
    if (!displayInsight || !onResearchThisInsight) {
      return;
    }

    await onResearchThisInsight({
      id: displayInsight.id,
      insight_type: displayInsight.insight_type,
      content: displayInsight.content,
      created: displayInsight.created,
      source_id: sourceId,
    });
  };

  const handleSaveToResearchThread = async () => {
    if (!displayInsight || !canUseResearchThreadSave || !onSaveToResearchThread) {
      return;
    }

    await onSaveToResearchThread({
      id: displayInsight.id,
      insight_type: displayInsight.insight_type,
      content: displayInsight.content,
      created: displayInsight.created,
      source_id: sourceId,
    });
  };

  const handleDelete = async () => {
    if (!insight?.id || !onDelete) {
      return;
    }
    setIsDeleting(true);
    try {
      await onDelete(insight.id);
      onOpenChange(false);
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  // Reset delete confirmation when dialog closes
  useEffect(() => {
    if (!open) {
      setShowDeleteConfirm(false);
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between gap-2">
            <span>{t.sources.sourceInsight}</span>
            <div className="flex items-center gap-2">
              {displayInsight?.insight_type && (
                <Badge variant="outline" className="text-xs uppercase">
                  {displayInsight.insight_type}
                </Badge>
              )}
              {onDelete && insight?.id && !showDeleteConfirm && (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setShowDeleteConfirm(true)}
                  disabled={isSaving}
                  aria-label="Delete insight"
                >
                  {t.common.delete}
                </Button>
              )}
            </div>
          </DialogTitle>
          <DialogDescription className="sr-only">{t.sources.sourceInsight}</DialogDescription>
        </DialogHeader>
        <div
          className="rounded-lg border bg-muted/20 p-4"
          data-testid="structured-insight-next-steps"
        >
          <p className="text-sm font-medium">{t.sources.insightsNextLaneTitle}</p>
          <p className="mt-2 text-sm text-muted-foreground">
            {t.sources.insightsNextLaneDescription}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {canShowSaveAsNote ? (
              <Badge variant="secondary">{t.sources.saveInsightAsNote}</Badge>
            ) : null}
            <Badge variant="outline">{t.sources.researchThisInsight}</Badge>
            {canShowSaveToResearchThread ? (
              <Badge variant="outline">{t.sources.saveInsightToResearchThread}</Badge>
            ) : null}
          </div>
        </div>
        {(!canUseNotebookSave && onSaveAsNote) ||
        (!canUseResearchThreadSave && onSaveToResearchThread) ? (
          <p className="text-sm text-muted-foreground">{t.sources.saveInsightNeedsNotebook}</p>
        ) : null}
        <div
          className="flex flex-wrap gap-2 rounded-lg border bg-muted/10 p-3"
          data-testid="structured-insight-actions"
        >
          {canShowSaveAsNote && (
            <Button
              size="sm"
              onClick={() => void handleSaveAsNote()}
              disabled={isSaving}
              className="gap-1"
              aria-busy={isSaving}
            >
              <StickyNote className="h-3 w-3" />
              {isSaving ? t.common.saving : t.sources.saveInsightAsNote}
            </Button>
          )}
          {canShowSaveToResearchThread ? (
            <Button
              variant={canShowSaveAsNote ? "outline" : "default"}
              size="sm"
              onClick={() => void handleSaveToResearchThread()}
              disabled={isSaving}
              className="gap-1"
              aria-busy={isSaving}
            >
              <GitBranchPlus className="h-3 w-3" />
              {isSavingToResearchThread ? t.common.saving : t.sources.saveInsightToResearchThread}
            </Button>
          ) : null}
          {canSaveDirectly && onResearchThisInsight ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => void handleResearchThisInsight()}
              disabled={isSaving}
              className="gap-1"
            >
              <MessageCircleQuestion className="h-3 w-3" />
              {t.sources.researchThisInsight}
            </Button>
          ) : null}
          {sourceId && (
            <Button variant="outline" size="sm" onClick={handleViewSource} className="gap-1">
              <FileText className="h-3 w-3" />
              {t.sources.viewSource}
            </Button>
          )}
        </div>

        {showDeleteConfirm ? (
          <div className="flex flex-col items-center justify-center py-8 gap-4">
            <p className="text-center text-muted-foreground">
              {t.sources.deleteInsightConfirm.split(/[?？]/)[0]}?<br />
              <span className="text-sm">
                {t.sources.deleteInsightConfirm.split(/[?？]/)[1]?.trim() || t.common.deleteForever}
              </span>
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting || isSaving}
              >
                {t.common.cancel}
              </Button>
              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={isDeleting || isSaving}
              >
                {isDeleting ? t.common.deleting : t.common.delete}
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto min-h-0">
            {isLoading ? (
              <div className="flex items-center justify-center py-10">
                <span className="text-sm text-muted-foreground">{t.common.loading}</span>
              </div>
            ) : displayInsight?.content ? (
              <div className="prose prose-sm prose-neutral dark:prose-invert max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    table: ({ children }) => (
                      <div className="my-4 overflow-x-auto">
                        <table className="min-w-full border-collapse border border-border">
                          {children}
                        </table>
                      </div>
                    ),
                    thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
                    tbody: ({ children }) => <tbody>{children}</tbody>,
                    tr: ({ children }) => <tr className="border-b border-border">{children}</tr>,
                    th: ({ children }) => (
                      <th className="border border-border px-3 py-2 text-left font-semibold">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="border border-border px-3 py-2">{children}</td>
                    ),
                  }}
                >
                  {displayInsight.content}
                </ReactMarkdown>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">{t.sources.noInsightSelected}</p>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
