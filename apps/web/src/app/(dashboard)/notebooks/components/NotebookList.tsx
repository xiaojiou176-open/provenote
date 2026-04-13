"use client";

import { Book, ChevronDown, Plus } from "lucide-react";
import type { CSSProperties } from "react";
import { useState } from "react";
import { EmptyState } from "@/components/common/EmptyState";
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { NotebookResponse } from "@/lib/types/api";
import { cn } from "@/lib/utils";
import { NotebookCard } from "./NotebookCard";

interface NotebookListProps {
  notebooks?: NotebookResponse[];
  isLoading: boolean;
  title: string;
  collapsible?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  onAction?: () => void;
  actionLabel?: string;
}

export function NotebookList({
  notebooks,
  isLoading,
  title,
  collapsible = false,
  emptyTitle,
  emptyDescription,
  onAction,
  actionLabel,
}: NotebookListProps) {
  const { t } = useTranslation();
  const [isExpanded, setIsExpanded] = useState(!collapsible);
  const panelId = `${title}-panel`.toLowerCase().replace(/\s+/g, "-");

  if (isLoading) {
    return (
      <div
        className="ui-skeleton-grid grid grid-cols-1 gap-4 py-2 md:grid-cols-2 lg:grid-cols-3"
        role="status"
        aria-live="polite"
        aria-label={t.common.loading}
      >
        {Array.from({ length: 6 }).map((_, index) => (
          <div
            key={`skeleton-${index}`}
            className="ui-skeleton-card rounded-xl border border-border p-4"
            style={{ "--skeleton-index": index } as CSSProperties}
          >
            <div className="ui-shimmer h-4 w-2/3 rounded-md bg-muted/70" />
            <div className="ui-shimmer mt-3 h-3 w-full rounded-md bg-muted/60" />
            <div className="ui-shimmer mt-2 h-3 w-5/6 rounded-md bg-muted/60" />
            <div className="mt-4 flex gap-2">
              <div className="ui-shimmer h-5 w-14 rounded-full bg-muted/60" />
              <div className="ui-shimmer h-5 w-14 rounded-full bg-muted/60" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!notebooks || notebooks.length === 0) {
    return (
      <EmptyState
        icon={Book}
        title={emptyTitle ?? t.common.noResults}
        description={emptyDescription ?? t.chat.startByCreating}
        action={
          onAction && actionLabel ? (
            <Button onClick={onAction} variant="outline" className="ui-icon-button mt-4">
              <Plus className="h-4 w-4 mr-2" />
              {actionLabel}
            </Button>
          ) : undefined
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="ui-toolbar-surface flex items-center gap-2 px-4 py-3">
        {collapsible && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-expanded={isExpanded}
            aria-controls={panelId}
            aria-label={title}
            className="rounded-xl"
          >
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform duration-200 ease-out",
                isExpanded ? "rotate-0" : "-rotate-90",
              )}
            />
          </Button>
        )}
        <h2 className="font-serif text-2xl leading-none tracking-[-0.03em]">{title}</h2>
        <span className="rounded-full border border-border/80 bg-card/85 px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
          {notebooks.length}
        </span>
      </div>

      <div
        id={panelId}
        data-state={isExpanded ? "open" : "closed"}
        aria-hidden={!isExpanded}
        hidden={!isExpanded}
        className={cn("ui-collapse-panel", isExpanded ? "ui-collapse-open" : "ui-collapse-closed")}
      >
        <div className="ui-stagger-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {notebooks.map((notebook, index) => (
            <div
              key={notebook.id}
              className="ui-stagger-item"
              style={{ "--stagger-index": index } as CSSProperties}
            >
              <NotebookCard notebook={notebook} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
