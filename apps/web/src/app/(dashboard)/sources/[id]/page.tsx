"use client";

import { ArrowLeft } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useCallback } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { AuditableMarkdownPanel } from "@/components/source/AuditableMarkdownPanel";
import { ChatPanel } from "@/components/source/ChatPanel";
import { SourceDetailContent } from "@/components/source/SourceDetailContent";
import { Button } from "@/components/ui/button";
import { useNavigation } from "@/lib/hooks/use-navigation";
import { useSource } from "@/lib/hooks/use-sources";
import { useTranslation } from "@/lib/hooks/use-translation";
import { useSourceChat } from "@/lib/hooks/useSourceChat";

export default function SourceDetailPage() {
  const router = useRouter();
  const params = useParams();
  const sourceId = params?.id ? decodeURIComponent(params.id as string) : "";
  const navigation = useNavigation();
  const { t } = useTranslation();
  const { data: source } = useSource(sourceId);

  // Initialize source chat
  const chat = useSourceChat(sourceId);

  const handleBack = useCallback(() => {
    const returnPath = navigation.getReturnPath();
    router.push(returnPath);
    navigation.clearReturnTo();
  }, [navigation, router]);

  const handleOpenNotebookDraftLane = useCallback(
    (notebookId: string) => {
      router.push(`/notebooks/${encodeURIComponent(notebookId)}`);
    },
    [router],
  );

  return (
    <AppShell>
      <div className="ui-page-shell flex h-full flex-col">
        {/* Back button */}
        <div className="ui-section-enter px-6 pb-4 pt-6">
          <Button variant="ghost" size="sm" onClick={handleBack} className="ui-icon-button mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            {navigation.getReturnLabel(t.sources.backToSources)}
          </Button>
        </div>

        {/* Main content: Source detail + Chat */}
        <div className="ui-section-enter grid flex-1 gap-6 overflow-hidden px-6 lg:grid-cols-[2fr_1fr]">
          {/* Left column - Source detail */}
          <div className="overflow-y-auto px-4 pb-6">
            <AuditableMarkdownPanel
              sourceId={sourceId}
              linkedNotebookIds={source?.notebooks ?? []}
              onUseInDraft={handleOpenNotebookDraftLane}
              className="mb-6"
            />
            <SourceDetailContent sourceId={sourceId} showChatButton={false} onClose={handleBack} />
          </div>

          {/* Right column - Chat */}
          <div className="overflow-y-auto px-4 pb-6">
            <ChatPanel
              messages={chat.messages}
              isStreaming={chat.isStreaming}
              contextIndicators={chat.contextIndicators}
              onSendMessage={(message, model) => chat.sendMessage(message, model)}
              modelOverride={chat.currentSession?.model_override}
              onModelChange={(model) => {
                if (chat.currentSessionId) {
                  chat.updateSession(chat.currentSessionId, { model_override: model });
                }
              }}
              sessions={chat.sessions}
              currentSessionId={chat.currentSessionId}
              onCreateSession={(title) => chat.createSession({ title })}
              onSelectSession={chat.switchSession}
              onUpdateSession={(sessionId, title) => chat.updateSession(sessionId, { title })}
              onDeleteSession={chat.deleteSession}
              loadingSessions={chat.loadingSessions}
            />
          </div>
        </div>
      </div>
    </AppShell>
  );
}
