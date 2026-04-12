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
  const scrollToSection = useCallback((sectionId: string) => {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  return (
    <AppShell>
      <div className="ui-page-shell flex h-full flex-col">
        {/* Back button */}
        <div className="ui-section-enter px-6 pb-4 pt-6">
          <Button variant="ghost" size="sm" onClick={handleBack} className="ui-icon-button mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            {navigation.getReturnLabel(t.sources.backToSources)}
          </Button>

          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border/70 bg-background/90 px-4 py-3 shadow-sm">
            <div className="min-w-0">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary">
                {t("sources.detailPage.eyebrow", "Sources-first workbench")}
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground">
                {t(
                  "sources.detailPage.title",
                  "Verify the source first, then move into auditable output or chat.",
                )}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {t(
                  "sources.detailPage.body",
                  "This page is split into three next-step lanes so you do not have to guess where to go after opening a source.",
                )}
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap gap-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                <span className="rounded-full border border-border/70 bg-background px-3 py-1.5">
                  {t("sources.detailPage.stepEvidence", "1. Source evidence")}
                </span>
                <span className="rounded-full border border-border/70 bg-background px-3 py-1.5">
                  {t("sources.detailPage.stepMarkdown", "2. Auditable markdown")}
                </span>
                <span className="rounded-full border border-border/70 bg-background px-3 py-1.5">
                  {t("sources.detailPage.stepChat", "3. Source chat")}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                className="cursor-pointer"
                onClick={() => scrollToSection("source-evidence-section")}
              >
                {t("sources.detailPage.evidenceAction", "Source evidence")}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="cursor-pointer"
                onClick={() => scrollToSection("auditable-markdown-section")}
              >
                {t("sources.detailPage.auditAction", "Auditable markdown")}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="cursor-pointer"
                onClick={() => scrollToSection("source-chat-section")}
              >
                {t("sources.detailPage.chatAction", "Source chat")}
              </Button>
            </div>
            </div>
          </div>
        </div>

        {/* Main content: Source detail + Chat */}
        <div className="ui-section-enter grid flex-1 gap-6 overflow-hidden px-6 lg:grid-cols-[2fr_1fr]">
          {/* Left column - Source detail */}
          <div className="overflow-y-auto px-4 pb-6">
            <div id="source-evidence-section">
              <SourceDetailContent
                sourceId={sourceId}
                showChatButton={false}
                onClose={handleBack}
              />
            </div>
            <div id="auditable-markdown-section">
              <AuditableMarkdownPanel
                sourceId={sourceId}
                linkedNotebookIds={source?.notebooks ?? []}
                onUseInDraft={handleOpenNotebookDraftLane}
                className="mb-6"
              />
            </div>
          </div>

          {/* Right column - Chat */}
          <div id="source-chat-section" className="overflow-y-auto px-4 pb-6">
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
