"use client";

import { formatDistanceToNow } from "date-fns";
import { Check, Clock, Edit2, MessageSquare, Plus, Trash2, X } from "lucide-react";
import { type KeyboardEvent, useMemo, useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useModels } from "@/lib/hooks/use-models";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { BaseChatSession } from "@/lib/types/api";
import { getDateLocale } from "@/lib/utils/date-locale";

interface SessionManagerProps {
  sessions: BaseChatSession[];
  currentSessionId: string | null;
  onCreateSession: (title: string) => void;
  onSelectSession: (sessionId: string) => void;
  onUpdateSession: (sessionId: string, title: string) => void;
  onDeleteSession: (sessionId: string) => void;
  loadingSessions: boolean;
}

export function SessionManager({
  sessions,
  currentSessionId,
  onCreateSession,
  onSelectSession,
  onUpdateSession,
  onDeleteSession,
  loadingSessions,
}: SessionManagerProps) {
  const { t, language } = useTranslation();
  const [isCreating, setIsCreating] = useState(false);
  const [newSessionTitle, setNewSessionTitle] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const { data: models } = useModels();

  // Helper to get model name from ID
  const customModelLabel = t.common.customModel;
  const getModelName = useMemo(() => {
    return (modelId: string) => {
      const model = models?.find((m) => m.id === modelId);
      return model?.name || customModelLabel;
    };
  }, [models, customModelLabel]);

  const handleCreateSession = () => {
    if (newSessionTitle.trim()) {
      onCreateSession(newSessionTitle.trim());
      setNewSessionTitle("");
      setIsCreating(false);
    }
  };

  const handleStartEdit = (session: BaseChatSession) => {
    setEditingId(session.id);
    setEditTitle(session.title);
  };

  const handleSaveEdit = () => {
    if (editingId && editTitle.trim()) {
      onUpdateSession(editingId, editTitle.trim());
      setEditingId(null);
      setEditTitle("");
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditTitle("");
  };

  const handleDeleteConfirm = () => {
    if (deleteConfirmId) {
      onDeleteSession(deleteConfirmId);
      setDeleteConfirmId(null);
    }
  };

  const handleCreateInputKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== "Enter") {
      return;
    }

    event.preventDefault();
    handleCreateSession();
  };

  return (
    <>
      <Card className="h-full flex flex-col">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              {t.chat.sessions}
            </span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setIsCreating(true)}
              aria-label={t.common.create}
              title={t.common.create}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 p-0 min-h-0">
          <ScrollArea className="h-full px-4">
            {isCreating && (
              <div className="p-3 border rounded-lg mb-3">
                <Input
                  value={newSessionTitle}
                  onChange={(e) => setNewSessionTitle(e.target.value)}
                  placeholder={t.chat.sessionTitlePlaceholder}
                  className="mb-2"
                  autoFocus
                  onKeyDown={handleCreateInputKeyDown}
                />
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleCreateSession}>
                    {t.common.create}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setIsCreating(false);
                      setNewSessionTitle("");
                    }}
                  >
                    {t.common.cancel}
                  </Button>
                </div>
              </div>
            )}

            {loadingSessions ? (
              <div className="text-center py-8 text-muted-foreground">{t.common.loading}</div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-sm">{t.chat.noSessions}</p>
                <p className="text-xs mt-2">{t.chat.createToStart}</p>
              </div>
            ) : (
              <div className="space-y-2 pb-4">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className={`p-3 rounded-lg border transition-colors ${
                      currentSessionId === session.id
                        ? "bg-primary/10 border-primary"
                        : "hover:bg-muted"
                    }`}
                  >
                    {editingId === session.id ? (
                      <div className="space-y-2">
                        <Input
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              handleSaveEdit();
                            }
                            if (e.key === "Escape") {
                              handleCancelEdit();
                            }
                          }}
                          autoFocus
                        />
                        <div className="flex gap-2">
                          <Button size="sm" onClick={handleSaveEdit}>
                            <Check className="h-3 w-3" />
                          </Button>
                          <Button size="sm" variant="outline" onClick={handleCancelEdit}>
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-start justify-between mb-1 gap-2">
                          <button
                            type="button"
                            className="flex-1 text-left rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                            onClick={() => onSelectSession(session.id)}
                            aria-label={`${t.chat.sessions}: ${session.title}`}
                            aria-pressed={currentSessionId === session.id}
                          >
                            <h4 className="font-medium text-sm break-all">{session.title}</h4>
                          </button>
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 w-6 p-0"
                              onClick={() => handleStartEdit(session)}
                              aria-label={t.common.edit}
                              title={t.common.edit}
                            >
                              <Edit2 className="h-3 w-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 w-6 p-0"
                              onClick={() => setDeleteConfirmId(session.id)}
                              aria-label={t.common.delete}
                              title={t.common.delete}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                        <button
                          type="button"
                          className="w-full text-left rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                          onClick={() => onSelectSession(session.id)}
                          aria-label={`${t.chat.sessions}: ${session.title}`}
                          aria-pressed={currentSessionId === session.id}
                        >
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            {formatDistanceToNow(new Date(session.created), {
                              addSuffix: true,
                              locale: getDateLocale(language),
                            })}
                          </div>
                          {session.message_count != null && session.message_count > 0 && (
                            <Badge variant="secondary" className="mt-2 text-xs">
                              {t.chat.messagesCount.replace(
                                "{count}",
                                session.message_count.toString(),
                              )}
                            </Badge>
                          )}
                          {session.model_override && (
                            <Badge variant="outline" className="mt-2 ml-2 text-xs">
                              {getModelName(session.model_override)}
                            </Badge>
                          )}
                        </button>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      <AlertDialog open={!!deleteConfirmId} onOpenChange={() => setDeleteConfirmId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t.chat.deleteSession}</AlertDialogTitle>
            <AlertDialogDescription>{t.chat.deleteSessionDesc}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.common.cancel}</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteConfirm}>{t.common.delete}</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
