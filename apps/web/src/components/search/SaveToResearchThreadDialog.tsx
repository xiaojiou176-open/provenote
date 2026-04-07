"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { CheckboxList } from "@/components/ui/checkbox-list";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useNotebooks } from "@/lib/hooks/use-notebooks";
import { useCreateResearchThread } from "@/lib/hooks/use-research-threads";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { SearchResult } from "@/lib/types/search";

interface SaveToResearchThreadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: "ask" | "search";
  defaultTitle: string;
  defaultNotebookIds?: string[];
  question?: string;
  answer?: string;
  searchResults?: SearchResult[];
  sourceIds?: string[];
  noteIds?: string[];
}

const EMPTY_NOTEBOOK_IDS: string[] = [];

export function SaveToResearchThreadDialog({
  open,
  onOpenChange,
  mode,
  defaultTitle,
  defaultNotebookIds,
  question,
  answer,
  searchResults = [],
  sourceIds = [],
  noteIds = [],
}: SaveToResearchThreadDialogProps) {
  const { t } = useTranslation();
  const [selectedNotebookIds, setSelectedNotebookIds] = useState<string[]>([]);
  const [threadTitle, setThreadTitle] = useState(defaultTitle);
  const { data: notebooks, isLoading } = useNotebooks(false);
  const createResearchThread = useCreateResearchThread();
  const seededNotebookIds = defaultNotebookIds ?? EMPTY_NOTEBOOK_IDS;
  const seededNotebookIdsKey = seededNotebookIds.join("|");

  const notebookItems =
    notebooks?.map((notebook) => ({
      id: notebook.id,
      title: notebook.name,
      description: notebook.description || undefined,
    })) ?? [];

  useEffect(() => {
    if (!open) {
      return;
    }
    setThreadTitle(defaultTitle);
    setSelectedNotebookIds([...seededNotebookIds]);
  }, [defaultTitle, open, seededNotebookIdsKey]);

  const handleToggle = (notebookId: string) => {
    setSelectedNotebookIds((prev) =>
      prev.includes(notebookId) ? prev.filter((id) => id !== notebookId) : [...prev, notebookId],
    );
  };

  const handleSave = async () => {
    for (const notebookId of selectedNotebookIds) {
      await createResearchThread.mutateAsync({
        notebookId,
        payload: {
          title: threadTitle.trim() || defaultTitle,
          seed_kind: mode,
          question,
          answer,
          source_ids: sourceIds,
          note_ids: noteIds,
          search_results: searchResults.map((result) => ({ ...result })),
        },
      });
    }
    onOpenChange(false);
    setSelectedNotebookIds([]);
  };

  const resultTypeLabel =
    mode === "ask"
      ? t.searchPage.researchCaptureAnswerLabel
      : t.searchPage.researchCaptureSearchResultLabel;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>{t.searchPage.saveToResearchThreadTitle}</DialogTitle>
          <DialogDescription>
            {t("searchPage.saveToResearchThreadDescription", {
              resultType: resultTypeLabel,
            })}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <Input value={threadTitle} onChange={(event) => setThreadTitle(event.target.value)} />
          <CheckboxList
            items={notebookItems}
            selectedIds={selectedNotebookIds}
            onToggle={handleToggle}
            emptyMessage={
              isLoading ? t.searchPage.researchCaptureLoadingNotebooks : t.sources.noNotebooksFound
            }
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t.common.cancel}
          </Button>
          <Button
            onClick={handleSave}
            disabled={selectedNotebookIds.length === 0 || createResearchThread.isPending}
          >
            {t.searchPage.saveResearchThread}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
