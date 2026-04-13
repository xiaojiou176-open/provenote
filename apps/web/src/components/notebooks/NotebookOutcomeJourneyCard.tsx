"use client";

import {
  ArrowRight,
  CheckCircle2,
  CircleDashed,
  GitBranchPlus,
  Sparkles,
  Unplug,
} from "lucide-react";
import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useNotebookDrafts } from "@/lib/hooks/use-drafts";
import { useNotebookResearchThreads } from "@/lib/hooks/use-research-threads";
import { useTranslation } from "@/lib/hooks/use-translation";
import { getJourneyStateLabel, getWorkflowStateLabel } from "@/lib/i18n-state-labels";
import type { DraftResponse, SourceListResponse } from "@/lib/types/api";
import { getRecommendedResearchThread } from "./research-thread-recommendation";

type JourneyState = "complete" | "active" | "attention" | "todo";

interface NotebookOutcomeJourneyCardProps {
  notebookId: string;
  sources: SourceListResponse[];
  sourcesLoading?: boolean;
  onOpenDraftLane?: () => void;
  onOpenResearchThreadsLane?: () => void;
  draftSeedThreadId?: string;
}

function getStepVariant(state: JourneyState) {
  switch (state) {
    case "complete":
      return "default" as const;
    case "active":
      return "secondary" as const;
    case "attention":
      return "destructive" as const;
    default:
      return "outline" as const;
  }
}

function getStepIcon(state: JourneyState) {
  switch (state) {
    case "complete":
      return <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
    case "active":
      return <Sparkles className="h-4 w-4 text-amber-600" />;
    case "attention":
      return <Unplug className="h-4 w-4 text-destructive" />;
    default:
      return <CircleDashed className="h-4 w-4 text-muted-foreground" />;
  }
}

function JourneyStep({
  title,
  state,
  detail,
  stateLabel,
}: {
  title: string;
  state: JourneyState;
  detail: string;
  stateLabel: string;
}) {
  return (
    <div className="ui-card-surface flex items-start gap-3 rounded-[1.15rem] border border-border/75 bg-card/95 p-4 shadow-none">
      <div className="mt-0.5">{getStepIcon(state)}</div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-medium">{title}</p>
          <Badge variant={getStepVariant(state)}>{stateLabel}</Badge>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">{detail}</p>
      </div>
    </div>
  );
}

function scrollToTestId(testId: string) {
  const element = document.querySelector(`[data-testid="${testId}"]`);
  if (element instanceof HTMLElement) {
    element.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function getLatestDraft(drafts: DraftResponse[]) {
  return drafts[0] ?? null;
}

export function NotebookOutcomeJourneyCard({
  notebookId,
  sources,
  sourcesLoading = false,
  onOpenDraftLane,
  onOpenResearchThreadsLane,
  draftSeedThreadId,
}: NotebookOutcomeJourneyCardProps) {
  const { t } = useTranslation();
  const { drafts, isLoading: draftsLoading } = useNotebookDrafts(notebookId);
  const { data: threads = [], isLoading: threadsLoading } = useNotebookResearchThreads(notebookId);
  const latestDraft = getLatestDraft(drafts);
  const recommendedThread = getRecommendedResearchThread(threads);
  const draftSeedThread = draftSeedThreadId
    ? (threads.find((thread) => thread.id === draftSeedThreadId) ?? null)
    : null;
  const pendingSources = sources.filter((source) =>
    ["queued", "running", "new"].includes(source.status ?? ""),
  ).length;

  const sourceState: JourneyState =
    sourcesLoading || pendingSources > 0 ? "active" : sources.length > 0 ? "complete" : "todo";
  const draftState: JourneyState = draftsLoading
    ? "active"
    : !latestDraft
      ? "todo"
      : latestDraft.status === "failed"
        ? "attention"
        : latestDraft.status === "verified" || latestDraft.status === "completed"
          ? "complete"
          : "active";
  const verifyState: JourneyState = draftsLoading
    ? "active"
    : !latestDraft
      ? "todo"
      : latestDraft.status === "verified"
        ? "complete"
        : latestDraft.status === "failed"
          ? "attention"
          : "active";
  const threadState: JourneyState = threadsLoading
    ? "active"
    : threads.length > 0
      ? "complete"
      : "todo";

  let nextTitle = t.notebooks.outcomeCreateFirstTitle;
  let nextDescription = t.notebooks.outcomeCreateFirstDescription;
  let nextSubdetail: string | null = null;
  let nextAction: ReactNode = (
    <Button
      type="button"
      size="sm"
      onClick={() => {
        onOpenDraftLane?.();
        scrollToTestId("notebook-drafts-panel");
      }}
    >
      <ArrowRight className="mr-2 h-4 w-4" />
      {t.notebooks.outcomeJumpToDraftLane}
    </Button>
  );

  if (!latestDraft && threads.length > 0) {
    if (draftSeedThread) {
      nextTitle = t.notebooks.outcomeDraftSeedReadyTitle;
      nextDescription = t.notebooks.outcomeDraftSeedReadyDescription;
      nextSubdetail = t("notebooks.outcomeDraftSeedReadyPreview", {
        title: draftSeedThread.title,
        entryCount: draftSeedThread.entry_count,
        sourceCount: draftSeedThread.source_ids.length,
      });
    } else {
      nextTitle = t.notebooks.outcomeDraftFromThreadTitle;
      nextDescription = t.notebooks.outcomeDraftFromThreadDescription;
    }
    if (!draftSeedThread && recommendedThread) {
      nextSubdetail = t("notebooks.outcomeDraftFromThreadPreview", {
        title: recommendedThread.title,
        entryCount: recommendedThread.entry_count,
        sourceCount: recommendedThread.source_ids.length,
      });
    }
    nextAction = (
      <Button
        type="button"
        size="sm"
        variant="outline"
        onClick={() => {
          onOpenResearchThreadsLane?.();
          scrollToTestId("research-threads-panel");
        }}
      >
        <GitBranchPlus className="mr-2 h-4 w-4" />
        {t.notebooks.outcomeReviewResearchThreads}
      </Button>
    );
  } else if (sources.length === 0) {
    nextTitle = t.notebooks.outcomeAddSourcesTitle;
    nextDescription = t.notebooks.outcomeAddSourcesDescription;
    nextAction = null;
  } else if (pendingSources > 0) {
    nextTitle = t.notebooks.outcomeWaitSourcesTitle;
    nextDescription = t.notebooks.outcomeWaitSourcesDescription;
    nextAction = null;
  } else if (latestDraft && latestDraft.status !== "verified") {
    nextTitle = t.notebooks.outcomeCompareTitle;
    nextDescription = t.notebooks.outcomeCompareDescription;
    nextAction = (
      <Button
        type="button"
        size="sm"
        onClick={() => scrollToTestId(`draft-card-${latestDraft.id}`)}
      >
        <ArrowRight className="mr-2 h-4 w-4" />
        {t.notebooks.outcomeReviewLatestDraft}
      </Button>
    );
  } else if (latestDraft?.status === "verified") {
    nextTitle = t.notebooks.outcomeVerifiedReadyTitle;
    nextDescription = t.notebooks.outcomeVerifiedReadyDescription;
    nextAction = (
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => {
          onOpenResearchThreadsLane?.();
          scrollToTestId("research-threads-panel");
        }}
      >
        <GitBranchPlus className="mr-2 h-4 w-4" />
        {t.notebooks.outcomeReviewResearchThreads}
      </Button>
    );
  }

  return (
    <Card
      className="ui-workbench-hero rounded-[1.5rem] border-0 shadow-none"
      data-testid="notebook-outcome-journey-card"
    >
      <CardHeader>
        <p className="ui-workbench-kicker w-fit">{t.notebooks.outcomePathTitle}</p>
        <CardTitle className="font-serif text-[1.9rem] leading-none tracking-[-0.03em]">
          {t.notebooks.outcomePathTitle}
        </CardTitle>
        <CardDescription className="max-w-3xl text-sm leading-6">
          {t.notebooks.outcomePathDescription}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-2">
          <JourneyStep
            title={t.notebooks.outcomeSourcesReady}
            state={sourceState}
            stateLabel={getJourneyStateLabel(t, sourceState)}
            detail={
              sourcesLoading
                ? t.notebooks.outcomeSourcesLoading
                : pendingSources > 0
                  ? t("notebooks.outcomeSourcesPending", { count: pendingSources })
                  : sources.length > 0
                    ? t("notebooks.outcomeSourcesReadyDetail", { count: sources.length })
                    : t.notebooks.outcomeNoSources
            }
          />
          <JourneyStep
            title={t.notebooks.outcomeDraft}
            state={draftState}
            stateLabel={getJourneyStateLabel(t, draftState)}
            detail={
              draftsLoading
                ? t.notebooks.outcomeDraftLoading
                : latestDraft
                  ? t("notebooks.outcomeLatestDraftStatus", {
                      status: getWorkflowStateLabel(t, latestDraft.status),
                      version: latestDraft.version,
                    })
                  : t.notebooks.outcomeNoDraftDetail
            }
          />
          <JourneyStep
            title={t.notebooks.outcomeVerify}
            state={verifyState}
            stateLabel={getJourneyStateLabel(t, verifyState)}
            detail={
              latestDraft?.status === "verified"
                ? t.notebooks.outcomeVerifiedExists
                : latestDraft
                  ? t.notebooks.outcomeVerifyDetail
                  : t.notebooks.outcomeVerifyNeedsDraft
            }
          />
          <JourneyStep
            title={t.notebooks.outcomeResearchThreads}
            state={threadState}
            stateLabel={getJourneyStateLabel(t, threadState)}
            detail={
              threadsLoading
                ? t.notebooks.outcomeThreadsLoading
                : threads.length > 0
                  ? t("notebooks.outcomeThreadsReady", { count: threads.length })
                  : t.notebooks.outcomeNoThreads
            }
          />
        </div>

        <div className="rounded-md border bg-muted/30 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">{nextTitle}</p>
              <p className="mt-1 text-sm text-muted-foreground">{nextDescription}</p>
              {nextSubdetail ? (
                <p className="mt-2 text-xs text-muted-foreground">{nextSubdetail}</p>
              ) : null}
            </div>
            {nextAction}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
