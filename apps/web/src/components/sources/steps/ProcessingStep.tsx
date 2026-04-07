"use client";

import { Sparkles } from "lucide-react";
import { type Control, Controller } from "react-hook-form";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { CheckboxList } from "@/components/ui/checkbox-list";
import { FormSection } from "@/components/ui/form-section";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { SettingsResponse } from "@/lib/types/api";
import type { Transformation } from "@/lib/types/transformations";

interface CreateSourceFormData {
  type: "link" | "upload" | "text";
  title?: string;
  url?: string;
  content?: string;
  file?: unknown;
  notebooks?: string[];
  transformations?: string[];
  embed: boolean;
  async_processing: boolean;
}

interface ProcessingStepProps {
  control: Control<CreateSourceFormData>;
  transformations: Transformation[];
  selectedTransformations: string[];
  onToggleTransformation: (transformationId: string) => void;
  loading?: boolean;
  settings?: SettingsResponse;
}

const LONG_CONTEXT_TRANSFORMATION_ID = "transformation:chat_knowledgeization";

export function ProcessingStep({
  control,
  transformations,
  selectedTransformations,
  onToggleTransformation,
  loading = false,
  settings,
}: ProcessingStepProps) {
  const { t } = useTranslation();
  const orderedTransformations = [...transformations].sort((left, right) => {
    if (left.id === LONG_CONTEXT_TRANSFORMATION_ID) {
      return -1;
    }
    if (right.id === LONG_CONTEXT_TRANSFORMATION_ID) {
      return 1;
    }
    return left.title.localeCompare(right.title);
  });
  const longContextTransformation = orderedTransformations.find(
    (transformation) => transformation.id === LONG_CONTEXT_TRANSFORMATION_ID,
  );
  const longContextSelected = Boolean(
    longContextTransformation && selectedTransformations.includes(longContextTransformation.id),
  );
  const transformationItems = orderedTransformations.map((transformation) => ({
    id: transformation.id,
    title: transformation.title,
    description: transformation.description,
  }));

  return (
    <div className="space-y-8">
      {longContextTransformation ? (
        <FormSection
          title={t.sources.longContextPathTitle}
          description={t.sources.longContextPathDescription}
        >
          <div
            className="rounded-xl border bg-muted/30 p-4"
            data-testid="long-context-recommendation"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <span className="text-sm font-medium">{longContextTransformation.title}</span>
                  {longContextSelected ? (
                    <Badge variant="secondary">{t.sources.longContextPathSelected}</Badge>
                  ) : null}
                </div>
                <p className="text-xs text-muted-foreground">{t.sources.longContextPathHelper}</p>
              </div>
              <Button
                type="button"
                size="sm"
                variant={longContextSelected ? "secondary" : "default"}
                onClick={() => onToggleTransformation(longContextTransformation.id)}
              >
                {longContextSelected
                  ? t.sources.longContextPathRemove
                  : t.sources.longContextPathAdd}
              </Button>
            </div>

            <div className="mt-4 grid gap-2 text-xs text-muted-foreground md:grid-cols-3">
              <div className="rounded-md border bg-background px-3 py-2">
                {t.sources.longContextPathExampleChats}
              </div>
              <div className="rounded-md border bg-background px-3 py-2">
                {t.sources.longContextPathExampleWeb}
              </div>
              <div className="rounded-md border bg-background px-3 py-2">
                {t.sources.longContextPathExampleNotes}
              </div>
            </div>

            <p className="mt-3 text-xs text-muted-foreground">
              {t.sources.longContextBuiltOnTransformation.replace(
                "{title}",
                longContextTransformation.title,
              )}
            </p>
          </div>
        </FormSection>
      ) : null}

      <FormSection
        title={`${t.navigation.transformations} (${t.common.optional})`}
        description={t.sources.processDescription}
      >
        <CheckboxList
          items={transformationItems}
          selectedIds={selectedTransformations}
          onToggle={onToggleTransformation}
          loading={loading}
          emptyMessage={t.common.noMatches}
        />
      </FormSection>

      <FormSection title={t.navigation.settings} description={t.sources.processDescription}>
        <div className="space-y-4">
          {settings?.default_embedding_option === "ask" && (
            <Controller
              control={control}
              name="embed"
              render={({ field }) => (
                <label
                  htmlFor="enable-embedding"
                  className="flex items-start gap-3 cursor-pointer p-3 rounded-md hover:bg-muted"
                >
                  <Checkbox
                    id="enable-embedding"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    className="mt-0.5"
                  />
                  <div className="flex-1">
                    <span className="text-sm font-medium block">{t.sources.enableEmbedding}</span>
                    <p className="text-xs text-muted-foreground mt-1">{t.sources.embeddingDesc}</p>
                  </div>
                </label>
              )}
            />
          )}

          {settings?.default_embedding_option === "always" && (
            <div className="p-3 rounded-md bg-primary/10 border border-primary/30">
              <div className="flex items-start gap-3">
                <div className="w-4 h-4 bg-primary rounded-full mt-0.5 flex-shrink-0"></div>
                <div className="flex-1">
                  <span className="text-sm font-medium block text-primary">
                    {t.sources.embeddingAlways}
                  </span>
                  <p className="text-xs text-primary mt-1">
                    {t.sources.embeddingAlwaysDesc}
                    {t.sources.changeInSettings}{" "}
                    <span className="font-medium">{t.navigation.settings}</span>.
                  </p>
                </div>
              </div>
            </div>
          )}

          {settings?.default_embedding_option === "never" && (
            <div className="p-3 rounded-md bg-muted border border-border">
              <div className="flex items-start gap-3">
                <div className="w-4 h-4 bg-muted-foreground rounded-full mt-0.5 flex-shrink-0"></div>
                <div className="flex-1">
                  <span className="text-sm font-medium block text-foreground">
                    {t.sources.embeddingNever}
                  </span>
                  <p className="text-xs text-muted-foreground mt-1">
                    {t.sources.embeddingNeverDesc}
                    {t.sources.changeInSettings}{" "}
                    <span className="font-medium">{t.navigation.settings}</span>.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </FormSection>
    </div>
  );
}
