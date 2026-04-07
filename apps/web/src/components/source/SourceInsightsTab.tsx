"use client";

import {
  GitBranchPlus,
  Lightbulb,
  MessageCircleQuestion,
  Plus,
  StickyNote,
  Trash2,
} from "lucide-react";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TabsContent } from "@/components/ui/tabs";
import type { SourceInsightResponse } from "@/lib/api/insights";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { Transformation } from "@/lib/types/transformations";

interface SourceInsightsTabProps {
  insights: SourceInsightResponse[];
  transformations: Transformation[];
  selectedTransformation: string;
  creatingInsight: boolean;
  loadingInsights: boolean;
  canSaveInsightsAsNotes: boolean;
  canSaveInsightsToResearchThreads: boolean;
  savingInsightId?: string | null;
  savingInsightThreadId?: string | null;
  onSelectedTransformationChange: (value: string) => void;
  onCreateInsight: () => void;
  onViewInsight: (insight: SourceInsightResponse) => void;
  onDeleteInsight: (id: string) => void;
  onSaveInsightAsNote: (insight: SourceInsightResponse) => void;
  onResearchThisInsight: (insight: SourceInsightResponse) => void;
  onSaveInsightToResearchThread: (insight: SourceInsightResponse) => void;
}

export function SourceInsightsTab({
  insights,
  transformations,
  selectedTransformation,
  creatingInsight,
  loadingInsights,
  canSaveInsightsAsNotes,
  canSaveInsightsToResearchThreads,
  savingInsightId = null,
  savingInsightThreadId = null,
  onSelectedTransformationChange,
  onCreateInsight,
  onViewInsight,
  onDeleteInsight,
  onSaveInsightAsNote,
  onResearchThisInsight,
  onSaveInsightToResearchThread,
}: SourceInsightsTabProps) {
  const { t } = useTranslation();
  const canShowSaveAsNote = canSaveInsightsAsNotes;
  const canShowSaveToResearchThread = canSaveInsightsToResearchThreads;

  return (
    <TabsContent value="insights" className="mt-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5" />
              {t.common.insights}
            </span>
            <Badge variant="secondary">{insights.length}</Badge>
          </CardTitle>
          <CardDescription>{t.sources.insightsDesc}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border bg-muted/30 p-4">
            <Label
              htmlFor="transformation-select"
              className="mb-3 text-sm font-semibold flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              {t.sources.generateNewInsight}
            </Label>
            <div className="flex gap-2">
              <Select
                name="transformation"
                value={selectedTransformation}
                onValueChange={onSelectedTransformationChange}
                disabled={creatingInsight}
              >
                <SelectTrigger id="transformation-select" className="flex-1">
                  <SelectValue placeholder={t.sources.selectTransformation} />
                </SelectTrigger>
                <SelectContent>
                  {transformations.map((transformation) => (
                    <SelectItem key={transformation.id} value={transformation.id}>
                      {transformation.title || transformation.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                size="sm"
                onClick={onCreateInsight}
                disabled={!selectedTransformation || creatingInsight}
              >
                {creatingInsight ? (
                  <>
                    <LoadingSpinner className="mr-2 h-3 w-3" />
                    {t.common.creating}
                  </>
                ) : (
                  <>
                    <Plus className="mr-2 h-4 w-4" />
                    {t.common.create}
                  </>
                )}
              </Button>
            </div>
          </div>

          {loadingInsights ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : insights.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Lightbulb className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">{t.sources.noInsightsYet}</p>
              <p className="text-xs mt-1">{t.sources.createFirstInsight}</p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="rounded-lg border bg-muted/20 p-4">
                <p className="text-sm font-medium">{t.sources.insightsNextLaneTitle}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {t.sources.insightsNextLaneDescription}
                </p>
              </div>
              {insights.map((insight) => (
                <div key={insight.id} className="rounded-lg border bg-background p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="outline" className="text-xs uppercase">
                          {insight.insight_type}
                        </Badge>
                        {canShowSaveAsNote ? (
                          <Badge variant="secondary">{t.sources.saveInsightAsNote}</Badge>
                        ) : null}
                        {canShowSaveToResearchThread ? (
                          <Badge variant="outline">{t.sources.saveInsightToResearchThread}</Badge>
                        ) : null}
                      </div>
                    </div>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {insight.content.slice(0, 180)}
                    {insight.content.length > 180 ? "…" : ""}
                  </p>
                  <div className="mt-4 space-y-3 border-t pt-3">
                    <div className="flex flex-wrap gap-2">
                      {canShowSaveAsNote ? (
                        <Button
                          size="sm"
                          onClick={() => onSaveInsightAsNote(insight)}
                          disabled={savingInsightId === insight.id}
                        >
                          <StickyNote className="mr-2 h-4 w-4" />
                          {savingInsightId === insight.id
                            ? t.common.saving
                            : t.sources.saveInsightAsNote}
                        </Button>
                      ) : null}
                      {canShowSaveToResearchThread ? (
                        <Button
                          size="sm"
                          variant={canShowSaveAsNote ? "outline" : "default"}
                          onClick={() => onSaveInsightToResearchThread(insight)}
                          disabled={savingInsightThreadId === insight.id}
                        >
                          <GitBranchPlus className="mr-2 h-4 w-4" />
                          {savingInsightThreadId === insight.id
                            ? t.common.saving
                            : t.sources.saveInsightToResearchThread}
                        </Button>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button size="sm" variant="outline" onClick={() => onViewInsight(insight)}>
                        {t.sources.viewInsight}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onResearchThisInsight(insight)}
                      >
                        <MessageCircleQuestion className="mr-2 h-4 w-4" />
                        {t.sources.researchThisInsight}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onDeleteInsight(insight.id)}
                        className="text-destructive hover:text-destructive"
                        aria-label="Delete insight"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {!canSaveInsightsAsNotes && insights.length > 0 ? (
            <p className="text-xs text-muted-foreground">{t.sources.saveInsightNeedsNotebook}</p>
          ) : null}
        </CardContent>
      </Card>
    </TabsContent>
  );
}
