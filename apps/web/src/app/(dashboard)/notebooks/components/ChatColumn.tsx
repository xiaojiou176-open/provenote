"use client";

import { AlertCircle, Save } from "lucide-react";
import { useMemo } from "react";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ChatPanel } from "@/components/source/ChatPanel";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useNotes } from "@/lib/hooks/use-notes";
import { useCreateResearchThread } from "@/lib/hooks/use-research-threads";
import { useTranslation } from "@/lib/hooks/use-translation";
import { useNotebookChat } from "@/lib/hooks/useNotebookChat";
import type { SourceListResponse } from "@/lib/types/api";
import type { ContextSelections } from "@/lib/types/context";

interface ChatColumnProps {
  notebookId: string;
  contextSelections: ContextSelections;
  sources: SourceListResponse[];
  sourcesLoading: boolean;
  sourcesError?: unknown;
}

export function ChatColumn({
  notebookId,
  contextSelections,
  sources,
  sourcesLoading,
  sourcesError,
}: ChatColumnProps) {
  const { t } = useTranslation();
  const createResearchThread = useCreateResearchThread();

  // Fetch notes for this notebook
  const {
    data: notes = [],
    isLoading: notesLoading,
    error: notesError,
    refetch: refetchNotes,
  } = useNotes(notebookId);

  // Initialize notebook chat hook
  const chat = useNotebookChat({
    notebookId,
    sources,
    notes,
    contextSelections,
  });

  // Calculate context stats for indicator
  const contextStats = useMemo(() => {
    let sourcesInsights = 0;
    let sourcesFull = 0;
    let notesCount = 0;

    // Count sources by mode
    sources.forEach((source) => {
      const mode = contextSelections.sources[source.id];
      if (mode === "insights") {
        sourcesInsights++;
      } else if (mode === "full") {
        sourcesFull++;
      }
    });

    // Count notes that are included (not 'off')
    notes.forEach((note) => {
      const mode = contextSelections.notes[note.id];
      if (mode === "full") {
        notesCount++;
      }
    });

    return {
      sourcesInsights,
      sourcesFull,
      notesCount,
      tokenCount: chat.tokenCount,
      charCount: chat.charCount,
    };
  }, [sources, notes, contextSelections, chat.tokenCount, chat.charCount]);

  const selectedSourceIds = useMemo(
    () =>
      sources
        .filter((source) => {
          const mode = contextSelections.sources[source.id];
          return mode === "insights" || mode === "full";
        })
        .map((source) => source.id),
    [contextSelections.sources, sources],
  );

  const selectedNoteIds = useMemo(
    () =>
      notes.filter((note) => contextSelections.notes[note.id] === "full").map((note) => note.id),
    [contextSelections.notes, notes],
  );

  const handleSaveChatToThread = async () => {
    const latestHumanMessage = [...chat.messages]
      .reverse()
      .find((message) => message.type === "human");
    const aiTranscript = chat.messages
      .map((message) => `${message.type === "human" ? "User" : "Assistant"}: ${message.content}`)
      .join("\n\n");

    await createResearchThread.mutateAsync({
      notebookId,
      payload: {
        title: chat.currentSession?.title || "Notebook chat thread",
        seed_kind: "notebook_chat",
        question: latestHumanMessage?.content,
        answer: aiTranscript,
        source_ids: selectedSourceIds,
        note_ids: selectedNoteIds,
      },
    });
  };

  // Show loading state while sources/notes are being fetched
  if (sourcesLoading || notesLoading) {
    return (
      <Card className="h-full flex flex-col">
        <CardContent className="flex-1 flex items-center justify-center">
          <LoadingSpinner size="lg" />
        </CardContent>
      </Card>
    );
  }

  // Show error state if data fetch failed (unlikely but good to handle)
  if (sourcesError || notesError) {
    return (
      <Card className="h-full flex flex-col">
        <CardContent className="flex-1 flex items-center justify-center">
          <div className="text-center text-muted-foreground">
            <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm">{t.chat.unableToLoadChat}</p>
            <p className="text-xs mt-2">{t.common.refreshPage}</p>
            <button
              type="button"
              className="mt-4 text-sm text-primary underline-offset-2 hover:underline"
              onClick={() => {
                void refetchNotes();
              }}
            >
              {t.common.retry}
            </button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex h-full flex-col gap-3">
      {chat.messages.length > 0 ? (
        <div className="flex justify-end">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => void handleSaveChatToThread()}
            disabled={createResearchThread.isPending}
          >
            <Save className="mr-2 h-4 w-4" />
            Save chat to research thread
          </Button>
        </div>
      ) : null}
      <ChatPanel
        title={t.chat.chatWithNotebook}
        contextType="notebook"
        messages={chat.messages}
        isStreaming={chat.isSending}
        contextIndicators={null}
        onSendMessage={(message, modelOverride) => chat.sendMessage(message, modelOverride)}
        modelOverride={
          chat.currentSession?.model_override ?? chat.pendingModelOverride ?? undefined
        }
        onModelChange={(model) => chat.setModelOverride(model ?? null)}
        sessions={chat.sessions}
        currentSessionId={chat.currentSessionId}
        onCreateSession={(title) => chat.createSession(title)}
        onSelectSession={chat.switchSession}
        onUpdateSession={(sessionId, title) => chat.updateSession(sessionId, { title })}
        onDeleteSession={chat.deleteSession}
        loadingSessions={chat.loadingSessions}
        notebookContextStats={contextStats}
        notebookId={notebookId}
      />
    </div>
  );
}
