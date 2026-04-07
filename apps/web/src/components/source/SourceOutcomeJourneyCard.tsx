"use client";

import { ArrowRight, CheckCircle2, CircleDashed, ListChecks, Sparkles, Unplug } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useTranslation } from "@/lib/hooks/use-translation";
import { getJourneyStateLabel, getWorkflowStateLabel } from "@/lib/i18n-state-labels";
import type {
  AuditableRunResponse,
  DraftResponse,
  SourceDetailResponse,
  SourceProcessingReportResponse,
} from "@/lib/types/api";

type JourneyState = "complete" | "active" | "attention" | "todo";

interface SourceOutcomeJourneyCardProps {
  source: SourceDetailResponse;
  report?: SourceProcessingReportResponse;
  latestRun?: AuditableRunResponse | null;
  latestDraft?: DraftResponse | null;
  onOpenDetails: () => void;
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

function getProcessingState(report?: SourceProcessingReportResponse): JourneyState {
  const status = report?.processing_status;
  if (!status) {
    return "todo";
  }
  if (status === "failed") {
    return "attention";
  }
  if (["queued", "running", "new"].includes(status)) {
    return "active";
  }
  return "complete";
}

function getAuditableState(run?: AuditableRunResponse | null): JourneyState {
  if (!run) {
    return "todo";
  }
  if (run.status === "failed") {
    return "attention";
  }
  if (run.status === "queued" || run.status === "running") {
    return "active";
  }
  return "complete";
}

function getDraftState(source: SourceDetailResponse, draft?: DraftResponse | null): JourneyState {
  if (!source.notebooks?.length) {
    return "todo";
  }
  if (!draft) {
    return "active";
  }
  if (draft.status === "failed") {
    return "attention";
  }
  if (draft.status === "queued" || draft.status === "running") {
    return "active";
  }
  return "complete";
}

function getVerifyState(draft?: DraftResponse | null): JourneyState {
  if (!draft) {
    return "todo";
  }
  if (draft.status === "verified") {
    return "complete";
  }
  if (draft.status === "completed") {
    return "active";
  }
  if (draft.status === "failed") {
    return "attention";
  }
  return "todo";
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
    <div className="flex items-start gap-3 rounded-md border bg-muted/20 p-3">
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

export function SourceOutcomeJourneyCard({
  source,
  report,
  latestRun,
  latestDraft,
  onOpenDetails,
}: SourceOutcomeJourneyCardProps) {
  const { t } = useTranslation();
  const processingState = getProcessingState(report);
  const auditableState = getAuditableState(latestRun);
  const draftState = getDraftState(source, latestDraft);
  const verifyState = getVerifyState(latestDraft);
  const firstNotebookId = source.notebooks?.[0];
  const linkedNotebookCount = source.notebooks?.length ?? 0;
  const draftNotebookId = latestDraft?.notebook_id || firstNotebookId;

  let nextTitle = t.sources.outcomeRunAuditableTitle;
  let nextDescription = t.sources.outcomeRunAuditableDescription;
  let nextSubdetail: string | null = null;
  let nextAction: React.ReactNode = null;

  if (!source.notebooks?.length) {
    nextTitle = t.sources.outcomeAddNotebookTitle;
    nextDescription = t.sources.outcomeAddNotebookDescription;
    nextAction = (
      <Button type="button" variant="outline" size="sm" onClick={onOpenDetails}>
        <ListChecks className="mr-2 h-4 w-4" />
        {t.sources.outcomeOpenDetailsAndLinkNotebook}
      </Button>
    );
  } else if (!latestRun || latestRun.status !== "completed") {
    nextAction = (
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      >
        <ArrowRight className="mr-2 h-4 w-4" />
        {t.sources.outcomeReviewAuditableStatus}
      </Button>
    );
  } else if (!latestDraft && firstNotebookId) {
    nextTitle = t.sources.outcomeCreateDraftTitle;
    nextDescription = t.sources.outcomeCreateDraftDescription;
    if (linkedNotebookCount > 1) {
      nextTitle = t.sources.outcomeChooseDraftNotebookTitle;
      nextDescription = t("sources.outcomeChooseDraftNotebookDescription", {
        count: linkedNotebookCount,
      });
      nextAction = (
        <Button type="button" variant="outline" size="sm" onClick={onOpenDetails}>
          <ListChecks className="mr-2 h-4 w-4" />
          {t.sources.outcomeChooseDraftNotebookAction}
        </Button>
      );
    } else {
      nextAction = (
        <Button asChild type="button" size="sm">
          <Link href={`/notebooks/${encodeURIComponent(firstNotebookId)}`}>
            <ArrowRight className="mr-2 h-4 w-4" />
            {t.sources.outcomeOpenNotebookDraftLane}
          </Link>
        </Button>
      );
    }
  } else if (latestDraft && latestDraft.status !== "verified" && draftNotebookId) {
    nextTitle = t.sources.outcomeReviewLatestDraftTitle;
    nextDescription = t.sources.outcomeReviewLatestDraftDescription;
    nextAction = (
      <Button asChild type="button" size="sm">
        <Link href={`/notebooks/${encodeURIComponent(draftNotebookId)}`}>
          <ArrowRight className="mr-2 h-4 w-4" />
          {t.sources.outcomeOpenDraftReview}
        </Link>
      </Button>
    );
  } else if (latestDraft?.status === "verified") {
    nextTitle = t.sources.outcomeVerifiedReadyTitle;
    nextDescription = t.sources.outcomeVerifiedReadyDescription;
    nextAction = draftNotebookId ? (
      <Button asChild type="button" variant="outline" size="sm">
        <Link href={`/notebooks/${encodeURIComponent(draftNotebookId)}`}>
          <ArrowRight className="mr-2 h-4 w-4" />
          {t.sources.outcomeOpenVerifiedNotebook}
        </Link>
      </Button>
    ) : null;
  }

  return (
    <Card data-testid="source-outcome-journey-card">
      <CardHeader>
        <CardTitle>{t.sources.outcomePathTitle}</CardTitle>
        <CardDescription>{t.sources.outcomePathDescription}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-2">
          <JourneyStep
            title={t.sources.outcomeSourceProcessing}
            state={processingState}
            stateLabel={getJourneyStateLabel(t, processingState)}
            detail={
              report
                ? t("sources.outcomeProcessingReport", {
                    message: report.processing_message,
                    paragraphs: report.paragraph_count,
                    insights: report.insights_count,
                  })
                : t.sources.outcomeProcessingLoading
            }
          />
          <JourneyStep
            title={t.sources.outcomeAuditableMarkdown}
            state={auditableState}
            stateLabel={getJourneyStateLabel(t, auditableState)}
            detail={
              latestRun
                ? t("sources.outcomeLatestRunStatus", {
                    status: getWorkflowStateLabel(t, latestRun.status),
                    coverage: latestRun.metrics.coverage_rate.toFixed(2),
                  })
                : t.sources.outcomeNoRun
            }
          />
          <JourneyStep
            title={t.sources.outcomeNotebookDraft}
            state={draftState}
            stateLabel={getJourneyStateLabel(t, draftState)}
            detail={
              source.notebooks?.length
                ? latestDraft
                  ? t("sources.outcomeLatestDraftStatus", {
                      status: getWorkflowStateLabel(t, latestDraft.status),
                      notebookId: source.notebooks[0],
                    })
                  : t("sources.outcomeLinkedNotebookCount", {
                      count: source.notebooks.length,
                    })
                : t.sources.outcomeNoNotebookLink
            }
          />
          <JourneyStep
            title={t.sources.outcomeVerify}
            state={verifyState}
            stateLabel={getJourneyStateLabel(t, verifyState)}
            detail={
              latestDraft?.status === "verified"
                ? t.sources.outcomeVerifiedExists
                : latestDraft
                  ? t.sources.outcomeVerifyDetail
                  : t.sources.outcomeVerifyNeedsDraft
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
