"use client";

import { formatDistanceToNow } from "date-fns";
import {
  Archive,
  ArchiveRestore,
  FileText,
  MoreHorizontal,
  StickyNote,
  Trash2,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useUpdateNotebook } from "@/lib/hooks/use-notebooks";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { NotebookResponse } from "@/lib/types/api";
import { getDateLocale } from "@/lib/utils/date-locale";
import { NotebookDeleteDialog } from "./NotebookDeleteDialog";

interface NotebookCardProps {
  notebook: NotebookResponse;
}

export function NotebookCard({ notebook }: NotebookCardProps) {
  const { t, language } = useTranslation();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);
  const [isOpening, setIsOpening] = useState(false);
  const router = useRouter();
  const updateNotebook = useUpdateNotebook();

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  const handleArchiveToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    updateNotebook.mutate({
      id: notebook.id,
      data: { archived: !notebook.archived },
    });
  };

  const handleCardClick = () => {
    if (isOpening) {
      return;
    }
    setIsOpening(true);
    router.push(`/notebooks/${encodeURIComponent(notebook.id)}`);
  };

  const openNotebookLabel = `Open notebook ${notebook.name}`;

  return (
    <>
      <Card
        className="group card-hover ui-card-surface relative rounded-[1.35rem] border-border/80 bg-card/95 shadow-none"
        data-testid={`notebook-card-${notebook.id}`}
        aria-busy={isOpening}
        onClick={handleCardClick}
      >
        <button
          type="button"
          className="absolute inset-0 z-10 rounded-[inherit] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          onClick={(event) => {
            event.stopPropagation();
            handleCardClick();
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              event.stopPropagation();
              handleCardClick();
            }
          }}
          disabled={isOpening}
          aria-label={openNotebookLabel}
          data-testid={`notebook-open-${notebook.id}`}
        >
          <span className="sr-only">{openNotebookLabel}</span>
        </button>
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <CardTitle className="truncate font-serif text-[1.35rem] leading-none tracking-[-0.03em]">
                {notebook.name}
              </CardTitle>
              {notebook.archived && (
                <Badge variant="secondary" className="mt-2">
                  {t.notebooks.archived}
                </Badge>
              )}
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="ui-actions-reveal relative z-20 rounded-xl transition-transform duration-150 ease-out active:scale-[0.98]"
                  onClick={(e) => e.stopPropagation()}
                  aria-label={t.common.actions}
                >
                  <MoreHorizontal className="ui-icon-shift h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
                <DropdownMenuItem onClick={handleArchiveToggle}>
                  {notebook.archived ? (
                    <>
                      <ArchiveRestore className="ui-icon-shift h-4 w-4 mr-2" />
                      {t.notebooks.unarchive}
                    </>
                  ) : (
                    <>
                      <Archive className="ui-icon-shift h-4 w-4 mr-2" />
                      {t.notebooks.archive}
                    </>
                  )}
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowDeleteDialog(true);
                  }}
                  className="text-destructive"
                >
                  <Trash2 className="ui-icon-shift h-4 w-4 mr-2" />
                  {t.common.delete}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>

        <CardContent>
          <CardDescription className="line-clamp-3 text-sm leading-6">
            {notebook.description || t.chat.noDescription}
          </CardDescription>

          <div className="mt-4 border-t border-border/70 pt-4 text-xs text-muted-foreground">
            <span suppressHydrationWarning>
              {isHydrated
                ? t.common.updated.replace(
                    "{time}",
                    formatDistanceToNow(new Date(notebook.updated), {
                      addSuffix: true,
                      locale: getDateLocale(language),
                    }),
                  )
                : t.common.updated.replace("{time}", "...")}
            </span>
            {isOpening && <span className="ml-2 ui-shimmer">{t.common.processing}</span>}
          </div>

          {/* Item counts footer */}
          <div className="mt-4 flex items-center gap-2">
            <Badge
              variant="secondary"
              className="ui-data-chip flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em]"
            >
              <FileText className="h-3 w-3" />
              <span>{notebook.source_count}</span>
            </Badge>
            <Badge
              variant="secondary"
              className="ui-data-chip flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em]"
            >
              <StickyNote className="h-3 w-3" />
              <span>{notebook.note_count}</span>
            </Badge>
          </div>
        </CardContent>
      </Card>

      <NotebookDeleteDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        notebookId={notebook.id}
        notebookName={notebook.name}
      />
    </>
  );
}
