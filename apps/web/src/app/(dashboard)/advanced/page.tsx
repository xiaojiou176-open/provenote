"use client";

import { AppShell } from "@/components/layout/AppShell";
import { useTranslation } from "@/lib/hooks/use-translation";
import { RebuildEmbeddings } from "./components/RebuildEmbeddings";
import { SystemInfo } from "./components/SystemInfo";

export default function AdvancedPage() {
  const { t } = useTranslation();
  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="ui-page-shell p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="ui-section-enter" data-testid="a11y-route-advanced-ready">
              <h1 className="text-3xl font-bold">{t.advanced.title}</h1>
              <p className="text-muted-foreground mt-2">{t.advanced.desc}</p>
            </div>

            <div className="ui-section-enter">
              <SystemInfo />
            </div>
            <div className="ui-section-enter">
              <RebuildEmbeddings />
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
