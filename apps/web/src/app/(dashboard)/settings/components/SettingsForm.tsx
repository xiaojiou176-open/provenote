"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, CheckCircle2, ChevronDownIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSettings, useUpdateSettings } from "@/lib/hooks/use-settings";
import { useTranslation } from "@/lib/hooks/use-translation";

const settingsSchema = z.object({
  default_content_processing_engine_doc: z.enum(["auto", "docling", "simple"]).optional(),
  default_content_processing_engine_url: z.enum(["auto", "firecrawl", "jina", "simple"]).optional(),
  default_embedding_option: z.enum(["ask", "always", "never"]).optional(),
  auto_delete_files: z.enum(["yes", "no"]).optional(),
});

type SettingsFormData = z.infer<typeof settingsSchema>;

export function SettingsForm() {
  const { t } = useTranslation();
  const { data: settings, isLoading, error } = useSettings();
  const updateSettings = useUpdateSettings();
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    doc: false,
    url: false,
    embedding: false,
    files: false,
  });
  const [saveState, setSaveState] = useState<"idle" | "success" | "error">("idle");

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<SettingsFormData>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      default_content_processing_engine_doc: undefined,
      default_content_processing_engine_url: undefined,
      default_embedding_option: undefined,
      auto_delete_files: undefined,
    },
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };
  const syncedFormValues = useMemo<SettingsFormData | null>(() => {
    if (!settings) {
      return null;
    }

    return {
      default_content_processing_engine_doc: settings.default_content_processing_engine_doc as
        | "auto"
        | "docling"
        | "simple"
        | undefined,
      default_content_processing_engine_url: settings.default_content_processing_engine_url as
        | "auto"
        | "firecrawl"
        | "jina"
        | "simple"
        | undefined,
      default_embedding_option: settings.default_embedding_option as
        | "ask"
        | "always"
        | "never"
        | undefined,
      auto_delete_files: settings.auto_delete_files as "yes" | "no" | undefined,
    };
  }, [settings]);

  useEffect(() => {
    if (!syncedFormValues) {
      return;
    }
    reset(syncedFormValues, { keepDirtyValues: true });
  }, [reset, syncedFormValues]);

  useEffect(() => {
    if (isDirty) {
      setSaveState("idle");
    }
  }, [isDirty]);

  useEffect(() => {
    if (saveState === "idle" || updateSettings.isPending) {
      return;
    }
    const timer = window.setTimeout(() => setSaveState("idle"), 2200);
    return () => window.clearTimeout(timer);
  }, [saveState, updateSettings.isPending]);

  const onSubmit = async (data: SettingsFormData) => {
    setSaveState("idle");
    try {
      await updateSettings.mutateAsync(data);
      setSaveState("success");
    } catch {
      setSaveState("error");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>{t.settings.loadFailed}</AlertTitle>
        <AlertDescription>
          {error instanceof Error ? error.message : t.common.error}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t.settings.contentProcessing}</CardTitle>
          <CardDescription>{t.settings.contentProcessingDesc}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <Label htmlFor="doc_engine">{t.settings.docEngine}</Label>
            <Controller
              name="default_content_processing_engine_doc"
              control={control}
              render={({ field }) => (
                <Select
                  key={field.value}
                  name={field.name}
                  value={field.value || ""}
                  onValueChange={field.onChange}
                  disabled={field.disabled || isLoading}
                >
                  <SelectTrigger
                    id="doc_engine"
                    className="w-full"
                    data-testid="settings-doc-engine-trigger"
                  >
                    <SelectValue placeholder={t.settings.docEnginePlaceholder} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">{t.settings.autoRecommended}</SelectItem>
                    <SelectItem value="docling" data-testid="settings-doc-engine-docling">
                      {t.settings.docling}
                    </SelectItem>
                    <SelectItem value="simple">{t.settings.simple}</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
            <Collapsible open={expandedSections.doc} onOpenChange={() => toggleSection("doc")}>
              <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
                <ChevronDownIcon
                  className={`h-4 w-4 transition-transform ${expandedSections.doc ? "rotate-180" : ""}`}
                />
                {t.settings.helpMeChoose}
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2 text-sm text-muted-foreground space-y-2">
                <p>{t.settings.docHelp}</p>
              </CollapsibleContent>
            </Collapsible>
          </div>

          <div className="space-y-3">
            <Label htmlFor="url_engine">{t.settings.urlEngine}</Label>
            <Controller
              name="default_content_processing_engine_url"
              control={control}
              render={({ field }) => (
                <Select
                  key={field.value}
                  name={field.name}
                  value={field.value || ""}
                  onValueChange={field.onChange}
                  disabled={field.disabled || isLoading}
                >
                  <SelectTrigger id="url_engine" className="w-full">
                    <SelectValue placeholder={t.settings.urlEnginePlaceholder} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">{t.settings.autoRecommended}</SelectItem>
                    <SelectItem value="firecrawl">{t.settings.firecrawl}</SelectItem>
                    <SelectItem value="jina">{t.settings.jina}</SelectItem>
                    <SelectItem value="simple">{t.settings.simple}</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
            <Collapsible open={expandedSections.url} onOpenChange={() => toggleSection("url")}>
              <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
                <ChevronDownIcon
                  className={`h-4 w-4 transition-transform ${expandedSections.url ? "rotate-180" : ""}`}
                />
                {t.settings.helpMeChoose}
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2 text-sm text-muted-foreground space-y-2">
                <p>{t.settings.urlHelp}</p>
              </CollapsibleContent>
            </Collapsible>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t.settings.embeddingAndSearch}</CardTitle>
          <CardDescription>{t.settings.embeddingAndSearchDesc}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <Label htmlFor="embedding">{t.settings.defaultEmbeddingOption}</Label>
            <Controller
              name="default_embedding_option"
              control={control}
              render={({ field }) => (
                <Select
                  key={field.value}
                  name={field.name}
                  value={field.value || ""}
                  onValueChange={field.onChange}
                  disabled={field.disabled || isLoading}
                >
                  <SelectTrigger
                    id="embedding"
                    className="w-full"
                    data-testid="settings-embedding-trigger"
                  >
                    <SelectValue placeholder={t.settings.embeddingOptionPlaceholder} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ask">{t.settings.ask}</SelectItem>
                    <SelectItem value="always" data-testid="settings-embedding-always">
                      {t.settings.always}
                    </SelectItem>
                    <SelectItem value="never">{t.settings.never}</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
            <Collapsible
              open={expandedSections.embedding}
              onOpenChange={() => toggleSection("embedding")}
            >
              <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
                <ChevronDownIcon
                  className={`h-4 w-4 transition-transform ${expandedSections.embedding ? "rotate-180" : ""}`}
                />
                {t.settings.helpMeChoose}
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2 text-sm text-muted-foreground space-y-2">
                <p>{t.settings.embeddingHelp}</p>
              </CollapsibleContent>
            </Collapsible>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t.settings.fileManagement}</CardTitle>
          <CardDescription>{t.settings.fileManagementDesc}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <Label htmlFor="auto_delete">{t.settings.autoDeleteFiles}</Label>
            <Controller
              name="auto_delete_files"
              control={control}
              render={({ field }) => (
                <Select
                  key={field.value}
                  name={field.name}
                  value={field.value || ""}
                  onValueChange={field.onChange}
                  disabled={field.disabled || isLoading}
                >
                  <SelectTrigger id="auto_delete" className="w-full">
                    <SelectValue placeholder={t.settings.autoDeletePlaceholder} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="yes">{t.common.yes}</SelectItem>
                    <SelectItem value="no">{t.common.no}</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
            <Collapsible open={expandedSections.files} onOpenChange={() => toggleSection("files")}>
              <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
                <ChevronDownIcon
                  className={`h-4 w-4 transition-transform ${expandedSections.files ? "rotate-180" : ""}`}
                />
                {t.settings.helpMeChoose}
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2 text-sm text-muted-foreground space-y-2">
                <p>{t.settings.filesHelp}</p>
              </CollapsibleContent>
            </Collapsible>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <div className="flex items-center gap-3">
          <div className="min-h-5 text-sm" aria-live="polite">
            {saveState === "success" && !updateSettings.isPending && (
              <span className="ui-success-pop inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="h-4 w-4" />
                {t.common.saveSuccess}
              </span>
            )}
            {saveState === "error" && !updateSettings.isPending && (
              <span className="inline-flex items-center gap-1 text-destructive ui-form-error">
                <AlertCircle className="h-4 w-4" />
                {t.common.error}
              </span>
            )}
          </div>
          <Button
            type="submit"
            disabled={!isDirty || updateSettings.isPending}
            aria-busy={updateSettings.isPending}
            className="ui-primary-cta"
          >
            {updateSettings.isPending && <LoadingSpinner size="sm" className="mr-2" />}
            {updateSettings.isPending ? t.common.saving : t.common.save}
          </Button>
        </div>
      </div>
    </form>
  );
}
