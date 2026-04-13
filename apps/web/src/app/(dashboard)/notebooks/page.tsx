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
  const activeNotebookCount = filteredActive?.length ?? notebooks?.length ?? 0;
  const archivedNotebookCount = filteredArchived?.length ?? archivedNotebooks?.length ?? 0;

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="ui-page-shell space-y-6 p-4 md:p-6">
          <section className="ui-section-enter" style={{ "--enter-index": 0 } as CSSProperties}>
            <div className="ui-workbench-hero rounded-[1.5rem] p-6 md:p-8">
              <div className="ui-workbench-grid xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)] xl:items-start">
                <div className="space-y-4">
                  <span className="ui-workbench-kicker">{t.notebooks.activeNotebooks}</span>
                  <div className="space-y-3">
                    <h1 className="ui-page-title">{t.notebooks.title}</h1>
                    <p className="ui-page-lede">{t.notebooks.createNewDesc}</p>
                  </div>
                </div>

                <div className="ui-metric-grid">
                  <div className="ui-metric-card">
                    <p className="ui-metric-label">{t.notebooks.activeNotebooks}</p>
                    <p className="ui-metric-value">{activeNotebookCount}</p>
                    <p className="ui-metric-detail">{t.notebooks.title}</p>
                  </div>
                  <div className="ui-metric-card">
                    <p className="ui-metric-label">{t.notebooks.archivedNotebooks}</p>
                    <p className="ui-metric-value">{archivedNotebookCount}</p>
                    <p className="ui-metric-detail">
                      {hasArchived ? t.notebooks.archived : t.common.noResults}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section
            className="ui-toolbar-row ui-section-enter ui-toolbar-surface p-4"
            style={{ "--enter-index": 1 } as CSSProperties}
          >
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div className="ui-toolbar-row flex items-center gap-4">
                <div className="space-y-1">
                  <h2 className="font-serif text-2xl leading-none tracking-[-0.03em]">
                    {t.notebooks.title}
                  </h2>
                  <p className="text-sm text-muted-foreground">{t.notebooks.searchPlaceholder}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="ui-icon-button group rounded-xl"
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
                    "ui-search-field ui-notebook-search-input w-full rounded-2xl border-border/80 bg-card/90 sm:w-72",
                    normalizedQuery && "ui-search-active",
                  )}
                />
                <Button className="ui-primary-cta group" onClick={() => setCreateDialogOpen(true)}>
                  <Plus className="ui-icon-shift h-4 w-4 mr-2" />
                  {t.notebooks.newNotebook}
                </Button>
              </div>
            </div>
          </section>

          <div
            className="ui-section-enter space-y-8"
            style={{ "--enter-index": 2 } as CSSProperties}
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
