"use client";

import { Play, RefreshCw, Wand2 } from "lucide-react";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTransformations } from "@/lib/hooks/use-transformations";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { Transformation } from "@/lib/types/transformations";
import { DefaultPromptEditor } from "./components/DefaultPromptEditor";
import { LongContextTransformationStarter } from "./components/LongContextTransformationStarter";
import { TransformationPlayground } from "./components/TransformationPlayground";
import { TransformationsList } from "./components/TransformationsList";

export default function TransformationsPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("transformations");
  const [selectedTransformation, setSelectedTransformation] = useState<
    Transformation | undefined
  >();
  const { data: transformations, isLoading, refetch } = useTransformations();
  const longContextTransformation = useMemo(
    () =>
      transformations?.find(
        (transformation) =>
          transformation.id === "transformation:chat_knowledgeization" ||
          transformation.name === "chat_knowledgeization" ||
          transformation.name === "Chat Knowledgeization",
      ),
    [transformations],
  );

  const handlePlayground = (transformation: Transformation) => {
    setSelectedTransformation(transformation);
    setActiveTab("playground");
  };

  const handleOpenLongContextStarter = () => {
    if (!longContextTransformation) {
      return;
    }
    handlePlayground(longContextTransformation);
  };

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="ui-page-shell p-6 space-y-6">
          <div className="ui-section-enter flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold">{t.transformations.title}</h1>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                className="ui-icon-button"
                aria-label={t.common.refresh}
                title={t.common.refresh}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="ui-section-enter max-w-5xl">
            <p className="text-muted-foreground">{t.transformations.desc}</p>
          </div>

          {longContextTransformation ? (
            <LongContextTransformationStarter
              transformationName={longContextTransformation.title || longContextTransformation.name}
              onOpenPlayground={handleOpenLongContextStarter}
            />
          ) : null}

          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="ui-section-enter space-y-6"
          >
            <h2 className="sr-only">{t.transformations.workspace}</h2>
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {t.transformations.workspace}
              </p>
              <TabsList
                aria-label={t.common.accessibility.transformationViews}
                className="w-full max-w-xl"
              >
                <TabsTrigger value="transformations" className="flex items-center gap-2">
                  <Wand2 className="h-4 w-4" />
                  {t.transformations.title}
                </TabsTrigger>
                <TabsTrigger value="playground" className="flex items-center gap-2">
                  <Play className="h-4 w-4" />
                  {t.transformations.playground}
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="transformations" className="space-y-6">
              <DefaultPromptEditor />
              <TransformationsList
                transformations={transformations}
                isLoading={isLoading}
                onPlayground={handlePlayground}
              />
            </TabsContent>

            <TabsContent value="playground">
              <TransformationPlayground
                transformations={transformations}
                selectedTransformation={selectedTransformation}
              />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </AppShell>
  );
}
