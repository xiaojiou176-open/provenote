"use client";

import { Bot, Check, Edit, Key, Loader2, Plug, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";

import { ModelTestResultDialog } from "@/components/settings";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Credential } from "@/lib/api/credentials";
import { useCredential, useTestCredential } from "@/lib/hooks/use-credentials";
import { useDeleteModel, useTestModel } from "@/lib/hooks/use-models";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { Model, ModelDefaults } from "@/lib/types/models";

import {
  type ModelType,
  PROVIDER_DISPLAY_NAMES,
  PROVIDER_MODALITIES,
  TYPE_COLOR_INACTIVE,
  TYPE_COLORS,
  TYPE_ICONS,
  TYPE_LABELS,
} from "./constants";
import { CredentialFormDialog, DeleteCredentialDialog, DiscoverModelsDialog } from "./dialogs";

interface CredentialItemProps {
  credential: Credential;
  models: Model[];
  defaults: ModelDefaults | null;
  allCredentials: Credential[];
}

function CredentialItem({ credential, models, defaults, allCredentials }: CredentialItemProps) {
  const { t } = useTranslation();
  const { testCredential, isPending: isTestPending, testResults } = useTestCredential();
  const {
    testModel,
    isPending: isModelTestPending,
    testingModelId,
    testResult: modelTestResult,
    testedModelName,
    clearResult: clearModelTestResult,
  } = useTestModel();
  const deleteModel = useDeleteModel();

  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [discoverOpen, setDiscoverOpen] = useState(false);
  const { data: fullCredential } = useCredential(editOpen ? credential.id : "");

  const linkedModels = models.filter((model) => model.credential === credential.id);
  const activeTypes = new Set(linkedModels.map((model) => model.type));
  const testResult = testResults[credential.id];

  const testModelLabel = t.models.testModel;
  const deleteModelLabel = t.models.deleteModel;

  const defaultSlots: Record<string, string> = {};
  if (defaults) {
    const slotMap: Record<string, string | null | undefined> = {
      Chat: defaults.default_chat_model,
      Transform: defaults.default_transformation_model,
      Tools: defaults.default_tools_model,
      "Large Ctx": defaults.large_context_model,
      Embedding: defaults.default_embedding_model,
      TTS: defaults.default_text_to_speech_model,
      STT: defaults.default_speech_to_text_model,
    };
    for (const [slot, modelId] of Object.entries(slotMap)) {
      if (modelId) {
        defaultSlots[modelId] = slot;
      }
    }
  }

  return (
    <>
      <div className="border rounded-lg p-3 space-y-2" data-testid="credential-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-medium truncate">{credential.name}</span>
            <div className="flex gap-1">
              {credential.modalities.map((modality) => (
                <Badge
                  key={modality}
                  variant="secondary"
                  className={`text-[10px] gap-0.5 px-1 py-0 ${
                    activeTypes.has(modality as ModelType)
                      ? TYPE_COLORS[modality as ModelType] || ""
                      : TYPE_COLOR_INACTIVE
                  }`}
                >
                  {TYPE_ICONS[modality as ModelType]}
                  <span className="hidden sm:inline">
                    {TYPE_LABELS[modality as ModelType] || modality}
                  </span>
                </Badge>
              ))}
            </div>
            {credential.has_api_key && (
              <Badge variant="outline" className="text-[10px]">
                <Key className="h-2.5 w-2.5 mr-0.5" />
                Key
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {testResult &&
              (testResult.success ? (
                <Check className="h-4 w-4 text-emerald-500" />
              ) : (
                <X className="h-4 w-4 text-destructive" />
              ))}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => testCredential(credential.id)}
              disabled={isTestPending}
              title={t.apiKeys.testConnection}
            >
              {isTestPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plug className="h-4 w-4" />
              )}
              <span className="hidden sm:inline text-xs">Test</span>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              data-testid="credential-sync-models"
              onClick={() => setDiscoverOpen(true)}
              title={t.apiKeys.syncModels}
            >
              <Bot className="h-4 w-4" />
              <span className="hidden sm:inline text-xs">Models</span>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setEditOpen(true)}
              title={t.common.edit}
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              data-testid="credential-delete"
              onClick={() => setDeleteOpen(true)}
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
              title={t.common.delete}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {linkedModels.length > 0 && (
          <div className="space-y-1.5 pt-1">
            {(["language", "embedding", "text_to_speech", "speech_to_text"] as ModelType[])
              .filter((type) => linkedModels.some((model) => model.type === type))
              .map((type) => (
                <div key={type} className="flex items-start gap-1.5">
                  <Badge
                    variant="outline"
                    className={`text-[10px] gap-0.5 px-1 py-0 shrink-0 mt-0.5 ${TYPE_COLORS[type]}`}
                  >
                    {TYPE_ICONS[type]}
                    {TYPE_LABELS[type]}
                  </Badge>
                  <div className="flex flex-wrap gap-1">
                    {linkedModels
                      .filter((model) => model.type === type)
                      .map((model) => {
                        const defaultSlot = defaultSlots[model.id];
                        return (
                          <Badge
                            key={model.id}
                            variant={defaultSlot ? "default" : "secondary"}
                            className="text-xs gap-1 pr-0.5 group/model"
                          >
                            {model.name}
                            {defaultSlot && (
                              <span className="ml-0.5 opacity-75">({defaultSlot})</span>
                            )}
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="ml-0.5 h-5 w-5 opacity-0 group-hover/model:opacity-60 hover:!opacity-100 transition-opacity"
                              onClick={() => testModel(model.id, model.name)}
                              disabled={isModelTestPending && testingModelId === model.id}
                              title={testModelLabel}
                            >
                              {isModelTestPending && testingModelId === model.id ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <Plug className="h-3 w-3" />
                              )}
                            </Button>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-5 w-5 opacity-0 group-hover/model:opacity-60 hover:!opacity-100 hover:text-destructive transition-opacity"
                              onClick={() => deleteModel.mutate(model.id)}
                              title={deleteModelLabel}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </Badge>
                        );
                      })}
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>

      {editOpen && (
        <CredentialFormDialog
          open={editOpen}
          onOpenChange={setEditOpen}
          provider={credential.provider}
          credential={fullCredential || credential}
        />
      )}

      {deleteOpen && (
        <DeleteCredentialDialog
          open={deleteOpen}
          onOpenChange={setDeleteOpen}
          credential={credential}
          allCredentials={allCredentials}
        />
      )}

      {discoverOpen && (
        <DiscoverModelsDialog
          open={discoverOpen}
          onOpenChange={setDiscoverOpen}
          credential={credential}
        />
      )}

      <ModelTestResultDialog
        open={modelTestResult !== null}
        onOpenChange={(open) => {
          if (!open) {
            clearModelTestResult();
          }
        }}
        result={modelTestResult}
        modelName={testedModelName}
      />
    </>
  );
}

interface ProviderSectionProps {
  provider: string;
  credentials: Credential[];
  models: Model[];
  defaults: ModelDefaults | null;
  allCredentials: Credential[];
  encryptionReady: boolean;
}

export function ProviderSection({
  provider,
  credentials,
  models,
  defaults,
  allCredentials,
  encryptionReady,
}: ProviderSectionProps) {
  const { t } = useTranslation();
  const [addOpen, setAddOpen] = useState(false);

  const displayName = PROVIDER_DISPLAY_NAMES[provider] || provider;
  const modalities = PROVIDER_MODALITIES[provider] || ["language"];
  const hasCredentials = credentials.length > 0;

  const providerModels = models.filter((model) =>
    credentials.some((cred) => cred.id === model.credential),
  );
  const activeTypes = new Set(providerModels.map((model) => model.type));

  return (
    <Card className={!hasCredentials ? "opacity-80" : undefined}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-wrap">
            <CardTitle className="text-lg capitalize">{displayName}</CardTitle>
            <div className="flex items-center gap-1">
              {modalities.map((type) => (
                <Badge
                  key={type}
                  variant="secondary"
                  className={`text-xs gap-1 ${activeTypes.has(type) ? TYPE_COLORS[type] : TYPE_COLOR_INACTIVE}`}
                >
                  {TYPE_ICONS[type]}
                  <span className="hidden sm:inline">{TYPE_LABELS[type]}</span>
                </Badge>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {hasCredentials ? (
              <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-300">
                <Check className="mr-1 h-3 w-3" />
                {t.apiKeys.configured}
              </Badge>
            ) : (
              <Badge variant="outline" className="text-muted-foreground border-dashed">
                <X className="mr-1 h-3 w-3" />
                {t.apiKeys.notConfigured}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {credentials.map((credential) => (
          <CredentialItem
            key={credential.id}
            credential={credential}
            models={models}
            defaults={defaults}
            allCredentials={allCredentials}
          />
        ))}

        <Button
          variant="outline"
          size="sm"
          onClick={() => setAddOpen(true)}
          className="w-full gap-2"
          disabled={!encryptionReady}
        >
          <Plus className="h-4 w-4" />
          {t.apiKeys.addConfig}
        </Button>
      </CardContent>

      {addOpen && (
        <CredentialFormDialog open={addOpen} onOpenChange={setAddOpen} provider={provider} />
      )}
    </Card>
  );
}
