"use client";

import { Plus, RefreshCw } from "lucide-react";
import type { CSSProperties } from "react";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { CreateNotebookDialog } from "@/components/notebooks/CreateNotebookDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useNotebooks } from "@/lib/hooks/use-notebooks";
import { useTranslation } from "@/lib/hooks/use-translation";
import { cn } from "@/lib/utils";
import { NotebookList } from "./components/NotebookList";

export default function NotebooksPage() {
  const { t } = useTranslation();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const { data: notebooks, isLoading, refetch } = useNotebooks(false);
  const { data: archivedNotebooks } = useNotebooks(true);

  const normalizedQuery = searchTerm.trim().toLowerCase();

  const filteredActive = useMemo(() => {
    if (!notebooks) {
      return undefined;
    }
    if (!normalizedQuery) {
      return notebooks;
    }
    return notebooks.filter((notebook) => notebook.name.toLowerCase().includes(normalizedQuery));
  }, [notebooks, normalizedQuery]);

  const filteredArchived = useMemo(() => {
    if (!archivedNotebooks) {
      return undefined;
    }
    if (!normalizedQuery) {
      return archivedNotebooks;
    }
    return archivedNotebooks.filter((notebook) =>
      notebook.name.toLowerCase().includes(normalizedQuery),
    );
  }, [archivedNotebooks, normalizedQuery]);

  const hasArchived = (archivedNotebooks?.length ?? 0) > 0;
  const isSearching = normalizedQuery.length > 0;

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="ui-page-shell p-6 space-y-6">
          <div
            className="ui-toolbar-row ui-section-enter flex items-center justify-between"
            style={{ "--enter-index": 0 } as CSSProperties}
          >
            <div className="ui-toolbar-row flex items-center gap-4">
              <h1 className="text-2xl font-bold">{t.notebooks.title}</h1>
              <Button
                variant="outline"
                size="sm"
                className="ui-icon-button group"
                data-testid="notebooks-refresh"
                onClick={() => refetch()}
                aria-label={t.common.refresh}
                title={t.common.refresh}
              >
                <RefreshCw className="h-4 w-4 transition-transform duration-300 ease-out group-hover:rotate-90" />
              </Button>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
              <Input
                id="notebook-search"
                name="notebook-search"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder={t.notebooks.searchPlaceholder}
                autoComplete="off"
                aria-label={t.common.accessibility.searchNotebooks}
                className={cn(
                  "ui-search-field ui-notebook-search-input w-full sm:w-64",
                  normalizedQuery && "ui-search-active",
                )}
              />
              <Button className="ui-primary-cta group" onClick={() => setCreateDialogOpen(true)}>
                <Plus className="ui-icon-shift h-4 w-4 mr-2" />
                {t.notebooks.newNotebook}
              </Button>
            </div>
          </div>

          <div
            className="ui-section-enter space-y-8"
            style={{ "--enter-index": 1 } as CSSProperties}
          >
            <NotebookList
              notebooks={filteredActive}
              isLoading={isLoading}
              title={t.notebooks.activeNotebooks}
              emptyTitle={isSearching ? t.common.noMatches : undefined}
              emptyDescription={isSearching ? t.common.tryDifferentSearch : undefined}
              onAction={!isSearching ? () => setCreateDialogOpen(true) : undefined}
              actionLabel={!isSearching ? t.notebooks.newNotebook : undefined}
            />

            {hasArchived && (
              <NotebookList
                notebooks={filteredArchived}
                isLoading={false}
                title={t.notebooks.archivedNotebooks}
                collapsible
                emptyTitle={isSearching ? t.common.noMatches : undefined}
                emptyDescription={isSearching ? t.common.tryDifferentSearch : undefined}
              />
            )}
          </div>
        </div>
      </div>

      <CreateNotebookDialog open={createDialogOpen} onOpenChange={setCreateDialogOpen} />
    </AppShell>
  );
}
