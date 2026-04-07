"use client";

import { RefreshCw } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/button";
import { useSettings } from "@/lib/hooks/use-settings";
import { useTranslation } from "@/lib/hooks/use-translation";
import { SettingsForm } from "./components/SettingsForm";

export default function SettingsPage() {
  const { t } = useTranslation();
  const { refetch } = useSettings();

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="ui-page-shell p-6">
          <div className="max-w-4xl">
            <div className="ui-section-enter flex items-center gap-4 mb-6">
              <h1 className="text-2xl font-bold">{t.navigation.settings}</h1>
              <Button
                variant="outline"
                size="sm"
                className="ui-icon-button"
                data-testid="settings-refresh"
                onClick={() => refetch()}
                aria-label={t.common.refresh}
                title={t.common.refresh}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>

            <div className="ui-section-enter">
              <SettingsForm />
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
