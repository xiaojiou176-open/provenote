"use client";

import { AlertTriangle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useTranslation } from "@/lib/hooks/use-translation";

interface MigrationBannerProps {
  providersWithLegacyEnv: string[];
}

export function MigrationBanner({ providersWithLegacyEnv }: MigrationBannerProps) {
  const { t } = useTranslation();

  if (providersWithLegacyEnv.length === 0) {
    return null;
  }

  return (
    <Alert variant="destructive">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>{t.apiKeys.legacyEnvDetectedTitle}</AlertTitle>
      <AlertDescription>
        {t.apiKeys.legacyEnvDetectedDescription.replace(
          "{providers}",
          providersWithLegacyEnv.join(", "),
        )}
      </AlertDescription>
    </Alert>
  );
}
