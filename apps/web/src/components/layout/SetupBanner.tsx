"use client";

import { AlertTriangle, ArrowRight, ExternalLink, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { useMemo } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useCredentialStatus } from "@/lib/hooks/use-credentials";
import { useTranslation } from "@/lib/hooks/use-translation";
import { getRepositoryBlobUrl } from "@/lib/repo-links";

export function SetupBanner() {
  const { t } = useTranslation();
  const { data: credentialStatus } = useCredentialStatus();
  const encryptionDocsUrl = getRepositoryBlobUrl("docs/configuration.md");

  const encryptionReady = credentialStatus?.encryption_configured ?? true;

  const providersWithLegacyEnv = useMemo(() => {
    if (!credentialStatus) {
      return [];
    }
    return Object.entries(credentialStatus.legacy_env_detected || {})
      .filter(([, detected]) => detected)
      .map(([provider]) => provider);
  }, [credentialStatus]);

  if (encryptionReady && providersWithLegacyEnv.length === 0) {
    return null;
  }

  if (!encryptionReady) {
    return (
      <div className="px-4 pt-3">
        <Alert
          variant="destructive"
          className="ui-setup-banner rounded-[1.25rem] border-destructive/30 bg-destructive/5 shadow-none"
        >
          <ShieldAlert className="h-4 w-4" />
          <AlertTitle className="font-serif text-xl tracking-[-0.03em]">
            {t.setupBanner.encryptionRequired}
          </AlertTitle>
          <AlertDescription className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <span>{t.setupBanner.encryptionRequiredDescription}</span>
            {encryptionDocsUrl ? (
              <a
                href={encryptionDocsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center shrink-0 text-sm font-medium underline underline-offset-2 hover:text-foreground"
              >
                {t.setupBanner.viewDocs}
                <ExternalLink className="ml-1 h-3 w-3" />
              </a>
            ) : null}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="px-4 pt-3">
      <Alert
        variant="destructive"
        className="ui-setup-banner rounded-[1.25rem] border-destructive/30 bg-destructive/5 shadow-none"
      >
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle className="font-serif text-xl tracking-[-0.03em]">
          {t.setupBanner.legacyEnvBlockedTitle}
        </AlertTitle>
        <AlertDescription className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span>
            {t.setupBanner.legacyEnvBlockedDescription.replace(
              "{count}",
              String(providersWithLegacyEnv.length),
            )}
          </span>
          <Button
            variant="outline"
            size="sm"
            asChild
            className="ui-icon-button shrink-0 border-destructive/50 text-destructive hover:bg-destructive/5"
          >
            <Link href="/settings/api-keys">
              {t.setupBanner.openApiKeys}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </AlertDescription>
      </Alert>
    </div>
  );
}
