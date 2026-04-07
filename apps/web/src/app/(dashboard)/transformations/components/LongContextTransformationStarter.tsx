"use client";

import { ArrowRight, BookText, MessageSquareQuote, ScrollText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useTranslation } from "@/lib/hooks/use-translation";

interface LongContextTransformationStarterProps {
  transformationName: string;
  onOpenPlayground: () => void;
}

export function LongContextTransformationStarter({
  transformationName,
  onOpenPlayground,
}: LongContextTransformationStarterProps) {
  const { t } = useTranslation();

  return (
    <Card
      className="ui-section-enter border-primary/20 bg-primary/5"
      data-testid="long-context-starter"
    >
      <CardHeader className="gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{t.transformations.longContextStarterBuiltIn}</Badge>
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {t.transformations.longContextStarterTitle}
          </span>
        </div>
        <div className="space-y-2">
          <CardTitle>{t.transformations.longContextStarterHeading}</CardTitle>
          <CardDescription>{t.transformations.longContextStarterDescription}</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-lg border bg-background/80 p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium">
              <MessageSquareQuote className="h-4 w-4 text-primary" />
              {t.transformations.longContextStarterInputTitle}
            </div>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>{t.transformations.longContextStarterInput1}</li>
              <li>{t.transformations.longContextStarterInput2}</li>
              <li>{t.transformations.longContextStarterInput3}</li>
            </ul>
          </div>
          <div className="rounded-lg border bg-background/80 p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium">
              <BookText className="h-4 w-4 text-primary" />
              {t.transformations.longContextStarterOutputTitle}
            </div>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>{t.transformations.longContextStarterOutput1}</li>
              <li>{t.transformations.longContextStarterOutput2}</li>
              <li>{t.transformations.longContextStarterOutput3}</li>
            </ul>
          </div>
        </div>

        <div
          className="rounded-lg border bg-background/80 p-4"
          data-testid="long-context-next-ladder"
        >
          <div className="mb-3 flex items-center gap-2 text-sm font-medium">
            <ArrowRight className="h-4 w-4 text-primary" />
            {t.transformations.longContextStarterNextTitle}
          </div>
          <ol className="space-y-2 text-sm text-muted-foreground">
            <li>{t.transformations.longContextStarterNext1}</li>
            <li>{t.transformations.longContextStarterNext2}</li>
            <li>{t.transformations.longContextStarterNext3}</li>
            <li>{t.transformations.longContextStarterNext4}</li>
          </ol>
        </div>

        <div className="flex flex-col gap-3 rounded-lg border bg-background/80 p-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium">
              {t("transformations.longContextStarterTransformation", {
                name: transformationName,
              })}
            </p>
            <p className="text-sm text-muted-foreground">
              {t.transformations.longContextStarterHint}
            </p>
          </div>
          <Button
            onClick={onOpenPlayground}
            className="ui-primary-cta"
            data-testid="open-long-context-starter"
          >
            <ScrollText className="mr-2 h-4 w-4" />
            {t.transformations.longContextStarterAction}
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
