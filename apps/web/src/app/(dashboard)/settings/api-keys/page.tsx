"use client";

import { AlertCircle, Key, ShieldAlert } from "lucide-react";
import { useMemo } from "react";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { AppShell } from "@/components/layout/AppShell";
import { MigrationBanner } from "@/components/settings";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import type { Credential } from "@/lib/api/credentials";
import { useCredentialStatus, useCredentials } from "@/lib/hooks/use-credentials";
import { useModelDefaults, useModels } from "@/lib/hooks/use-models";
import { useTranslation } from "@/lib/hooks/use-translation";
import { getRepositoryBlobUrl } from "@/lib/repo-links";
import { ALL_PROVIDERS } from "./constants";
import { DefaultModelSelectors } from "./default-model-selectors";
import { ProviderSection } from "./provider-section";

export default function ApiKeysPage() {
  const { t } = useTranslation();
  const providersDocsUrl = getRepositoryBlobUrl("docs/configuration.md");

  const { data: credentials, isLoading: credentialsLoading } = useCredentials();
  const { data: models, isLoading: modelsLoading } = useModels();
  const { data: defaults, isLoading: defaultsLoading } = useModelDefaults();
  const { data: credentialStatus } = useCredentialStatus();

  const encryptionReady = credentialStatus?.encryption_configured ?? true;

  const credentialsByProvider = useMemo(() => {
    const grouped: Record<string, Credential[]> = {};
    for (const provider of ALL_PROVIDERS) {
      grouped[provider] = [];
    }
    if (credentials) {
      for (const credential of credentials) {
        if (!grouped[credential.provider]) {
          grouped[credential.provider] = [];
        }
        grouped[credential.provider].push(credential);
      }
    }
    return grouped;
  }, [credentials]);

  const providersWithLegacyEnv = useMemo(() => {
    if (!credentialStatus) {
      return [];
    }
    return Object.entries(credentialStatus.legacy_env_detected || {})
      .filter(([, detected]) => detected)
      .map(([provider]) => provider);
  }, [credentialStatus]);

  const sortedProviders = useMemo(() => {
    return [...ALL_PROVIDERS].sort((a, b) => {
      const aHas = (credentialsByProvider[a]?.length || 0) > 0 ? 1 : 0;
      const bHas = (credentialsByProvider[b]?.length || 0) > 0 ? 1 : 0;
      return bHas - aHas;
    });
  }, [credentialsByProvider]);

  const isLoading = credentialsLoading || modelsLoading || defaultsLoading;
  if (isLoading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-[60vh]">
          <LoadingSpinner size="lg" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div
          className="ui-page-shell p-6 space-y-6"
          data-testid="a11y-route-settings-api-keys-ready"
        >
          <div className="ui-section-enter">
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Key className="h-6 w-6" />
              {t.apiKeys.title}
            </h1>
            <p className="text-muted-foreground mt-1">{t.apiKeys.description}</p>
          </div>

          {!encryptionReady && (
            <Alert variant="destructive" className="ui-section-enter bg-destructive/10">
              <ShieldAlert className="h-4 w-4" />
              <AlertTitle>{t.apiKeys.encryptionRequired}</AlertTitle>
              <AlertDescription>
                <code className="text-xs bg-destructive/15 px-1 py-0.5 rounded">
                  {t.apiKeys.encryptionRequiredDescription}
                </code>
              </AlertDescription>
            </Alert>
          )}

          {encryptionReady && (
            <div className="ui-section-enter">
              <MigrationBanner providersWithLegacyEnv={providersWithLegacyEnv} />
            </div>
          )}

          {providersWithLegacyEnv.length > 0 && (
            <Alert variant="destructive" className="ui-section-enter bg-destructive/10">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>{t.apiKeys.legacyEnvDetectedTitle}</AlertTitle>
              <AlertDescription>
                {t.apiKeys.legacyEnvDetectedDescription.replace(
                  "{providers}",
                  providersWithLegacyEnv.join(", "),
                )}
              </AlertDescription>
            </Alert>
          )}

          {models && defaults && providersWithLegacyEnv.length === 0 && (
            <div className="ui-section-enter">
              <DefaultModelSelectors models={models} defaults={defaults} />
            </div>
          )}

          {providersWithLegacyEnv.length === 0 && (
            <div className="ui-section-enter grid gap-4">
              {sortedProviders.map((provider) => (
                <ProviderSection
                  key={provider}
                  provider={provider}
                  credentials={credentialsByProvider[provider] || []}
                  models={models || []}
                  defaults={defaults || null}
                  allCredentials={credentials || []}
                  encryptionReady={encryptionReady}
                />
              ))}
            </div>
          )}

          {providersDocsUrl && (
            <div className="ui-section-enter border-t pt-4">
              <a
                href={providersDocsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline"
              >
                {t.apiKeys.learnMore}
              </a>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
