"use client";

import { formatDistanceToNow } from "date-fns";
import { GitBranchPlus, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useCreateDraftFromResearchThread,
  useNotebookResearchThreads,
} from "@/lib/hooks/use-research-threads";
import { useTranslation } from "@/lib/hooks/use-translation";
import { getDateLocale } from "@/lib/utils/date-locale";
import {
  compareResearchThreadsForDraftSeed,
  getRecommendedResearchThread,
} from "./research-thread-recommendation";

interface ResearchThreadsPanelProps {
  notebookId: string;
  draftSeedThreadId?: string;
}

function scrollToTestId(testId: string) {
  const element = document.querySelector(`[data-testid="${testId}"]`);
  if (element instanceof HTMLElement) {
    element.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

export function ResearchThreadsPanel({ notebookId, draftSeedThreadId }: ResearchThreadsPanelProps) {
  const { t, language } = useTranslation();
  const dfLocale = getDateLocale(language);
  const { data, isLoading } = useNotebookResearchThreads(notebookId);
  const createDraftFromThread = useCreateDraftFromResearchThread(notebookId);
  const threads = data ?? [];
  const sortedThreads = [...threads].sort(compareResearchThreadsForDraftSeed);
  const recommendedThread = getRecommendedResearchThread(threads);
  const draftSeedThread = draftSeedThreadId
    ? (threads.find((thread) => thread.id === draftSeedThreadId) ?? null)
    : null;
  const listedThreads = sortedThreads.filter((thread) => {
    if (draftSeedThread?.id === thread.id) {
      return false;
    }
    if (recommendedThread?.id === thread.id) {
      return false;
    }
    return true;
  });
  const formatSeedKind = (seedKind: string) => seedKind.replace(/_/g, " ");

  const handleCreateDraftFromThread = (threadId: string) => {
    createDraftFromThread.mutate(threadId, {
      onSuccess: () => {
        scrollToTestId("notebook-drafts-panel");
      },
    });
  };

  return (
    <Card id="research-threads-panel" data-testid="research-threads-panel">
      <CardHeader>
        <CardTitle className="text-base">{t.notebooks.researchThreadsTitle}</CardTitle>
        <CardDescription>{t.notebooks.researchThreadsDescription}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            {t.notebooks.loadingResearchThreads}
          </div>
        ) : threads.length === 0 ? (
          <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
            {t.notebooks.noResearchThreads}
          </div>
        ) : (
          <>
            {draftSeedThread ? (
              <div
                className="rounded-md border border-primary/30 bg-primary/5 p-4"
                data-testid="research-thread-draft-bridge"
              >
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge>{t.notebooks.researchThreadBridgeBadge}</Badge>
                      <p className="text-sm font-medium">{t.notebooks.researchThreadBridgeTitle}</p>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {t("notebooks.researchThreadBridgeDescription", {
                        title: draftSeedThread.title,
                        entryCount: draftSeedThread.entry_count,
                        sourceCount: draftSeedThread.source_ids.length,
                      })}
                    </p>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => handleCreateDraftFromThread(draftSeedThread.id)}
                    disabled={createDraftFromThread.isPending}
                  >
                    <GitBranchPlus className="mr-2 h-4 w-4" />
                    {t.notebooks.researchThreadBridgeAction}
                  </Button>
                </div>
              </div>
            ) : null}
            {recommendedThread ? (
              <div
                className="rounded-md border bg-muted/20 p-4"
                data-testid="research-thread-recommendation"
              >
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="secondary">
                        {t.notebooks.researchThreadRecommendedBadge}
                      </Badge>
                      <p className="text-sm font-medium">
                        {t.notebooks.researchThreadRecommendedTitle}
                      </p>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {t("notebooks.researchThreadRecommendedDescription", {
                        title: recommendedThread.title,
                        entryCount: recommendedThread.entry_count,
                        sourceCount: recommendedThread.source_ids.length,
                      })}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {t("notebooks.researchThreadRecommendedWhy", {
                        seedKind: formatSeedKind(recommendedThread.seed_kind),
                      })}
                    </p>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => handleCreateDraftFromThread(recommendedThread.id)}
                    disabled={createDraftFromThread.isPending}
                  >
                    <GitBranchPlus className="mr-2 h-4 w-4" />
                    {t.notebooks.researchThreadStartRecommendedDraft}
                  </Button>
                </div>
              </div>
            ) : null}
            {listedThreads.map((thread) => {
              const isRecommended = recommendedThread?.id === thread.id;
              const isDraftSeedThread = draftSeedThread?.id === thread.id;

              return (
                <div
                  key={thread.id}
                  className="rounded-md border p-3"
                  data-testid={`research-thread-card-${thread.id}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-medium">{thread.title}</p>
                        {isRecommended ? (
                          <Badge variant="outline">
                            {t.notebooks.researchThreadCardRecommended}
                          </Badge>
                        ) : null}
                        {isDraftSeedThread ? (
                          <Badge>{t.notebooks.researchThreadCardDraftSeed}</Badge>
                        ) : null}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {t("notebooks.researchThreadSummary", {
                          seedKind: formatSeedKind(thread.seed_kind),
                          entryCount: thread.entry_count,
                          sourceCount: thread.source_ids.length,
                        })}
                      </p>
                      {isRecommended ? (
                        <p className="text-xs text-muted-foreground">
                          {t("notebooks.researchThreadCardRecommendedReason", {
                            entryCount: thread.entry_count,
                            sourceCount: thread.source_ids.length,
                          })}
                        </p>
                      ) : null}
                      {isDraftSeedThread ? (
                        <p className="text-xs text-muted-foreground">
                          {t("notebooks.researchThreadCardDraftSeedReason", {
                            seedKind: formatSeedKind(thread.seed_kind),
                          })}
                        </p>
                      ) : null}
                      <p className="text-xs text-muted-foreground">
                        {t("notebooks.researchThreadUpdated", {
                          time: formatDistanceToNow(new Date(thread.updated), {
                            addSuffix: true,
                            locale: dfLocale,
                          }),
                        })}
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleCreateDraftFromThread(thread.id)}
                      disabled={createDraftFromThread.isPending}
                    >
                      <GitBranchPlus className="mr-2 h-4 w-4" />
                      {t.notebooks.researchThreadCreateDraft}
                    </Button>
                  </div>
                </div>
              );
            })}
          </>
        )}
      </CardContent>
    </Card>
  );
}
