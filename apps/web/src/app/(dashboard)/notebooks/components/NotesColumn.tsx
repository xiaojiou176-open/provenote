"use client";

import { formatDistanceToNow } from "date-fns";
import { Bot, MoreVertical, Plus, StickyNote, Trash2, User } from "lucide-react";
import { useMemo, useState } from "react";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { ContextToggle } from "@/components/common/ContextToggle";
import { EmptyState } from "@/components/common/EmptyState";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { CollapsibleColumn, createCollapseButton } from "@/components/notebooks/CollapsibleColumn";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useDeleteNote } from "@/lib/hooks/use-notes";
import { useTranslation } from "@/lib/hooks/use-translation";
import { appLog } from "@/lib/log";
import { useNotebookColumnsStore } from "@/lib/stores/notebook-columns-store";
import type { NoteResponse } from "@/lib/types/api";
import type { ContextMode } from "@/lib/types/context";
import { getDateLocale } from "@/lib/utils/date-locale";
import { NoteEditorDialog } from "./NoteEditorDialog";

interface NotesColumnProps {
  notes?: NoteResponse[];
  isLoading: boolean;
  notebookId: string;
  contextSelections?: Record<string, ContextMode>;
  onContextModeChange?: (noteId: string, mode: ContextMode) => void;
}

export function NotesColumn({
  notes,
  isLoading,
  notebookId,
  contextSelections,
  onContextModeChange,
}: NotesColumnProps) {
  const { t, language } = useTranslation();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingNote, setEditingNote] = useState<NoteResponse | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [noteToDelete, setNoteToDelete] = useState<string | null>(null);
  const processLabel = t.navigation?.process ?? "Process";

  const deleteNote = useDeleteNote();

  // Collapsible column state
  const { notesCollapsed, toggleNotes } = useNotebookColumnsStore();
  const collapseButton = useMemo(
    () => createCollapseButton(toggleNotes, t.common.notes),
    [toggleNotes, t.common.notes],
  );

  const handleDeleteClick = (noteId: string) => {
    setNoteToDelete(noteId);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!noteToDelete) {
      return;
    }

    try {
      await deleteNote.mutateAsync(noteToDelete);
      setDeleteDialogOpen(false);
      setNoteToDelete(null);
    } catch (error) {
      appLog.error("notes-column", "Failed to delete note", { noteId: noteToDelete, error });
    }
  };

  return (
    <>
      <CollapsibleColumn
        isCollapsed={notesCollapsed}
        onToggle={toggleNotes}
        collapsedIcon={StickyNote}
        collapsedLabel={t.common.notes}
      >
        <Card className="ui-elevated-panel h-full flex flex-col flex-1 overflow-hidden shadow-none">
          <CardHeader className="pb-4 flex-shrink-0">
            <div className="flex items-center justify-between gap-2">
              <div className="space-y-1">
                <p className="ui-metric-label">{processLabel}</p>
                <CardTitle className="font-serif text-2xl leading-none tracking-[-0.03em]">
                  {t.common.notes}
                </CardTitle>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  className="rounded-2xl"
                  onClick={() => {
                    setEditingNote(null);
                    setShowAddDialog(true);
                  }}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  {t.common.writeNote}
                </Button>
                {collapseButton}
              </div>
            </div>
          </CardHeader>

          <CardContent className="flex-1 overflow-y-auto min-h-0">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : !notes || notes.length === 0 ? (
              <EmptyState
                icon={StickyNote}
                title={t.notebooks.noNotesYet}
                description={t.sources.createFirstNote}
              />
            ) : (
              <div className="space-y-3">
                {notes.map((note) => (
                  <div
                    key={note.id}
                    className="ui-card-surface group relative rounded-[1.25rem] border border-border/75 bg-card/95 p-4 shadow-none"
                  >
                    <div className="flex items-start justify-between mb-2 gap-2">
                      <button
                        type="button"
                        className="flex items-center gap-2 text-left rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                        onClick={() => setEditingNote(note)}
                        aria-label={note.title || t.common.notes}
                      >
                        {note.note_type === "ai" ? (
                          <Bot className="h-4 w-4 text-primary" />
                        ) : (
                          <User className="h-4 w-4 text-muted-foreground" />
                        )}
                        <Badge
                          variant="secondary"
                          className="rounded-full text-[11px] uppercase tracking-[0.14em]"
                        >
                          {note.note_type === "ai" ? t.common.aiGenerated : t.common.human}
                        </Badge>
                      </button>

                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(note.updated), {
                            addSuffix: true,
                            locale: getDateLocale(language),
                          })}
                        </span>

                        {/* Context toggle - only show if handler provided */}
                        {onContextModeChange && contextSelections?.[note.id] && (
                          <div onClick={(event) => event.stopPropagation()}>
                            <ContextToggle
                              mode={contextSelections[note.id]}
                              hasInsights={false}
                              onChange={(mode) => onContextModeChange(note.id, mode)}
                            />
                          </div>
                        )}

                        {/* Ellipsis menu for delete action */}
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 rounded-xl p-0 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 focus-visible:opacity-100 transition-opacity"
                              onClick={(e) => e.stopPropagation()}
                              aria-label={t.common.actions}
                            >
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-48">
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteClick(note.id);
                              }}
                              className="text-red-600 focus:text-red-600"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              {t.notebooks.deleteNote}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>

                    <button
                      type="button"
                      className="block w-full text-left rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      onClick={() => setEditingNote(note)}
                      aria-label={note.title || t.common.notes}
                    >
                      {note.title && (
                        <h4 className="mb-2 font-serif text-lg leading-tight tracking-[-0.02em] break-all">
                          {note.title}
                        </h4>
                      )}

                      {note.content && (
                        <p className="text-sm leading-6 text-muted-foreground line-clamp-3 break-all">
                          {note.content}
                        </p>
                      )}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </CollapsibleColumn>

      <NoteEditorDialog
        open={showAddDialog || Boolean(editingNote)}
        onOpenChange={(open) => {
          if (!open) {
            setShowAddDialog(false);
            setEditingNote(null);
          } else {
            setShowAddDialog(true);
          }
        }}
        notebookId={notebookId}
        note={editingNote ?? undefined}
      />

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title={t.notebooks.deleteNote}
        description={t.notebooks.deleteNoteConfirm}
        confirmText={t.common.delete}
        onConfirm={handleDeleteConfirm}
        isLoading={deleteNote.isPending}
        confirmVariant="destructive"
      />
    </>
  );
}
