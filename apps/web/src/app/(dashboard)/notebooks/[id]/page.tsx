"use client";

import { FileText, MessageSquare, ScrollText, StickyNote } from "lucide-react";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { AppShell } from "@/components/layout/AppShell";
import { NotebookDraftPanel } from "@/components/notebooks/NotebookDraftPanel";
import { NotebookOutcomeJourneyCard } from "@/components/notebooks/NotebookOutcomeJourneyCard";
import { ResearchThreadsPanel } from "@/components/notebooks/ResearchThreadsPanel";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useIsDesktop } from "@/lib/hooks/use-media-query";
import { useNotebook } from "@/lib/hooks/use-notebooks";
import { useNotes } from "@/lib/hooks/use-notes";
import { useNotebookSources } from "@/lib/hooks/use-sources";
import { useTranslation } from "@/lib/hooks/use-translation";
import { useNotebookColumnsStore } from "@/lib/stores/notebook-columns-store";
import type { ContextSelections } from "@/lib/types/context";
import { cn } from "@/lib/utils";
import { ChatColumn } from "../components/ChatColumn";
import { NotebookHeader } from "../components/NotebookHeader";
import { NotesColumn } from "../components/NotesColumn";
import { SourcesColumn } from "../components/SourcesColumn";

export type ContextMode = "off" | "insights" | "full";

function scrollToTestId(testId: string) {
  if (typeof document === "undefined") {
    return;
  }
  const element = document.querySelector(`[data-testid="${testId}"]`);
  if (element instanceof HTMLElement) {
    element.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

export default function NotebookPage() {
  const { t } = useTranslation();
  const params = useParams();
  const searchParams = useSearchParams();

  // Ensure the notebook ID is properly decoded from URL
  const notebookId = params?.id ? decodeURIComponent(params.id as string) : "";
  const draftSeedThreadId = searchParams?.get("draftSeedThread") || "";

  const { data: notebook, isLoading: notebookLoading } = useNotebook(notebookId);
  const {
    sources,
    isLoading: sourcesLoading,
    refetch: refetchSources,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
    error: sourcesError,
  } = useNotebookSources(notebookId);
  const { data: notes, isLoading: notesLoading } = useNotes(notebookId);

  // Get collapse states for dynamic layout
  const { sourcesCollapsed, notesCollapsed } = useNotebookColumnsStore();

  // Detect desktop to avoid double-mounting ChatColumn
  const isDesktop = useIsDesktop();

  // Mobile tab state (Sources, Notes, Chat, or Drafts)
  const [mobileActiveTab, setMobileActiveTab] = useState<"sources" | "notes" | "chat" | "drafts">(
    "chat",
  );

  // Context selection state
  const [contextSelections, setContextSelections] = useState<ContextSelections>({
    sources: {},
    notes: {},
  });

  const openDraftsTabAndScroll = (testId: string) => {
    setMobileActiveTab("drafts");
    if (typeof window !== "undefined") {
      window.setTimeout(() => {
        scrollToTestId(testId);
      }, 0);
    }
  };

  useEffect(() => {
    if (!draftSeedThreadId || isDesktop) {
      return;
    }

    openDraftsTabAndScroll("research-threads-panel");
  }, [draftSeedThreadId, isDesktop]);

  // Initialize and update selections when sources load or change
  useEffect(() => {
    if (sources && sources.length > 0) {
      setContextSelections((prev) => {
        const newSourceSelections = { ...prev.sources };
        sources.forEach((source) => {
          const currentMode = newSourceSelections[source.id];
          const hasInsights = source.insights_count > 0;

          if (currentMode === undefined) {
            // Initial setup - default based on insights availability
            newSourceSelections[source.id] = hasInsights ? "insights" : "full";
          } else if (currentMode === "full" && hasInsights) {
            // Source gained insights while in 'full' mode - auto-switch to 'insights'
            newSourceSelections[source.id] = "insights";
          }
        });
        return { ...prev, sources: newSourceSelections };
      });
    }
  }, [sources]);

  useEffect(() => {
    if (notes && notes.length > 0) {
      setContextSelections((prev) => {
        const newNoteSelections = { ...prev.notes };
        notes.forEach((note) => {
          // Only set default if not already set
          if (!(note.id in newNoteSelections)) {
            // Notes default to 'full'
            newNoteSelections[note.id] = "full";
          }
        });
        return { ...prev, notes: newNoteSelections };
      });
    }
  }, [notes]);

  // Handler to update context selection
  const handleContextModeChange = (itemId: string, mode: ContextMode, type: "source" | "note") => {
    setContextSelections((prev) => ({
      ...prev,
      [type === "source" ? "sources" : "notes"]: {
        ...(type === "source" ? prev.sources : prev.notes),
        [itemId]: mode,
      },
    }));
  };

  if (notebookLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!notebook) {
    return (
      <AppShell>
        <div className="p-6">
          <h1 className="text-2xl font-bold mb-4">{t.notebooks.notFound}</h1>
          <p className="text-muted-foreground">{t.notebooks.notFoundDesc}</p>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="flex flex-col flex-1 min-h-0 gap-6 p-4 md:p-6">
        <div className="flex-shrink-0">
          <NotebookHeader notebook={notebook} />
        </div>

        <div className="flex-1 overflow-x-auto flex flex-col gap-4">
          {/* Mobile: Tabbed interface - only render on mobile to avoid double-mounting */}
          {!isDesktop && (
            <>
              <div className="lg:hidden">
                <Tabs
                  value={mobileActiveTab}
                  onValueChange={(value) =>
                    setMobileActiveTab(value as "sources" | "notes" | "chat" | "drafts")
                  }
                >
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="sources" className="gap-2">
                      <FileText className="h-4 w-4" />
                      {t.navigation.sources}
                    </TabsTrigger>
                    <TabsTrigger value="notes" className="gap-2">
                      <StickyNote className="h-4 w-4" />
                      {t.common.notes}
                    </TabsTrigger>
                    <TabsTrigger value="chat" className="gap-2">
                      <MessageSquare className="h-4 w-4" />
                      {t.common.chat}
                    </TabsTrigger>
                    <TabsTrigger value="drafts" className="gap-2">
                      <ScrollText className="h-4 w-4" />
                      {t.notebooks.draftsTitle}
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>

              {/* Mobile: Show only active tab */}
              <div className="flex-1 overflow-hidden lg:hidden">
                <div className="mb-4">
                  <NotebookOutcomeJourneyCard
                    notebookId={notebookId}
                    sources={sources}
                    sourcesLoading={sourcesLoading}
                    onOpenDraftLane={() => openDraftsTabAndScroll("notebook-drafts-panel")}
                    onOpenResearchThreadsLane={() =>
                      openDraftsTabAndScroll("research-threads-panel")
                    }
                    draftSeedThreadId={draftSeedThreadId || undefined}
                  />
                </div>
                {mobileActiveTab === "sources" && (
                  <SourcesColumn
                    sources={sources}
                    isLoading={sourcesLoading}
                    notebookId={notebookId}
                    notebookName={notebook?.name}
                    onRefresh={refetchSources}
                    contextSelections={contextSelections.sources}
                    onContextModeChange={(sourceId, mode) =>
                      handleContextModeChange(sourceId, mode, "source")
                    }
                    hasNextPage={hasNextPage}
                    isFetchingNextPage={isFetchingNextPage}
                    fetchNextPage={fetchNextPage}
                  />
                )}
                {mobileActiveTab === "notes" && (
                  <NotesColumn
                    notes={notes}
                    isLoading={notesLoading}
                    notebookId={notebookId}
                    contextSelections={contextSelections.notes}
                    onContextModeChange={(noteId, mode) =>
                      handleContextModeChange(noteId, mode, "note")
                    }
                  />
                )}
                {mobileActiveTab === "chat" && (
                  <ChatColumn
                    notebookId={notebookId}
                    contextSelections={contextSelections}
                    sources={sources}
                    sourcesLoading={sourcesLoading}
                    sourcesError={sourcesError}
                  />
                )}
                {mobileActiveTab === "drafts" && (
                  <div className="space-y-4">
                    <NotebookDraftPanel
                      notebookId={notebookId}
                      notebookName={notebook?.name}
                      sources={sources}
                      sourcesLoading={sourcesLoading}
                      draftSeedThreadId={draftSeedThreadId || undefined}
                    />
                    <ResearchThreadsPanel
                      notebookId={notebookId}
                      draftSeedThreadId={draftSeedThreadId || undefined}
                    />
                  </div>
                )}
              </div>
            </>
          )}

          {/* Desktop: Collapsible columns layout */}
          <div className="hidden lg:flex h-full min-h-0 flex-col gap-6">
            <NotebookOutcomeJourneyCard
              notebookId={notebookId}
              sources={sources}
              sourcesLoading={sourcesLoading}
              onOpenDraftLane={() => openDraftsTabAndScroll("notebook-drafts-panel")}
              onOpenResearchThreadsLane={() => openDraftsTabAndScroll("research-threads-panel")}
              draftSeedThreadId={draftSeedThreadId || undefined}
            />
            <NotebookDraftPanel
              notebookId={notebookId}
              notebookName={notebook?.name}
              sources={sources}
              sourcesLoading={sourcesLoading}
              draftSeedThreadId={draftSeedThreadId || undefined}
            />
            <ResearchThreadsPanel
              notebookId={notebookId}
              draftSeedThreadId={draftSeedThreadId || undefined}
            />
            <div
              className={cn(
                "hidden lg:flex h-full min-h-0 gap-6 transition-all duration-150",
                "flex-row",
              )}
            >
              {/* Sources Column */}
              <div
                className={cn(
                  "transition-all duration-150",
                  sourcesCollapsed ? "w-12 flex-shrink-0" : "flex-none basis-1/3",
                )}
              >
                <SourcesColumn
                  sources={sources}
                  isLoading={sourcesLoading}
                  notebookId={notebookId}
                  notebookName={notebook?.name}
                  onRefresh={refetchSources}
                  contextSelections={contextSelections.sources}
                  onContextModeChange={(sourceId, mode) =>
                    handleContextModeChange(sourceId, mode, "source")
                  }
                  hasNextPage={hasNextPage}
                  isFetchingNextPage={isFetchingNextPage}
                  fetchNextPage={fetchNextPage}
                />
              </div>

              {/* Notes Column */}
              <div
                className={cn(
                  "transition-all duration-150",
                  notesCollapsed ? "w-12 flex-shrink-0" : "flex-none basis-1/3",
                )}
              >
                <NotesColumn
                  notes={notes}
                  isLoading={notesLoading}
                  notebookId={notebookId}
                  contextSelections={contextSelections.notes}
                  onContextModeChange={(noteId, mode) =>
                    handleContextModeChange(noteId, mode, "note")
                  }
                />
              </div>

              {/* Chat Column - always expanded, takes remaining space */}
              <div className="transition-all duration-150 flex-1 min-w-0 lg:pr-6 lg:-mr-6">
                <ChatColumn
                  notebookId={notebookId}
                  contextSelections={contextSelections}
                  sources={sources}
                  sourcesLoading={sourcesLoading}
                  sourcesError={sourcesError}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
