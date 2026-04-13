"use client";

import { formatDistanceToNow } from "date-fns";
import { Archive, ArchiveRestore, Trash2 } from "lucide-react";
import { useState } from "react";
import { InlineEdit } from "@/components/common/InlineEdit";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useUpdateNotebook } from "@/lib/hooks/use-notebooks";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { NotebookResponse } from "@/lib/types/api";
import { getDateLocale } from "@/lib/utils/date-locale";
import { NotebookDeleteDialog } from "./NotebookDeleteDialog";

interface NotebookHeaderProps {
  notebook: NotebookResponse;
}

export function NotebookHeader({ notebook }: NotebookHeaderProps) {
  const { t, language } = useTranslation();
  const dfLocale = getDateLocale(language);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const sourcesLabel = t.navigation?.sources ?? "Sources";
  const notesLabel = t.common.notes ?? "Notes";
  const sourceCount = notebook.source_count ?? 0;
  const noteCount = notebook.note_count ?? 0;

  const updateNotebook = useUpdateNotebook();

  const handleUpdateName = async (name: string) => {
    if (!name || name === notebook.name) {
      return;
    }

    await updateNotebook.mutateAsync({
      id: notebook.id,
      data: { name },
    });
  };

  const handleUpdateDescription = async (description: string) => {
    if (description === notebook.description) {
      return;
    }

    await updateNotebook.mutateAsync({
      id: notebook.id,
      data: { description: description || undefined },
    });
  };

  const handleArchiveToggle = () => {
    updateNotebook.mutate({
      id: notebook.id,
      data: { archived: !notebook.archived },
    });
  };

  return (
    <>
      <div className="ui-workbench-hero rounded-[1.5rem] p-6 md:p-8">
        <div className="ui-workbench-grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)] xl:items-start">
          <div className="space-y-4">
            <span className="ui-workbench-kicker">{t.notebooks.activeNotebooks}</span>
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div className="flex flex-1 items-start gap-3">
                <div className="min-w-0 flex-1 space-y-2">
                  <InlineEdit
                    id="notebook-name"
                    name="notebook-name"
                    value={notebook.name}
                    onSave={handleUpdateName}
                    className="ui-page-title text-left"
                    inputClassName="ui-page-title"
                    placeholder={t.notebooks.namePlaceholder}
                  />
                  {notebook.archived && <Badge variant="secondary">{t.notebooks.archived}</Badge>}
                  <InlineEdit
                    id="notebook-description"
                    name="notebook-description"
                    value={notebook.description || ""}
                    onSave={handleUpdateDescription}
                    className="ui-page-lede"
                    inputClassName="ui-page-lede"
                    placeholder={t.notebooks.addDescription}
                    multiline
                    emptyText={t.notebooks.addDescription}
                  />
                </div>
              </div>
              <div className="flex flex-wrap gap-2 xl:justify-end">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleArchiveToggle}
                  className="rounded-2xl"
                >
                  {notebook.archived ? (
                    <>
                      <ArchiveRestore className="h-4 w-4 mr-2" />
                      {t.notebooks.unarchive}
                    </>
                  ) : (
                    <>
                      <Archive className="h-4 w-4 mr-2" />
                      {t.notebooks.archive}
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowDeleteDialog(true)}
                  className="rounded-2xl text-red-600 hover:text-red-700"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  {t.common.delete}
                </Button>
              </div>
            </div>
          </div>

          <div className="ui-metric-grid">
            <div className="ui-metric-card">
              <p className="ui-metric-label">{sourcesLabel}</p>
              <p className="ui-metric-value">{sourceCount}</p>
              <p className="ui-metric-detail">{t.notebooks.draftSourceSelection}</p>
            </div>
            <div className="ui-metric-card">
              <p className="ui-metric-label">{notesLabel}</p>
              <p className="ui-metric-value">{noteCount}</p>
              <p className="ui-metric-detail">{t.notebooks.noNotesYet}</p>
            </div>
            <div className="ui-metric-card md:col-span-2">
              <p className="ui-metric-label">{t.common.updated.replace("{time}", "").trim()}</p>
              <p className="mt-3 text-base font-semibold">
                {t.common.created.replace(
                  "{time}",
                  formatDistanceToNow(new Date(notebook.created), {
                    addSuffix: true,
                    locale: dfLocale,
                  }),
                )}
              </p>
              <p className="ui-metric-detail">
                {t.common.updated.replace(
                  "{time}",
                  formatDistanceToNow(new Date(notebook.updated), {
                    addSuffix: true,
                    locale: dfLocale,
                  }),
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      <NotebookDeleteDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        notebookId={notebook.id}
        notebookName={notebook.name}
        redirectAfterDelete
      />
    </>
  );
}
