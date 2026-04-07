"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTranslation } from "@/lib/hooks/use-translation";

interface AuditableClaimReviewWorkspaceProps {
  claims: Array<Record<string, unknown>>;
  sections: Array<Record<string, unknown>>;
  onRepairClaim: (index: number) => void;
  onRepairSection: (index: number) => void;
  repairClaimPending?: boolean;
  repairSectionPending?: boolean;
}

function getPidList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => String(item))
    .map((item) => item.trim())
    .filter(Boolean);
}

function getLinkedSectionTitles(
  claimPids: string[],
  sections: Array<Record<string, unknown>>,
): string[] {
  if (claimPids.length === 0) {
    return [];
  }
  const pidSet = new Set(claimPids);
  return sections
    .filter((section) => getPidList(section.source_pids).some((pid) => pidSet.has(pid)))
    .map((section, index) => String(section.title ?? `Section ${index + 1}`));
}

export function AuditableClaimReviewWorkspace({
  claims,
  sections,
  onRepairClaim,
  onRepairSection,
  repairClaimPending = false,
  repairSectionPending = false,
}: AuditableClaimReviewWorkspaceProps) {
  const { t } = useTranslation();

  return (
    <Card data-testid="auditable-claim-review-workspace">
      <CardHeader>
        <CardTitle>{t.sources.auditableClaimReviewTitle}</CardTitle>
        <CardDescription>{t.sources.auditableClaimReviewDescription}</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="claims" className="space-y-4">
          <TabsList>
            <TabsTrigger value="claims">{t.sources.auditableClaimReviewClaimsTab}</TabsTrigger>
            <TabsTrigger value="sections">{t.sources.auditableClaimReviewSectionsTab}</TabsTrigger>
          </TabsList>

          <TabsContent value="claims" className="space-y-3">
            {claims.length === 0 ? (
              <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
                {t.sources.auditableClaimReviewEmptyClaims}
              </div>
            ) : (
              claims.map((claim, index) => {
                const claimPids = getPidList(claim.source_pids);
                const linkedSections = getLinkedSectionTitles(claimPids, sections);
                return (
                  <div
                    key={`claim-${index}`}
                    className="rounded-md border bg-muted/20 p-4"
                    data-testid={`claim-review-card-${index}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm font-medium">
                            {t("sources.auditableClaimReviewClaimLabel", {
                              index: index + 1,
                            })}
                          </p>
                          <p className="mt-1 text-sm">{String(claim.text ?? "")}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-muted-foreground">
                            {t.sources.auditableClaimReviewEvidencePids}
                          </p>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {claimPids.length > 0 ? (
                              claimPids.map((pid) => (
                                <Badge key={pid} variant="secondary">
                                  {pid}
                                </Badge>
                              ))
                            ) : (
                              <span className="text-sm text-muted-foreground">
                                {t.sources.auditableClaimReviewNoEvidence}
                              </span>
                            )}
                          </div>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-muted-foreground">
                            {t.sources.auditableClaimReviewLinkedSections}
                          </p>
                          <p className="mt-1 text-sm text-muted-foreground">
                            {linkedSections.length > 0
                              ? linkedSections.join(", ")
                              : t.sources.auditableClaimReviewNoLinkedSections}
                          </p>
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => onRepairClaim(index)}
                        disabled={repairClaimPending}
                      >
                        {t.sources.auditableClaimReviewRepairClaim}
                      </Button>
                    </div>
                  </div>
                );
              })
            )}
          </TabsContent>

          <TabsContent value="sections" className="space-y-3">
            {sections.length === 0 ? (
              <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
                {t.sources.auditableClaimReviewEmptySections}
              </div>
            ) : (
              sections.map((section, index) => {
                const sectionPids = getPidList(section.source_pids);
                return (
                  <div
                    key={`section-${index}`}
                    className="rounded-md border bg-muted/20 p-4"
                    data-testid={`section-review-card-${index}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm font-medium">
                            {String(
                              section.title ??
                                t("sources.auditableClaimReviewSectionFallback", {
                                  index: index + 1,
                                }),
                            )}
                          </p>
                          <p className="mt-1 text-sm text-muted-foreground">
                            {sectionPids.length > 0
                              ? t("sources.auditableClaimReviewSectionEvidenceCount", {
                                  count: sectionPids.length,
                                })
                              : t.sources.auditableClaimReviewSectionNoEvidence}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-muted-foreground">
                            {t.sources.auditableClaimReviewSectionPids}
                          </p>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {sectionPids.length > 0 ? (
                              sectionPids.map((pid) => (
                                <Badge key={pid} variant="outline">
                                  {pid}
                                </Badge>
                              ))
                            ) : (
                              <span className="text-sm text-muted-foreground">
                                {t.sources.auditableClaimReviewNoEvidence}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => onRepairSection(index)}
                        disabled={repairSectionPending}
                      >
                        {t.sources.auditableClaimReviewRepairSection}
                      </Button>
                    </div>
                  </div>
                );
              })
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
