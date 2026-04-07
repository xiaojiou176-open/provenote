"use client";

import { AlertCircle, Loader2, Plus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type {
  CreateCredentialRequest,
  Credential,
  DiscoveredModel,
  UpdateCredentialRequest,
} from "@/lib/api/credentials";
import {
  useCreateCredential,
  useDeleteCredential,
  useDiscoverModels,
  useRegisterModels,
  useUpdateCredential,
} from "@/lib/hooks/use-credentials";
import { useTranslation } from "@/lib/hooks/use-translation";

import {
  type ModelType,
  PROVIDER_DISPLAY_NAMES,
  PROVIDER_DOCS,
  PROVIDER_MODALITIES,
  TYPE_ICONS,
  TYPE_LABELS,
} from "./constants";

interface CredentialFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  provider: string;
  credential?: Credential | null;
}

export function CredentialFormDialog({
  open,
  onOpenChange,
  provider,
  credential,
}: CredentialFormDialogProps) {
  const { t } = useTranslation();
  const createCredential = useCreateCredential();
  const updateCredential = useUpdateCredential();
  const isEditing = Boolean(credential);
  const isSubmitting = createCredential.isPending || updateCredential.isPending;

  const isVertex = provider === "vertex";
  const isOllama = provider === "ollama";
  const isOpenAICompatible = provider === "openai_compatible";
  const requiresApiKey = !isVertex && !isOllama && !isOpenAICompatible;

  const [name, setName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [project, setProject] = useState("");
  const [location, setLocation] = useState("");
  const [credentialsPath, setCredentialsPath] = useState("");
  const [modalities, setModalities] = useState<string[]>([]);

  useEffect(() => {
    if (credential) {
      setName(credential.name || "");
      setBaseUrl(credential.base_url || "");
      setApiKey("");
      setProject(credential.project || "");
      setLocation(credential.location || "");
      setCredentialsPath(credential.credentials_path || "");
      setModalities(credential.modalities || []);
      return;
    }

    setName("");
    setBaseUrl("");
    setApiKey("");
    setProject("");
    setLocation("");
    setCredentialsPath("");
    setModalities(PROVIDER_MODALITIES[provider] || ["language"]);
  }, [credential, provider]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const onSuccess = () => {
      onOpenChange(false);
    };

    if (isEditing && credential) {
      const data: UpdateCredentialRequest = {};
      if (name !== credential.name) {
        data.name = name;
      }
      if (apiKey.trim()) {
        data.api_key = apiKey.trim();
      }
      if (baseUrl !== (credential.base_url || "")) {
        data.base_url = baseUrl || undefined;
      }
      if (JSON.stringify(modalities) !== JSON.stringify(credential.modalities)) {
        data.modalities = modalities;
      }
      if (isVertex) {
        if (project !== (credential.project || "")) {
          data.project = project.trim() || undefined;
        }
        if (location !== (credential.location || "")) {
          data.location = location.trim() || undefined;
        }
        if (credentialsPath !== (credential.credentials_path || "")) {
          data.credentials_path = credentialsPath.trim() || undefined;
        }
      }
      updateCredential.mutate({ credentialId: credential.id, data }, { onSuccess });
      return;
    }

    const data: CreateCredentialRequest = {
      name: name || `${PROVIDER_DISPLAY_NAMES[provider] || provider} Config`,
      provider,
      modalities,
      api_key: apiKey.trim() || undefined,
      base_url: baseUrl || undefined,
    };
    if (isVertex) {
      data.project = project.trim() || undefined;
      data.location = location.trim() || undefined;
      data.credentials_path = credentialsPath.trim() || undefined;
    }
    createCredential.mutate(data, { onSuccess });
  };

  const isValid = isEditing
    ? true
    : isVertex
      ? name.trim() !== "" && project.trim() !== "" && location.trim() !== ""
      : name.trim() !== "" && (!requiresApiKey || apiKey.trim() !== "");

  const docsUrl = PROVIDER_DOCS[provider];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEditing
              ? t.apiKeys.editConfig.replace(
                  "{provider}",
                  PROVIDER_DISPLAY_NAMES[provider] || provider,
                )
              : t.apiKeys.addConfig.replace(
                  "{provider}",
                  PROVIDER_DISPLAY_NAMES[provider] || provider,
                )}
          </DialogTitle>
          <DialogDescription>{t.apiKeys.configNameHint}</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="cred-name">{t.apiKeys.configName}</Label>
            <Input
              id="cred-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={`${PROVIDER_DISPLAY_NAMES[provider] || provider} Production`}
              disabled={isSubmitting}
            />
            <p className="text-xs text-muted-foreground">{t.apiKeys.configNameHint}</p>
          </div>

          {isVertex ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="vertex-project">{t.apiKeys.vertexProject}</Label>
                <Input
                  id="vertex-project"
                  value={project}
                  onChange={(e) => setProject(e.target.value)}
                  placeholder="my-gcp-project"
                  disabled={isSubmitting}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="vertex-location">{t.apiKeys.vertexLocation}</Label>
                <Input
                  id="vertex-location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="us-central1"
                  disabled={isSubmitting}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="vertex-creds">
                  {t.apiKeys.vertexCredentials}
                  <span className="text-muted-foreground font-normal ml-1">
                    ({t.common.optional})
                  </span>
                </Label>
                <Input
                  id="vertex-creds"
                  value={credentialsPath}
                  onChange={(e) => setCredentialsPath(e.target.value)}
                  placeholder="/path/to/service-account.json"
                  disabled={isSubmitting}
                />
              </div>
            </>
          ) : (
            <div className="space-y-2">
              <Label htmlFor="api-key">
                {t.models.apiKey}
                {!requiresApiKey && (
                  <span className="text-muted-foreground font-normal ml-1">
                    ({t.common.optional})
                  </span>
                )}
              </Label>
              <div className="relative">
                <Input
                  id="api-key"
                  type={showApiKey ? "text" : "password"}
                  className="pr-10"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={isEditing ? "••••••••••••" : "sk-..."}
                  disabled={isSubmitting}
                  autoComplete="off"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-1 top-1/2 h-8 -translate-y-1/2 px-2 text-xs text-muted-foreground hover:text-foreground"
                  aria-label={showApiKey ? "Hide API key" : "Show API key"}
                  title={showApiKey ? "Hide API key" : "Show API key"}
                  aria-pressed={showApiKey}
                >
                  {showApiKey ? "Hide" : "Show"}
                </Button>
              </div>
              {isEditing && (
                <p className="text-xs text-muted-foreground">{t.apiKeys.apiKeyEditHint}</p>
              )}
              {docsUrl && (
                <a
                  href={docsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline"
                >
                  {t.apiKeys.getApiKey} &rarr;
                </a>
              )}
            </div>
          )}

          {!isVertex && (
            <div className="space-y-2">
              <Label htmlFor="base-url" className="text-muted-foreground">
                {t.apiKeys.baseUrl}
              </Label>
              <Input
                id="base-url"
                type="url"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder={
                  isOllama ? "http://localhost:11434" : "https://services.api.example.com/v1"
                }
                disabled={isSubmitting}
              />
              <p className="text-xs text-muted-foreground">{t.apiKeys.baseUrlOverrideHint}</p>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              {t.common.cancel}
            </Button>
            <Button type="submit" disabled={!isValid || isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              {isEditing ? t.common.save : t.apiKeys.addConfig}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

interface DiscoverModelsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  credential: Credential;
}

export function DiscoverModelsDialog({
  open,
  onOpenChange,
  credential,
}: DiscoverModelsDialogProps) {
  const { t } = useTranslation();
  const discoverModels = useDiscoverModels();
  const registerModels = useRegisterModels();
  const [discoveredModels, setDiscoveredModels] = useState<DiscoveredModel[]>([]);
  const [selectedModels, setSelectedModels] = useState<Set<string>>(new Set());
  const [hasDiscovered, setHasDiscovered] = useState(false);
  const [discoveryError, setDiscoveryError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [customModelSelected, setCustomModelSelected] = useState(false);
  const [selectedType, setSelectedType] = useState<ModelType>(
    (credential.modalities[0] as ModelType) || "language",
  );

  useEffect(() => {
    if (open && !hasDiscovered) {
      setDiscoveryError(null);
      discoverModels.mutate(credential.id, {
        onSuccess: (result) => {
          const seen = new Set<string>();
          const unique = result.discovered.filter((model) => {
            if (seen.has(model.name)) {
              return false;
            }
            seen.add(model.name);
            return true;
          });
          setDiscoveredModels(unique);
          setSelectedModels(new Set());
          setHasDiscovered(true);
        },
        onError: (error: unknown) => {
          setHasDiscovered(true);
          const msg = error instanceof Error ? error.message : String(error);
          setDiscoveryError(msg);
        },
      });
    }

    if (!open) {
      setHasDiscovered(false);
      setDiscoveredModels([]);
      setSelectedModels(new Set());
      setDiscoveryError(null);
      setSearchQuery("");
      setCustomModelSelected(false);
      setSelectedType((credential.modalities[0] as ModelType) || "language");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentionally only fires on open/close
  }, [open, credential.id, credential.modalities[0], discoverModels.mutate, hasDiscovered]);

  useEffect(() => {
    setCustomModelSelected(false);
  }, []);

  const filteredModels = useMemo(() => {
    if (!searchQuery.trim()) {
      return discoveredModels;
    }
    const query = searchQuery.toLowerCase();
    return discoveredModels.filter((model) => model.name.toLowerCase().includes(query));
  }, [discoveredModels, searchQuery]);

  const showCustomOption = useMemo(() => {
    if (!searchQuery.trim()) {
      return false;
    }
    const query = searchQuery.trim().toLowerCase();
    return !discoveredModels.some((model) => model.name.toLowerCase() === query);
  }, [discoveredModels, searchQuery]);

  const handleRegister = () => {
    const selected = discoveredModels
      .filter((model) => selectedModels.has(model.name))
      .map((model) => ({
        name: model.name,
        provider: model.provider,
        model_type: selectedType,
      }));

    if (customModelSelected && showCustomOption) {
      selected.push({
        name: searchQuery.trim(),
        provider: credential.provider,
        model_type: selectedType,
      });
    }

    registerModels.mutate(
      { credentialId: credential.id, models: selected },
      { onSuccess: () => onOpenChange(false) },
    );
  };

  const totalSelected = selectedModels.size + (customModelSelected && showCustomOption ? 1 : 0);

  const toggleModel = (name: string) => {
    setSelectedModels((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const toggleAll = () => {
    const filteredNames = filteredModels.map((model) => model.name);
    const allFilteredSelected = filteredNames.every((name) => selectedModels.has(name));

    if (allFilteredSelected) {
      setSelectedModels((prev) => {
        const next = new Set(prev);
        filteredNames.forEach((name) => next.delete(name));
        return next;
      });
      return;
    }

    setSelectedModels((prev) => {
      const next = new Set(prev);
      filteredNames.forEach((name) => next.add(name));
      return next;
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {t.models.discoverModels} -{" "}
            {PROVIDER_DISPLAY_NAMES[credential.provider] || credential.provider}
          </DialogTitle>
          <DialogDescription>{credential.name}</DialogDescription>
        </DialogHeader>

        {discoverModels.isPending ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : discoveryError ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{discoveryError}</AlertDescription>
          </Alert>
        ) : (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>{t.models.modelType}</Label>
              <Select
                value={selectedType}
                onValueChange={(value) => setSelectedType(value as ModelType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(
                    PROVIDER_MODALITIES[credential.provider] ||
                    (credential.modalities as ModelType[])
                  ).map((type) => (
                    <SelectItem key={type} value={type}>
                      <div className="flex items-center gap-2">
                        {TYPE_ICONS[type]}
                        {TYPE_LABELS[type]}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">{t.models.modelTypeHint}</p>
            </div>

            <Input
              type="text"
              placeholder={t.models.searchOrAddModel}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />

            {filteredModels.length > 0 && (
              <div className="flex items-center justify-between">
                <Button variant="outline" size="sm" onClick={toggleAll}>
                  {filteredModels.every((model) => selectedModels.has(model.name))
                    ? t.common.remove
                    : t.common.addSelected}{" "}
                  ({selectedModels.size}/{filteredModels.length})
                </Button>
              </div>
            )}

            <div className="space-y-1 max-h-60 overflow-y-auto">
              {filteredModels.map((model) => (
                <label
                  key={model.name}
                  className="flex items-center gap-2 p-1.5 rounded hover:bg-muted cursor-pointer text-sm"
                >
                  <Checkbox
                    checked={selectedModels.has(model.name)}
                    onCheckedChange={() => toggleModel(model.name)}
                  />
                  <span className="truncate">{model.name}</span>
                  {model.description && model.description !== model.name && (
                    <span className="text-xs text-muted-foreground truncate">
                      ({model.description})
                    </span>
                  )}
                </label>
              ))}

              {showCustomOption && (
                <label
                  className={`flex items-center gap-2 p-1.5 rounded hover:bg-muted cursor-pointer text-sm${
                    filteredModels.length > 0 ? " border-t mt-1 pt-2" : ""
                  }`}
                >
                  <Checkbox
                    checked={customModelSelected}
                    onCheckedChange={(checked) => setCustomModelSelected(Boolean(checked))}
                  />
                  <Plus className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  <span className="truncate">
                    {t.models.addCustomModel.replace("{name}", searchQuery.trim())}
                  </span>
                </label>
              )}

              {filteredModels.length === 0 && !showCustomOption && (
                <p className="text-center py-4 text-muted-foreground text-sm">
                  {t.models.noModelsFound}
                </p>
              )}
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t.common.cancel}
          </Button>
          <Button
            onClick={handleRegister}
            disabled={totalSelected === 0 || registerModels.isPending}
          >
            {registerModels.isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
            {t.common.add} ({totalSelected})
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

interface DeleteCredentialDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  credential: Credential;
  allCredentials: Credential[];
}

export function DeleteCredentialDialog({
  open,
  onOpenChange,
  credential,
  allCredentials,
}: DeleteCredentialDialogProps) {
  const { t } = useTranslation();
  const deleteCredential = useDeleteCredential();
  const [migrateToId, setMigrateToId] = useState<string>("");

  const otherCredentials = allCredentials.filter(
    (item) => item.id !== credential.id && item.provider === credential.provider,
  );

  const handleDeleteWithModels = () => {
    deleteCredential.mutate(
      { credentialId: credential.id, options: { delete_models: true } },
      { onSuccess: () => onOpenChange(false) },
    );
  };

  const handleMigrate = () => {
    if (!migrateToId) {
      return;
    }
    deleteCredential.mutate(
      { credentialId: credential.id, options: { migrate_to: migrateToId } },
      { onSuccess: () => onOpenChange(false) },
    );
  };

  const handleDeleteOnly = () => {
    deleteCredential.mutate(
      { credentialId: credential.id },
      { onSuccess: () => onOpenChange(false) },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t.apiKeys.deleteConfig}</DialogTitle>
          <DialogDescription>
            {t.apiKeys.deleteConfigConfirm.replace("{name}", credential.name)}
          </DialogDescription>
        </DialogHeader>

        {credential.model_count > 0 && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              This credential has {credential.model_count} linked model(s).
              {otherCredentials.length > 0 && (
                <div className="mt-2">
                  <Label>Migrate models to:</Label>
                  <Select value={migrateToId} onValueChange={setMigrateToId}>
                    <SelectTrigger className="mt-1">
                      <SelectValue placeholder="Select credential" />
                    </SelectTrigger>
                    <SelectContent>
                      {otherCredentials.map((item) => (
                        <SelectItem key={item.id} value={item.id}>
                          {item.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </AlertDescription>
          </Alert>
        )}

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t.common.cancel}
          </Button>
          {credential.model_count > 0 && migrateToId && (
            <Button onClick={handleMigrate} disabled={deleteCredential.isPending}>
              {deleteCredential.isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Migrate & Delete
            </Button>
          )}
          <Button
            variant="destructive"
            onClick={credential.model_count > 0 ? handleDeleteWithModels : handleDeleteOnly}
            disabled={deleteCredential.isPending}
          >
            {deleteCredential.isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
            {credential.model_count > 0 ? "Delete with Models" : t.common.delete}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
